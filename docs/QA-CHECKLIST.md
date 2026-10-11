# Manual QA checklist — v0.2.0 pre-release

Run the backend and frontend together with `python -m backend.server --serve-frontend`, then open `http://127.0.0.1:8080/`.

- [ ] At a narrow browser viewport, confirm controls fit, labels remain readable, and no horizontal overflow appears.
- [ ] At a wide viewport, confirm the two-column layout, status panel, scene progress, and history remain aligned.
- [ ] Switch between text-to-video and image-to-video; the image control should be hidden in text mode.
- [ ] Select a PNG/JPEG/WebP image under 10 MiB; confirm preview and remove-image behavior. Confirm the test-pattern provider reports image-to-video as unsupported rather than pretending to use the image.
- [ ] Click **Check backend**. Confirm provider list and `test_pattern` kind appear, or confirm the UI distinguishes unreachable backend from missing FFmpeg/provider unavailable.
- [ ] Submit a short test job (for example duration 3, scene count 3, clip length 1 when using the API) or a default 30-second job in the UI. Confirm scene progress updates.
- [ ] Confirm the result label says **TEST PATTERN: not AI generated** and playback starts.
- [ ] Seek within the video to exercise HTTP Range requests; confirm the player can seek.
- [ ] Download the MP4 and open it with a local player.
- [ ] Confirm history labels the result as test-pattern and not AI. Confirm Mock mode only simulates progress and does not create or save a video.
- [ ] Cancel during submission and during active rendering. Confirm UI remains Cancelled, late responses do not replace it, and active FFmpeg work stops.
- [ ] Clear history and reload; confirm local history is cleared.
- [ ] Compare Pages behavior with local same-origin behavior. Pages is static-only; HTTPS-to-local-HTTP/private-network calls may be blocked by browser policy.
- [ ] Confirm Settings → Pages → Source is GitHub Actions before expecting a deployment.

## Not covered by automated tests

Real browser rendering, accessibility audit, PowerShell script execution, Windows FFmpeg installation/codec availability, macOS and Android runtime behavior, actual GitHub Pages deployment for this commit, and real AI generation (no AI provider is included).
