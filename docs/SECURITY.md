# Security notes

The local backend is an unauthenticated development service. It binds to `127.0.0.1` by default. Non-loopback binding requires explicit `--host` and prints a warning, but that flag does not add authentication or TLS. Do not expose the backend to an untrusted network.

- CORS uses an explicit allowlist and rejects `*`; CORS is not authentication and does not prevent non-browser clients from calling the API.
- The server caps request bodies at 15 MiB, decoded images at 10 MiB, prompts at 4,000 characters, scenes at 30, and active jobs at a configurable limit.
- Image MIME declarations are checked against PNG/JPEG/WebP magic bytes. This is format validation, not malware scanning.
- Job IDs are random UUID hex values. Paths are derived from validated IDs and fixed filenames under the configured data directory; arbitrary file paths are not accepted from API requests.
- Metadata is persisted locally. The `data/` directory may contain prompts, job metadata, intermediate clips, frames, and MP4 outputs. It is gitignored and should be protected and deleted when no longer needed.
- TTL cleanup removes old job directories. It is not secure erasure.
- FFmpeg is launched with argument lists, not shell interpolation. Keep FFmpeg updated and only process trusted inputs. The current test-pattern provider does not invoke user prompt text as an FFmpeg expression.
- Browser history is local metadata. Test-pattern jobs are labeled as not AI-generated. The mock provider creates no video and is not saved to history.
- Optional HTTP endpoints receive prompt/image data only after submission. Use only endpoints you trust.

Report sensitive vulnerabilities privately through GitHub's private reporting feature where available. Never commit credentials, private keys, private URLs, generated `data/`, or real user media.


## File bundles and imported manifests

A job bundle can contain private prompt text and the complete starting image as base64. The browser discloses that the file leaves the browser only if the user uploads it to a notebook or machine they choose. Image payloads are capped at 10 MiB and validated by MIME magic bytes and SHA-256. The browser caps `job.json` and manifest import sizes, validates the bundle ID and schema, checks MP4 `ftyp`, computes SHA-256 with Web Crypto, and verifies browser playback before presenting a result.

The manifest is not signed. Its `kind`, model ID, revision, GPU, dtype and VRAM fields are self-reported by the worker and can be forged if both files are replaced. The UI therefore says “self-reported by the worker; not independently verified”. SHA-256 protects against accidental mismatch, not malicious authorship. No video bytes are persisted in browser history; history stores metadata only. Imported videos use a blob URL for the current session.

The GPU worker does not accept inbound network connections. A live tunnel/HTTP worker is design-only and is not implemented. Do not expose the local backend to an untrusted network.
