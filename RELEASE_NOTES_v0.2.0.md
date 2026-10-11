# SYJ Video Forge v0.2.0 — PRE-RELEASE

This pre-release adds a local Python standard-library backend and a test-pattern video pipeline for validating job creation, cancellation, per-scene progress, FFmpeg media handling, MP4 seeking, and downloads.

## Included

- Local API and bounded thread queue with persistent job metadata and TTL cleanup.
- FFmpeg `test-pattern` provider; result kind is `test_pattern` and is labeled **TEST PATTERN: not AI generated** in the UI and history.
- Per-scene progress, result preview, download, and cancellation handling.
- CORS allowlist and same-origin local frontend mode.
- Regression tests for disclosure, HTTP provider behavior, cancellation guards, backend validation, Range requests, and an FFmpeg/ffprobe integration path.
- GitHub Pages workflow builds and publishes `site/` only.

## Important limitations

- **No real AI model or inference backend is included.** The test-pattern provider does not interpret prompts.
- The test-pattern provider does not support image conditioning or negative prompts.
- Browser layout, PowerShell, Windows, and GitHub Pages deployment must be verified by the maintainer. A successful CI run does not prove that repository Pages settings are configured correctly.
- Before deployment, set **Settings → Pages → Build and deployment → Source** to **GitHub Actions**.

This is an early pre-release intended for QA and pipeline validation, not a production AI video-generation service.
