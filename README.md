# SYJ Video Forge

A static browser interface, a standard-library local backend, and a file-bundle GPU worker for open video models. The worker runs on a GPU environment controlled by the user; the static site creates a `job.json` bundle and imports `result.mp4` plus `manifest.json` after manual transfer. No tunnel or inbound worker service is implemented.

## Status — v0.3.0 PRE-RELEASE

**The real inference path is implemented but UNVERIFIED ON REAL HARDWARE.** No Kaggle/Colab GPU session or local NVIDIA GPU is available to this build process. Do not infer that the selected model works on a T4/P100 until a verification report exists. The `Mock` provider remains **SIMULATED**. The backend `test-pattern` and worker `FakeEngine` are synthetic and are never described as AI generation. The FakeEngine is test-only and cannot be selected in the UI or normal CLI.

Zero-cost is the default: no paid APIs, model weights, cloud-storage integration, analytics, telemetry, CDN scripts, remote fonts, or secrets are included. The worker downloads selected model weights at runtime, so internet access and disk space are required on the worker. GPU availability and platform session limits are not guaranteed.

## Browser file-bundle workflow

1. Choose **GPU worker (file bundle)** and configure prompt, optional starting image, scene prompts, engine, duration, seed, and continuity.
2. Select **Create job bundle** to download `job.json`.
3. Run the worker on a GPU you control (Kaggle notebook, Colab where permitted, or a local NVIDIA GPU machine). The bundle stays local unless you upload it yourself.
4. Return with `result.mp4` and `manifest.json`, select both, and import. The browser checks the bundle ID, schema, MP4 signature, size, SHA-256, and browser playback.
5. AI model/GPU metadata is self-reported by the worker and is not independently attested. The UI labels it accordingly. A `test_pattern` result is explicitly labeled **TEST PATTERN: not AI generated**.

The privacy notice is intentional: **This file contains your prompt and image. It leaves your device only if you upload it to a notebook service or machine you choose.**

## Run the local backend

Requirements: Python 3.10–3.14 and FFmpeg on `PATH` for test-pattern MP4 output. The backend itself uses only the Python standard library.

```sh
python -m backend.server --serve-frontend
```

Open `http://127.0.0.1:8080/`. The local backend and test-pattern provider remain available and unchanged. The GPU bundle workflow works from the static GitHub Pages site without a backend and also from this local UI. See `docs/ARCHITECTURE.md` and `docs/PROVIDERS.md`.

## GPU worker

The worker package imports without PyTorch. Heavy libraries are loaded lazily only inside real engine adapters.

```sh
python -m worker engines
python -m worker smoke-test --engine ltx-video --out worker-output
python -m worker run job.json --out OUT_DIR --engine ltx-video
python -m worker run job.json --out OUT_DIR --engine ltx-video --resume
```

See `worker/notebook/syj_video_forge_gpu.ipynb`, `docs/WORKER-VERIFY.md`, `docs/BUNDLE-FORMAT.md`, `docs/MODELS.md`, and `docs/PLATFORM-POLICIES.md`. **UNVERIFIED ON REAL HARDWARE** until a report is reviewed.

## Verify locally

```sh
sh scripts/verify.sh
```

PowerShell equivalent: `./scripts/verify.ps1`. The verification suite includes the existing Node/Python tests, FFmpeg backend integration, worker unit tests, a fake-engine MP4/ffprobe integration (skipped explicitly when FFmpeg/ffprobe are absent), notebook structure checks, syntax checks, static checks, and site build. The build environment's actual output should be recorded in `QA-REPORT-v0.3.0.md`.

## GitHub Pages

The static UI is published from generated `site/`. In repository settings, choose **Settings → Pages → Build and deployment → Source → GitHub Actions**. A workflow cannot enable that setting itself. Pages is not an inference server; the worker communicates only through manually transferred files.
