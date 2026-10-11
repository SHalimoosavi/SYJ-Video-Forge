"""Configuration and strict input validation for the local backend."""
from __future__ import annotations
import base64, binascii, math, os, re
from pathlib import Path
from typing import Any

MAX_BODY_BYTES = 15 * 1024 * 1024
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_PROMPT_CHARS = 4000
DEFAULT_CORS = ("http://127.0.0.1:8080", "http://localhost:8080", "https://shalimoosavi.github.io")
JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")
IMAGE_SIGNATURES = {
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/webp": (b"RIFF",),
}

def validate_image_payload(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) - {"mime", "data"} or not isinstance(value.get("mime"), str) or not isinstance(value.get("data"), str):
        raise ValueError("image must contain mime and base64 data fields")
    mime, encoded = value["mime"], value["data"]
    if mime not in IMAGE_SIGNATURES:
        raise ValueError("image MIME type must be PNG, JPEG, or WebP")
    if len(encoded) > ((MAX_IMAGE_BYTES + 2) // 3) * 4 + 8:
        raise ValueError("image exceeds the 10 MiB limit")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("image data is not valid base64") from exc
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("image must be non-empty and no larger than 10 MiB")
    if mime == "image/webp":
        valid = len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP"
    else:
        valid = any(raw.startswith(sig) for sig in IMAGE_SIGNATURES[mime])
    if not valid:
        raise ValueError("image bytes do not match the declared MIME type")
    return {"mime": mime, "bytes": raw}

def validate_job_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("request body must be a JSON object")
    allowed = {"prompt", "negativePrompt", "duration", "aspectRatio", "seed", "model", "mode", "image", "scenes", "clip_seconds"}
    extra = set(value) - allowed
    if extra:
        raise ValueError("unknown request field(s): " + ", ".join(sorted(extra)))
    prompt = value.get("prompt")
    if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= MAX_PROMPT_CHARS:
        raise ValueError("prompt must contain 1 to 4000 non-whitespace characters")
    duration = value.get("duration", 30)
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(float(duration)) or duration <= 0 or duration > 600:
        raise ValueError("duration must be a number greater than 0 and no more than 600 seconds")
    mode = value.get("mode", "text")
    if mode not in ("text", "image"):
        raise ValueError("mode must be text or image")
    ratio = value.get("aspectRatio", "16:9")
    if ratio not in ("16:9", "9:16", "1:1"):
        raise ValueError("aspectRatio must be 16:9, 9:16, or 1:1")
    seed = value.get("seed")
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 2147483647):
        raise ValueError("seed must be an integer from 0 to 2147483647")
    negative = value.get("negativePrompt", "")
    if not isinstance(negative, str) or len(negative) > MAX_PROMPT_CHARS:
        raise ValueError("negativePrompt must be a string no longer than 4000 characters")
    image = validate_image_payload(value.get("image"))
    if mode == "image" and image is None:
        raise ValueError("image mode requires a valid image")
    scenes = value.get("scenes")
    clip_seconds = value.get("clip_seconds", 5)
    if isinstance(clip_seconds, bool) or not isinstance(clip_seconds, (int, float)) or not math.isfinite(float(clip_seconds)) or not 0.1 <= clip_seconds <= 30:
        raise ValueError("clip_seconds must be between 0.1 and 30 seconds")
    if scenes is not None and (isinstance(scenes, bool) or not isinstance(scenes, int) or not 1 <= scenes <= 30):
        raise ValueError("scenes must be an integer from 1 to 30")
    return {"prompt": prompt.strip(), "negativePrompt": negative, "duration": float(duration), "aspectRatio": ratio, "seed": seed, "model": value.get("model"), "mode": mode, "image": image, "scenes": scenes, "clip_seconds": float(clip_seconds)}

def safe_child(root: Path, *parts: str) -> Path:
    root_resolved = root.resolve()
    candidate = root_resolved.joinpath(*parts).resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ValueError("path escapes configured data directory")
    return candidate

def cors_origins(raw: str | None = None) -> tuple[str, ...]:
    text = raw if raw is not None else os.environ.get("SYJ_CORS_ORIGINS", "")
    if not text.strip():
        return DEFAULT_CORS
    origins = tuple(x.strip().rstrip("/") for x in text.split(",") if x.strip())
    if "*" in origins:
        raise ValueError("wildcard CORS origins are not permitted")
    for origin in origins:
        if not re.match(r"^https?://[A-Za-z0-9.\-\[\]:]+$", origin):
            raise ValueError("invalid CORS origin: " + origin)
    return origins
