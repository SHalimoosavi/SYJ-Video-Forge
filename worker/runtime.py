"""Job orchestration, incremental manifest, resume and smoke test."""
from __future__ import annotations
import hashlib, importlib.metadata, json, os, platform, shutil, subprocess, threading, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .engines import create_engine, FakeEngine
from .engines.base import Engine, EngineError
from .media import ffmpeg_path, frame_luma_stats, write_mp4, extract_last_frame, stitch
from .planning import plan_scenes, scene_seed
from .schema import BundleError, load_job, new_manifest, sha256_bytes, write_json_atomic

def _version(name):
    try: return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError: return "not installed"

def _decode_image(job, out: Path):
    rec=job.get("image")
    if not rec: return None
    import base64
    raw=base64.b64decode(rec["base64"])
    p=out/"input-image.bin"; p.write_bytes(raw)
    try:
        from PIL import Image
        image=Image.open(p).convert("RGB")
        p.unlink(missing_ok=True)
        return image
    except Exception as exc: raise EngineError(f"Could not decode starting image: {exc}") from exc

def _sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def _merge_hardware(manifest, hardware):
    old_peak=manifest.get("hardware",{}).get("vram_peak_bytes")
    new_peak=hardware.get("vram_peak_bytes")
    manifest.setdefault("hardware",{}).update(hardware)
    peaks=[int(x) for x in (old_peak,new_peak) if isinstance(x,(int,float)) and x>0]
    manifest["hardware"]["vram_peak_bytes"]=max(peaks) if peaks else None

