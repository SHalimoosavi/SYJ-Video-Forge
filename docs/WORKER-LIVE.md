# Live worker transport — design only

> **NOT IMPLEMENTED.** SYJ Video Forge v0.3.0 supports file bundles only. No tunnel, HTTP-worker mode, remote polling, reverse proxy, or inbound worker listener is shipped.

A future design would need an explicit threat model, authentication, replay protection, request size limits, CORS policy, cancellation semantics, TLS, and an opt-in review before any live transport could be enabled. Do not expose the current local backend or a notebook runtime to the public internet.
