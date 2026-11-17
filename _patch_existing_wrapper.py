"""Add perf_test_mode input + wiring to an existing exported wrapper flow.

Usage:
    py -3 _patch_existing_wrapper.py <path-to-exported-wrapper.json>

Writes <same-name>.perf.json next to the input. Preserves uuid / identifier /
title so re-importing into HS overwrites the existing flow in place
(external system bindings stay intact).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

PERF_TEST_MODE_INPUT_SPEC = {
    "name": "perf_test_mode",
    "type": "boolean",
    "title": "Perf Test Mode (auto-fill supervision)",
    "description": (
        "TEMPORARY: When true, the custom supervision step is auto-filled "
        "with intent_1='Add_Named_Insured' + transaction_type='MidTermChange', "
        "and Policy Number / Effective Date / Instructions are populated with "
        "hardcoded values. Leave FALSE for regular UAT / prod runs."
    ),
    "value": False,
    "optional": True,
}


def patch(path: Path) -> Path:
    flow = json.loads(path.read_text(encoding="utf-8"))

    # 1) declare the flag in manifest.input[] if missing
    inputs = flow.setdefault("manifest", {}).setdefault("input", [])
    if not any(i.get("name") == "perf_test_mode" for i in inputs):
        inputs.append(copy.deepcopy(PERF_TEST_MODE_INPUT_SPEC))
        print("added perf_test_mode to manifest.input[]")
    else:
        print("perf_test_mode already in manifest.input[] (skipped)")

    # 2) wire the value into the core subflow block
    wired = False
    for b in flow.get("blocks", []):
        if b.get("reference_name") == "__idp_core__":
            b.setdefault("input", {})["perf_test_mode"] = (
                "${workflow.input.perf_test_mode}"
            )
            wired = True
            print("wired perf_test_mode into __idp_core__.input")
            break
    if not wired:
        raise SystemExit(
            "No block with reference_name '__idp_core__' found. "
            "Is this the wrapper flow?"
        )

    # 3) default flow-level input value (safe default = false)
    flow.setdefault("input", {}).setdefault("perf_test_mode", False)

    path.write_text(json.dumps(flow, indent=2), encoding="utf-8")
    print(f"patched in place -> {path}")
    return path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: py -3 _patch_existing_wrapper.py <wrapper.json>")
    patch(Path(sys.argv[1]).resolve())


if __name__ == "__main__":
    main()
