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
