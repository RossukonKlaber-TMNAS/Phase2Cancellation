"""Sync `refactored_export/` from the canonical reference zip
`refactored_export (4).zip`, then surgically overlay the freshly-built
intent list and transaction-type titles from `build_flow.py`
(`dropdown_core.json`).

Rules of engagement:
  * The reference zip is now the source of truth for the wrapper flow, the
    core flow layout, the `log_pre_export` and `set_transformed_output`
    blocks, and the `cob_http_export_sync_policy_txn_to_sf` Salesforce
    connector. Do NOT regenerate those from stale Downloads snapshots.
  * We ONLY overwrite two data-level fields on the core flow's
    `build_supervision_template` block:
      - `input.data.intent_oneof`
            - `input.data.transaction_type_oneof`
            - `input.code` for the runtime supervision-template builder
  * The reference zip contains a top-level `refactored_export/` wrapper
    folder; we flatten that on extract so `DST` mirrors the folder shape
    HS Studio's import UI expects.
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REF_ZIP = ROOT / "archive" / "flow_exports" / "refactored_export (4).zip"
DST = ROOT / "refactored_export"
CORE_UUID_FRAG = "a1b2c3d4-e5f6-47a8-9b10-1d2e3f4a5b6c"
# Original wrapper UUID from the reference zip (do not change).
ORIGINAL_WRAPPER_UUID = "b2c3d4e5-f6a7-48b9-ac10-2e3f4a5b6c7d"
# Distinct UUID / title so this imports as a NEW wrapper in HS (does not
# overwrite the existing 3 wrappers that share the core flow).
WRAPPER_UUID_FRAG = "4c623343-6b58-4a18-a4de-243e88a741b8"
PERF_WRAPPER_TITLE = "Endorsement Automation Dev Sample - PERF TEST"
ORIGINAL_WRAPPER_TITLE = "Endorsement Automation Dev Sample - Custom Flow"
SAAS_PYTHON_BLOCK_IDENTIFIER = "PYTHON_3_14_CODE"

# UI titles the client asked for. Consts stay unchanged so downstream
# Salesforce mapping is not affected.
TRANSACTION_TYPE_TITLES = {
    "None": "-- None --",
    "MidTermChange": "Mid Term Change",
    "MidTermQuote": "Mid Term Quote",
    "Exception": "Exception",
}

# ----------------------------------------------------------------------------
# TEMPORARY: perf-test wiring. Remove this whole section once UAT + perf
# testing are done and the flow is being cut for prod.
# ----------------------------------------------------------------------------
PERF_EFFECTIVE_DATE = "08/26/2026"
PERF_INSTRUCTIONS = "add john doe to the policy"
PERF_INTENT_1_CONST = "Add_Named_Insured"
PERF_TRANSACTION_TYPE_CONST = "MidTermChange"

PERF_PREPROCESSOR_CODE = r'''
from typing import Any
from blocks.base_python_block import WFEngineTaskResult, Block, WFEngineTask
from blocks.types import BlockInputs


class CustomCodeBlockProxyInputs(BlockInputs):
    submission: Any
    perf_test_mode: Any = False


PERF_EFFECTIVE_DATE = "08/26/2026"
PERF_INSTRUCTIONS = "add john doe to the policy"
PERF_INTENT_1 = "Add_Named_Insured"
PERF_TRANSACTION_TYPE = "MidTermChange"

FIELD_DEFAULTS = {
    "Effective Date of Change": PERF_EFFECTIVE_DATE,
    "Instructions": PERF_INSTRUCTIONS,
}

# Mirrors build_salesforce_payload._clean_name so we match fields the way the
# downstream connector does (ZWSP-strip + alias-resolve).
ZWSP = "\u200b"
FIELD_NAME_ALIASES = {
    "Policy Producer Contact": "Policy Endorsement Contact",
    "Path ID": "Path Id",
}


def _clean(name):
    if not isinstance(name, str):
        return ""
    cleaned = name.replace(ZWSP, "").strip()
    return FIELD_NAME_ALIASES.get(cleaned, cleaned)


def _target_document(submission):
    documents = [d for d in submission.get("documents") or [] if isinstance(d, dict)]
    if not documents:
        return None
    for doc in documents:
        metadata = doc.get("metadata") or {}
        filename = " ".join(
            str(doc.get(key) or metadata.get(key) or "")
            for key in ("filename", "file_name", "name", "original_filename", "source_filename")
        )
        if "email" in filename.lower():
            return doc
    return documents[0]


def _inject_field_defaults(submission):
    if not isinstance(submission, dict):
        return submission
    doc = _target_document(submission)
    if doc is None:
        return submission
    fields = doc.setdefault("document_fields", [])
    by_name = {}
    for f in fields:
        if not isinstance(f, dict):
            continue
        if f.get("occurrence_index", 0) != 0:
            continue
        key = _clean(f.get("output_name") or f.get("field_name") or f.get("name"))
        if key and key not in by_name:
            by_name[key] = f
    for name, value in FIELD_DEFAULTS.items():
        existing = by_name.get(name)
        if existing is not None:
            existing["transcription"] = value
            existing["transcription_normalized"] = value
            existing["transcription_source"] = "human_transcription"
            existing["transcription_confidence"] = "sure"
            existing["state"] = "complete"
        else:
            fields.append({
                "id": None,
                "output_name": name,
                "field_name": name,
                "occurrence_index": 0,
                "page_number": 1,
                "identification_source": "human_identification",
                "identification_confidence": "sure",
                "transcription": value,
                "transcription_normalized": value,
                "transcription_source": "human_transcription",
                "transcription_confidence": "sure",
                "required": False,
                "multiline": False,
                "state": "complete",
            })
    return submission


def _perf_prefill(submission):
    doc = _target_document(submission) if isinstance(submission, dict) else None
    doc_ids = [doc.get("id") if doc is not None else None]
    selected = []
    for did in doc_ids:
        selected.append({
            "document_id": did,
            "decision": "intent_1",
            "choice": PERF_INTENT_1,
            "task_purpose_id": 2005,
        })
    selected.append({
        "document_id": doc_ids[0],
        "decision": "transaction_type",
        "choice": PERF_TRANSACTION_TYPE,
        "task_purpose_id": 2005,
    })
    return {"selected_choices": selected}


def _preprocess(submission, perf_test_mode=False):
    if not perf_test_mode:
        return {"submission": submission, "supervision_data": {}}
    modified = _inject_field_defaults(submission)
    return {"submission": modified, "supervision_data": _perf_prefill(modified)}


def process_task(
    proxy: Block, task: WFEngineTask[CustomCodeBlockProxyInputs]
) -> WFEngineTaskResult:
    return _preprocess(**task.inputData.dict())
'''

BYPASS_SUPERVISION_CODE = r'''
from typing import Any
from blocks.base_python_block import WFEngineTaskResult, Block, WFEngineTask
from blocks.types import BlockInputs


class CustomCodeBlockProxyInputs(BlockInputs):
    submission: Any
    supervision_data: Any = None


def process_task(
    proxy: Block, task: WFEngineTask[CustomCodeBlockProxyInputs]
) -> WFEngineTaskResult:
    inp = task.inputData
    return {"submission": inp.submission, "decisions": inp.supervision_data or {"selected_choices": []}}
'''

SUPERVISION_NORMALIZER_CODE = r'''
from typing import Any
from blocks.base_python_block import WFEngineTaskResult, Block, WFEngineTask
from blocks.types import BlockInputs


class CustomCodeBlockProxyInputs(BlockInputs):
    submission: Any
    decisions: Any = None


def process_task(
    proxy: Block, task: WFEngineTask[CustomCodeBlockProxyInputs]
) -> WFEngineTaskResult:
    inp = task.inputData
    return {"submission": inp.submission, "decisions": inp.decisions or {"selected_choices": []}}
'''

PERF_TEST_MODE_INPUT_SPEC = {
    "name": "perf_test_mode",
    "type": "boolean",
    "title": "Perf Test Mode (auto-fill supervision)",
    "description": (
        "TEMPORARY: When true, the custom supervision step is auto-filled with "
        f"intent_1='{PERF_INTENT_1_CONST}' + transaction_type="
        f"'{PERF_TRANSACTION_TYPE_CONST}', and Effective Date / Instructions are "
        "populated with hardcoded values. Also set "
        "manual_field_id_enabled=false and manual_transcription_enabled=false "
        "for a fully hands-off run. Leave FALSE for regular UAT / prod runs."
    ),
    "value": False,
    "optional": True,
}



def load_new_intent_oneof() -> list:
    """The 86-intent list lives in
    `build_supervision_template.input.data.intent_oneof` inside the freshly
    built dropdown_core.json."""
    core = json.loads((ROOT / "dropdown_core.json").read_text(encoding="utf-8"))
    for b in core.get("blocks", []):
        if b.get("reference_name") == "build_supervision_template":
            oneof = b.get("input", {}).get("data", {}).get("intent_oneof")
            if isinstance(oneof, list) and oneof and "const" in oneof[0]:
                return copy.deepcopy(oneof)
    raise SystemExit(
        "intent_oneof not found in dropdown_core.json > build_supervision_template"
    )


def _extract_reference(zip_path: Path, dst: Path) -> None:
    """Extract the reference zip into `dst`, flattening the top-level
    `refactored_export/` wrapper folder if present."""
    # Delete file contents individually (tolerant to OneDrive holding empty
    # directories open, which blocks a full rmtree).
    if dst.exists():
        for p in sorted(dst.rglob("*"), key=lambda x: -len(x.parts)):
            try:
                if p.is_file() or p.is_symlink():
                    p.unlink()
                elif p.is_dir():
                    try:
                        p.rmdir()
                    except OSError:
                        pass
            except (PermissionError, OSError):
                pass
    dst.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(dst)

    # If the zip contained a wrapper folder (as `refactored_export (4).zip`
    # does), move its contents up to DST so downstream tooling sees the
    # flat manifest.json + flows/ shape.
    wrapper = dst / "refactored_export"
    if wrapper.is_dir() and (wrapper / "manifest.json").exists():
        for child in wrapper.iterdir():
            target = dst / child.name
            if child.is_dir():
                # Merge-move: copy each file over, overwriting; keep target
                # directory (OneDrive may hold empty dirs open on Windows).
                target.mkdir(parents=True, exist_ok=True)
                for sub in child.rglob("*"):
                    rel = sub.relative_to(child)
                    dest = target / rel
                    if sub.is_dir():
                        dest.mkdir(parents=True, exist_ok=True)
                    else:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(sub), str(dest))
            else:
                if target.exists():
                    try:
                        target.unlink()
                    except PermissionError:
                        pass
                shutil.copy2(str(child), str(target))
        # Best-effort cleanup of the inner wrapper folder.
        try:
            shutil.rmtree(wrapper)
        except (PermissionError, OSError):
            pass


def _rebrand_wrapper_as_perf(flows_dir: Path) -> None:
    """Rename the wrapper flow (file + uuid + identifier + title) so it
    imports into HS as a NEW distinct flow instead of overwriting the
    original wrapper. Core flow is intentionally left with its shared uuid."""
    src = next(
        (p for p in flows_dir.glob("*.json") if ORIGINAL_WRAPPER_UUID in p.name),
        None,
    )
    if src is None:
        # Already rebranded on a previous run — nothing to do.
        return
    text = src.read_text(encoding="utf-8")
    text = text.replace(ORIGINAL_WRAPPER_UUID, WRAPPER_UUID_FRAG)
    text = text.replace(
        f'"title": "{ORIGINAL_WRAPPER_TITLE}"',
        f'"title": "{PERF_WRAPPER_TITLE}"',
    )
    dst_name = src.name.replace(
        ORIGINAL_WRAPPER_UUID, WRAPPER_UUID_FRAG
    ).replace(
        "Endorsement_Automation_Dev_Sample_-_Custom_Flow",
        "Endorsement_Automation_Dev_Sample_-_PERF_TEST",
    )
    dst = src.with_name(dst_name)
    dst.write_text(text, encoding="utf-8")
    src.unlink()
    print(f"Rebranded wrapper -> {dst.name}")
    _disable_salesforce_output(dst)


def _disable_salesforce_output(wrapper_path: Path) -> None:
    """The Salesforce output block's secret refs are keyed to the ORIGINAL
    wrapper uuid; after rebrand they no longer resolve in HS. Disable the
    output block and clear the stale secret references so import succeeds."""
    flow = json.loads(wrapper_path.read_text(encoding="utf-8"))
    for b in flow.get("blocks", []):
        if b.get("reference_name") != "outputs":
            continue
        for out in b.get("blocks", []) or []:
            if out.get("reference_name") == "cob_http_export_sync_policy_txn_to_sf":
                out["enabled"] = False
                inp = out.setdefault("input", {})
                inp["enabled"] = False
                inp["client_secret"] = ""
                inp["endpoint_secrets"] = ""
    wrapper_path.write_text(json.dumps(flow, indent=2), encoding="utf-8")
    print("Disabled Salesforce output block on perf wrapper (secrets not needed).")


# ---------------------------------------------------------------------------
# TEMPORARY: perf-test overlay helpers. Delete this section (and their calls
# in main()) to strip perf-test from the export.
# ---------------------------------------------------------------------------

def _ensure_perf_flag_in_manifest(flow: dict) -> bool:
    """Add perf_test_mode to a flow's manifest.input[] if not already there."""
    inputs = flow.setdefault("manifest", {}).setdefault("input", [])
    if any(inp.get("name") == "perf_test_mode" for inp in inputs):
        return False
    inputs.append(copy.deepcopy(PERF_TEST_MODE_INPUT_SPEC))
    return True


