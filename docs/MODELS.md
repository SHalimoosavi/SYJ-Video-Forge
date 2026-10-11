# Candidate model comparison — research snapshot 2026-10-11

No model is bundled or tested. VRAM varies by variant, resolution, frame count, precision, offloading and implementation. Model terms apply independently from this repository.

| Candidate | License | Typical VRAM | Max clip length | Image-to-video |
|---|---|---|---|---|
| Wan 2.2 | Check exact official checkpoint license; family-wide terms not verified here | Unverified for a universal family value | Unverified as a universal limit | Supported by I2V variants; verify checkpoint |
| LTX family | Official LTX-Video repository lists Apache-2.0; verify selected checkpoint terms | Unverified family-wide | Unverified family-wide | Supported in LTX-Video workflows; verify variant |
| HunyuanVideo 1.5 | Tencent Hunyuan Community License Agreement; not standard OSI permissive license | Official repo says minimum 14 GB with model offloading | A single maximum across configurations unverified | Yes; official repo describes T2V and I2V |
| LongCat-Video | Official repository LICENSE declares MIT; verify checkpoint/assets separately | Collaborator guidance says 80 GB for full demo; 48 GB with changes; 24 GB may require community modifications; not a guarantee | Universal maximum unverified | Verify exact pipeline/task configuration |

Sources: official [LTX-Video](https://github.com/Lightricks/LTX-Video), [HunyuanVideo 1.5](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5), [LongCat-Video](https://github.com/meituan-longcat/LongCat-Video) repositories and their model documentation. For Wan 2.2, check the exact official checkpoint/model card before adoption; unverified details are deliberately not guessed. No speed claims are included because no benchmark was run. Re-check current licenses, hardware, duration, resolution and task support before integrating.
