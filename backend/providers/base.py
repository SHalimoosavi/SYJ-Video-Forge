"""Provider contract for local video clip generation."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Callable

ProgressCallback = Callable[[float, str], None]

class ProviderError(RuntimeError):
    """A provider cannot perform the requested operation."""

@dataclass(frozen=True)
class Capabilities:
    text: bool
    image: bool
    negative_prompt: bool
    max_clip_seconds: float
    supports_start_image: bool
    kind: str

    def as_dict(self) -> dict[str, object]:
        return {"text": self.text, "image": self.image, "negative_prompt": self.negative_prompt, "max_clip_seconds": self.max_clip_seconds, "supports_start_image": self.supports_start_image, "kind": self.kind}

class VideoProvider(ABC):
    name = "abstract"
    capabilities = Capabilities(False, False, False, 0, False, "unavailable")
    @abstractmethod
    def available(self) -> tuple[bool, str]:
        """Return availability and an operator-facing reason when unavailable."""
    @abstractmethod
    def generate_clip(self, prompt: str, start_image: Path | None, seconds: float, seed: int, output: Path, progress_cb: ProgressCallback, cancel_event: Event) -> None:
        """Generate one clip at output or raise ProviderError; honor cancellation."""
