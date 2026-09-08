#!/usr/bin/env python3
"""Run reproducible cold/warm extraction benchmarks on user-supplied corpora."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def run_once(extract_script: Path, inputs: list[str], output_dir: Path, no_cache: bool) -> dict:
    command = [sys.executable, str(extract_script), *inputs, "--output-dir", str(output_dir), "--ocr", "off"]
    if no_cache:
        command.append("--no-cache")
    started = time.perf_counter()
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    elapsed = round(time.perf_counter() - started, 6)
    report_path = output_dir / "performance-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    return {
        "returnCode": completed.returncode,
        "wallSeconds": elapsed,
        "reported": report,
        "stderrTail": completed.stderr[-2000:],
    }


def benchmark(inputs: list[str], output_root: Path) -> dict:
    extract_script = Path(__file__).with_name("extract.py")
    output_root.mkdir(parents=True, exist_ok=True)
    cold = run_once(extract_script, inputs, output_root, no_cache=True)
    warm_seed = run_once(extract_script, inputs, output_root, no_cache=False)
    warm = run_once(extract_script, inputs, output_root, no_cache=False)
    return {
        "schemaVersion": "learn-from-materials/benchmark-v1",
        "inputs": inputs,
        "cold": cold,
        "warmSeed": warm_seed,
        "warm": warm,
        "passed": all(item["returnCode"] == 0 for item in (cold, warm_seed, warm)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark extraction latency and incremental reuse")
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="learn-materials-benchmark-") as temp:
        result = benchmark(args.inputs, Path(temp) / "work")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Benchmark {'passed' if result['passed'] else 'failed'} -> {args.output}")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
