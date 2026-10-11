# SYJ Video Forge v0.2.0 — QA Report

**Status:** PRE-RELEASE foundation. **Not an AI video-generation product.**

## Repository and packaging

- Baseline: v0.1.0 commit `0bbe185b7c549a2eb098c192e29ca97a7ee0f632`.
- ZIP is an overlay archive with files at repository root.
- Local test environment: Python 3.13.5, Node.js v22.16.0, FFmpeg and ffprobe available.
- No Git history was created or rewritten in this build environment.
- No real model, model weights, paid service, cloud storage, telemetry, CDN, or remote fonts are included.

## Audit items: reproduction and fix evidence

### 1. GitHub Pages workflow

**Reproduced from the actual failed run.** Run `38140327274` failed in `actions/configure-pages@v5`, before artifact upload. The log's actual error was: `Get Pages site failed. Please verify that the repository has Pages enabled and configured to build using GitHub Actions ... Not Found`. This indicates the Pages site/repository setting was unavailable to the action; it was not a Jekyll or static-site compile failure. The later historical dynamic Pages run `38140433953` succeeded, but that does not establish deployment of this v0.2.0 build.

**Fix included:** the workflow uses `contents: read`, `pages: write`, `id-token: write`, `actions/configure-pages`, `actions/upload-pages-artifact`, `actions/deploy-pages`, the `github-pages` environment, and the `pages` concurrency group. It builds and uploads only `site/`. `scripts/build-site.sh` and `scripts/build-site.ps1` copy only `index.html`, `styles.css`, and `src/`.

**Maintainer action required:** set **Settings → Pages → Build and deployment → Source → GitHub Actions**. A workflow cannot enable this setting. Pages deployment was not attempted from this ZIP build; do not infer deployment success.

### 2. Provider destination disclosure

**Reproduced against v0.1.0 code:** `requestDisclosure("custom", "https://example.test")` returned `After submission, prompthttps://example.test and, in image mode, the selected image are sent to https://example.test. Only use an endpoint you trust.` The prompt label was joined directly to the URL.

**Fix and regression evidence:** disclosure strings are explicit for `mock`, `local`, `custom`, and unknown providers. The new Node test asserts the exact string for all four. Final result: passed.

### 3. Cancellation race

**Reproduction/documented behavior:** v0.1.0 assigned the job ID only after the submit request resolved and had no abort signal or stale-response guard. Cancel before the ID arrived could not abort the request; late submit/status/result work could still update the UI.

**Fix and tests:** `RunGate` and `AbortController` abort in-flight HTTP requests and invalidate stale responses. When a job ID is known, the UI sends `POST /api/jobs/{id}/cancel`. The backend uses a `threading.Event` and terminates a running FFmpeg subprocess. Node regression tests cover cancel before ID return, cancel after an ID is known, and discarded late results. Python tests cover event-driven cancellation, FFmpeg subprocess termination, and saving a supported image within the job directory. All passed.

**Known boundary:** if the server creates a job but the response containing its ID never reaches the browser, the client cannot send an ID-specific cancel. The job remains bounded by active-job limits and TTL cleanup.

### 4. HTTP provider tests and errors

**Reproduction/documented behavior:** v0.1.0 had core-helper tests but no injected-fetch HTTP provider test suite. Non-JSON error bodies could lose their message after attempting JSON parsing; network errors lacked actionable CORS/private-network guidance.

**Fix and tests:** the provider now supports injected fetch, request timeout, caller abort, readable non-JSON errors, HTTP status errors, text/image submissions, status polling, result URL resolution, and cancellation. Tests cover health success/failure, timeout, network/CORS-style failure, non-JSON responses, 4xx/5xx, submit text/image, status, result, and cancel. All passed.

### 5. Release metadata and commit email

GitHub release metadata showed v0.1.0 had `prerelease: false`. `CHANGELOG.md` records that the v0.1.0 release is intended to be a pre-release and is being corrected manually by the repository owner. This build does not modify v0.1.0 release metadata or rewrite Git history. `RELEASE_NOTES_v0.2.0.md` explicitly marks v0.2.0 as **PRE-RELEASE**.

