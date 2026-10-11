"""Video IO and frame-health checks; optional media dependencies are lazy."""
from __future__ import annotations
import math, os, shutil, statistics, subprocess, tempfile
from pathlib import Path
from typing import Any
from .engines.base import EngineError

def ffmpeg_path() -> str | None:
    path=shutil.which("ffmpeg")
    if path: return path
    try:
        import imageio_ffmpeg
        candidate=imageio_ffmpeg.get_ffmpeg_exe()
        return candidate if Path(candidate).is_file() else None
    except Exception: return None

def ffprobe_path() -> str | None:
    path=shutil.which("ffprobe")
    if path: return path
    exe=ffmpeg_path()
    if exe:
        p=Path(exe); candidate=p.with_name("ffprobe" + p.suffix)
        if candidate.exists(): return str(candidate)
    return None

def _frame_bytes(frame: Any, width: int, height: int) -> bytes:
    if isinstance(frame,(bytes,bytearray,memoryview)):
        raw=bytes(frame)
    elif hasattr(frame,"convert") and hasattr(frame,"tobytes"):
        raw=frame.convert("RGB").tobytes()
    elif isinstance(frame,(list,tuple)):
        flat=[]
        def flatten(value):
            if isinstance(value,(list,tuple)):
                for item in value: flatten(item)
            else: flat.append(value)
        flatten(frame)
        if len(flat)!=width*height*3: raise EngineError("Nested frame data has an unsupported shape")
        if any(not isinstance(v,(int,float)) or not math.isfinite(float(v)) for v in flat): raise EngineError("Degenerate output: frame contains NaN or infinite values")
        scale=255 if flat and max(flat)<=1 else 1
        raw=bytes(max(0,min(255,round(float(v)*scale))) for v in flat)
    else:
        try:
            import numpy as np
            arr=np.asarray(frame)
            if not np.isfinite(arr).all(): raise EngineError("Degenerate output: frame contains NaN or infinite values")
            if arr.ndim!=3 or arr.shape[2] not in (3,4): raise EngineError("Engine returned a frame with an unsupported shape")
            if arr.shape[2]==4: arr=arr[:,:,:3]
            if arr.dtype.kind=='f': arr=np.clip(arr*255 if arr.max(initial=0)<=1 else arr,0,255)
            raw=arr.astype(np.uint8).tobytes()
        except EngineError: raise
        except Exception as exc: raise EngineError(f"Cannot convert generated frame to RGB: {exc}") from exc
    if len(raw)!=width*height*3: raise EngineError(f"Frame byte length {len(raw)} does not match {width}x{height} RGB")
    return raw

def frame_luma_stats(frames: list[Any], width: int, height: int) -> dict:
    means=[]; stds=[]; bad=False
    for frame in frames:
        try: raw=_frame_bytes(frame,width,height)
        except EngineError as exc:
            if "NaN" in str(exc) or "infinite" in str(exc): return {"nonFinite":True,"frames":len(frames),"means":means,"stddevs":stds,"degenerate":True,"reason":str(exc)}
            raise
        lum=[]
        for i in range(0,len(raw),3): lum.append(0.2126*raw[i]+0.7152*raw[i+1]+0.0722*raw[i+2])
        mean=statistics.fmean(lum) if lum else 0.0
        std=statistics.pstdev(lum) if len(lum)>1 else 0.0
        means.append(round(mean,4)); stds.append(round(std,4))
        if not math.isfinite(mean) or not math.isfinite(std): bad=True
    black=bool(means) and all(x<1.5 for x in means)
    uniform=bool(stds) and all(x<2.0 for x in stds)
    degenerate=bad or black or uniform
    reason="non-finite frame values" if bad else "all-black frames" if black else "near-uniform frames" if uniform else ""
    return {"frames":len(frames),"meanLuma":means,"stdLuma":stds,"meanLumaOverall":round(statistics.fmean(means),4) if means else None,
            "stdLumaOverall":round(statistics.fmean(stds),4) if stds else None,"nonFinite":bad,"allBlack":black,"nearUniform":uniform,"degenerate":degenerate,"reason":reason}

