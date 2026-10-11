from .base import Capabilities, ProviderError, VideoProvider
from .testpattern import TestPatternProvider

def provider_registry(ffmpeg: str | None = None) -> list[VideoProvider]:
    return [TestPatternProvider(ffmpeg)]

__all__ = ["Capabilities", "ProviderError", "VideoProvider", "TestPatternProvider", "provider_registry"]
