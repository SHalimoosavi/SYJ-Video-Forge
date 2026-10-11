# Changelog

## v0.2.0 — PRE-RELEASE

- Added a standard-library Python local API and bounded thread-based job manager.
- Added an FFmpeg test-pattern pipeline, last-frame extraction, concat stream-copy/re-encode fallback, MP4 byte-range responses, and explicit non-AI labeling.
- Added request validation, image signature checks, CORS allowlisting, job TTL cleanup, cancellation events, and local metadata persistence.
- Fixed provider destination disclosure formatting and asynchronous cancellation guards; expanded provider and backend tests.
- GitHub Pages now publishes the generated `site/` folder only. Repository Pages source must be set to GitHub Actions manually.
- **No real AI model, model weights, paid provider, cloud storage, or analytics are included.**

## v0.1.0 — FOUNDATION PRE-RELEASE

The v0.1.0 release was published as a normal release instead of being marked as a pre-release. The repository owner is correcting that release metadata manually; this changelog records the intended pre-release status without rewriting Git history.

- Static UI and provider interface foundation.
- Mock mode simulates interface progress only; it does not create video.