def write_mp4(frames: list[Any], output: Path, width: int, height: int, fps: int) -> None:
    exe=ffmpeg_path()
    if not exe: raise EngineError("Neither ffmpeg on PATH nor imageio-ffmpeg is available. Install FFmpeg or the pinned worker media dependency.")
    output.parent.mkdir(parents=True,exist_ok=True)
    cmd=[exe,"-y","-v","error","-f","rawvideo","-pixel_format","rgb24","-video_size",f"{width}x{height}","-framerate",str(fps),"-i","pipe:0","-an","-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart",str(output)]
    try:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        assert proc.stdin is not None
        for frame in frames: proc.stdin.write(_frame_bytes(frame,width,height))
        proc.stdin.close(); stderr=proc.stderr.read() if proc.stderr else b""; code=proc.wait(timeout=120)
        if proc.stderr: proc.stderr.close()
        if code: raise EngineError("FFmpeg failed writing MP4: "+stderr.decode("utf-8","replace")[-2000:])
    except BrokenPipeError as exc:
        if proc.stderr: err=proc.stderr.read().decode("utf-8","replace")[-2000:]
        else: err=str(exc)
        raise EngineError("FFmpeg closed the frame pipe: "+err) from exc
    if not output.is_file() or output.stat().st_size<100: raise EngineError("FFmpeg did not produce a valid scene MP4")

def extract_last_frame(video: Path, output: Path) -> None:
    exe=ffmpeg_path()
    if not exe: raise EngineError("FFmpeg is required for last-frame continuity")
    p=subprocess.run([exe,"-y","-v","error","-i",str(video),"-vf","reverse","-frames:v","1","-update","1",str(output)],capture_output=True,text=True)
    if p.returncode or not output.exists(): raise EngineError("Could not extract previous scene's last frame: "+p.stderr[-1000:])

def stitch(clips: list[Path], output: Path, fps: int, width: int, height: int, frame_count: int) -> dict:
    exe=ffmpeg_path()
    if not exe: raise EngineError("Neither ffmpeg nor imageio-ffmpeg is available; cannot stitch result.mp4")
    listfile=output.parent/".concat-list.txt"
    def quote(p: Path): return str(p.resolve()).replace("'", "'\\''")
    listfile.write_text("\n".join("file '"+quote(p)+"'" for p in clips)+"\n",encoding="utf-8")
    try:
        cmd=[exe,"-y","-v","error","-f","concat","-safe","0","-i",str(listfile),"-r",str(fps)]
        if frame_count > 0:
            cmd.extend(["-frames:v",str(frame_count)])
        cmd.extend(["-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart",str(output)])
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
    finally: listfile.unlink(missing_ok=True)
    if p.returncode: raise EngineError("FFmpeg stitching failed: "+p.stderr[-2000:])
    probe=ffprobe_path()
    if probe:
        q=subprocess.run([probe,"-v","error","-show_entries","format=duration:stream=codec_name,width,height,r_frame_rate","-of","json",str(output)],capture_output=True,text=True)
        if q.returncode==0:
            import json
            data=json.loads(q.stdout); stream=(data.get("streams") or [{}])[0]; duration=float((data.get("format") or {}).get("duration") or 0)
            return {"file":"result.mp4","duration":duration,"width":stream.get("width"),"height":stream.get("height"),"fps":stream.get("r_frame_rate"),"codec":stream.get("codec_name")}
    return {"file":"result.mp4","duration":round(frame_count/fps,6) if fps else None,"width":width,"height":height,"fps":fps,"codec":"h264","warning":"ffprobe unavailable; dimensions/codec/fps are inferred from the worker encode parameters, not independently probed"}
