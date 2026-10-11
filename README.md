# SYJ Video Forge

Open video-workflow foundation by SAYANJALI NEXUS PRIVATE LIMITED. The project includes a standard-library Python local backend and an FFmpeg test-pattern provider for validating the job, media, cancellation, and playback pipeline.

## Status — v0.2.0 pre-release

**A real AI video engine is not included.** The shipped `test-pattern` provider creates synthetic FFmpeg test-pattern clips; it does not interpret prompts or generate AI content. Its output and history entries are labeled `TEST PATTERN: not AI generated`. The `Mock` provider only simulates interface progress and never creates a video. No model weights, model downloads, paid providers, cloud storage, analytics, ads, trackers, CDN assets, remote fonts, or mandatory paid services are included.

## Run locally

Requirements: Python 3.10–3.14 and FFmpeg on `PATH` for test-pattern MP4 output. No pip dependencies are required.

```sh
python -m backend.server --serve-frontend
```

Open `http://127.0.0.1:8080/`. The backend binds to loopback by default. Stop it with Ctrl+C. To serve only the API, omit `--serve-frontend`. For command options, CORS allowlisting, and FFmpeg setup, see `docs/PLATFORMS.md` and `docs/PROVIDERS.md`.

## GitHub Pages

The static UI is published from the generated `site/` directory. In the repository, open **Settings → Pages → Build and deployment → Source** and select **GitHub Actions**. A workflow cannot enable that repository setting by itself. The Pages UI is served over HTTPS; browsers may restrict calls from it to a local HTTP backend. For local generation, run the frontend and backend on the same local origin with `--serve-frontend`.

## Verify

```sh
sh scripts/verify.sh
```

PowerShell equivalent: `./scripts/verify.ps1`. The test suite includes an FFmpeg/ffprobe integration test; it is explicitly skipped if either executable is unavailable. `sh scripts/build-site.sh` generates only `site/index.html`, `site/styles.css`, and `site/src/`.

## Long-video pipeline

The backend builds a storyboard from sequential clips, extracts each intermediate clip's last frame, passes that frame to the next provider call, and concatenates the clips with FFmpeg. The included test-pattern provider deliberately ignores image conditioning and is not an AI model. A future provider may use the start frame if its capability declaration supports it. The pipeline validates mechanics, not semantic continuity or model quality.

## Documentation

See `docs/ARCHITECTURE.md`, `docs/PROVIDERS.md`, `docs/PLATFORMS.md`, `docs/TROUBLESHOOTING.md`, `docs/MODELS.md`, `docs/SECURITY.md`, and `docs/QA-CHECKLIST.md`. Source code is MIT licensed; FFmpeg and any future model weights or external services have their own licenses and terms.
