"""Lazy Diffusers adapter for Wan 2.2 TI2V-5B; memory-heavy fallback."""
from __future__ import annotations
from .base import Engine, EngineError

class Wan22Engine(Engine):
    id="wan2.2-ti2v-5b"
    model_id="Wan-AI/Wan2.2-TI2V-5B"
    license_info="Apache-2.0 per official Wan-AI Hugging Face model card and Wan2.2 repository."
    capabilities={"text":True,"image":True,"negative_prompt":True,"frame_rule":"4n+1","fps":24,
                  "resolutions":["512x288","288x512","384x384"]}
    def load(self):
        try:
            import torch
            from diffusers import WanPipeline, WanImageToVideoPipeline
        except Exception as exc: raise EngineError(f"Wan Diffusers dependencies unavailable: {exc}") from exc
        if not torch.cuda.is_available(): raise EngineError("Wan 2.2 requires a CUDA GPU in this worker profile.")
        props=torch.cuda.get_device_properties(0); major,minor=torch.cuda.get_device_capability(0)
        bf16=major>=8 and bool(getattr(torch.cuda,"is_bf16_supported",lambda:False)())
        dtype=torch.bfloat16 if bf16 else torch.float16
        self.hardware={"gpu":props.name,"vram_total_bytes":int(props.total_memory),"vram_peak_bytes":None,"compute_capability":f"{major}.{minor}","dtype":"bf16" if bf16 else "fp16"}
        self._text_cls=WanPipeline; self._image_cls=WanImageToVideoPipeline; self.torch=torch; self.dtype=dtype
        # Defer actual pipeline load until the job mode is known; offload where supported.
        self.pipe=None
    def _ensure_pipe(self,image):
        cls=self._image_cls if image is not None else self._text_cls
        if self.pipe is not None and not isinstance(self.pipe,cls): self.pipe=None
        if self.pipe is None:
            try:
                self.pipe=cls.from_pretrained(self.model_id,torch_dtype=self.dtype)
                if hasattr(self.pipe,"enable_model_cpu_offload"): self.pipe.enable_model_cpu_offload()
                else: self.pipe.to("cuda")
            except Exception as exc: raise EngineError(f"Could not load Wan model {self.model_id}: {exc}. Official reference indicates 24 GB VRAM for the standard 720p path; 16 GB-class GPUs are unverified.") from exc
    def generate_clip(self,prompt,start_image,frames,seed,steps,cancel_event,progress_cb):
        if cancel_event.is_set(): raise EngineError("Cancelled before inference")
        self._ensure_pipe(start_image)
        import torch
        kwargs={"prompt":prompt,"negative_prompt":getattr(self,"negative_prompt",""),"num_frames":frames,"num_inference_steps":steps,
                "width":getattr(self,"width",512),"height":getattr(self,"height",288),"generator":torch.Generator(device="cuda").manual_seed(seed)}
        if start_image is not None: kwargs["image"]=start_image
        try:
            torch.cuda.reset_peak_memory_stats()
            result=self.pipe(**kwargs); progress_cb(1.0)
            self.hardware["vram_peak_bytes"]=int(torch.cuda.max_memory_allocated())
            return result.frames[0]
        except Exception as exc: raise EngineError(f"Wan inference failed: {exc}. Dtype selected from device capability; verify the model's current Diffusers API and VRAM requirements.") from exc
