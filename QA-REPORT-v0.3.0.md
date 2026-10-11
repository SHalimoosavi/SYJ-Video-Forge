# QA Report — SYJ Video Forge v0.3.0 PRE-RELEASE

Research/build date: 2026-10-11. This report describes the local overlay build. No Git history, existing tag, or remote repository was modified.

## Release status

**Real model inference is implemented but UNVERIFIED ON REAL HARDWARE.** This build environment has CPU-only PyTorch (`2.10.0+cpu`), no CUDA device, and no installed Diffusers/Transformers/Accelerate. The smoke-test failure below is an honest environment failure, not a GPU pass. Do not remove the hardware-verification warning until a user submits and reviews a real GPU report.

## Build environment

- Python: `3.13.5`
- Node.js: `v22.16.0`
- OS: Linux x86_64, glibc 2.41
- FFmpeg: `7.1.5-0+deb13u1`, `/usr/bin/ffmpeg`
- ffprobe: `7.1.5-0+deb13u1`, `/usr/bin/ffprobe`
- PyTorch: `2.10.0+cpu`; `torch.cuda.is_available() == False`; CUDA version `None`
- `diffusers`: not installed; `transformers`: not installed; `accelerate`: not installed
- PowerShell (`pwsh`): not installed
- The worker import check confirms that importing `worker`, `worker.schema`, `worker.runtime`, and `worker.engines` does not import `torch`.

## Engine research and decision

Sources below are official model/platform pages reviewed on 2026-10-11. Model facts and license summaries are in `docs/MODELS.md`; platform policy summaries are in `docs/PLATFORM-POLICIES.md`.

- **Primary:** `Lightricks/LTX-Video`, using Diffusers `LTXPipeline` for text-to-video and `LTXConditionPipeline` for image conditioning. The official model card documents 24 fps and an `8n+1` frame rule for the model family. Its LTXV Open Weights License 0.X is not Apache-2.0: it has use-based restrictions, and commercial-use terms apply to qualifying entities at USD 10,000,000 annual revenue. This was selected as the more plausible low-resolution experiment for a 16 GB-class GPU, but the exact adapter, fp16 stability, memory fit, and model revision are **UNVERIFIED ON REAL HARDWARE**.
- **Fallback:** `Wan-AI/Wan2.2-TI2V-5B`, which the official card documents for text-to-video and image-to-video at 720p/24 fps under Apache-2.0. The official standard 720p inference instructions state at least 24 GB VRAM. It is therefore a fallback for sufficiently large GPUs, not a promised 16 GB path. The adapter API and offload behavior are **UNVERIFIED**.
- No model weights are included. The worker downloads model weights at runtime. The reviewed model pages did not indicate gated access for these selected repositories; if that changes, users must review/accept the official license and supply any token only through a platform secret store or hidden prompt.
- Pinned dependency release pages were checked on PyPI for `diffusers==0.35.1`, `transformers==4.57.1`, `accelerate==1.10.1`, `huggingface-hub==0.36.0`, `safetensors==0.6.2`, `numpy==2.2.6`, `Pillow==11.3.0`, `imageio==2.37.0`, and `imageio-ffmpeg==0.6.0`. The dependency set was not installed in this build environment; compatibility with the preinstalled PyTorch/CUDA versions on hosted notebooks remains **UNVERIFIED**.

Official research links:

- LTX Diffusers API: https://huggingface.co/docs/diffusers/api/pipelines/ltx_video
- LTX model card: https://huggingface.co/Lightricks/LTX-Video
- LTXV Open Weights License 0.X: https://huggingface.co/Lightricks/LTX-Video/blob/main/LTX-Video-Open-Weights-License-0.X.txt
- Wan 2.2 TI2V-5B model card: https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B
- Wan 2.2 official repository/inference instructions: https://github.com/Wan-Video/Wan2.2
- Kaggle notebook documentation: https://www.kaggle.com/docs/notebooks
- Kaggle GPU usage guidance: https://www.kaggle.com/docs/efficient-gpu-usage
- Kaggle terms: https://www.kaggle.com/terms
- Colab FAQ: https://research.google.com/colaboratory/faq.html
- Colab terms: https://research.google.com/colaboratory/tos_v3.html
- PyPI pins: https://pypi.org/project/diffusers/0.35.1/ ; https://pypi.org/project/transformers/4.57.1/ ; https://pypi.org/project/accelerate/1.10.1/ ; https://pypi.org/project/huggingface-hub/0.36.0/ ; https://pypi.org/project/safetensors/0.6.2/ ; https://pypi.org/project/numpy/2.2.6/ ; https://pypi.org/project/pillow/11.3.0/ ; https://pypi.org/project/ImageIO/2.37.0/ ; https://pypi.org/project/imageio-ffmpeg/0.6.0/

