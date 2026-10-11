"""FFmpeg test-pattern provider. This is a pipeline validator, not AI."""
from __future__ import annotations
import shutil, subprocess, time
from pathlib import Path
from pathlib import Path
from threading import Event
from .base import Capabilities, ProviderError, VideoProvider, ProgressCallback

class TestPatternProvider(VideoProvider):
    name = "test-pattern"
    capabilities = Capabilities(text=True, image=False, negative_prompt=False, max_clip_seconds=30, supports_start_image=False, kind="test_pattern")
    def __init__(self, ffmpeg: str | None = None):
        self.ffmpeg = ffmpeg or shutil.which("ffmpeg")
    def available(self) -> tuple[bool, str]:
        return (True, "") if self.ffmpeg and Path(self.ffmpeg).is_file() else (False, "FFmpeg was not found. Install FFmpeg and ensure ffmpeg is on PATH, then restart the backend.")
    def generate_clip(self, prompt: str, start_image: Path | None, seconds: float, seed: int, output: Path, progress_cb: ProgressCallback, cancel_event: Event) -> None:
        ok, reason = self.available()
        if not ok: raise ProviderError(reason)
        if cancel_event.is_set(): raise ProviderError("Job cancelled")
        # Seed changes hue to make scene-to-scene variation deterministic; no prompt inference occurs.
        hue = (seed * 37) % 360
        cmd = [self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=size=640x360:rate=24, hue=h={hue}:s=1", "-t", str(seconds), "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)]
        progress_cb(5, "Generating deterministic FFmpeg test pattern")
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        except OSError as exc:
            raise ProviderError("Could not start FFmpeg: " + str(exc)) from exc
        while proc.poll() is None:
            if cancel_event.wait(0.05):
                proc.terminate()
                try: proc.wait(timeout=1)
                except subprocess.TimeoutExpired: proc.kill(); proc.wait()
                if proc.stderr: proc.stderr.close()
                raise ProviderError("Job cancelled")
            progress_cb(25, "FFmpeg is rendering a test-pattern clip")
        stderr = proc.stderr.read() if proc.stderr else ""
        if proc.stderr: proc.stderr.close()
        if cancel_event.is_set(): raise ProviderError("Job cancelled")
        if proc.returncode != 0:
            raise ProviderError("FFmpeg failed to generate test-pattern clip: " + stderr[-1200:])
        progress_cb(100, "Test-pattern clip completed")
