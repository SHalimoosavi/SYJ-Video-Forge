# Model selection and compatibility notes

**Research snapshot: 2026-10-11.** This is documentation of official pages reviewed on this date, not a GPU validation report. The model path is **UNVERIFIED ON REAL HARDWARE** until a user runs `python -m worker smoke-test` and the one-scene and six-scene procedures in `docs/WORKER-VERIFY.md`. No model weights are stored in this repository.

## Decision

- **Primary: `ltx-video` — `Lightricks/LTX-Video`.** Diffusers documents `LTXPipeline` for text-to-video and `LTXConditionPipeline` for image-conditioned video. Its official documentation describes approximately 10 GB VRAM for an LTX setup and a frame count rule of `8n+1`, with resolution dimensions divisible by 32. This is the best fit among the candidates for an initial low-resolution 16 GB-class experiment, but fp16 stability on T4/P100 and this exact adapter remain **UNVERIFIED ON REAL HARDWARE**.
- **Fallback: `wan2.2-ti2v-5b` — `Wan-AI/Wan2.2-TI2V-5B`.** The official model card confirms text-to-video and image-to-video, 720p at 24 fps, and Apache-2.0. The official repository's standard 720p inference instructions state at least 24 GB VRAM. This makes it a fallback for GPUs with sufficient memory, not a promised 16 GB solution. CPU/group offloading behavior on 16 GB cards is **UNVERIFIED**.

Neither engine is guaranteed to work in a hosted notebook. The code selects bf16 only when CUDA capability and `torch.cuda.is_bf16_supported()` indicate support; otherwise it selects fp16. The adapters and fp16 behavior still require hardware verification. They never claim a completed AI generation merely because a model download or pipeline load succeeded.

## Candidate facts

| Candidate / confirmed official model ID | License and conditions | Inputs / frames / fps / resolution | Memory / dtype notes | Status |
|---|---|---|---|---|
| LTX-Video, `Lightricks/LTX-Video` | Checkpoint family uses LTXV Open Weights License 0.X for v0.9.6 and later, not Apache-2.0. The official license grants a worldwide, non-transferable, royalty-free limited license subject to use-based restrictions. Entities with annual revenue at least USD 10,000,000 are eligible for a separate paid commercial-use license; commercial use by such entities must follow the commercial agreement. The license includes restrictions covering unlawful harm, impersonation/deepfakes without consent, harassment, and other prohibited uses; read the complete license. | Text and image-conditioned video are documented. The model card says 24 fps at 768×512 for the model family; dimensions should be divisible by 32. Frame counts follow `8n+1` (for example, 257); the pipeline pads/crops unsupported sizes. The worker uses lower target sizes and frame counts for an initial test. | Current Diffusers docs show LTX examples using bf16 and describe ~10 GB VRAM for the documented setup. VAE/text encoder can use fp16, but transformer examples recommend bf16. T4/P100 native bf16 support is not assumed; fp16 on those GPUs and any offloading combination are **UNVERIFIED ON REAL HARDWARE**. | Primary adapter implemented; not GPU-tested here. |
| Wan 2.2 TI2V-5B, `Wan-AI/Wan2.2-TI2V-5B` | Apache License 2.0 according to the official Hugging Face model card/repository. No territory or revenue threshold is stated in the reviewed Apache-2.0 model license; follow Apache notice and attribution requirements. | Text-to-video and image-to-video; official card says 720p at 24 fps. The worker adapter targets small 512×288 / 288×512 / 384×384 outputs; exact small-resolution frame constraints and adapter API are **UNVERIFIED**. Worker planning uses `4n+1` as a conservative adapter rule, subject to verification. | Official repository says standard 720p inference needs at least 24 GB VRAM and provides model offloading flags. Exact fp16/bf16 behavior and whether offloading fits 16 GB are **UNVERIFIED ON REAL HARDWARE**. Dtype is selected by device capability, never blindly set to bf16. | Fallback adapter implemented; not GPU-tested here. |

## Source links (official; reviewed 2026-10-11)

1. Diffusers LTX pipeline API: https://huggingface.co/docs/diffusers/api/pipelines/ltx_video
2. Current Diffusers LTX examples and memory/offloading notes: https://huggingface.co/docs/diffusers/main/api/pipelines/ltx_video
3. Official LTX-Video model card and checkpoint-specific license links: https://huggingface.co/Lightricks/LTX-Video
4. Official LTXV Open Weights License 0.X (applicable to v0.9.6 and later): https://huggingface.co/Lightricks/LTX-Video/blob/main/LTX-Video-Open-Weights-License-0.X.txt
5. Official Wan 2.2 TI2V-5B model card: https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B
6. Official Wan 2.2 repository / inference instructions: https://github.com/Wan-Video/Wan2.2
7. Apache-2.0 license text: https://www.apache.org/licenses/LICENSE-2.0

## Pinned worker dependencies

The versions in `requirements-worker.txt` were checked against their published PyPI release pages on 2026-10-11. The build environment did not install this GPU dependency set, and compatibility with a platform's preinstalled PyTorch/CUDA remains **UNVERIFIED**. PyPI release references: [diffusers 0.35.1](https://pypi.org/project/diffusers/0.35.1/), [transformers 4.57.1](https://pypi.org/project/transformers/4.57.1/), [accelerate 1.10.1](https://pypi.org/project/accelerate/1.10.1/), [huggingface-hub 0.36.0](https://pypi.org/project/huggingface-hub/0.36.0/), [safetensors 0.6.2](https://pypi.org/project/safetensors/0.6.2/), [numpy 2.2.6](https://pypi.org/project/numpy/2.2.6/), [Pillow 11.3.0](https://pypi.org/project/pillow/11.3.0/), [ImageIO 2.37.0](https://pypi.org/project/ImageIO/2.37.0/), and [imageio-ffmpeg 0.6.0](https://pypi.org/project/imageio-ffmpeg/0.6.0/). PyTorch is deliberately omitted so the notebook can reuse a compatible preinstalled build.

## Weight downloads and gated access

Weights are downloaded at worker runtime from the Hugging Face Hub; the repository contains no checkpoints. The reviewed candidate pages did not indicate that these selected repositories are gated, but that can change. If the Hub asks for access, stop and review the exact model card/license, accept the terms on the official model page, then authenticate with a Hugging Face token supplied through the notebook platform's secret store or a hidden input prompt. Never hardcode or commit a token. The user is responsible for model-license compliance.

## Unverified claims

No generation speed, visual quality, 16 GB fit, session compatibility, dtype stability, model revision, or successful real-hardware run is asserted by this document. Record observations in `docs/verification/REPORT-TEMPLATE.md`.