def _wire_perf_flag_in_wrapper(wrapper: dict) -> None:
    """Wrapper edits: declare flag, pass to core subflow, set default in
    the flow-level `input` defaults block."""
    _ensure_perf_flag_in_manifest(wrapper)
    for b in wrapper.get("blocks", []):
        if b.get("reference_name") == "__idp_core__":
            b.setdefault("input", {}).setdefault(
                "perf_test_mode", "${workflow.input.perf_test_mode}"
            )
    wrapper.setdefault("input", {}).setdefault("perf_test_mode", False)


def _insert_perf_preprocessor(core: dict) -> None:
    """Insert perf_test_preprocessor PythonBlock and rewire supervision
    inputs to consume its output."""
    blocks = core.get("blocks", [])

    prep = next(
        (b for b in blocks if b.get("reference_name") == "perf_test_preprocessor"),
        None,
    )
    if prep is None:
        insert_at = None
        for i, b in enumerate(blocks):
            if b.get("reference_name") == "manual_transcription":
                insert_at = i + 1
                break
        if insert_at is None:
            raise SystemExit("manual_transcription block not found; cannot insert perf preprocessor")
        prep = {
            "identifier": SAAS_PYTHON_BLOCK_IDENTIFIER,
            "reference_name": "perf_test_preprocessor",
            "input": {
                "data": {
                    "submission": "${manual_transcription.output.submission}",
                    "perf_test_mode": "${workflow.input.perf_test_mode}",
                },
                "code": PERF_PREPROCESSOR_CODE,
            },
            "title": "Perf Test Preprocessor",
            "description": (
                "TEMPORARY: When perf_test_mode=true, injects default field "
                "values into the submission and pre-fills supervision decisions "
                "so the custom supervision step auto-completes without a UI task."
            ),
        }
        blocks.insert(insert_at, prep)
    else:
        prep.setdefault("input", {}).setdefault("data", {})[
            "perf_test_mode"
        ] = "${workflow.input.perf_test_mode}"
        prep["input"]["code"] = PERF_PREPROCESSOR_CODE

    # Python code blocks nest their return dict under output.result.*
    prep_sub = "${perf_test_preprocessor.output.result.submission}"
    prep_sup = "${perf_test_preprocessor.output.result.supervision_data}"
    for b in blocks:
        rn = b.get("reference_name")
        if rn == "build_supervision_template":
            data = b.setdefault("input", {}).setdefault("data", {})
            if data.get("submission") in (
                "${manual_transcription.output.submission}",
                "${perf_test_preprocessor.output.submission}",
            ):
                data["submission"] = prep_sub
        elif rn == "intent_supervision":
            inp = b.setdefault("input", {})
            if inp.get("submission") in (
                "${manual_transcription.output.submission}",
                "${perf_test_preprocessor.output.submission}",
            ):
                inp["submission"] = prep_sub
            inp["data"] = prep_sup


