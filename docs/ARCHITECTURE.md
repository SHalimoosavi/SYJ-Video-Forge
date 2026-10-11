# Architecture

## Current components

- `index.html`, `styles.css`, and `src/`: static browser UI, validation, disclosure, provider client, progress display, cancellation guard, local history, video preview, and download.
- `backend/server.py`: `http.server.ThreadingHTTPServer`, JSON API, explicit CORS allowlist, request-size enforcement, optional same-origin static frontend, and byte-range MP4 responses.
- `backend/jobs.py`: bounded thread queue, unguessable UUID job IDs, persisted JSON metadata, TTL cleanup, cancellation events, restart recovery, scene progress, and output confinement.
- `backend/providers/base.py`: abstract provider contract and capability declaration.
- `backend/providers/testpattern.py`: FFmpeg `lavfi` test-pattern provider, explicitly not AI.
- `backend/media.py`: argument-list subprocess calls, last-frame extraction, concat demuxer with re-encode fallback, and Range parsing.

## Job flow

A request is schema-validated before a job is queued. The worker renders each storyboard scene into a private job directory. For every scene except the last, it extracts the clip's final frame and passes that frame path to the next provider call. The provider may use or ignore it according to its declared capabilities. FFmpeg concatenates clips using stream copy first, then re-encodes if stream copy fails. The completed MP4 is exposed only through the job result endpoint, which supports single byte ranges for seeking.

The default storyboard is six 5-second scenes for 30 seconds. Short durations and explicit scene counts are allowed for tests. This implementation is a pipeline validator; the included provider produces test patterns, not prompt-conditioned footage.

## Safety and limits

The server binds to `127.0.0.1:8080` by default. Non-loopback binding requires an explicit `--host` flag and prints a warning, but does not add authentication. Request bodies, image sizes, prompt length, scene count, active job count, and job retention are bounded. Job IDs are random UUID hex strings; paths are derived only from validated IDs and fixed filenames under the configured data directory. Subprocesses use argument arrays and do not invoke a shell. Cancellation sets a thread event and terminates a running FFmpeg process.

The default CORS allowlist is intentionally explicit. Browser private-network behavior differs by browser and origin; use `--serve-frontend` to serve the UI and API on one local origin where possible.