The placeholder commit email is being fixed by the owner; this build does not touch Git history.

## Implemented backend and QA coverage

- Python standard-library HTTP server, loopback default, explicit warning for non-loopback binding.
- API health/capabilities/jobs/status/result/cancel/delete routes.
- Hand-validated JSON, request-size limit, image base64 cap and PNG/JPEG/WebP magic-byte validation, prompt/duration/seed/scene checks.
- Explicit CORS allowlist, rejected wildcard, preflight and Private Network Access response header.
- Random UUID-hex job IDs, fixed paths under configured data directory, metadata persistence, restart recovery, TTL cleanup, active job cap.
- Thread queue with queued/running/completed/failed/cancelled states and per-scene progress.
- FFmpeg test-pattern provider, last-frame extraction between clips, concat demuxer stream-copy and re-encode fallback, MP4 Range support.
- Test-pattern output and history entries carry `kind: test_pattern`; UI label is **TEST PATTERN: not AI generated**. Mock remains simulated and does not create a video.
- Supported provider image input is stored within the job directory; the shipped test-pattern provider honestly rejects image-to-video.
- Static Pages artifact is built separately into `site/`.

## Final test result

`sh scripts/verify.sh` exited **0**.

- Node: 22 tests passed, 0 failed, 0 skipped.
- Python unittest: 17 tests passed, 0 failed, 0 skipped.
- Real server integration: passed. Started the HTTP server on a random port, submitted a 3-scene × 1-second test-pattern job, polled to completion, downloaded MP4, and used ffprobe to validate H.264 video codec and approximately 3-second duration.
- FFmpeg cancellation test: passed; subprocess stopped after cancellation.
- Static check: passed; expected files and five built-site files validated, local asset links resolved, no known secret patterns found.
- Python compile and JavaScript syntax checks: passed.
- Skipped tests: none in this environment. The FFmpeg integration test is designed to skip explicitly if ffmpeg or ffprobe is missing; both were present here.
- Git whitespace check inside `verify.sh`: skipped because the build/ZIP staging directory is not a Git working tree. Run it after overlaying into your Git clone.

## Known bugs / limitations

- No real AI model or prompt-conditioned video generation is implemented.
- Test-pattern provider intentionally rejects image-to-video and negative prompts.
- If cancellation occurs before the job ID response arrives, the browser cannot identify that server job to cancel; stale client responses are still discarded.
- The unauthenticated backend should remain loopback-only. CORS is not authentication.
- HTTPS GitHub Pages to local HTTP API calls may be blocked by browser private-network/mixed-origin rules; same-origin local serving is recommended.
- Python standard-library server is intended for local QA, not public production exposure.

## Unverified by this build

- Real browser visual/accessibility behavior at narrow and wide widths.
- PowerShell script execution.
- Windows FFmpeg/codec availability and behavior.
- macOS and Android runtime behavior.
- GitHub Pages deployment of this v0.2.0 revision; maintainer must verify repository Pages source setting and Actions run.
- Any real AI generation, because no AI provider is included.

## Project file tree

```text
.github/workflows/ci.yml
.github/workflows/pages.yml
.gitignore
CHANGELOG.md
CONTRIBUTING.md
DELETED-RENAMED-FILES.md
LICENSE
QA-REPORT-v0.2.0.md
README.md
RELEASE_NOTES_v0.1.0.md
RELEASE_NOTES_v0.2.0.md
SECURITY.md
backend/__init__.py
backend/config.py
backend/jobs.py
backend/media.py
backend/providers/__init__.py
backend/providers/base.py
backend/providers/testpattern.py
backend/server.py
backend/tests/__init__.py
backend/tests/test_backend.py
docs/ARCHITECTURE.md
docs/AUDIT-v0.1.0.md
docs/MODELS.md
docs/PLATFORMS.md
docs/PROVIDERS.md
docs/QA-CHECKLIST.md
docs/SECURITY.md
docs/TROUBLESHOOTING.md
index.html
scripts/build-site.ps1
scripts/build-site.sh
scripts/dev-server.mjs
scripts/dev_server.py
scripts/static_check.py
scripts/verify.ps1
scripts/verify.sh
src/app.js
src/core.js
src/providers.js
styles.css
tests/core.test.js
tests/providers.test.js
```

