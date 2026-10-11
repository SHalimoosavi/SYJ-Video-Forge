"""Lazy engine registry. Heavy ML modules are imported only inside Engine.load()."""
from .base import Engine, EngineError
from .fake import FakeEngine

ENGINE_IDS=("ltx-video","wan2.2-ti2v-5b")

def create_engine(engine_id: str, *, for_tests: bool=False):
    if engine_id=="ltx-video":
        from .ltx import LTXVideoEngine
        return LTXVideoEngine()
    if engine_id=="wan2.2-ti2v-5b":
        from .wan import Wan22Engine
        return Wan22Engine()
    if engine_id=="fake-test-pattern" and for_tests:
        return FakeEngine()
    raise EngineError(f"Unknown engine id: {engine_id}. FakeEngine is tests-only.")