def _wrap_supervision_in_routing(core: dict) -> None:
    """Wrap `intent_supervision` in a ROUTING block keyed on perf_test_mode.

    - case "true"  -> bypass_supervision python block (emits {submission, decisions})
    - case "false" -> intent_supervision + supervision_normalizer python block

    Both branches terminate in a Python code block so `intent_routing.output`
    is uniformly `{result: {submission, decisions}}` for downstream consumers.
    """
    blocks = core.get("blocks", [])
    if any(b.get("reference_name") == "intent_routing" for b in blocks):
        return  # already wrapped

    sup_idx = None
    sup_block = None
    for i, b in enumerate(blocks):
        if b.get("reference_name") == "intent_supervision":
            sup_idx = i
            sup_block = b
            break
    if sup_idx is None:
        raise SystemExit("intent_supervision block not found; cannot wrap in routing")

    bypass_block = {
        "identifier": SAAS_PYTHON_BLOCK_IDENTIFIER,
        "reference_name": "bypass_supervision",
        "input": {
            "data": {
                "submission": "${perf_test_preprocessor.output.result.submission}",
                "supervision_data": "${perf_test_preprocessor.output.result.supervision_data}",
            },
            "code": BYPASS_SUPERVISION_CODE,
        },
        "title": "Bypass Supervision (perf)",
        "description": "TEMPORARY perf-test bypass: forwards preprocessor submission + prefilled decisions without opening a supervision task.",
    }
    normalizer_block = {
        "identifier": SAAS_PYTHON_BLOCK_IDENTIFIER,
        "reference_name": "supervision_normalizer",
        "input": {
            "data": {
                "submission": "${intent_supervision.output.submission}",
                "decisions": "${intent_supervision.output.decisions}",
            },
            "code": SUPERVISION_NORMALIZER_CODE,
        },
        "title": "Supervision Normalizer",
        "description": "Wraps supervision output under .result so downstream references are uniform across both routing branches.",
    }

    routing_block = {
        "identifier": "ROUTING",
        "reference_name": "intent_routing",
        "title": "Intent Supervision Routing",
        "description": "TEMPORARY: routes around Custom Supervision when perf_test_mode=true.",
        "branches": [
            {
                "case": "true",
                "label": "perf-bypass",
                "output": "bypass_supervision",
                "blocks": [bypass_block],
            },
            {
                "case": "false",
                "label": "normal",
                "output": "supervision_normalizer",
                "blocks": [sup_block, normalizer_block],
            },
        ],
        "decision": "${workflow.input.perf_test_mode}",
    }

    blocks.pop(sup_idx)
    blocks.insert(sup_idx, routing_block)

    adapter_sub = "${intent_routing.output.result.submission}"
    adapter_dec = "${intent_routing.output.result.decisions}"
    for b in blocks:
        rn = b.get("reference_name")
        if rn == "build_salesforce_payload":
            data = b.setdefault("input", {}).setdefault("data", {})
            if data.get("submission") == "${intent_supervision.output.submission}":
                data["submission"] = adapter_sub
            if data.get("decisions") == "${intent_supervision.output.decisions}":
                data["decisions"] = adapter_dec
        elif rn == "complete_submission":
            inp = b.setdefault("input", {})
            if inp.get("submission") == "${intent_supervision.output.submission}":
                inp["submission"] = adapter_sub


