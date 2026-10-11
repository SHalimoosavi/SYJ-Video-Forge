"""Deterministic scene/frame planning independent of torch."""
from __future__ import annotations
import math

def frame_count(seconds: float, fps: int, rule: str) -> int:
    raw = max(1, round(seconds * fps))
    if rule == "8n+1": return max(9, math.ceil((raw - 1) / 8) * 8 + 1)
    if rule == "4n+1": return max(5, math.ceil((raw - 1) / 4) * 4 + 1)
    return raw

def plan_scenes(total_seconds: int, clip_seconds: int, fps: int, frame_rule: str) -> list[dict]:
    if total_seconds < 1 or clip_seconds < 1 or fps < 1: raise ValueError("duration, clip length and fps must be positive")
    count = math.ceil(total_seconds / clip_seconds)
    result=[]
    for i in range(count):
        seconds=min(clip_seconds,total_seconds-i*clip_seconds)
        result.append({"index":i+1,"seconds":seconds,"frames":frame_count(seconds,fps,frame_rule)})
    return result

def scene_seed(base_seed: int, index: int) -> int:
    if index < 1: raise ValueError("scene index starts at 1")
    return (int(base_seed) + index) % 2147483648
