# Provider contract and local API

## Shipped provider

`test-pattern` uses FFmpeg `lavfi` to create deterministic synthetic clips with a seed-based visual variation. Its `kind` is `test_pattern`. It is a pipeline validator, **not AI generation**. It supports text prompts as job metadata but does not interpret them. It does not support image-to-video or negative prompts. When FFmpeg is missing, health reports the missing executable and jobs fail with installation guidance; no output is fabricated.

## Provider interface

`backend/providers/base.py` defines `VideoProvider.available()` and `generate_clip(prompt, start_image, seconds, seed, output, progress_cb, cancel_event)`. The capability object declares `text`, `image`, `negative_prompt`, `max_clip_seconds`, `supports_start_image`, and `kind`. Providers must honor cancellation and raise `ProviderError` on failure. A future AI provider must declare its actual capabilities and licensing requirements; none is bundled now.

## API

Base URL when running the default server: `http://127.0.0.1:8080`.

### `GET /api/health`

Example response:

```json
{
  "ok": true,
  "ffmpeg": {"available": true, "path": "/usr/bin/ffmpeg", "message": ""},
  "ffprobe": {"available": true},
  "providers": [{"name":"test-pattern","available":true,"reason":"","kind":"test_pattern"}]
}
```

### `GET /api/capabilities`

Returns provider availability and its capability declaration, including `kind`, `supports_start_image`, maximum clip duration, supported durations, and aspect ratios.

### `POST /api/jobs`

Content-Type: `application/json`; maximum request body is 15 MiB. Image bytes, when supplied, are base64 and separately limited to 10 MiB. PNG/JPEG/WebP magic bytes must match the declared MIME type.

```json
{
  "prompt": "A test scene",
  "negativePrompt": "",
  "duration": 30,
  "aspectRatio": "16:9",
  "seed": 42,
  "mode": "text"
}
```

For an image-mode provider that supports it, `image` is `{ "mime": "image/png", "data": "<base64>" }`. The included provider rejects image-to-video because it does not support starting-image conditioning. Optional test controls `scenes` and `clip_seconds` allow shorter integration jobs.

Successful submission returns HTTP 202 and a job record, for example:

```json
{"id":"<32-hex-character-id>","status":"queued","progress":0,"kind":"test_pattern","provider":"test-pattern","scenes":[{"index":1,"duration":5,"progress":0,"status":"queued"}],"result_url":null}
```

### `GET /api/jobs/{id}`

Returns `queued`, `running`, `completed`, `failed`, or `cancelled`, aggregate progress, per-scene progress, `kind`, `error`, and `result_url` when completed. The server persists metadata as JSON under the configured data directory. Active jobs at restart are marked failed with a retry message.

### `GET /api/jobs/{id}/result`

Returns `video/mp4` only after completion. Supports one `Range: bytes=start-end` request and returns HTTP 206 with `Content-Range`; unsatisfiable ranges return HTTP 416. The browser video element can use range requests to seek.

### Cancellation

`POST /api/jobs/{id}/cancel` and `DELETE /api/jobs/{id}` both request cancellation. The response contains the updated job record. Cancellation sets an event and terminates a running FFmpeg subprocess. Cancellation is best-effort at process boundaries; completed jobs remain completed.

## CORS

Default allowed origins are `http://127.0.0.1:8080`, `http://localhost:8080`, and `https://shalimoosavi.github.io`. Configure with `--cors-origins https://example.test,http://127.0.0.1:8080`. Wildcard origins are rejected. Preflight supports `Content-Type`, `Range`, and the `Access-Control-Request-Private-Network` header. CORS is not authentication. Prefer `--serve-frontend` to avoid cross-origin calls on local use.
