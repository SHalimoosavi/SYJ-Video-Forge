"""Safe FFmpeg helpers and byte-range parsing."""
from __future__ import annotations
import shutil, subprocess
from pathlib import Path
from threading import Event
from .providers.base import ProviderError

def ffmpeg_path() -> str | None: return shutil.which("ffmpeg")
def ffprobe_path() -> str | None: return shutil.which("ffprobe")

def extract_last_frame(ffmpeg: str, clip: Path, output: Path, cancel_event: Event) -> None:
    cmd=[ffmpeg,"-hide_banner","-loglevel","error","-y","-sseof","-0.1","-i",str(clip),"-frames:v","1",str(output)]
    run_process(cmd,cancel_event,"Could not extract the last frame")

def run_process(cmd: list[str], cancel_event: Event, label: str) -> None:
    try: proc=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    except OSError as exc: raise ProviderError(label+": "+str(exc)) from exc
    while proc.poll() is None:
        if cancel_event.wait(.05):
            proc.terminate()
            try: proc.wait(timeout=1)
            except subprocess.TimeoutExpired: proc.kill();proc.wait()
            if proc.stderr: proc.stderr.close()
            raise ProviderError("Job cancelled")
    err=proc.stderr.read() if proc.stderr else ""
    if proc.stderr: proc.stderr.close()
    if cancel_event.is_set(): raise ProviderError("Job cancelled")
    if proc.returncode: raise ProviderError(label+": "+err[-1200:])

def concatenate(ffmpeg: str, clips: list[Path], output: Path, workdir: Path, cancel_event: Event) -> str:
    if not clips: raise ProviderError("No clips were generated")
    manifest=workdir/"concat.txt"
    # Generated paths are inside our private work directory; quote apostrophes for concat demuxer.
    lines=["file '"+str(p.resolve()).replace("'", "'\\''")+"'" for p in clips]
    manifest.write_text("\n".join(lines)+"\n",encoding="utf-8")
    copy_cmd=[ffmpeg,"-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(manifest),"-c","copy","-movflags","+faststart",str(output)]
    try:
        run_process(copy_cmd,cancel_event,"Stream-copy concatenation failed")
        return "stream_copy"
    except ProviderError as exc:
        if cancel_event.is_set(): raise
        output.unlink(missing_ok=True)
        reencode=[ffmpeg,"-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(manifest),"-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p","-an","-movflags","+faststart",str(output)]
        run_process(reencode,cancel_event,"Re-encode concatenation failed (stream copy: "+str(exc)+")")
        return "reencode"

def parse_range(header: str | None, size: int) -> tuple[int,int] | None:
    if not header: return None
    if not header.startswith("bytes=") or "," in header: raise ValueError("Only one byte range is supported")
    spec=header[6:]
    if "-" not in spec: raise ValueError("Invalid byte range")
    first,last=spec.split("-",1)
    try:
        if first=="":
            suffix=int(last)
            if suffix<=0: raise ValueError("Invalid suffix range")
            start=max(0,size-suffix);end=size-1
        else:
            start=int(first);end=int(last) if last else size-1
            if start<0 or end<start: raise ValueError("Invalid byte range")
            end=min(end,size-1)
    except ValueError as exc: raise ValueError("Invalid byte range") from exc
    if size<=0 or start>=size: raise ValueError("Range not satisfiable")
    return start,end
