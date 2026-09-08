"""Content fingerprints and a conservative local extraction cache."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from extractor.config import EXTRACTOR_SCHEMA_VERSION


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def cache_key(file_hash: str, extraction_mode: str, ocr_mode: str) -> str:
    material = f"{EXTRACTOR_SCHEMA_VERSION}\0{file_hash}\0{extraction_mode}\0{ocr_mode}"
    return sha256_text(material)


def load_cached_extraction(cache_dir: Path, key: str) -> dict | None:
    path = cache_dir / f"{key}.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict) or value.get("cacheSchema") != EXTRACTOR_SCHEMA_VERSION:
        return None
    result = value.get("result")
    return result if isinstance(result, dict) and isinstance(result.get("text"), str) else None


def save_cached_extraction(cache_dir: Path, key: str, result: dict) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{key}.json"
    payload = {"cacheSchema": EXTRACTOR_SCHEMA_VERSION, "result": result}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
