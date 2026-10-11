from __future__ import annotations
import base64, json, os, tempfile, threading, time, unittest, urllib.error, urllib.request
from pathlib import Path
from backend.config import validate_job_payload, validate_image_payload, safe_child, cors_origins, MAX_BODY_BYTES
from backend.jobs import JobManager
from backend.media import parse_range, ffmpeg_path, ffprobe_path
from backend.providers.base import Capabilities, VideoProvider, ProviderError
from backend.server import make_server

PNG=b"\x89PNG\r\n\x1a\n"+b"fake-data"
def payload(**kw):
    v={"prompt":"make a pattern","duration":3,"mode":"text","clip_seconds":1,"scenes":3};v.update(kw);return validate_job_payload(v)

class SlowProvider(VideoProvider):
    name="slow-test";capabilities=Capabilities(True,False,False,5,False,"test_pattern")
    def __init__(self):self.started=threading.Event();self.stopped=threading.Event()
    def available(self):return True,""
    def generate_clip(self,prompt,start_image,seconds,seed,output,progress_cb,cancel_event):
        self.started.set()
        while not cancel_event.wait(.02):progress_cb(10,"waiting")
        self.stopped.set();raise ProviderError("Job cancelled")

class ImageSlowProvider(SlowProvider):
    capabilities=Capabilities(True,True,False,5,True,"test_pattern")