## File tree — added files

```text
DELETED-RENAMED-FILES.md
QA-REPORT-v0.3.0.md
RELEASE_NOTES_v0.3.0.md
requirements-worker.txt
src/
  bundles.js
  bundle-flow.js
worker/
  __init__.py
  __main__.py
  cli.py
  schema.py
  planning.py
  media.py
  runtime.py
  engines/
    __init__.py
    base.py
    fake.py
    ltx.py
    wan.py
  tests/
    __init__.py
    test_worker.py
  notebook/
    syj_video_forge_gpu.ipynb
docs/
  BUNDLE-FORMAT.md
  PLATFORM-POLICIES.md
  WORKER-LIVE.md
  WORKER-VERIFY.md
  verification/
    REPORT-TEMPLATE.md
scripts/
  test_notebook.py
tests/
  bundles.test.js
```

## Existing files updated

- `.gitignore`
- `.github/workflows/ci.yml` (installs FFmpeg and runs `scripts/verify.sh`)
- `CHANGELOG.md`, `README.md`, `index.html`, `styles.css`
- `src/app.js`, `src/core.js`
- `scripts/build-site.sh`, `scripts/build-site.ps1`, `scripts/static_check.py`, `scripts/verify.sh`, `scripts/verify.ps1`
- `backend/tests/test_backend.py` (closes the HTTP 413 `HTTPError` response)
- `docs/ARCHITECTURE.md`, `docs/MODELS.md`, `docs/PLATFORMS.md`, `docs/PROVIDERS.md`, `docs/SECURITY.md`, `docs/TROUBLESHOOTING.md`, `docs/QA-CHECKLIST.md`

No existing files were deleted or renamed.

## Test results — actual local output

Command: `PYTHONWARNINGS=error::ResourceWarning sh scripts/verify.sh`

- **Node.js:** `# tests 38`, `# pass 38`, `# fail 0`, `# skipped 0`.
  - Includes bundle creation, 30-second/six-scene planning, image magic/MIME validation, image SHA, manifest import success, wrong SHA, wrong job ID, wrong schema, oversized video, unknown-kind spoof rejection, test-pattern labeling, and bundle-state transitions.
  - All 22 pre-existing Node tests also passed.
- **Backend Python unittest:** `Ran 17 tests ... OK`.
  - Includes the existing real-server FFmpeg test-pattern MP4 integration.
  - `test_request_size_limit` passed with `ResourceWarning` promoted to an error; no unclosed-HTTPError warning was emitted.
- **Worker Python unittest:** latest run `Ran 15 tests ... OK`; all 15 passed, including the changed-input resume invalidation and per-scene frame-normalization regressions. The earlier isolated `python -S -m unittest discover -s worker/tests -v` run passed all 13 tests that existed at that time with site packages disabled; this older isolated result is not a rerun of the current 15-test suite.
  - Scene planning for `8n+1` and `4n+1`; 30-second/six-scene plan; base-seed-plus-one-based-index; schema and image magic validation; no eager torch import; FakeEngine blocked from normal engine registry; black/constant/NaN/normal frame health tests; degenerate output marks job failed and removes any final MP4; incremental manifest writes; resume skips hash-matching scene files; changed-job resume invalidation; per-scene frame normalization; FakeEngine end-to-end creates a stitched MP4 that `ffprobe` reads as H.264 with positive duration.
- **Latest full verification:** `sh scripts/verify.sh` exited `0`; Node.js 38/38, backend Python 17/17, worker Python 15/15 — **70 automated tests passed, 0 failed**. Python/JavaScript syntax, notebook structure, static-site build, static checks, and Git whitespace check also passed.
  - FFmpeg/ffprobe integration was **not skipped** because both executables were present.
- **Python syntax:** passed for backend, worker, scripts, and tests.
- **JavaScript syntax:** passed for core, providers, app, bundles, and bundle flow.
- **Notebook structure:** `NOTEBOOK CHECK: PASS (nbformat 4, 16 cells, 8 code cells compile, required platform/worker sections present)`.
- **Static check:** `STATIC CHECK: PASS (30 required files; 7 built-site files; local runtime assets; documented external anchors allowed; no known secret patterns)`.
- **Static site build:** `Built static site into .../site` and exact expected file set checked.
- **Full verification:** exit code `0`, `VERIFY: PASS`.
- The Git whitespace step in `verify.sh` reported `SKIP: not a Git working tree` because the overlay was built from the release ZIP rather than a Git clone. The recipient should run `git diff --check` after overlaying it on their clone.

### Smoke-test failure path (not a GPU verification)

