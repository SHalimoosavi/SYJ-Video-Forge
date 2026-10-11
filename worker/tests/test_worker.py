from __future__ import annotations
import hashlib, json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from worker.schema import BundleError, load_job, validate_job, validate_manifest, write_json_atomic
from worker.planning import frame_count, plan_scenes, scene_seed
from worker.media import frame_luma_stats
from worker.engines import create_engine
from worker.engines.base import EngineError
from worker.engines.fake import FakeEngine
from worker.runtime import run_job

class WorkerTests(unittest.TestCase):
    def make_job(self, root, seconds=10, clip=5):
        job={"schemaVersion":1,"jobId":"1234567890abcdef1234567890abcdef","createdAt":"2026-10-11T00:00:00Z","mode":"text","preset":"Long" if seconds>=30 else "Custom","prompt":"A simple scene","negativePrompt":"","aspect":"16:9","resolution":"512x288","seed":100,"totalSeconds":seconds,"fps":8,"clipSeconds":clip,"continuity":"last_frame","engine":{"id":"ltx-video"},"steps":2,"scenes":[{"index":i+1,"prompt":f"Scene {i+1}"} for i in range((seconds+clip-1)//clip)],"image":None}
        p=Path(root)/"job.json"; p.write_text(json.dumps(job),encoding="utf-8"); return p,job
    def test_schema_validates_bundle_and_rejects_wrong_schema(self):
        with tempfile.TemporaryDirectory() as d:
            p,job=self.make_job(d,30); self.assertEqual(load_job(p)["jobId"],job["jobId"])
            job["schemaVersion"]=2
            with self.assertRaisesRegex(BundleError,"schemaVersion"): validate_job(job)
    def test_image_magic_and_sha_validation(self):
        import base64
        raw=b"not-an-image"
        job={"schemaVersion":1,"jobId":"a"*32,"createdAt":"2026-10-11T00:00:00Z","mode":"image","preset":"Custom","prompt":"x","negativePrompt":"","aspect":"16:9","resolution":"512x288","seed":0,"totalSeconds":5,"fps":24,"clipSeconds":5,"continuity":"last_frame","engine":{"id":"ltx-video"},"scenes":[{"index":1,"prompt":"x"}],"image":{"mime":"image/png","sha256":hashlib.sha256(raw).hexdigest(),"base64":base64.b64encode(raw).decode()}}
        with self.assertRaisesRegex(BundleError,"magic bytes"): validate_job(job)
    def test_30_second_planning_respects_frame_rules(self):
        ltx=plan_scenes(30,5,24,"8n+1"); wan=plan_scenes(30,5,24,"4n+1")
        self.assertEqual(len(ltx),6); self.assertEqual(len(wan),6)
        self.assertTrue(all(x["frames"]%8==1 for x in ltx)); self.assertTrue(all(x["frames"]%4==1 for x in wan))
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"SKIPPED: ffmpeg or ffprobe is missing")
    def test_model_extra_frames_are_trimmed_per_scene_before_stitch(self):
        class FrameRuleFake(FakeEngine):
            capabilities = {**FakeEngine.capabilities, "frame_rule": "8n+1"}

        with tempfile.TemporaryDirectory() as d:
            p, job = self.make_job(d, 11, 5)
            out = Path(d) / "out"
            manifest = run_job(p, out, engine_override=FrameRuleFake())

            self.assertEqual([s["generatedFrames"] for s in manifest["scenes"]], [41, 41, 9])
            self.assertEqual([s["frames"] for s in manifest["scenes"]], [40, 40, 8])
            self.assertEqual(sum(s["frames"] for s in manifest["scenes"]), 88)

            probe = subprocess.run(
                [shutil.which("ffprobe"), "-v", "error", "-count_frames",
                 "-show_entries", "format=duration:stream=nb_read_frames",
                 "-of", "json", str(out / "result.mp4")],
                capture_output=True, text=True
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            info = json.loads(probe.stdout)
            self.assertAlmostEqual(float(info["format"]["duration"]), 11.0, delta=1 / job["fps"])
            self.assertEqual(int(info["streams"][0]["nb_read_frames"]), 88)

    def test_scene_seed_is_base_plus_one_based_index(self):
        self.assertEqual(scene_seed(100,1),101); self.assertEqual(scene_seed(100,6),106); self.assertEqual(scene_seed(2147483647,1),0)
    def test_degenerate_guard_black_constant_nan_and_normal_frames(self):
        black=frame_luma_stats([bytes([0,0,0])],1,1); self.assertTrue(black["allBlack"]); self.assertTrue(black["degenerate"])
        constant=frame_luma_stats([bytes([120,120,120])],1,1); self.assertTrue(constant["nearUniform"])
        nan=frame_luma_stats([[[float("nan"),0,0]]],1,1); self.assertTrue(nan["nonFinite"]); self.assertTrue(nan["degenerate"])
        normal=frame_luma_stats([bytes([255,0,0,0,255,0,0,0,255,255,255,255])],2,2); self.assertFalse(normal["degenerate"])
    def test_importing_worker_does_not_import_torch(self):
        code="import sys, worker, worker.schema, worker.runtime, worker.engines; assert 'torch' not in sys.modules, 'torch imported eagerly'"
        p=subprocess.run([sys.executable,"-c",code],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
    def test_fake_engine_is_not_a_normal_cli_engine(self):
        with self.assertRaisesRegex(EngineError,"Unknown engine id"): create_engine("fake-test-pattern")
        self.assertEqual(create_engine("fake-test-pattern",for_tests=True).kind,"test_pattern")
    def test_engine_load_failure_writes_failed_manifest(self):
        class BrokenFake(FakeEngine):
            def load(self): raise EngineError("synthetic engine load failure")
        with tempfile.TemporaryDirectory() as d:
            p,_=self.make_job(d,5); out=Path(d)/"out"
            with self.assertRaisesRegex(EngineError,"synthetic engine load failure"): run_job(p,out,engine_override=BrokenFake())
            manifest=json.loads((out/"manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"],"failed"); self.assertIsNone(manifest["final"])
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"SKIPPED: ffmpeg or ffprobe is missing")
    def test_fake_engine_end_to_end_stitches_mp4_and_ffprobe_reads_it(self):
        with tempfile.TemporaryDirectory() as d:
            p,job=self.make_job(d,10)
            m=run_job(p,Path(d)/"out",engine_override=FakeEngine())
            out=Path(d)/"out"; self.assertEqual(m["kind"],"test_pattern"); self.assertEqual(m["status"],"completed")
            self.assertTrue((out/"result.mp4").is_file()); self.assertEqual(len(m["scenes"]),2)
            q=subprocess.run([shutil.which("ffprobe"),"-v","error","-show_entries","format=duration:stream=codec_name","-of","json",str(out/"result.mp4")],capture_output=True,text=True)
            self.assertEqual(q.returncode,0,q.stderr); info=json.loads(q.stdout); duration=float(info["format"]["duration"]); self.assertAlmostEqual(duration,job["totalSeconds"],delta=1/job["fps"]); self.assertEqual(info["streams"][0]["codec_name"],"h264")
            self.assertEqual(m["final"]["sha256"],hashlib.sha256((out/"result.mp4").read_bytes()).hexdigest())
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"SKIPPED: ffmpeg or ffprobe is missing")
    def test_resume_skips_scene_when_file_sha_matches_manifest(self):
        class CountingFake(FakeEngine):
            def __init__(self): super().__init__(); self.calls=0
            def generate_clip(self,*a,**kw): self.calls+=1; return super().generate_clip(*a,**kw)
        with tempfile.TemporaryDirectory() as d:
            p,_=self.make_job(d,10); out=Path(d)/"out"; first=CountingFake(); run_job(p,out,engine_override=first); self.assertEqual(first.calls,2)
            second=CountingFake(); m=run_job(p,out,resume=True,engine_override=second); self.assertEqual(second.calls,0); self.assertEqual(m["status"],"completed")
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"SKIPPED: ffmpeg or ffprobe is missing")
    def test_resume_rejects_manifest_when_job_inputs_change(self):
        class CountingFake(FakeEngine):
            def __init__(self):
                super().__init__()
                self.calls = 0
            def generate_clip(self, *args, **kwargs):
                self.calls += 1
                return super().generate_clip(*args, **kwargs)

        with tempfile.TemporaryDirectory() as d:
            p, job = self.make_job(d, 5)
            out = Path(d) / "out"
            run_job(p, out, engine_override=CountingFake())
            job["scenes"][0]["prompt"] = "Changed prompt"
            p.write_text(json.dumps(job), encoding="utf-8")
            engine = CountingFake()
            result = run_job(p, out, resume=True, engine_override=engine)
            self.assertEqual(engine.calls, 1)
            self.assertEqual(result["status"], "completed")
            self.assertNotEqual(result["jobFingerprint"], "")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"SKIPPED: ffmpeg or ffprobe is missing")
    def test_degenerate_scene_fails_job_and_never_leaves_successful_final(self):
        class BlackFake(FakeEngine):
            def generate_clip(self,prompt,start_image,frames,seed,steps,cancel_event,progress_cb):
                progress_cb(1.0); return [bytes(self.width*self.height*3) for _ in range(frames)]
        with tempfile.TemporaryDirectory() as d:
            p,_=self.make_job(d,5); out=Path(d)/"out"
            with self.assertRaisesRegex(EngineError,"all-black frames"): run_job(p,out,engine_override=BlackFake())
            manifest=json.loads((out/"manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"],"failed"); self.assertIsNone(manifest["final"])
            self.assertFalse((out/"result.mp4").exists()); self.assertTrue(manifest["degenerateChecks"][0]["allBlack"])
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"SKIPPED: ffmpeg or ffprobe is missing")
    def test_manifest_is_written_incrementally_after_each_scene(self):
        with tempfile.TemporaryDirectory() as d:
            p,_=self.make_job(d,10); original=__import__("worker.runtime",fromlist=["write_json_atomic"]).write_json_atomic; counts=[]
            def spy(path,obj):
                if Path(path).name=="manifest.json": counts.append(len(obj.get("scenes",[])))
                return original(path,obj)
            with patch("worker.runtime.write_json_atomic",side_effect=spy): run_job(p,Path(d)/"out",engine_override=FakeEngine())
            self.assertIn(0,counts); self.assertIn(1,counts); self.assertIn(2,counts)
    def test_manifest_rejects_wrong_job_id(self):
        job={"jobId":"a"*32}; manifest={"schemaVersion":1,"jobId":"b"*32,"kind":"test_pattern","final":{"file":"result.mp4","sha256":"0"*64},"scenes":[]}
        with self.assertRaisesRegex(BundleError,"jobId"): validate_manifest(manifest,job)

if __name__=="__main__": unittest.main()
