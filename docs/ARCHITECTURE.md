# Architecture
Vanilla HTML/CSS/ES modules. `src/core.js` holds pure validation, state transition, history and scene-plan logic. `src/providers.js` exposes `health()`, `capabilities()`, `submitText()`, `submitImage()`, `status()`, `result()`, and `cancel()`. `src/app.js` binds controls.

There is no inference engine, Python API, queue, GPU worker or ffmpeg pipeline. Real backend results are downloaded directly; browser history contains metadata only. Mock mode sends nothing and makes no video.

Long-video target: six 5-second scenes for 30 seconds, with each clip conditioned on the previous final frame and backend ffmpeg stitching. Drift, inconsistent motion, and stitching artifacts can occur. Future worker design may use local GPU or a user-controlled free notebook tunnel; neither is included.
