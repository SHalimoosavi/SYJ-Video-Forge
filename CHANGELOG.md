# Changelog

## v0.3.0 — PRE-RELEASE

- Added the first real AI inference path through manually transferred, versioned job/result bundles and user-controlled GPU workers.
- Added lazy LTX-Video and Wan 2.2 TI2V-5B adapters, scene planning, incremental manifests, resume, continuity, FFmpeg stitching, and degenerate-output checks.
- Added browser import verification, worker notebook, platform policy notes, model license research, and a GPU verification report template.
- Added worker tests that run without importing PyTorch and a test-only FFmpeg FakeEngine.
- Fixed the HTTP 413 test's unclosed `HTTPError` response warning.
- **UNVERIFIED ON REAL HARDWARE** until a user-run report is reviewed. Live transport is not implemented.

## v0.2.0 — PRE-RELEASE

- Added a standard-library Python local API and bounded thread-based job manager.
- Added an FFmpeg test-pattern pipeline, last-frame extraction, concat fallback, MP4 byte-range responses, and explicit non-AI labeling.
- Added request validation, image signature checks, CORS allowlisting, job TTL cleanup, cancellation events, and local metadata persistence.
- GitHub Pages publishes the generated `site/` folder only. Repository Pages source must be set to GitHub Actions manually.

## v0.1.0 — FOUNDATION PRE-RELEASE

- Static UI and provider interface foundation.
- Mock mode simulates interface progress only; it does not create video.