def _apply_perf_test_overlay(flows_dir: Path, update_wrapper: bool = True) -> None:
    """Apply the perf-test preprocessor to the core and optionally wire wrapper."""
    core_path = next(
        (p for p in flows_dir.glob("*.json") if CORE_UUID_FRAG in p.name), None,
    )
    if core_path is None:
        raise SystemExit("core flow file not found for perf overlay")

    core = json.loads(core_path.read_text(encoding="utf-8"))
    _ensure_perf_flag_in_manifest(core)
    _insert_perf_preprocessor(core)
    _wrap_supervision_in_routing(core)
    core_path.write_text(json.dumps(core, indent=2), encoding="utf-8")

    if update_wrapper:
        wrapper_path = next(
            (p for p in flows_dir.glob("*.json") if WRAPPER_UUID_FRAG in p.name), None,
        )
        if wrapper_path is None:
            raise SystemExit("wrapper flow file not found for perf overlay")
        wrapper = json.loads(wrapper_path.read_text(encoding="utf-8"))
        _wire_perf_flag_in_wrapper(wrapper)
        wrapper_path.write_text(json.dumps(wrapper, indent=2), encoding="utf-8")
    print("Applied perf-test overlay to core flow only.")


def _recompile_python_identifiers(flow: dict) -> int:
    """Use the V44 SaaS-targeted Python block identifier recursively."""
    changed = 0

    def visit(blocks) -> None:
        nonlocal changed
        if not isinstance(blocks, list):
            return
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if block.get("identifier") in {"PYTHON_CODE", "PYTHON_3_12_CODE"}:
                block["identifier"] = SAAS_PYTHON_BLOCK_IDENTIFIER
                changed += 1
            visit(block.get("blocks"))
            for branch in block.get("branches", []):
                if isinstance(branch, dict):
                    visit(branch.get("blocks"))

    visit(flow.get("blocks"))
    return changed


