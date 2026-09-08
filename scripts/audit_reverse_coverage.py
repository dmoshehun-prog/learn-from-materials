#!/usr/bin/env python3
"""Audit whether extracted source blocks map back to units and claims."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def audit(source_map: list[dict], coverage_audit: dict, sample_size: int = 12) -> dict:
    blocks = coverage_audit.get("sourceBlocks")
    if not isinstance(blocks, list):
        blocks = []
    block_by_id = {
        str(item.get("sourceId") or ""): item
        for item in blocks if isinstance(item, dict) and item.get("sourceId")
    }
    locators = [item for item in source_map if isinstance(item, dict) and item.get("source_id")]
    outcomes = []
    for locator in locators:
        source_id = str(locator["source_id"])
        mapped = block_by_id.get(source_id)
        units = mapped.get("mappedUnits", []) if isinstance(mapped, dict) else []
        claims = mapped.get("mappedClaims", []) if isinstance(mapped, dict) else []
        status = mapped.get("status") if isinstance(mapped, dict) else None
        covered = status in {"covered", "no-content", "duplicate", "quick-omitted"} and (
            status != "covered" or bool(units or claims)
        )
        outcomes.append({
            "sourceId": source_id,
            "filename": Path(str(locator.get("source_file") or "")).name,
            "locatorType": locator.get("locator_type"),
            "covered": covered,
            "mappedUnits": units,
            "mappedClaims": claims,
            "status": status or "missing",
        })
    ordered = sorted(outcomes, key=lambda item: hashlib.sha256(item["sourceId"].encode()).hexdigest())
    sample = ordered[:max(0, min(sample_size, len(ordered)))]
    uncovered = [item["sourceId"] for item in outcomes if not item["covered"]]
    omitted = [item["sourceId"] for item in outcomes if item["status"] == "quick-omitted"]
    return {
        "schemaVersion": "learn-from-materials/reverse-coverage-report-v1",
        "totalSourceBlocks": len(outcomes),
        "mappedSourceBlocks": len(outcomes) - len(uncovered),
        "unmappedSourceBlocks": len(uncovered),
        "unmappedRatio": round(len(uncovered) / len(outcomes), 6) if outcomes else 0.0,
        "unmappedSourceIds": uncovered,
        "intentionallyOmittedSourceBlocks": len(omitted),
        "intentionallyOmittedRatio": round(len(omitted) / len(outcomes), 6) if outcomes else 0.0,
        "intentionallyOmittedSourceIds": omitted,
        "sampleSize": len(sample),
        "sample": sample,
        "passed": not uncovered and all(item["covered"] for item in sample),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Reverse-check source-to-unit and source-to-claim coverage")
    parser.add_argument("--source-map", type=Path, required=True)
    parser.add_argument("--coverage-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=12)
    args = parser.parse_args()
    try:
        source_map = load_json(args.source_map)
        coverage = load_json(args.coverage_audit)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(source_map, list) or not isinstance(coverage, dict):
        print("ERROR: source_map must be an array and coverage audit must be an object", file=sys.stderr)
        raise SystemExit(2)
    result = audit(source_map, coverage, args.sample_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Reverse coverage: {result['mappedSourceBlocks']}/{result['totalSourceBlocks']} blocks mapped")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
