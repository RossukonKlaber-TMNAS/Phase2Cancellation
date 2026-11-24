"""Refactor the imported "Endorsement Automation Dev Sample - Custom Flow"
export so its core subflow uses our dropdown supervision blocks instead of the
shipped custom Python blocks (validate_effective_date / get_submission_details
/ identify_productcode / mark_as_complete / sync_transformed) and the
Flexible Extraction block. Also renames "NB" → "Endorsement" in titles and
filenames.

Reads from   : C:\\Users\\<user>\\Downloads\\Flow-Endorsement_Automation_Dev_Sample_-_Custom_Flow-45c5dd9e-...
Writes to    : ./refactored_export/
"""
from __future__ import annotations

import copy
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = Path(
    r"C:\Users\rohchallapalli\Downloads\Flow-Endorsement_Automation_Dev_Sample_-_Custom_Flow-45c5dd9e-9b74-4a02-b3da-d5ed2a87be7d"
)
DST = ROOT / "refactored_export"

# New identity for the duplicated flows. Hard-coded so re-running the script
# is idempotent (same UUIDs each run, no accidental new flow records in HS).
NEW_CORE_UUID = "a1b2c3d4-e5f6-47a8-9b10-1d2e3f4a5b6c"
NEW_CORE_IDENTIFIER = "ENDORSEMENT_CUSTOM_CORE_V41"
ORIGINAL_CORE_IDENTIFIER = "CUSTOM_PRODUCT_CODE_IDENTIFIER_CORE_V41"

NEW_WRAPPER_UUID = "b2c3d4e5-f6a7-48b9-ac10-2e3f4a5b6c7d"
NEW_WRAPPER_IDENTIFIER_SUFFIX = "__hs_b2c3d4e5-f6a7-48b9-ac10-2e3f4a5b6c7d__"
ORIGINAL_WRAPPER_UUID = "45c5dd9e-9b74-4a02-b3da-d5ed2a87be7d"
ORIGINAL_WRAPPER_IDENTIFIER_SUFFIX = "__hs_45c5dd9e-9b74-4a02-b3da-d5ed2a87be7d__"

# Blocks to delete from the core subflow.
REMOVE_BLOCKS = {
    "validate_effective_date",
    "flexible_extraction",
    "get_submission_details",
    "identify_productcode",
    "mark_as_complete",
    "sync_transformed",
}

