"""Engine contract. Importing this module never imports ML libraries."""
from __future__ import annotations
from typing import Any, Callable

class EngineError(RuntimeError): pass

class Engine:
    id = "base"
    model_id = ""
    license_info = "See the official model card and license before use."
    capabilities = {"text": True, "image": False, "negative_prompt": True, "frame_rule": "any", "fps": 24,
                    "resolutions": ["512x288"]}
    kind = "ai_generated"
    def __init__(self): self.pipe=None; self.hardware={"gpu":"unknown","vram_total_bytes":None,"vram_peak_bytes":None,"dtype":"unknown"}
    def load(self) -> None: raise NotImplementedError
    def generate_clip(self, prompt: str, start_image: Any, frames: int, seed: int, steps: int,
                      cancel_event: Any, progress_cb: Callable[[float], None]) -> list[Any]: raise NotImplementedError
    def unload(self) -> None:
        self.pipe=None
