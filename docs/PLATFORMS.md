# Platforms and prerequisites

The application and backend use browser APIs and Python's standard library. Python 3.10–3.14 is the target range. No pip packages, Docker, compilation, or model downloads are required. FFmpeg is required for actual test-pattern MP4 output; without it the health endpoint reports the missing tool and generation fails honestly.

## Run

From the repository root:

```sh
python -m backend.server --serve-frontend
```

Open `http://127.0.0.1:8080/`. The server binds to loopback by default. To change the data location, use `--data-dir ./data`; retention defaults to 24 hours and active jobs are limited to 12. Non-loopback binding requires an explicit `--host` and emits a security warning.

## Install FFmpeg

Use the official FFmpeg download page to select a distribution appropriate to your OS. Verify with `ffmpeg -version` and, when available, `ffprobe -version`.

- **Windows:** install a trusted FFmpeg build, add its `bin` directory to `PATH`, open a new terminal, and verify `ffmpeg -version`.
- **macOS:** install FFmpeg from a trusted package manager or the official download page; verify it is available in the terminal's `PATH`.
- **Linux:** use the distribution's package manager or an official FFmpeg build; verify `ffmpeg -version`.
- **Android:** Android builds and environments vary. Install a compatible FFmpeg executable from a trusted source supported by the environment, ensure it can execute and is on `PATH`, then verify `ffmpeg -version`. In Termux, this is commonly managed with its package manager, but package availability varies by device and repository state.

Official reference: https://ffmpeg.org/download.html. Package availability and codec support vary; the integration test requires H.264 encoding and `ffprobe`.

## GPU worker environment (v0.3.0)

Real model inference runs on a GPU worker chosen and controlled by the user. The browser bundle workflow also works from the static Pages site and does not need the local backend. Install the pinned worker dependencies with `python -m pip install -r requirements-worker.txt` in a compatible GPU environment; the file intentionally omits PyTorch so a CUDA-compatible build already present in the notebook image can be reused. Run `python -m worker engines` to inspect dependency availability, then follow `docs/WORKER-VERIFY.md`. Real model inference is **UNVERIFIED ON REAL HARDWARE** until a report is reviewed. GPU availability, free quotas, session duration, model downloads and memory fit are not guaranteed.

## Local origin versus Pages

GitHub Pages serves HTTPS, while the default backend uses HTTP on loopback. Browsers may block or restrict cross-origin/private-network requests. For local use, serve the frontend and API together with `--serve-frontend`. If using Pages, add its exact origin to the backend allowlist and understand that browser private-network restrictions may still prevent the request. Do not expose the unauthenticated backend to an untrusted network.