# Wrapper input keys to drop now that identify_productcode is gone.
WRAPPER_INPUT_KEYS_TO_REMOVE = {
    "Layout-Product code Mapping",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_dropdown_blocks() -> tuple[dict, dict]:
    """Pull the build_supervision_template and intent_supervision blocks
    out of the already-built dropdown_core.json so we don't have to
    re-serialize the python source by hand.
    """
    core = load_json(ROOT / "dropdown_core.json")
    builder = supervision = None
    for b in core.get("blocks", []):
        if b.get("reference_name") == "build_supervision_template":
            builder = copy.deepcopy(b)
        elif b.get("reference_name") == "intent_supervision":
            supervision = copy.deepcopy(b)
    if builder is None or supervision is None:
        raise SystemExit("dropdown_core.json missing supervision blocks")
    return builder, supervision


def get_submission_details_block() -> dict:
    """Fetch the persisted submission record from the HS API. This is the only
    place the platform exposes the caller-supplied `external_id`; the in-flight
    pipeline submission (`intent_supervision.output.submission`) does not carry
    it. Mirrors the reference flow's `get_submission_details` HTTP_REST block.
    """
    return {
        "identifier": "HTTP_REST",
        "reference_name": "get_submission_details",
        "input": {
            "method": "GET",
            "sdm_app_endpoint": "api/v5/submissions/${submission_bootstrap.output.result.submission.id}?flat=false",
            "timeout": 600,
        },
        "title": "Get Submission Details",
        "description": "Fetch persisted submission record (carries external_id).",
    }


def build_salesforce_payload_block() -> dict:
    """Construct the salesforce-payload PythonBlock by reading the source
    from `code_blocks/build_salesforce_payload.py`. Editing the .py file is
    enough — re-running this script re-embeds it into the flow.
    """
    src_path = ROOT / "code_blocks" / "build_salesforce_payload.py"
    code = src_path.read_text(encoding="utf-8")
    return {
        "identifier": "PYTHON_3_12_CODE",
        "reference_name": "build_salesforce_payload",
        "input": {
            "data": {
                "submission": "${intent_supervision.output.submission}",
                "decisions": "${intent_supervision.output.decisions}",
                "submission_record": "${get_submission_details.output.result.data}",
            },
            "code": code,
        },
        "title": "Build Salesforce Payload",
        "description": "Reshape native HS submission to the Salesforce contract shape.",
    }



def refactor_core_flow(flow: dict) -> dict:
    flow = copy.deepcopy(flow)
    flow["title"] = "Endorsement Custom Core Flow_V41"
    # Give the duplicated core flow its own UUID + manifest identifier so it
    # becomes a separate flow record in HS instead of overwriting the shared
    # "NB SF Custom Product Code Core Flow V41".
    flow["uuid"] = NEW_CORE_UUID
    if isinstance(flow.get("manifest"), dict):
        flow["manifest"]["identifier"] = NEW_CORE_IDENTIFIER
    if isinstance(flow.get("description"), str):
        flow["description"] = flow["description"].replace("NB SF", "Endorsement")

    # Drop unwanted blocks.
    flow["blocks"] = [b for b in flow["blocks"] if b.get("reference_name") not in REMOVE_BLOCKS]

    # Re-wire manual_transcription to feed directly off machine_transcription.
    for b in flow["blocks"]:
        if b.get("reference_name") == "manual_transcription":
            b["input"]["submission"] = "${machine_transcription.output.submission}"

    # Insert build_supervision_template + intent_supervision after manual_transcription.
    builder, supervision = get_dropdown_blocks()
    # Both blocks already wire submission to ${manual_transcription.output.submission}.
    insert_at = next(
        (i for i, b in enumerate(flow["blocks"]) if b.get("reference_name") == "manual_transcription"),
        len(flow["blocks"]) - 1,
    ) + 1
    flow["blocks"][insert_at:insert_at] = [builder, supervision]

    # Insert salesforce-payload transformer immediately after intent_supervision.
    # First fetch the persisted submission record (carries external_id), then
    # build the payload from it.
    submission_details = get_submission_details_block()
    sf_payload = build_salesforce_payload_block()
    insert_sf_at = next(
        (i for i, b in enumerate(flow["blocks"]) if b.get("reference_name") == "intent_supervision"),
        len(flow["blocks"]) - 1,
    ) + 1
    flow["blocks"][insert_sf_at:insert_sf_at] = [submission_details, sf_payload]

    # Re-wire complete_submission to read from intent_supervision instead of mark_as_complete.
    for b in flow["blocks"]:
        if b.get("reference_name") == "complete_submission":
            for key in ("submission", "payload"):
                if key in b["input"]:
                    b["input"][key] = "${intent_supervision.output.submission}"

    return flow


def refactor_wrapper(flow: dict, new_core_title: str) -> dict:
    flow = copy.deepcopy(flow)
    # Give the wrapper its own UUID + identifier so importing it does not
    # overwrite the original "Endorsement Automation Dev Sample - Custom Flow".
    flow["uuid"] = NEW_WRAPPER_UUID
    if isinstance(flow.get("manifest"), dict):
        old_id = flow["manifest"].get("identifier", "")
        flow["manifest"]["identifier"] = old_id.replace(
            ORIGINAL_WRAPPER_IDENTIFIER_SUFFIX, NEW_WRAPPER_IDENTIFIER_SUFFIX
        )

    # Rewrite ${system.secrets.<old-uuid-no-dashes>__...} references so they
    # are scoped to the new wrapper UUID. Secret values themselves must be
    # re-created under the new flow in the HS Secrets manager after import.
    old_prefix = ORIGINAL_WRAPPER_UUID.replace("-", "")
    new_prefix = NEW_WRAPPER_UUID.replace("-", "")
    blob = json.dumps(flow)
    blob = blob.replace(f"system.secrets.{old_prefix}__", f"system.secrets.{new_prefix}__")
    flow = json.loads(blob)
    # Title is already "Endorsement Automation Dev Sample - Custom Flow"; leave alone.
    for b in flow.get("blocks", []):
        if b.get("reference_name") == "__idp_core__":
            # Re-point the subflow reference at our duplicated core flow.
            if b.get("identifier") == ORIGINAL_CORE_IDENTIFIER:
                b["identifier"] = NEW_CORE_IDENTIFIER
            for k in list(b.get("input", {}).keys()):
                if k in WRAPPER_INPUT_KEYS_TO_REMOVE:
                    b["input"].pop(k, None)
            # Strip ingestion secret references — not configured yet for the
            # endorsement flow. Submissions will be created manually via UI
            # until S3/OCS bootstrap is wired up.
            for k in ("submission_bootstrap_s3_config", "submission_bootstrap_ocs_config"):
                if k in b.get("input", {}):
                    b["input"][k] = None
            # Update the human-readable title of the subflow node.
            if "title" in b:
                b["title"] = b["title"].replace("NB", "Endorsement")
        if b.get("reference_name") == "outputs":
            # Historically we stripped `cob_http_export_*` sub-blocks because
            # the source snapshot carried NB-side Salesforce push connectors
            # that would have failed on import for the endorsement wrapper.
            # Salesforce push and the preceding log block are now configured
            # in HS Studio and must survive re-runs, so we preserve every
            # sub-block from the source as-is. To restore old behavior,
            # re-enable the filter below and refresh the source snapshot.
            #
            # b["blocks"] = [
            #     sb for sb in b.get("blocks", [])
            #     if not str(sb.get("reference_name", "")).startswith("cob_http_export_")
            # ]
            pass
    # Drop matching keys from the wrapper-level input schema, if declared.
    if isinstance(flow.get("input"), dict):
        for k in list(flow["input"].keys()):
            if k in WRAPPER_INPUT_KEYS_TO_REMOVE:
                flow["input"].pop(k, None)
    return flow


def refactor_on_error(flow: dict) -> dict:
    flow = copy.deepcopy(flow)
    if isinstance(flow.get("title"), str):
        flow["title"] = flow["title"].replace(" - NB", " - Endorsement").replace(" NB ", " Endorsement ")
    return flow


def rename_file(name: str) -> str:
    return (
        name.replace("NB_SF_Custom_Product_Code_Core_Flow_V41", "Endorsement_Custom_Core_Flow_V41")
        .replace("On-Error_with_included_Submission_data_-_NB", "On-Error_with_included_Submission_data_-_Endorsement")
        .replace("bc01b5ef-f9e4-49dd-aa0f-a8e3bd89fa00", NEW_CORE_UUID)
        .replace(ORIGINAL_WRAPPER_UUID, NEW_WRAPPER_UUID)
    )


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"Source folder not found: {SRC}")

    if DST.exists():
        shutil.rmtree(DST)
    DST.mkdir(parents=True)

    # Copy manifest verbatim.
    shutil.copy2(SRC / "manifest.json", DST / "manifest.json")

    src_flows = SRC / "flows"
    dst_flows = DST / "flows"
    dst_flows.mkdir(parents=True, exist_ok=True)

    new_core_title = "Endorsement Custom Core Flow_V41"

    for fn in os.listdir(src_flows):
        src_path = src_flows / fn
        flow = load_json(src_path)
        title = flow.get("title", "")

        if "Custom Product Code Core Flow" in title or "NB SF" in title:
            new_flow = refactor_core_flow(flow)
        elif "Endorsement Automation Dev Sample" in title:
            new_flow = refactor_wrapper(flow, new_core_title)
        elif "On-Error" in title:
            new_flow = refactor_on_error(flow)
        else:
            new_flow = flow

        new_name = rename_file(fn)
        dump_json(dst_flows / new_name, new_flow)
        print(f"  {fn} -> {new_name}  (title: {new_flow.get('title')!r})")

    print(f"\nRefactored export written to: {DST}")


if __name__ == "__main__":
    main()