class BackendUnitTests(unittest.TestCase):
    def test_schema_validation(self):
        self.assertEqual(payload()["prompt"],"make a pattern")
        for bad in ({"prompt":" "},{"prompt":"x","unknown":1},{"prompt":"x","duration":-1},{"prompt":"x","mode":"image"},{"prompt":"x","seed":-1}):
            with self.assertRaises(ValueError):validate_job_payload(bad)
    def test_image_size_and_magic_validation(self):
        data=base64.b64encode(PNG).decode();self.assertIsNotNone(validate_image_payload({"mime":"image/png","data":data}))
        with self.assertRaises(ValueError):validate_image_payload({"mime":"image/png","data":base64.b64encode(b"not png").decode()})
        with self.assertRaises(ValueError):validate_image_payload({"mime":"image/gif","data":data})
        with self.assertRaises(ValueError):validate_image_payload({"mime":"image/png","data":"!"})
        from backend.config import MAX_IMAGE_BYTES
        with self.assertRaises(ValueError):validate_image_payload({"mime":"image/png","data":"A" * (((MAX_IMAGE_BYTES + 2) // 3) * 4 + 9)})
    def test_path_safety(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.assertEqual(safe_child(root,"abc","x.txt"),root/"abc"/"x.txt")
            with self.assertRaises(ValueError):safe_child(root,"..","secret")
    def test_cors_allowlist_rejects_wildcard(self):
        with self.assertRaises(ValueError):cors_origins("*")
        self.assertIn("https://shalimoosavi.github.io",cors_origins())
    def test_range_parsing(self):
        self.assertEqual(parse_range("bytes=2-5",10),(2,5));self.assertEqual(parse_range("bytes=-3",10),(7,9));self.assertEqual(parse_range("bytes=4-",10),(4,9));self.assertIsNone(parse_range(None,10))
        with self.assertRaises(ValueError):parse_range("bytes=99-",10)
        with self.assertRaises(ValueError):parse_range("bytes=0-1,3-4",10)
    @unittest.skipUnless(ffmpeg_path(), "SKIPPED: ffmpeg is not available")
    def test_ffmpeg_provider_terminates_process_on_cancel(self):
        from backend.providers.testpattern import TestPatternProvider
        from backend.providers.base import ProviderError
        with tempfile.TemporaryDirectory() as d:
            provider=TestPatternProvider(ffmpeg_path());event=threading.Event();out=Path(d)/"clip.mp4";errors=[]
            def progress(_value,message):
                if message.startswith("Generating deterministic"):
                    event.set()
            def work():
                try:provider.generate_clip("ignored",None,30,1,out,progress,event)
                except Exception as exc:errors.append(exc)
            t=threading.Thread(target=work);t.start();t.join(5)
            self.assertFalse(t.is_alive(), "FFmpeg provider did not stop after cancellation")
            self.assertTrue(errors);self.assertIsInstance(errors[0],ProviderError);self.assertIn("cancelled",str(errors[0]).lower())
    def test_supported_image_is_saved_inside_job_directory(self):
        with tempfile.TemporaryDirectory() as d:
            provider=ImageSlowProvider();m=JobManager(d,providers=[provider],ffmpeg=ffmpeg_path() or "/missing/ffmpeg")
            try:
                image={"mime":"image/png","data":base64.b64encode(PNG).decode()}
                job=m.create(payload(mode="image",image=image));path=Path(d)/job["id"] / "input-image.png"
                self.assertTrue(path.is_file());self.assertEqual(path.read_bytes(),PNG)
                self.assertEqual(path.resolve().parent, (Path(d)/job["id"]).resolve())
                m.cancel(job["id"])
            finally:m.close()
    def test_job_lifecycle(self):
        with tempfile.TemporaryDirectory() as d:
            m=JobManager(d,providers=[SlowProvider()],ffmpeg="/missing/ffmpeg")
            try:
                j=m.create(payload());self.assertIn(j["status"],("queued","running"))
                deadline=time.time()+3
                while time.time()<deadline and m.get(j["id"])["status"] not in ("failed","completed"):time.sleep(.03)
                self.assertEqual(m.get(j["id"])["status"],"failed");self.assertIn("FFmpeg",m.get(j["id"])["error"])
                self.assertTrue((Path(d)/j["id"]/"job.json").is_file())
            finally:m.close()
    def test_cancel_stops_work(self):
        with tempfile.TemporaryDirectory() as d:
            p=SlowProvider();m=JobManager(d,providers=[p],ffmpeg=ffmpeg_path())
            try:
                j=m.create(payload());self.assertTrue(p.started.wait(2));c=m.cancel(j["id"]);self.assertEqual(c["status"],"cancelled");self.assertTrue(p.stopped.wait(2));self.assertEqual(m.get(j["id"])["status"],"cancelled")
            finally:m.close()
    def test_active_job_limit(self):
        with tempfile.TemporaryDirectory() as d:
            provider=SlowProvider();m=JobManager(d,max_jobs=1,providers=[provider],ffmpeg=ffmpeg_path() or "/missing/ffmpeg")
            try:
                m.create(payload())
                with self.assertRaisesRegex(ValueError,"Job limit reached"):
                    m.create(payload())
            finally:m.close()
    def test_running_job_is_marked_failed_after_restart(self):
        with tempfile.TemporaryDirectory() as d:
            jid="b"*32;directory=Path(d)/jid;directory.mkdir()
            (directory/"job.json").write_text(json.dumps({"id":jid,"status":"running","created_at":time.time(),"updated_at":time.time(),"progress":35,"scenes":[],"kind":"test_pattern"}),encoding="utf-8")
            m=JobManager(d,ffmpeg=ffmpeg_path())
            try:
                state=m.get(jid);self.assertEqual(state["status"],"failed");self.assertIn("restart",state["error"])
            finally:m.close()
    def test_ttl_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            m=JobManager(d,ttl_seconds=60,ffmpeg="/missing/ffmpeg")
            try:
                old=Path(d)/"old";old.mkdir();os.utime(old,(time.time()-120,time.time()-120));m.cleanup();self.assertFalse(old.exists())
            finally:m.close()
    def test_preflight_cors_and_private_network(self):
        with tempfile.TemporaryDirectory() as d:
            s=make_server("127.0.0.1",0,d);t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
            try:
                req=urllib.request.Request(f"http://127.0.0.1:{s.server_address[1]}/api/health",method="OPTIONS",headers={"Origin":"https://shalimoosavi.github.io","Access-Control-Request-Method":"POST","Access-Control-Request-Private-Network":"true"})
                with urllib.request.urlopen(req,timeout=3) as r:
                    self.assertEqual(r.status,204);self.assertEqual(r.headers.get("Access-Control-Allow-Origin"),"https://shalimoosavi.github.io");self.assertEqual(r.headers.get("Access-Control-Allow-Private-Network"),"true")
            finally:s.shutdown();s.server_close();s.manager.close();t.join(2)
    def test_request_size_limit(self):
        with tempfile.TemporaryDirectory() as d:
            s=make_server("127.0.0.1",0,d);t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
            try:
                req=urllib.request.Request(f"http://127.0.0.1:{s.server_address[1]}/api/jobs",data=b"",method="POST",headers={"Content-Type":"application/json","Content-Length":str(MAX_BODY_BYTES+1)})
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    urllib.request.urlopen(req, timeout=3)
                try:
                    self.assertEqual(ctx.exception.code, 413)
                finally:
                    ctx.exception.close()
            finally:s.shutdown();s.server_close();s.manager.close();t.join(2)
    def test_range_http_response(self):
        with tempfile.TemporaryDirectory() as d:
            s=make_server("127.0.0.1",0,d);t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
            try:
                jid="a"*32;directory=Path(d)/jid;directory.mkdir();data=bytes(range(100));(directory/"output.mp4").write_bytes(data)
                s.manager._jobs[jid]={"id":jid,"status":"completed","result_file":"output.mp4","kind":"test_pattern"};s.manager._events[jid]=threading.Event()
                req=urllib.request.Request(f"http://127.0.0.1:{s.server_address[1]}/api/jobs/{jid}/result",headers={"Range":"bytes=10-19"})
                with urllib.request.urlopen(req,timeout=3) as r:self.assertEqual(r.status,206);self.assertEqual(r.headers.get("Content-Range"),"bytes 10-19/100");self.assertEqual(r.read(),data[10:20])
            finally:s.shutdown();s.server_close();s.manager.close();t.join(2)
    def test_concat_helper_reports_stream_copy_or_fallback(self):
        # Pure helper contract: no shell interpolation and paths are passed as argv items.
        import inspect
        from backend import media
        self.assertIn("subprocess.Popen(cmd",inspect.getsource(media.run_process))
        self.assertNotIn("shell=True",inspect.getsource(media))

class IntegrationTests(unittest.TestCase):
    @unittest.skipUnless(ffmpeg_path() and ffprobe_path(),"SKIPPED: ffmpeg and ffprobe are not both available")
    def test_real_server_testpattern_mp4_pipeline(self):
        with tempfile.TemporaryDirectory() as d:
            s=make_server("127.0.0.1",0,Path(d)/"data");t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
            try:
                base=f"http://127.0.0.1:{s.server_address[1]}"
                req=urllib.request.Request(base+"/api/jobs",data=json.dumps({"prompt":"integration test","duration":3,"scenes":3,"clip_seconds":1,"mode":"text","seed":17}).encode(),headers={"Content-Type":"application/json"},method="POST")
                with urllib.request.urlopen(req,timeout=10) as r:self.assertEqual(r.status,202);job=json.load(r)
                deadline=time.time()+60
                while time.time()<deadline:
                    with urllib.request.urlopen(base+f"/api/jobs/{job['id']}",timeout=5) as r:state=json.load(r)
                    if state["status"] in ("completed","failed","cancelled"):break
                    time.sleep(.15)
                self.assertEqual(state["status"],"completed",state.get("error"));self.assertEqual(state["kind"],"test_pattern");self.assertEqual(len(state["scenes"]),3);self.assertIn(state["concat_mode"],("stream_copy","reencode"))
                with urllib.request.urlopen(base+f"/api/jobs/{job['id']}/result",timeout=10) as r:mp4=r.read();self.assertEqual(r.headers.get_content_type(),"video/mp4")
                out=Path(d)/"download.mp4";out.write_bytes(mp4);self.assertGreater(len(mp4),1000)
                import subprocess
                probe=subprocess.run([ffprobe_path(),"-v","error","-show_entries","format=duration:stream=codec_name,codec_type","-of","json",str(out)],capture_output=True,text=True,timeout=10,check=True)
                meta=json.loads(probe.stdout);self.assertTrue(any(x.get("codec_name")=="h264" and x.get("codec_type")=="video" for x in meta["streams"]));self.assertAlmostEqual(float(meta["format"]["duration"]),3.0,delta=.5)
            finally:s.shutdown();s.server_close();s.manager.close();t.join(2)

if __name__=="__main__":unittest.main(verbosity=2)
