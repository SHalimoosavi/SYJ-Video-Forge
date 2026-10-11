# Provider contract
Interface methods: `health()`, `capabilities()`, `submitText(payload)`, `submitImage(payload)`, `status(jobId)`, `result(jobId)`, `cancel(jobId)`.

HTTP client contract: `GET /health`, `GET /capabilities`, `POST /jobs` (JSON), `POST /jobs/image` (multipart), `GET /jobs/{id}`, `GET /jobs/{id}/result`, `DELETE /jobs/{id}`. Capability response may declare models, durations, ratios, image support, and negative prompt support. This contract is not a backend implementation.

Mock (demo only) is local UI simulation; label is `SIMULATED, not AI generated`; no video file or history entry is created. Local backend default is `http://127.0.0.1:8080`; loopback points to the visitor's own device. Optional Custom HTTP endpoint is off by default. After submit, prompt and, in image mode, the image are sent to that configured endpoint. Use only endpoints you trust. No credentials belong in URLs or source code.
