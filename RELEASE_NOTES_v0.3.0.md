# SYJ Video Forge v0.3.0 — PRE-RELEASE

**Inference status: UNVERIFIED ON REAL HARDWARE.** This release adds a real model-inference adapter path but has not been run on a Kaggle, Colab, or local NVIDIA GPU in the release build environment. Review `QA-REPORT-v0.3.0.md` and submit a report using `docs/verification/REPORT-TEMPLATE.md` before treating inference as verified.

## Added

- Browser-created version 1 `job.json` bundles and editable per-scene prompts.
- Manual file-transfer workflow for a user-controlled GPU worker; no tunnel or inbound network service.
- Lazy-loaded LTX-Video primary and Wan 2.2 TI2V-5B fallback engine adapters; weights download only at worker runtime.
- Incremental scene manifests, resumable hash-matched scene outputs, deterministic scene seeds, last-frame continuity, ffmpeg stitching, and a per-frame luminance/NaN degenerate-output guard.
- `result.mp4` and `manifest.json` import validation in the browser, including bundle ID, schema, MP4 signature, size limit, SHA-256 and playback checks.
- A notebook for Kaggle/Colab/local GPU use, platform policy notes, verification instructions, and a report template.
- Standard-library worker unit tests and a FakeEngine test-only FFmpeg path.
- Fixed the HTTP 413 test to explicitly close its `HTTPError` response; added resume invalidation when job inputs change; normalized model-generated scene frames before stitching to preserve exact requested duration.

## Engine and license notes

LTX-Video uses its LTXV Open Weights License 0.X and has use-based restrictions and commercial terms for qualifying entities. Wan 2.2 TI2V-5B is documented as Apache-2.0 but the official standard 720p path lists at least 24 GB VRAM. See the current official sources and research date in `docs/MODELS.md`. No model weights are included.

## Honesty and limitations

- **UNVERIFIED ON REAL HARDWARE:** real model load, fp16/bf16 behavior, VRAM fit, output quality, and speed.
- **UNVERIFIED:** Kaggle and Colab session behavior, real browser import across browsers, Windows execution, and PowerShell verification unless the QA report records an actual run.
- Model/GPU fields in the manifest are self-reported, not cryptographically attested.
- Hosted notebook use is subject to the platform's current terms and content rules; the user is responsible for compliance.
- Live tunnel/HTTP worker mode is design-only and not implemented.
