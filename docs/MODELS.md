# Candidate model notes — research snapshot

No AI model is bundled, downloaded, integrated, or benchmarked in v0.2.0. The test-pattern provider is synthetic and is not a model. Model requirements and licenses vary by exact checkpoint, task, resolution, frame count, precision, and inference implementation.

| Candidate family | License note | Memory and duration | Integration status |
|---|---|---|---|
| Wan 2.2 | Verify the exact official checkpoint license before adoption; family-wide terms are not asserted here. | Universal VRAM and duration figures are unverified here. | Not integrated. |
| LTX-Video | The official project has described Apache-2.0 licensing; verify the chosen checkpoint and assets independently. | Universal memory and duration figures are unverified here. | Not integrated. |
| HunyuanVideo 1.5 | Tencent Hunyuan Community License Agreement; do not assume it is a standard OSI-permissive license. | Hardware requirements depend on configuration; verify the official current documentation. | Not integrated. |
| LongCat-Video | Verify repository and checkpoint license/asset terms before adoption. | Hardware and maximum-duration figures are configuration-dependent and not asserted here. | Not integrated. |

References for independent re-checking: https://github.com/Lightricks/LTX-Video, https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5, https://github.com/meituan-longcat/LongCat-Video. No compatibility or speed claims are made. Re-check current model cards, license files, platform requirements, and output rights before implementing a provider.
