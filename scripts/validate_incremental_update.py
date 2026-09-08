#!/usr/bin/env python3
"""Verify that an incremental build preserves identity and untouched units."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

PLAN_SCHEMA = "learn-from-materials/incremental-update-plan-v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def dependency_page_id(kb: Path) -> str:
    value = load_json(kb / "unit-dependency-map.json")
    return str(value.get("pageId") or "") if isinstance(value, dict) else ""


def validate(old_kb: Path, new_kb: Path, plan: dict) -> list[str]:
    errors: list[str] = []
    if plan.get("schemaVersion") != PLAN_SCHEMA:
        return [f'incremental plan schemaVersion 必须为 "{PLAN_SCHEMA}"']
    if plan.get("requiresFullRebuild") is True:
        return ["计划要求全量重建，不能声称本次为语义增量更新"]
    old_page_id = dependency_page_id(old_kb)
    new_page_id = dependency_page_id(new_kb)
    if not old_page_id or old_page_id != new_page_id:
        errors.append("增量更新前后 pageId 必须非空且保持不变")
    impacted = {str(value) for value in plan.get("impactedUnitIds", [])}
    manual = {
        str(item.get("unitId") or "")
        for item in plan.get("manualExpansions", []) if isinstance(item, dict)
    }
    allowed_changes = impacted | manual
    old_units = {path.stem: path for path in (old_kb / "units").glob("*.md")}
    new_units = {path.stem: path for path in (new_kb / "units").glob("*.md")}
    for unit_id in sorted(set(old_units) & set(new_units)):
        if unit_id not in allowed_changes and digest(old_units[unit_id]) != digest(new_units[unit_id]):
            errors.append(f"未受影响单元被改写：{unit_id}")
    missing_untouched = sorted((set(old_units) - set(new_units)) - allowed_changes)
    if missing_untouched:
        errors.append("未受影响单元被删除：" + "、".join(missing_untouched))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a semantic incremental knowledge-base update")
    parser.add_argument("--old-kb", type=Path, required=True)
    parser.add_argument("--new-kb", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = load_json(args.plan)
        if not isinstance(plan, dict):
            raise ValueError("plan 根节点必须是对象")
        errors = validate(args.old_kb, args.new_kb, plan)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if errors:
        for error in errors:
            print(f"❌ {error}")
        raise SystemExit(1)
    print("✅ 增量更新身份与未受影响单元校验通过")


if __name__ == "__main__":
    main()
