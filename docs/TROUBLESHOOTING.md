# Troubleshooting

- **Backend unreachable:** start `python -m backend.server --serve-frontend`, check the configured URL and port, and try the local frontend on `http://127.0.0.1:8080/`.
- **FFmpeg missing:** run `ffmpeg -version`; install a compatible FFmpeg build and restart the backend. `GET /api/health` reports availability. No video is fabricated if FFmpeg is absent.
- **Provider unavailable:** inspect `/api/capabilities`. The included test-pattern provider must be available for a job to run and does not support image-to-video or negative prompts.
- **CORS or private-network error:** use `--serve-frontend` to keep the frontend and API on the same origin. Otherwise configure the exact frontend origin with `--cors-origins`; wildcard origins are rejected. A correct CORS policy cannot override browser-level private-network restrictions.
- **Image rejected:** use a valid PNG/JPEG/WebP file under 10 MiB. The MIME type and magic bytes must agree. The test-pattern provider does not accept images as conditioning input.
- **Request too large:** the JSON request limit is 15 MiB and the decoded image limit is 10 MiB.
- **Job interrupted after restart:** the backend marks persisted queued/running jobs failed rather than pretending they resumed. Submit a new job.
- **Cancellation:** the UI aborts in-flight requests and ignores late responses; if a job ID is known it also asks the backend to stop it. A request cancelled before the server's job ID reaches the browser may leave a job briefly running server-side; it will still be bounded by job limits and TTL cleanup.
- **Seeking fails:** confirm the endpoint responds with `Accept-Ranges: bytes` and `206 Partial Content` to a Range request. Some proxies or browser policies may interfere.
- **GitHub Pages workflow fails at configure-pages:** verify **Settings → Pages → Build and deployment → Source = GitHub Actions**. The workflow cannot change this repository setting itself.


## GPU worker bundle issues (v0.3.0)

- **CUDA unavailable:** select an available GPU accelerator or use a local CUDA-enabled environment. `python -m worker smoke-test` exits non-zero if loading/inference fails.
- **bf16/fp16 errors:** the worker chooses bf16 only when CUDA reports support; otherwise it selects fp16. Some checkpoints may still fail in fp16. Capture the exact error and hardware report; do not edit a failed manifest to mark success.
- **Out of memory:** try the primary LTX-Video adapter at the documented low resolution, reduce scene/clip complexity, or use a GPU with more VRAM. Wan 2.2's official standard 720p instructions state at least 24 GB VRAM; 16 GB compatibility is unverified.
- **Degenerate output:** if a scene is black, near-uniform or contains non-finite values, the worker fails the scene and records luminance metrics. The error mentions dtype as one possible cause. Do not treat the output as a successful generation.
- **Resume:** `--resume` skips only scenes whose existing file SHA-256 matches the incremental manifest. A changed/missing hash causes regeneration.
- **Import rejects result:** select `result.mp4` and `manifest.json` together, and create the bundle in this session or select the matching earlier `job.json`. Do not rename files away from the manifest's expected names. The browser checks the MP4 SHA-256.
- **Model download/terms:** review the exact model page and license. If access is gated, accept the terms on the official model page and provide a token only through a platform secret store or hidden prompt. Never put tokens in job.json or repository files.
- **Hosted notebook restriction:** follow the current Kaggle/Colab policies. This project does not implement an HTTP worker or tunnel.