Command: `python -m worker smoke-test --engine ltx-video --out /tmp/syj-v03-smoke`

- Exit code: `1` (expected for this environment).
- Report status: `failed`.
- GPU: `CUDA unavailable`; no VRAM or compute capability available.
- PyTorch: `2.10.0+cpu`; Diffusers/Transformers/Accelerate not installed.
- Exact error: `EngineError: LTX dependencies unavailable: No module named 'diffusers'. Install requirements-worker.txt in the GPU environment.`
- The command wrote `/tmp/syj-v03-smoke/smoke.json`, confirming the failure report is written and the CLI exits non-zero. This does **not** count as a successful inference test.

## Explicitly unverified / not run

- **UNVERIFIED ON REAL HARDWARE:** LTX load/inference, Wan load/inference, fp16/bf16 numerical stability, VRAM peak on a GPU, output visual quality, speed, and model frame compatibility.
- Kaggle notebook execution, Google Colab execution, Internet/model download behavior on those platforms, platform-specific policy approval, and session/quota behavior.
- Real browser execution, video decode/import in Chrome/Firefox/Safari/Edge, mobile browser behavior, and end-user file picker interactions. Node tests exercise bundle/manifest logic but are not browser tests.
- Windows execution and PowerShell `scripts/verify.ps1` (PowerShell was not installed in the build environment).
- Installing the pinned ML dependency set together with a platform-preinstalled PyTorch/CUDA stack.
- The LTX and Wan adapter calls against the currently hosted model repositories; both are implemented but not runtime-tested here.
- GitHub Actions/Pages deployment and actual public Pages state. No remote push, tag creation, or release publication was performed.

## Known risks / follow-up

1. The model adapters may need API adjustments after the first real model load; check the exact Diffusers version and model card before interpreting a failure as a model limitation.
2. LTX-Video's license is not a blanket Apache license. Review its complete license and revenue/use restrictions before commercial use. Wan's documented standard 720p path lists 24 GB VRAM; do not promise it fits 16 GB.
3. The browser verifies integrity, not authenticity. The manifest is unsigned; model/GPU/VRAM fields are self-reported and can be forged by an actor replacing both files.
4. A generated bundle contains the prompt and optional image. It leaves the browser only if the user uploads it to a notebook or machine they choose.
5. The UI and backend still require real-browser regression testing before a public release. The local backend/test-pattern provider remains synthetic and is not labeled AI generation.
6. Live tunnel/HTTP-worker mode is explicitly **NOT IMPLEMENTED**; it remains design-only in `docs/WORKER-LIVE.md`.

## Commands for the owner after downloading the overlay

Place the ZIP beside the existing clone, then run from the repository root. Python's standard library `zipfile` is used so the extraction command works wherever Python is available:

```sh
python -c "import zipfile; z=zipfile.ZipFile('../SYJ-Video-Forge-v0.3.0.zip'); z.extractall('.')"
sh scripts/verify.sh

git status --short --branch
git status --ignored --short
git diff --check
git diff --stat

git add -A
git diff --cached --check
git diff --cached --stat
git commit -m "feat: add GPU worker bundle flow"
git push origin main

# Wait for the latest CI run to finish successfully before tagging.
gh run list --repo SHalimoosavi/SYJ-Video-Forge --limit 5
gh run watch <RUN_ID> --exit-status

# Only after CI is green and the v0.3.0 tag does not already exist:
git tag -a v0.3.0 -m "SYJ Video Forge v0.3.0 pre-release"
git push origin refs/tags/v0.3.0

# Publish the pre-release with the same notes and attach the ZIP/checksum/QA report:
gh release create v0.3.0 --verify-tag --prerelease \
  --title "SYJ Video Forge v0.3.0 (Pre-release)" \
  --notes-file RELEASE_NOTES_v0.3.0.md \
  ../SYJ-Video-Forge-v0.3.0.zip \
  ../SYJ-Video-Forge-v0.3.0.zip.sha256 \
  QA-REPORT-v0.3.0.md
```

For PowerShell, use `./scripts/verify.ps1` instead of `sh scripts/verify.sh`; its execution was not verified here. Review `git status --ignored --short` before `git add -A`, and do not commit local output folders or secrets.

## Per-test result list

All entries below were emitted by the final `PYTHONWARNINGS=error::ResourceWarning sh scripts/verify.sh` run and passed. No test was reported as skipped in this environment.

### Node.js tests — 38 PASS