def main() -> None:
    core_only = "--core-only" in sys.argv[1:]
    if not core_only and not REF_ZIP.exists():
        raise SystemExit(f"Reference zip not found: {REF_ZIP}")

    if not core_only:
        _extract_reference(REF_ZIP, DST)

    new_intents = load_new_intent_oneof()
    print(
        f"New intent_oneof length: {len(new_intents)}  "
        f"(first: {new_intents[0]['const']})"
    )

    flows_dir = DST / "flows"
    if not core_only:
        _rebrand_wrapper_as_perf(flows_dir)
    core_path = next(
        (p for p in flows_dir.glob("*.json") if CORE_UUID_FRAG in p.name),
        None,
    )
    if core_path is None:
        raise SystemExit(
            f"Core flow file (containing {CORE_UUID_FRAG}) not found in {flows_dir}"
        )

    core = json.loads(core_path.read_text(encoding="utf-8"))
    patched = False
    for b in core.get("blocks", []):
        if b.get("reference_name") != "build_supervision_template":
            continue
        data = b.setdefault("input", {}).setdefault("data", {})

        # 1) intent_oneof: surgical overwrite from fresh dropdown_core.json.
        old_intent_len = len(data.get("intent_oneof") or [])
        data["intent_oneof"] = new_intents
        print(f"intent_oneof: {old_intent_len} -> {len(new_intents)}")

        # 2) transaction_type_oneof: keep existing consts, relabel titles.
        tx = data.get("transaction_type_oneof")
        if not isinstance(tx, list) or not tx:
            raise SystemExit(
                "transaction_type_oneof missing in reference zip; refusing to "
                "invent one and risk changing production UI structure."
            )
        for opt in tx:
            const = opt.get("const")
            if const in TRANSACTION_TYPE_TITLES:
                new_title = TRANSACTION_TYPE_TITLES[const]
                if opt.get("title") != new_title:
                    print(
                        f"transaction_type[{const}].title: "
                        f"{opt.get('title')!r} -> {new_title!r}"
                    )
                    opt["title"] = new_title
        if not any(opt.get("const") == "None" for opt in tx):
            tx.insert(0, {"const": "None", "title": "-- None --"})
            print("transaction_type_oneof: prepended 'None'")
        if not any(opt.get("const") == "Exception" for opt in tx):
            tx.append({"const": "Exception", "title": "Exception"})
            print("transaction_type_oneof: appended 'Exception'")

        code = b.setdefault("input", {}).get("code") or ""
        submission_level_snippet = '''    inputs.append({
        "name": "transaction_type",
        "type": "decision",
        "title": "Transaction Type",
        "optional": True,
        "schema": {"oneOf": tx_oneof},
    })'''
        document_level_snippet = '''    inputs.append({
        "name": "transaction_type",
        "type": "decision",
        "title": "Transaction Type",
        "relation": {"type": "document"},
        "required": True,
        "schema": {"oneOf": tx_oneof},
    })'''
        multiple_tx_snippet = '''    inputs.append({
        "name": "multiple_transaction_type",
        "type": "decision",
        "title": "Multiple Transaction Type",
        "relation": {"type": "document"},
        "schema": {
            "oneOf": [
                {"const": "True", "title": "True"},
                {"const": "False", "title": "False"},
            ]
        },
    })'''
        if submission_level_snippet in code:
            code = code.replace(submission_level_snippet, document_level_snippet, 1)
            print("transaction_type: required per selected document")
        code, removed_count = re.subn(
            r'\n    inputs\.append\(\{\n'
            r'        "name": "multiple_transaction_type",.*?\n'
            r'    \}\)',
            "",
            code,
            flags=re.DOTALL,
        )
        if removed_count:
            print(f"multiple_transaction_type: removed {removed_count} existing definition(s)")
        if document_level_snippet in code:
            code = code.replace(
                document_level_snippet,
                document_level_snippet + "\n" + multiple_tx_snippet,
                1,
            )
            print("multiple_transaction_type: inserted one canonical definition")
        else:
            raise SystemExit("transaction_type input snippet not found in template code")

        code = code.replace(
            'groups.append({"title": "", "fields": ["transaction_type"]})',
            'groups.append({"title": "", "fields": ["transaction_type", "multiple_transaction_type"]})',
            1,
        )

        b["input"]["code"] = code
        patched = True
        break

    if not patched:
        raise SystemExit("build_supervision_template block not found in core flow")

    # Sync build_salesforce_payload code from code_blocks/ into the flow so
    # local edits (e.g. the -- None -- skip) actually land in HS.
    payload_src = (ROOT / "code_blocks" / "build_salesforce_payload.py").read_text(
        encoding="utf-8"
    )
    synced = False
    for b in core.get("blocks", []):
        if b.get("reference_name") == "build_salesforce_payload":
            b.setdefault("input", {})["code"] = payload_src
            synced = True
            print(f"synced build_salesforce_payload code ({len(payload_src)} bytes)")
            break
    if not synced:
        print("WARNING: build_salesforce_payload block not found; code not synced")

    core_path.write_text(json.dumps(core, indent=2), encoding="utf-8")
    print(f"\nWrote patched core flow -> {core_path.name}")

    # TEMPORARY: apply perf-test overlay. Remove this call (and the helper
    # section above) to strip perf-test wiring from the export.
    _apply_perf_test_overlay(flows_dir, update_wrapper=False)

    # The reference export may contain legacy Python identifiers. Recompile
    # all nested Python blocks to the runtime selected for SaaS V44.
    recompiled = 0
    for flow_path in flows_dir.glob("*.json"):
        flow = json.loads(flow_path.read_text(encoding="utf-8"))
        changed = _recompile_python_identifiers(flow)
        if changed:
            flow_path.write_text(json.dumps(flow, indent=2), encoding="utf-8")
            recompiled += changed
    print(f"Recompiled {recompiled} Python block(s) to {SAAS_PYTHON_BLOCK_IDENTIFIER}.")

    print(
        "Done. refactored_export/ = reference zip contents with intent_oneof "
        "and transaction_type titles synced from build_flow.py."
    )


if __name__ == "__main__":
    main()
