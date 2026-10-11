# GPU worker verification procedure

> **UNVERIFIED ON REAL HARDWARE** until the results below are run and a report is saved. The authoring environment cannot attest to Kaggle, Colab, or local GPU behavior.

## 1. Prepare a GPU session

### Kaggle

1. Create a notebook and open its settings.
2. Enable Internet if permitted for the notebook and select an available GPU accelerator. Some sessions may offer roughly 16 GB-class devices such as a P100 or T4, but hardware availability and session limits are not guaranteed.
3. Confirm the model's license and any platform model-use conditions before downloading weights.
4. Run the checked-in notebook `worker/notebook/syj_video_forge_gpu.ipynb` from top to bottom.

### Google Colab

1. Open the notebook in Colab.
2. Choose Runtime → Change runtime type → GPU (if offered).
3. Ensure Internet access is available for the session, and review the current Colab FAQ and terms. Colab restricts deepfakes and several web-service/remote-control uses; do not use this workflow for prohibited purposes.
4. Run the notebook cells in order. Free GPU availability, runtime length, and limits are not guaranteed.

### Local NVIDIA GPU

Use a Python environment compatible with the pinned worker dependencies and an installed FFmpeg executable. Keep the machine under your control. No inbound port is needed.

## 2. Smoke test

The notebook prints Python, GPU, CUDA, library versions, and free disk, then runs:

```sh
python -m worker smoke-test --engine ltx-video --out worker-output
```

A successful run writes `worker-output/smoke.json` and a short MP4. A non-zero exit means the engine did not pass. Do not report success if a file exists but the command failed.

## 3. One-scene verification

Create a job bundle in the browser with a simple text prompt, 5 seconds, `LTX-Video`, no starting image, and seed `123`. Save `job.json`, upload it to the notebook, and run:

```sh
python -m worker run job.json --out one-scene --engine ltx-video
```

Check `one-scene/result.mp4`, `one-scene/manifest.json`, each scene's luminance metrics, and playback. Import both result files into the browser and confirm SHA-256 verification and the self-reported hardware label.

## 4. Six-scene 30-second verification

Create a new 30-second `Long` bundle with six edited scene prompts. Use the default `last_frame` continuity and seed `123`. Run:

```sh
python -m worker run job.json --out six-scene --engine ltx-video
```

Check that six scene MP4s and incremental manifest entries exist, scene seeds increment by index, `result.mp4` has a valid duration/codec via `ffprobe`, and no degenerate guard failed. If the session stops, rerun with `--resume` and verify that unchanged scene hashes are skipped.

## 5. Report

Copy `docs/verification/REPORT-TEMPLATE.md` to a new report file. Record exact output and failures. Include no tokens or private prompts. If a run fails, attach the relevant sanitized error and manifest; do not edit the manifest to claim a pass.
