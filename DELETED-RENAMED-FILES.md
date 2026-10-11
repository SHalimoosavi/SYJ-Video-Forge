# Deleted / renamed files for v0.2.0 overlay

## Tracked source files deleted or renamed

- None. v0.2.0 is an overlay on the v0.1.0 repository; existing source paths are retained.

## Generated/stale files to remove or regenerate after overlay

- `scripts/__pycache__/` — stale Python bytecode from v0.1.0; safe to remove.
- `backend/__pycache__/`, `backend/providers/__pycache__/`, `backend/tests/__pycache__/` — generated Python bytecode; safe to remove.
- `site/` — generated Pages artifact; `scripts/build-site.sh` or `scripts/build-site.ps1` recreates it. It is intentionally not included in the source ZIP.

## Local runtime data

- `data/` is gitignored and contains local job metadata, intermediate clips, frames, and MP4 output. It is intentionally not included in the ZIP. Do not remove it unless you intend to delete locally generated jobs and videos.
