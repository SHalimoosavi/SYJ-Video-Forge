"""Fake engine for tests only. Uses FFmpeg testsrc; never offered by the UI."""
from __future__ import annotations
import shutil, subprocess
from .base import Engine, EngineError

class FakeEngine(Engine):
    id="fake-test-pattern"; model_id="ffmpeg:testsrc"; license_info="FFmpeg-generated synthetic test pattern"; kind="test_pattern"
    capabilities={"text":True,"image":False,"negative_prompt":False,"frame_rule":"any","fps":8,"resolutions":["160x90"]}
    def __init__(self): super().__init__(); self.width=160; self.height=90; self.fps=8
    def load(self):
        if not shutil.which("ffmpeg"): raise EngineError("FFmpeg is required for FakeEngine tests")
        self.hardware={"gpu":"not used (test pattern)","vram_total_bytes":None,"vram_peak_bytes":None,"dtype":"n/a"}
    def generate_clip(self,prompt,start_image,frames,seed,steps,cancel_event,progress_cb):
        if cancel_event.is_set(): raise EngineError("Cancelled")
        count=max(1,frames); dur=count/self.fps
        cmd=[shutil.which("ffmpeg"),"-v","error","-f","lavfi","-i",f"testsrc2=size={self.width}x{self.height}:rate={self.fps}","-frames:v",str(count),"-f","rawvideo","-pix_fmt","rgb24","-"]
        try: proc=subprocess.run(cmd,check=True,capture_output=True,timeout=max(30,dur*4))
        except Exception as exc: raise EngineError(f"FFmpeg testsrc failed: {exc}") from exc
        frame_bytes=self.width*self.height*3
        if len(proc.stdout)<frame_bytes*count: raise EngineError("FFmpeg returned too few test-pattern frames")
        progress_cb(1.0)
        return [proc.stdout[i*frame_bytes:(i+1)*frame_bytes] for i in range(count)]
