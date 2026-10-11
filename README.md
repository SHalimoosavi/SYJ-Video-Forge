# SYJ Video Forge

Open-source video workflow foundation by SAYANJALI NEXUS PRIVATE LIMITED.

## Current status and limitations

**Pre-release v0.1.0; foundation only. Phase 1 includes no real inference engine.** Mock mode simulates UI progress and never creates a video. Real generation requires a separately implemented compatible backend and model. A 30-second output is a design target, not a working capability.

Zero-cost by default: no mandatory paid API, hosting, credits, subscription, cloud storage, analytics, ads, trackers, CDN scripts, or remote fonts. Optional custom HTTP endpoint is off by default. Provider terms and possible costs are independent; no free tier is represented as unlimited.

## Run locally
Requires Python 3 or Node.js. No npm install or model download.
```sh
python3 scripts/dev_server.py
```
Open `http://127.0.0.1:8000/`. Windows: `python scripts/dev_server.py` or `py scripts/dev_server.py`. Optional Node server: `node scripts/dev-server.mjs`.

## GitHub Pages
Target: `https://shalimoosavi.github.io/SYJ-Video-Forge/`. Pages does not assume localhost is the developer's machine. Without a configured backend the app reports that the backend is unavailable. See `docs/TROUBLESHOOTING.md` for CORS, mixed content, Private Network Access and Safari restrictions.

## Verify
```sh
sh scripts/verify.sh
```
PowerShell: `./scripts/verify.ps1`. Node built-in test runner is required for unit tests.

## Long-video design
30 seconds is planned as six 5-second scenes. A future backend would condition each clip on the previous clip's final frame and stitch clips using ffmpeg. Scene drift is an expected quality trade-off. This is design only. A future worker might use a local GPU or a user-controlled notebook session through a tunnel; that is not operational.

## Docs
Architecture, provider contract, candidate models, troubleshooting and platform notes are in `docs/`. Project code is MIT licensed; model weights and external services have independent terms.
