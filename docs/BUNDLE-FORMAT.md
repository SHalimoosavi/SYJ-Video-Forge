# File bundle format — schema v1

The browser creates `job.json`. The GPU worker reads it locally and writes `result.mp4` plus `manifest.json`. Files are exchanged manually; there is no tunnel, inbound network listener, cloud storage, or worker HTTP mode.

## job.json

Required fields: `schemaVersion: 1`, random 128-bit lowercase hex `jobId`, ISO `createdAt`, `mode` (`text` or `image`), `prompt`, `negativePrompt`, `aspect`, `resolution`, integer `seed`, `totalSeconds`, `fps`, `clipSeconds`, `preset`, `scenes`, `continuity` (`last_frame` or `none`), `engine: {id}`, and `image` (null or `{mime, sha256, base64}`). `Long` preset requires at least 30 seconds. Image MIME is PNG/JPEG/WebP; magic bytes and SHA-256 are checked and payload is capped at 10 MiB. The complete bundle can contain private prompts and image bytes. Do not upload it to a service you do not trust.

`scenes` contains ordered `{index, prompt}` entries. Default prompts use the base prompt plus a short continuity suffix generated locally; no paid language model is called. The UI lets the user edit every scene. Scene count is `ceil(totalSeconds / clipSeconds)`. Per-scene seed is `base seed + 1-based scene index` modulo 2^31. Engine frame constraints are applied by the worker and recorded in the manifest.

## manifest.json

The worker writes this incrementally. Fields include `schemaVersion`, `jobId`, `kind` (`ai_generated` or `test_pattern`), `engine` (`id`, model repo ID, revision if known, license), `libraries`, `hardware` (`gpu`, total/peak VRAM, compute dtype), `parameters`, per-scene index/seed/frame count/seconds/file/SHA-256/generation seconds/luminance metrics/status, `final` (file, SHA-256, duration, width, height, fps, codec), timestamps, warnings, and `degenerateChecks`.

`kind: ai_generated` is a self-reported worker claim, not a cryptographic attestation. Browser import checks the schema, job ID, MP4 signature, size limit and SHA-256, then asks the browser to parse the MP4. The manifest can still be forged by someone who can replace both files; the UI therefore explicitly labels model/GPU information as self-reported. No model weights are included in the repository.

## Result import

Select `result.mp4` and `manifest.json` together. The job ID must match the bundle created in the current session, or a previously saved `job.json` selected for that import. Video bytes are held in a session blob URL only; history persists metadata, never video bytes.