def _job_fingerprint(job, engine_id):
    # Resume only when all generation-relevant inputs are unchanged.
    payload = {
        "job": job,
        "engine": engine_id,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _load_existing_manifest(path, job, engine_id):
    if not path.exists():
        return None
    try:
        m = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(m, dict):
        return None
    if m.get("schemaVersion") != 1 or m.get("jobId") != job["jobId"]:
        return None
    if m.get("jobFingerprint") != _job_fingerprint(job, engine_id):
        return None
    if not isinstance(m.get("scenes"), list):
        return None
    return m

def run_job(job_path: str | Path, out_dir: str | Path, engine_id: str | None=None, resume: bool=False,
            cancel_event: threading.Event | None=None, progress_cb=None, engine_override: Engine | None=None) -> dict:
    job=load_job(job_path); out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    if cancel_event is None: cancel_event=threading.Event()
    if progress_cb is None: progress_cb=lambda *_:None
    selected=engine_id or job["engine"]["id"]
    engine=engine_override or create_engine(selected)
    if engine.kind=="test_pattern" and engine_override is None: raise EngineError("FakeEngine is test-only and cannot be selected for normal CLI inference")
    caps=engine.capabilities
    clip_seconds=int(job.get("clipSeconds",5))
    plans=plan_scenes(job["totalSeconds"],clip_seconds,int(job["fps"]),caps["frame_rule"])
    scene_prompts={s["index"]:s["prompt"] for s in job["scenes"]}
    manifest_path=out/"manifest.json"
    fingerprint = _job_fingerprint(job, selected)
    previous = _load_existing_manifest(manifest_path, job, selected) if resume else None
    manifest = previous or new_manifest(job, {"id": engine.id, "model": engine.model_id, "revision": None, "license": engine.license_info})
    manifest["jobFingerprint"] = fingerprint
    manifest["kind"]=engine.kind
    manifest["engine"]={"id":engine.id,"model":engine.model_id,"revision":None,"license":engine.license_info}
    manifest["libraries"]={"python":platform.python_version(),"torch":_version("torch"),"diffusers":_version("diffusers"),"transformers":_version("transformers"),"accelerate":_version("accelerate"),"imageio":_version("imageio"),"imageio-ffmpeg":_version("imageio-ffmpeg")}
    manifest["parameters"]={"steps":int(job.get("steps",8)),"fps":int(job["fps"]),"resolution":job["resolution"],"continuity":job.get("continuity","last_frame"),"baseSeed":job["seed"],"clipSeconds":clip_seconds,"negativePrompt":job.get("negativePrompt","")}
    manifest["status"]="running"; manifest["final"]=None
    (out/"result.mp4").unlink(missing_ok=True)
    scenes_dir=out/"scenes"; scenes_dir.mkdir(exist_ok=True)
    records={int(x.get("index",0)):x for x in manifest.get("scenes",[]) if isinstance(x,dict)}
    # Derive dimensions only from the job's documented resolution target.
    width,height=map(int,job["resolution"].split("x"))
    if isinstance(engine, FakeEngine): width,height=engine.width,engine.height
    engine.width,engine.height=width,height
    engine.negative_prompt=job.get("negativePrompt", "")
    start=time.monotonic(); clip_paths=[]
    write_json_atomic(manifest_path,manifest)
    try:
        start_image=_decode_image(job,out)
        engine._want_image=(start_image is not None)
        engine.load()
        _merge_hardware(manifest,engine.hardware)
        if engine.kind=="test_pattern": manifest["warnings"].append("TEST PATTERN: not AI generated")
        write_json_atomic(manifest_path,manifest)
        for plan in plans:
            if cancel_event.is_set(): raise EngineError("Job cancelled")
            idx=plan["index"]; clip=scenes_dir/f"scene-{idx:03d}.mp4"; rec=records.get(idx)
            if resume and rec and clip.is_file() and rec.get("sha256")==_sha(clip):
                clip_paths.append(clip); progress_cb(idx,len(plans),"resumed")
                continue
            if idx>1 and job.get("continuity","last_frame")=="last_frame":
                last=scenes_dir/f"scene-{idx-1:03d}-last.png"
                if clip_paths: extract_last_frame(clip_paths[-1],last)
                if last.exists():
                    try:
                        from PIL import Image
                        start_image=Image.open(last).convert("RGB")
                    except Exception: start_image=None
            elif idx>1 and job.get("continuity")=="none": start_image=None
            t0=time.monotonic(); frames=engine.generate_clip(scene_prompts.get(idx,job["prompt"]),start_image,plan["frames"],scene_seed(job["seed"],idx),int(job.get("steps",8)),cancel_event,lambda _p:progress_cb(idx,len(plans),"generating"))
            metrics=frame_luma_stats(frames,width,height)
            check={"scene":idx,**metrics}; manifest.setdefault("degenerateChecks",[]).append(check)
            if metrics.get("degenerate"):
                rec={"index":idx,"seed":scene_seed(job["seed"],idx),"frames":plan["frames"],"seconds":plan["seconds"],"file":str(clip.relative_to(out)).replace("\\","/"),"sha256":None,"gen_seconds":round(time.monotonic()-t0,3),"luma":metrics,"status":"failed_degenerate"}
                records[idx]=rec; manifest["scenes"]=[records[k] for k in sorted(records)]; manifest["warnings"].append(f"Scene {idx} rejected by degenerate-output guard: {metrics.get('reason')}. Check fp16/bf16 support and the engine's compute dtype."); write_json_atomic(manifest_path,manifest)
                raise EngineError(f"Scene {idx} rejected: {metrics.get('reason')}. This can indicate an fp16/bf16 or compute-dtype problem; output is not marked successful.")
            generated_frames = len(frames)
            target_scene_frames = int(plan["seconds"]) * int(job["fps"])
            if generated_frames < target_scene_frames:
                raise EngineError(
                    f"Scene {idx} produced {generated_frames} frames; "
                    f"{target_scene_frames} are required for its requested duration."
                )
            # Keep model-required frame counts for inference, but normalize each
            # encoded scene independently so the final scene is never tail-truncated.
            write_mp4(frames[:target_scene_frames],clip,width,height,int(job["fps"]))
            rec={"index":idx,"seed":scene_seed(job["seed"],idx),"frames":target_scene_frames,"generatedFrames":generated_frames,"seconds":plan["seconds"],"file":str(clip.relative_to(out)).replace("\\","/"),"sha256":_sha(clip),"gen_seconds":round(time.monotonic()-t0,3),"luma":metrics,"status":"completed"}
            records[idx]=rec; clip_paths.append(clip); manifest["scenes"]=[records[k] for k in sorted(records)]; _merge_hardware(manifest,engine.hardware); write_json_atomic(manifest_path,manifest)
            progress_cb(idx,len(plans),"completed")
        if len(clip_paths)!=len(plans): raise EngineError("Not all scenes completed; refusing to stitch a partial result")
        final=out/"result.mp4"; target_frames=int(job["totalSeconds"])*int(job["fps"]); meta=stitch(clip_paths,final,int(job["fps"]),width,height,target_frames)
        meta["sha256"]=_sha(final); meta["durationRequested"]=job["totalSeconds"]
        manifest["final"]=meta; manifest["timestamps"]["finishedAt"]=datetime.now(timezone.utc).isoformat(); manifest["elapsed_seconds"]=round(time.monotonic()-start,3)
        manifest["status"]="completed"; write_json_atomic(manifest_path,manifest)
        return manifest
    except Exception as exc:
        manifest["status"]="cancelled" if cancel_event.is_set() else "failed"; manifest["final"]=None; manifest.setdefault("warnings",[]).append(str(exc)); (out/"result.mp4").unlink(missing_ok=True); write_json_atomic(manifest_path,manifest); raise
    finally:
        try: engine.unload()
        except Exception: pass

def smoke_test(engine_id: str, out_dir: str | Path) -> dict:
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True); t0=time.monotonic(); errors=[]
    gpu={"name":"unavailable","vram_total_bytes":None,"compute_capability":"unknown"}
    try:
        import torch
        if torch.cuda.is_available():
            p=torch.cuda.get_device_properties(0); gpu={"name":p.name,"vram_total_bytes":int(p.total_memory),"compute_capability":".".join(map(str,torch.cuda.get_device_capability(0)))}
        else: gpu["name"]="CUDA unavailable"
    except Exception as exc: errors.append(f"torch/GPU inspection: {exc}")
    usage=shutil.disk_usage(out)
    report={"schemaVersion":1,"kind":"verification_report","status":"running","startedAt":datetime.now(timezone.utc).isoformat(),"python":platform.python_version(),"platform":platform.platform(),"gpu":gpu,"free_disk_bytes":usage.free,"ffmpeg":ffmpeg_path(),"libraries":{"torch":_version("torch"),"diffusers":_version("diffusers"),"transformers":_version("transformers"),"accelerate":_version("accelerate")},"engine":engine_id,"errors":errors,"warning":"UNVERIFIED ON REAL HARDWARE until a user-generated verification report is reviewed."}
    try:
        engine=create_engine(engine_id)
        # A one-scene low-resolution job, deliberately small and bounded.
        import secrets
        job={"schemaVersion":1,"jobId":secrets.token_hex(16),"createdAt":datetime.now(timezone.utc).isoformat(),"mode":"text","prompt":"A simple red ball on a plain neutral background, static camera","negativePrompt":"","aspect":"16:9","resolution":"512x288","seed":7,"totalSeconds":1,"fps":24,"preset":"Smoke test","clipSeconds":1,"continuity":"none","engine":{"id":engine_id},"steps":2,"scenes":[{"index":1,"prompt":"A simple red ball on a plain neutral background, static camera"}],"image":None}
        jobfile=out/"smoke-job.json"; write_json_atomic(jobfile,job)
        # smoke schema duration is 1s and the schema permits it; engine frame constraints still apply.
        result=run_job(jobfile,out/"smoke-job-output",engine_id,engine_override=engine)
        report["status"]="passed"; report["result_sha256"]=result["final"]["sha256"]; report["hardware"]=result.get("hardware",{})
    except Exception as exc:
        report["status"]="failed"; report["errors"].append(f"{type(exc).__name__}: {exc}")
    report["elapsed_seconds"]=round(time.monotonic()-t0,3); report["finishedAt"]=datetime.now(timezone.utc).isoformat()
    write_json_atomic(out/"smoke.json",report)
    return report
