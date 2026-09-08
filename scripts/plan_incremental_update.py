#!/usr/bin/env python3
"""Build a deterministic source/block-level incremental update plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEPENDENCY_SCHEMA = "learn-from-materials/unit-dependency-map-v1"
PLAN_SCHEMA = "learn-from-materials/incremental-update-plan-v1"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def unique_by_filename(manifest: dict) -> dict[str, dict]:
    output: dict[str, dict] = {}
    for item in manifest.get("sources", []):
        if not isinstance(item, dict):
            continue
        filename = str(item.get("filename") or "").strip()
        if not filename:
            continue
        if filename in output:
            raise ValueError(f"manifest 含重复文件名，无法安全增量匹配：{filename}")
        output[filename] = item
    return output


def locator_ordinal(item: dict) -> str:
    kind = str(item.get("locator_type") or "document")
    field = {"pdf_page": "pdf_page", "slide": "slide", "epub_section": "epub_section"}.get(kind)
    if field and isinstance(item.get(field), int):
        return str(item[field])
    return "1"


def source_key(item: dict) -> str:
    filename = Path(str(item.get("source_file") or "")).name
    kind = str(item.get("locator_type") or "document")
    return f"{filename}#{kind}:{locator_ordinal(item)}"


def map_blocks(source_map: list[dict]) -> dict[str, dict]:
    output: dict[str, dict] = {}
    for item in source_map:
        if not isinstance(item, dict):
            continue
        key = source_key(item)
        if key in output:
            raise ValueError(f"source_map 产生重复稳定定位键：{key}")
        output[key] = item
    return output


def build_plan(old_manifest: dict, new_manifest: dict, old_map: list[dict], new_map: list[dict],
               dependencies: dict | None) -> dict:
    old_sources = unique_by_filename(old_manifest)
    new_sources = unique_by_filename(new_manifest)
    old_names = set(old_sources)
    new_names = set(new_sources)
    added_sources = sorted(new_names - old_names)
    deleted_sources = sorted(old_names - new_names)
    unchanged_sources: list[str] = []
    modified_sources: list[str] = []
    for name in sorted(old_names & new_names):
        old_hash = str(old_sources[name].get("text_sha256") or old_sources[name].get("sha256") or "")
        new_hash = str(new_sources[name].get("text_sha256") or new_sources[name].get("sha256") or "")
        (unchanged_sources if old_hash and old_hash == new_hash else modified_sources).append(name)

    old_blocks = map_blocks(old_map)
    new_blocks = map_blocks(new_map)
    old_keys = set(old_blocks)
    new_keys = set(new_blocks)
    new_source_keys = sorted(new_keys - old_keys)
    deleted_source_keys = sorted(old_keys - new_keys)
    changed_source_keys: list[str] = []
    unchanged_source_keys: list[str] = []
    for key in sorted(old_keys & new_keys):
        old_hash = str(old_blocks[key].get("content_sha256") or "")
        new_hash = str(new_blocks[key].get("content_sha256") or "")
        (unchanged_source_keys if old_hash and old_hash == new_hash else changed_source_keys).append(key)

    dependency_valid = isinstance(dependencies, dict) and dependencies.get("schemaVersion") == DEPENDENCY_SCHEMA
    dependency_entries = dependencies.get("entries", []) if dependency_valid else []
    by_key = {
        str(item.get("sourceKey") or ""): item
        for item in dependency_entries if isinstance(item, dict) and item.get("sourceKey")
    }
    impact_keys = set(changed_source_keys) | set(deleted_source_keys)
    impacted_units: set[str] = set()
    impacted_claims: set[str] = set()
    impacted_derived: set[str] = set()
    missing_dependency_keys: list[str] = []
    if dependency_valid:
        for key in sorted(impact_keys):
            entry = by_key.get(key)
            if not entry:
                missing_dependency_keys.append(key)
                continue
            impacted_units.update(str(value) for value in entry.get("unitIds", []) if str(value).strip())
            impacted_claims.update(str(value) for value in entry.get("claimIds", []) if str(value).strip())
            impacted_derived.update(str(value) for value in entry.get("derivedRefs", []) if str(value).strip())

    requires_full = not dependency_valid or bool(missing_dependency_keys)
    reason = []
    if not dependency_valid:
        reason.append("旧知识库缺少有效 unit-dependency-map.json")
    if missing_dependency_keys:
        reason.append("变化或删除来源块缺少旧依赖记录")
    return {
        "schemaVersion": PLAN_SCHEMA,
        "pageId": str(dependencies.get("pageId") or "") if dependency_valid else "",
        "requiresFullRebuild": requires_full,
        "fullRebuildReasons": reason,
        "addedSources": added_sources,
        "modifiedSources": modified_sources,
        "deletedSources": deleted_sources,
        "unchangedSources": unchanged_sources,
        "newSourceKeys": new_source_keys,
        "changedSourceKeys": changed_source_keys,
        "deletedSourceKeys": deleted_source_keys,
        "unchangedSourceKeys": unchanged_source_keys,
        "impactedUnitIds": sorted(impacted_units),
        "impactedClaimIds": sorted(impacted_claims),
        "impactedDerivedRefs": sorted(impacted_derived),
        "missingDependencyKeys": missing_dependency_keys,
        "manualExpansions": [],
        "hasMaterialChanges": bool(added_sources or modified_sources or deleted_sources),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan an incremental learning knowledge-base update")
    parser.add_argument("--old-kb", type=Path, required=True)
    parser.add_argument("--new-extraction", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        old_manifest = load_json(args.old_kb / "source_manifest.json")
        new_manifest = load_json(args.new_extraction / "source_manifest.json")
        old_map = load_json(args.old_kb / "source_map.json")
        new_map = load_json(args.new_extraction / "source_map.json")
        dependency_path = args.old_kb / "unit-dependency-map.json"
        dependencies = load_json(dependency_path) if dependency_path.is_file() else None
        if not isinstance(old_manifest, dict) or not isinstance(new_manifest, dict):
            raise ValueError("source_manifest.json 根节点必须是对象")
        if not isinstance(old_map, list) or not isinstance(new_map, list):
            raise ValueError("source_map.json 根节点必须是数组")
        plan = build_plan(old_manifest, new_manifest, old_map, new_map, dependencies if isinstance(dependencies, dict) else None)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    mode = "full rebuild" if plan["requiresFullRebuild"] else "incremental"
    print(f"Update plan: {mode}; {len(plan['impactedUnitIds'])} existing unit(s) impacted")


if __name__ == "__main__":
    main()