- PASS — `bundle creation follows schema v1 and plans six scenes for 30 seconds`
- PASS — `Long preset is 30 seconds and bundle has random 128-bit id`
- PASS — `image validation checks MIME, size and magic bytes`
- PASS — `oversized starting image is rejected`
- PASS — `bundle validator rejects a wrong schema version`
- PASS — `image bundle records matching SHA-256 and base64`
- PASS — `manifest import succeeds only when bundle id, schema, signature and SHA match`
- PASS — `manifest import rejects wrong SHA-256`
- PASS — `manifest import rejects wrong jobId`
- PASS — `manifest import rejects wrong schema`
- PASS — `manifest import rejects oversized video before reading it`
- PASS — `failed/incomplete manifest is never importable`
- PASS — `manifest kind spoof attempt with unknown kind is rejected`
- PASS — `test-pattern manifest is accepted only as a test-pattern label`
- PASS — `AI kind cannot be spoofed with the test-only engine identity`
- PASS — `bundle state machine includes awaiting_worker, importing, completed, failed and cancelled`
- PASS — `state transitions`
- PASS — `prompt validation`
- PASS — `image validation`
- PASS — `URL normalization`
- PASS — `history accepts only real metadata`
- PASS — `30 seconds creates six scenes`
- PASS — `disclosure states destination`
- PASS — `destination disclosure exact text for each provider`
- PASS — `HTTP health success and provider capabilities`
- PASS — `HTTP health reports 4xx and 5xx status errors`
- PASS — `HTTP health network and CORS-style failures have useful guidance`
- PASS — `HTTP request supports caller abort`
- PASS — `HTTP request timeout aborts fetch with a clear error`
- PASS — `non-JSON success body is reported`
- PASS — `non-JSON 5xx response preserves HTTP status`
- PASS — `submitText sends JSON to API and returns job id`
- PASS — `submitImage encodes bytes as base64 with MIME metadata`
- PASS — `status polling reads job state and progress`
- PASS — `result builds direct MP4 URL and cancel calls API`
- PASS — `cancel before job id returns aborts request and discards late response`
- PASS — `cancel mid-progress preserves job id for backend cancellation`
- PASS — `late result after cancel is discarded`

### Backend Python tests — 17 PASS

- PASS — `test_active_job_limit`
- PASS — `test_cancel_stops_work`
- PASS — `test_concat_helper_reports_stream_copy_or_fallback`
- PASS — `test_cors_allowlist_rejects_wildcard`
- PASS — `test_ffmpeg_provider_terminates_process_on_cancel`
- PASS — `test_image_size_and_magic_validation`
- PASS — `test_job_lifecycle`
- PASS — `test_path_safety`
- PASS — `test_preflight_cors_and_private_network`
- PASS — `test_range_http_response`
- PASS — `test_range_parsing`
- PASS — `test_request_size_limit`
- PASS — `test_running_job_is_marked_failed_after_restart`
- PASS — `test_schema_validation`
- PASS — `test_supported_image_is_saved_inside_job_directory`
- PASS — `test_ttl_cleanup`
- PASS — `test_real_server_testpattern_mp4_pipeline`

### Worker Python tests — 15 PASS

- PASS — `test_30_second_planning_respects_frame_rules`
- PASS — `test_degenerate_guard_black_constant_nan_and_normal_frames`
- PASS — `test_degenerate_scene_fails_job_and_never_leaves_successful_final`
- PASS — `test_engine_load_failure_writes_failed_manifest`
- PASS — `test_fake_engine_end_to_end_stitches_mp4_and_ffprobe_reads_it`
- PASS — `test_fake_engine_is_not_a_normal_cli_engine`
- PASS — `test_image_magic_and_sha_validation`
- PASS — `test_importing_worker_does_not_import_torch`
- PASS — `test_manifest_is_written_incrementally_after_each_scene`
- PASS — `test_manifest_rejects_wrong_job_id`
- PASS — `test_model_extra_frames_are_trimmed_per_scene_before_stitch`
- PASS — `test_resume_rejects_manifest_when_job_inputs_change`
- PASS — `test_resume_skips_scene_when_file_sha_matches_manifest`
- PASS — `test_scene_seed_is_base_plus_one_based_index`
- PASS — `test_schema_validates_bundle_and_rejects_wrong_schema`

### Archive/overlay validation

- PASS — ZIP archive integrity (`ZipFile.testzip()` returned no corrupt member).
- PASS — all archive paths are relative and contain no `..` traversal components.
- PASS — archive contains no generated `site/`, `.git/`, bytecode, MP4 output, or model-weight files.
- PASS — SHA-256 sidecar matched the archive at packaging time.
- PASS — overlay applied to a clean extraction of the v0.2.0 base and the full verification suite passed.
- PASS — `git diff --no-index --check` between the original ZIP extraction and the overlay tree emitted no whitespace diagnostics (exit code 1 only because files differ).