## Full verification output

Captured output from the final `sh scripts/verify.sh` run (ANSI control sequences removed for readability):

```text
=== Node.js tests ===
TAP version 13
# Subtest: state transitions
ok 1 - state transitions
  ---
  duration_ms: 1.517636
  type: 'test'
  ...
# Subtest: prompt validation
ok 2 - prompt validation
  ---
  duration_ms: 0.244429
  type: 'test'
  ...
# Subtest: image validation
ok 3 - image validation
  ---
  duration_ms: 0.187072
  type: 'test'
  ...
# Subtest: URL normalization
ok 4 - URL normalization
  ---
  duration_ms: 0.28484
  type: 'test'
  ...
# Subtest: history accepts only real metadata
ok 5 - history accepts only real metadata
  ---
  duration_ms: 0.545544
  type: 'test'
  ...
# Subtest: 30 seconds creates six scenes
ok 6 - 30 seconds creates six scenes
  ---
  duration_ms: 0.287705
  type: 'test'
  ...
# Subtest: disclosure states destination
ok 7 - disclosure states destination
  ---
  duration_ms: 0.337249
  type: 'test'
  ...
# Subtest: destination disclosure exact text for each provider
ok 8 - destination disclosure exact text for each provider
  ---
  duration_ms: 1.236317
  type: 'test'
  ...
# Subtest: HTTP health success and provider capabilities
ok 9 - HTTP health success and provider capabilities
  ---
  duration_ms: 25.05934
  type: 'test'
  ...
# Subtest: HTTP health reports 4xx and 5xx status errors
ok 10 - HTTP health reports 4xx and 5xx status errors
  ---
  duration_ms: 1.308275
  type: 'test'
  ...
# Subtest: HTTP health network and CORS-style failures have useful guidance
ok 11 - HTTP health network and CORS-style failures have useful guidance
  ---
  duration_ms: 0.296959
  type: 'test'
  ...
# Subtest: HTTP request supports caller abort
ok 12 - HTTP request supports caller abort
  ---
  duration_ms: 0.322898
  type: 'test'
  ...
# Subtest: HTTP request timeout aborts fetch with a clear error
ok 13 - HTTP request timeout aborts fetch with a clear error
  ---
  duration_ms: 10.552651
  type: 'test'
  ...
# Subtest: non-JSON success body is reported
ok 14 - non-JSON success body is reported
  ---
  duration_ms: 0.52358
  type: 'test'
  ...
# Subtest: non-JSON 5xx response preserves HTTP status
ok 15 - non-JSON 5xx response preserves HTTP status
  ---
  duration_ms: 0.838316
  type: 'test'
  ...
# Subtest: submitText sends JSON to API and returns job id
ok 16 - submitText sends JSON to API and returns job id
  ---
  duration_ms: 0.656762
  type: 'test'
  ...
# Subtest: submitImage encodes bytes as base64 with MIME metadata
ok 17 - submitImage encodes bytes as base64 with MIME metadata
  ---
  duration_ms: 0.999388
  type: 'test'
  ...
# Subtest: status polling reads job state and progress
ok 18 - status polling reads job state and progress
  ---
  duration_ms: 0.730243
  type: 'test'
  ...
# Subtest: result builds direct MP4 URL and cancel calls API
ok 19 - result builds direct MP4 URL and cancel calls API
  ---
  duration_ms: 1.074322
  type: 'test'
  ...
# Subtest: cancel before job id returns aborts request and discards late response
ok 20 - cancel before job id returns aborts request and discards late response
  ---
  duration_ms: 0.333333
  type: 'test'
  ...
# Subtest: cancel mid-progress preserves job id for backend cancellation
ok 21 - cancel mid-progress preserves job id for backend cancellation
  ---
  duration_ms: 0.104919
  type: 'test'
  ...
# Subtest: late result after cancel is discarded
ok 22 - late result after cancel is discarded
  ---
  duration_ms: 0.146852
  type: 'test'
  ...
1..22
# tests 22
# suites 0
# pass 22
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 113.040859
=== Python unittest suite (integration is explicitly skipped if ffmpeg/ffprobe are absent) ===
test_active_job_limit (test_backend.BackendUnitTests.test_active_job_limit) ... ok
test_cancel_stops_work (test_backend.BackendUnitTests.test_cancel_stops_work) ... ok
test_concat_helper_reports_stream_copy_or_fallback (test_backend.BackendUnitTests.test_concat_helper_reports_stream_copy_or_fallback) ... ok
test_cors_allowlist_rejects_wildcard (test_backend.BackendUnitTests.test_cors_allowlist_rejects_wildcard) ... ok
test_ffmpeg_provider_terminates_process_on_cancel (test_backend.BackendUnitTests.test_ffmpeg_provider_terminates_process_on_cancel) ... ok
test_image_size_and_magic_validation (test_backend.BackendUnitTests.test_image_size_and_magic_validation) ... ok
test_job_lifecycle (test_backend.BackendUnitTests.test_job_lifecycle) ... ok
test_path_safety (test_backend.BackendUnitTests.test_path_safety) ... ok
test_preflight_cors_and_private_network (test_backend.BackendUnitTests.test_preflight_cors_and_private_network) ... SYJ Video Forge: "OPTIONS /api/health HTTP/1.1" 204 -
ok
test_range_http_response (test_backend.BackendUnitTests.test_range_http_response) ... SYJ Video Forge: "GET /api/jobs/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/result HTTP/1.1" 206 -
ok
test_range_parsing (test_backend.BackendUnitTests.test_range_parsing) ... ok
test_request_size_limit (test_backend.BackendUnitTests.test_request_size_limit) ... SYJ Video Forge: "POST /api/jobs HTTP/1.1" 413 -
ok
test_running_job_is_marked_failed_after_restart (test_backend.BackendUnitTests.test_running_job_is_marked_failed_after_restart) ... ok
test_schema_validation (test_backend.BackendUnitTests.test_schema_validation) ... ok
test_supported_image_is_saved_inside_job_directory (test_backend.BackendUnitTests.test_supported_image_is_saved_inside_job_directory) ... ok
test_ttl_cleanup (test_backend.BackendUnitTests.test_ttl_cleanup) ... ok
test_real_server_testpattern_mp4_pipeline (test_backend.IntegrationTests.test_real_server_testpattern_mp4_pipeline) ... SYJ Video Forge: "POST /api/jobs HTTP/1.1" 202 -
SYJ Video Forge: "GET /api/jobs/46feee70ed58446ebb795100b179eb7d HTTP/1.1" 200 -
SYJ Video Forge: "GET /api/jobs/46feee70ed58446ebb795100b179eb7d HTTP/1.1" 200 -
SYJ Video Forge: "GET /api/jobs/46feee70ed58446ebb795100b179eb7d HTTP/1.1" 200 -
SYJ Video Forge: "GET /api/jobs/46feee70ed58446ebb795100b179eb7d HTTP/1.1" 200 -
SYJ Video Forge: "GET /api/jobs/46feee70ed58446ebb795100b179eb7d HTTP/1.1" 200 -
SYJ Video Forge: "GET /api/jobs/46feee70ed58446ebb795100b179eb7d HTTP/1.1" 200 -
SYJ Video Forge: "GET /api/jobs/46feee70ed58446ebb795100b179eb7d HTTP/1.1" 200 -
SYJ Video Forge: "GET /api/jobs/46feee70ed58446ebb795100b179eb7d HTTP/1.1" 200 -
SYJ Video Forge: "GET /api/jobs/46feee70ed58446ebb795100b179eb7d/result HTTP/1.1" 200 -
ok

----------------------------------------------------------------------
Ran 17 tests in 3.157s

OK
=== Python syntax ===
=== JavaScript syntax ===
=== Build static site ===
Built static site into /tmp/SYJ-Video-Forge-v0.2.0/site
=== Static checks ===
STATIC CHECK: PASS (15 required files; 5 built-site files; local links resolved; no known secret patterns)
=== Git whitespace check for tracked/staged changes (when inside Git) ===
SKIP: not a Git working tree
VERIFY: PASS
```
