"""Version 1 bundle/manifest validation using Python's standard library only."""
from __future__ import annotations
import base64, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
MAX_IMAGE_BYTES = 10 * 1024 * 1024
JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")
MIME_MAGIC = {
    "image/png": lambda b: b.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/jpeg": lambda b: b.startswith(b"\xff\xd8\xff"),
    "image/webp": lambda b: len(b) >= 12 and b[:4] == b"RIFF" and b[8:12] == b"WEBP",
}

class BundleError(ValueError):
    pass

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def validate_image_record(record: Any) -> bytes | None:
    if record is None:
        return None
    if not isinstance(record, dict):
        raise BundleError("image must be an object or null")
    mime, encoded, digest = record.get("mime"), record.get("base64"), record.get("sha256")
    if mime not in MIME_MAGIC or not isinstance(encoded, str):
        raise BundleError("image MIME must be PNG, JPEG, or WebP and base64 must be a string")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise BundleError("image base64 is invalid") from exc
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        raise BundleError("image must be non-empty and at most 10 MiB")
    if not MIME_MAGIC[mime](raw):
        raise BundleError("image magic bytes do not match the declared MIME type")
    if digest != sha256_bytes(raw):
        raise BundleError("image SHA-256 does not match")
    return raw

def validate_job(job: Any) -> dict[str, Any]:
    if not isinstance(job, dict) or job.get("schemaVersion") != SCHEMA_VERSION:
        raise BundleError("job schemaVersion must be 1")
    if not isinstance(job.get("jobId"), str) or not JOB_ID_RE.fullmatch(job["jobId"]):
        raise BundleError("jobId must be 32 lowercase hexadecimal characters")
    if job.get("mode") not in ("text", "image"):
        raise BundleError("mode must be text or image")
    if not isinstance(job.get("prompt"), str) or not job["prompt"].strip() or len(job["prompt"]) > 4000:
        raise BundleError("prompt must contain 1-4000 characters")
    if not isinstance(job.get("negativePrompt", ""), str) or len(job.get("negativePrompt", "")) > 2000:
        raise BundleError("negativePrompt must be a string of at most 2000 characters")
    if job.get("aspect") not in ("16:9", "9:16", "1:1"):
        raise BundleError("aspect must be 16:9, 9:16, or 1:1")
    if job.get("resolution") not in ("512x288", "288x512", "384x384", "704x384", "384x704", "512x512"):
        raise BundleError("unsupported resolution target")
    for key, lo, hi in (("seed", 0, 2147483647), ("totalSeconds", 1, 3600), ("fps", 1, 60)):
        val = job.get(key)
        if isinstance(val, bool) or not isinstance(val, int) or not lo <= val <= hi:
            raise BundleError(f"{key} must be an integer in [{lo}, {hi}]")
    if job.get("preset") == "Long" and job["totalSeconds"] < 30:
        raise BundleError("the Long preset requires totalSeconds >= 30")
    if job.get("continuity", "last_frame") not in ("last_frame", "none"):
        raise BundleError("continuity must be last_frame or none")
    engine = job.get("engine")
    if not isinstance(engine, dict) or engine.get("id") not in ("ltx-video", "wan2.2-ti2v-5b"):
        raise BundleError("engine request must name a documented AI engine")
    clip_seconds = job.get("clipSeconds", 5)
    if isinstance(clip_seconds, bool) or not isinstance(clip_seconds, int) or not 1 <= clip_seconds <= 60:
        raise BundleError("clipSeconds must be an integer in [1, 60]")
    scenes = job.get("scenes")
    if not isinstance(scenes, list) or not scenes or len(scenes) > 120:
        raise BundleError("scenes must be a non-empty list of at most 120 scenes")
    expected_scenes = (job["totalSeconds"] + clip_seconds - 1) // clip_seconds
    if len(scenes) != expected_scenes:
        raise BundleError(f"scene count must equal ceil(totalSeconds / clipSeconds) = {expected_scenes}")
    for i, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict) or scene.get("index") != i or not isinstance(scene.get("prompt"), str) or not scene["prompt"].strip():
            raise BundleError("scenes must have ordered indexes and non-empty prompts")
    image_bytes = validate_image_record(job.get("image"))
    if job["mode"] == "image" and image_bytes is None:
        raise BundleError("image mode requires an image record")
    created = job.get("createdAt")
    if not isinstance(created, str):
        raise BundleError("createdAt must be an ISO timestamp")
    try:
        datetime.fromisoformat(created.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BundleError("createdAt must be an ISO timestamp") from exc
    return job

def load_job(path: str | Path) -> dict[str, Any]:
    try:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BundleError(f"cannot read job JSON: {exc}") from exc
    return validate_job(obj)

def write_json_atomic(path: str | Path, obj: dict[str, Any]) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(p)

def validate_manifest(manifest: Any, job: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, dict) or manifest.get("schemaVersion") != SCHEMA_VERSION:
        raise BundleError("manifest schemaVersion must be 1")
    if manifest.get("jobId") != job.get("jobId"):
        raise BundleError("manifest jobId does not match job bundle")
    if manifest.get("kind") not in ("ai_generated", "test_pattern"):
        raise BundleError("manifest kind must be ai_generated or test_pattern")
    final = manifest.get("final")
    if not isinstance(final, dict) or final.get("file") != "result.mp4":
        raise BundleError("manifest final.file must be result.mp4")
    if not re.fullmatch(r"[0-9a-f]{64}", str(final.get("sha256", ""))):
        raise BundleError("manifest final.sha256 must be a SHA-256 hex digest")
    if not isinstance(manifest.get("scenes"), list):
        raise BundleError("manifest scenes must be a list")
    return manifest

def new_manifest(job: dict[str, Any], engine: dict[str, Any]) -> dict[str, Any]:
    return {"schemaVersion": SCHEMA_VERSION, "jobId": job["jobId"], "kind": "ai_generated", "engine": engine,
            "libraries": {}, "hardware": {"gpu": "unknown", "vram_total_bytes": None, "vram_peak_bytes": None, "dtype": "unknown"},
            "parameters": {}, "scenes": [], "final": None,
            "timestamps": {"startedAt": datetime.now(timezone.utc).isoformat(), "finishedAt": None},
            "warnings": ["UNVERIFIED ON REAL HARDWARE: no GPU verification report is bundled."],
            "degenerateChecks": []}
