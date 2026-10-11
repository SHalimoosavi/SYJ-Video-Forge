"""Lazy Diffusers adapter for LTX-Video. Real-hardware status is unverified."""
from __future__ import annotations
from .base import Engine, EngineError

class LTXVideoEngine(Engine):
    id="ltx-video"
    model_id="Lightricks/LTX-Video"
    license_info="LTX-Video Open Weights License 0.X; review checkpoint-specific terms and use restrictions."
    capabilities={"text":True,"image":True,"negative_prompt":True,"frame_rule":"8n+1","fps":24,
                  "resolutions":["512x288","288x512","384x384","704x384","384x704","512x512"]}
    def load(self):
        try:
            import torch
            from diffusers import LTXPipeline, LTXConditionPipeline
        except Exception as exc: raise EngineError(f"LTX dependencies unavailable: {exc}. Install requirements-worker.txt in the GPU environment.") from exc
        if not torch.cuda.is_available(): raise EngineError("LTX engine requires a CUDA GPU; CPU-only inference is not supported by this worker profile.")
        props=torch.cuda.get_device_properties(0); major,minor=torch.cuda.get_device_capability(0)
        bf16=major>=8 and bool(getattr(torch.cuda,"is_bf16_supported",lambda:False)())
        self.torch=torch; self.dtype=torch.bfloat16 if bf16 else torch.float16
        self._text_cls=LTXPipeline; self._image_cls=LTXConditionPipeline
        self._offload=props.total_memory < 12*1024**3
        self.hardware={"gpu":props.name,"vram_total_bytes":int(props.total_memory),"vram_peak_bytes":None,"compute_capability":f"{major}.{minor}","dtype":"bf16" if bf16 else "fp16"}
        self._load_pipeline(bool(getattr(self,"_want_image",False)))
    def _load_pipeline(self,use_image):
        cls=self._image_cls if use_image else self._text_cls
        try:
            self.pipe=cls.from_pretrained(self.model_id,torch_dtype=self.dtype)
            if self._offload and hasattr(self.pipe,"enable_model_cpu_offload"): self.pipe.enable_model_cpu_offload()
            else: self.pipe.to("cuda")
        except Exception as exc:
            self.pipe=None
            raise EngineError(f"Could not load {self.model_id}: {exc}. Check the current model card, license, Diffusers compatibility and available VRAM.") from exc
    def generate_clip(self,prompt,start_image,frames,seed,steps,cancel_event,progress_cb):
        if self.pipe is None: raise EngineError("Engine is not loaded")
        if cancel_event.is_set(): raise EngineError("Cancelled before inference")
        import torch
        from diffusers import LTXConditionPipeline
        want_image=start_image is not None
        if want_image != isinstance(self.pipe,LTXConditionPipeline):
            # The first image-conditioned scene may be followed by text-only scenes when continuity='none'.
            self.pipe=None
            self._load_pipeline(want_image)
        kwargs={"prompt":prompt,"negative_prompt":getattr(self,"negative_prompt",""),"num_frames":frames,"num_inference_steps":steps,
                "width":getattr(self,"width",512),"height":getattr(self,"height",288),"generator":torch.Generator(device="cuda").manual_seed(seed)}
        if start_image is not None: kwargs["image"]=start_image
        try:
            torch.cuda.reset_peak_memory_stats()
            result=self.pipe(**kwargs)
            progress_cb(1.0)
            self.hardware["vram_peak_bytes"]=int(torch.cuda.max_memory_allocated())
            return result.frames[0]
        except Exception as exc: raise EngineError(f"LTX inference failed: {exc}. Use fp16 on hardware without native bf16 support; bf16 is enabled only when hardware reports support.") from exc
