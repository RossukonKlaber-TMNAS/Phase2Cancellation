"""Hyperscience PythonBlock source for `build_salesforce_payload`.

Reads the native HS submission produced by `intent_supervision` and emits a
Salesforce-shaped payload matching
`samples/salesforce_payload/sample_endorsement_native_hs.json`.

Contract:
- Output is a dict with keys: `id`, `external_id`, `classification_review_needed`,
  `unassigned_pages`, `cases`, `document_folders`, `documents[]`.
- For every document, the canonical 12 identification fields + `Transaction Type`
  + `Instructions` are guaranteed present in `document_fields[]`. Missing values
  are emitted as empty strings (`transcription: ""`, `transcription_normalized: ""`).
- Source mapping:
    * `transcription.source == "machine_transcription"` → "machine"
    * `transcription.source == "human_transcription"`   → "human"
    * Decision-derived rows (intents, single_policy_flag) → "supervision"
- `layout_field_uuid` is intentionally NOT emitted (Option A).

Embedded into the flow via `refactor_export.py`.
"""
from typing import Any, Dict, List
from blocks.base_python_block import WFEngineTaskResult
from blocks.types import BlockInputs
from blocks.base_python_block import Block, WFEngineTask


# Used to deserialize json inputs by the CCB.
class CustomCodeBlockProxyInputs(BlockInputs):
    submission: Any
    decisions: Any = None
    submission_record: Any = None


# Canonical AC field list (US-S2.5 / US-S2.9). Order is preserved on output.
EXPECTED_FIELDS = [
    "Policy Endorsement Contact",
    "Effective Date of Change",
    "New Expiration Date",
    "ERP Effective Date",
    "ERP Expiration Date",
    "Unlimited",
    "New Mailing Address",
    "Customer Account Number",
    "Customer Account",
    "Path Id",
    "Transaction Type",
    "Instructions",
]

# Aliases observed in current layouts → canonical AC name.
FIELD_NAME_ALIASES = {
    "Policy Producer Contact": "Policy Endorsement Contact",
    "Path ID": "Path Id",
}

ZWSP = "\u200b"


def _clean_name(name):
    if not isinstance(name, str):
        return ""
    cleaned = name.replace(ZWSP, "").strip()
    return FIELD_NAME_ALIASES.get(cleaned, cleaned)


def _map_source(raw_source):
    if raw_source == "machine_transcription":
        return "machine"
    if raw_source == "human_transcription":
        return "human"
    if raw_source in ("supervision", "machine", "human"):
        return raw_source
    return "machine"


def _flatten_field(field):
    """Convert HS field dict to flat Salesforce shape.

    Tolerates two shapes for the transcription block:
      * In-flow (intent_supervision output): flat keys
            transcription, transcription_normalized, transcription_source,
            transcription_confidence
      * Post-complete API: nested
            transcription: {raw, normalized, source, ...}
    """
    name = _clean_name(field.get("output_name") or field.get("field_name") or field.get("name") or "")
    occurrence = field.get("occurrence_index", 0) or 0
    # Per Salesforce contract: output_name stays bare for every occurrence;
    # field_name is suffixed with the occurrence number for occurrences >= 1
    # (e.g. "Policy Number", "Policy Number 1", ...).
    field_name = name if occurrence == 0 else f"{name} {occurrence}"

    transcription_val = field.get("transcription")
    if isinstance(transcription_val, dict):
        raw = transcription_val.get("raw") or ""
        normalized = transcription_val.get("normalized")
        if normalized is None:
            normalized = raw or ""
        src_raw = transcription_val.get("source")
    else:
        raw = transcription_val if isinstance(transcription_val, str) else ""
        normalized = field.get("transcription_normalized")
        if not isinstance(normalized, str):
            normalized = raw
        src_raw = field.get("transcription_source") or field.get("identification_source")

    src = _map_source(src_raw)

    fda = field.get("field_definition_attributes") or {}
    required = field.get("required")
    if required is None:
        required = fda.get("required", False)
    multiline = field.get("multiline")
    if multiline is None:
        multiline = fda.get("multiline", False)

    return {
        "id": field.get("id"),
        "output_name": name,
        "field_name": field_name,
        "occurrence_index": occurrence,
        "page_number": field.get("page_number") or 1,
        "identification_source": _map_source(field.get("identification_source") or src_raw),
        "identification_confidence": field.get("identification_confidence") or "sure",
        "transcription": raw if isinstance(raw, str) else "",
        "transcription_normalized": normalized if isinstance(normalized, str) else "",
        "transcription_source": src,
        "transcription_confidence": field.get("transcription_confidence") or "sure",
        "required": bool(required),
        "multiline": bool(multiline),
        "state": field.get("state", "complete"),
    }


def _empty_field(name, page_number=1):
    return {
        "id": None,
        "output_name": name,
        "field_name": name,
        "occurrence_index": 0,
        "page_number": page_number,
        "identification_source": "machine",
        "identification_confidence": "sure",
        "transcription": "",
        "transcription_normalized": "",
        "transcription_source": "machine",
        "transcription_confidence": "sure",
        "required": False,
        "multiline": False,
        "state": "complete",
    }


def _normalize_supervision_decisions(decisions_obj):
    """Convert the supervision-block `decisions` output port into a
    per-document list of {decision, choice} dicts.

    Accepts both shapes:
      * In-flow supervision output:
            {"selected_choices": [
                {"document_id": 31373,
                 "decision_choice": {
                     "decision": {"name": "intent_1"},
                     "choice":   {"name": "add_auto"}}}, ...]}
      * Pre-flattened list (already keyed by document_id) — passthrough.

    Returns: {document_id_or_None: [{"decision": str, "choice": str}, ...]}
    """
    by_doc: Dict[Any, List[Dict[str, Any]]] = {}
    if not decisions_obj:
        return by_doc
    if isinstance(decisions_obj, dict):
        choices = decisions_obj.get("selected_choices") or []
    elif isinstance(decisions_obj, list):
        choices = decisions_obj
    else:
        return by_doc
    for sc in choices:
        if not isinstance(sc, dict):
            continue
        # Already-flattened shape
        if "decision" in sc and isinstance(sc.get("decision"), str):
            doc_id = sc.get("document_id")
            by_doc.setdefault(doc_id, []).append({
                "decision": sc.get("decision") or "",
                "choice": sc.get("choice"),
            })
            continue
        dc = sc.get("decision_choice") or {}
        d_obj = dc.get("decision") or {}
        c_obj = dc.get("choice") or {}
        name = d_obj.get("name") if isinstance(d_obj, dict) else None
        choice = c_obj.get("name") if isinstance(c_obj, dict) else None
        if not name:
            continue
        doc_id = sc.get("document_id")
        by_doc.setdefault(doc_id, []).append({
            "decision": name,
            "choice": choice,
        })
    return by_doc


def _decisions_to_field_rows(decisions, next_id_seed):
    """Translate per-document decisions list into supervision field rows.

    All intents share `output_name: "Intent"`. Their `field_name` is suffixed
    starting at 1: "Intent 1", "Intent 2", "Intent 3". `occurrence_index`
    starts at 0 and increments.
    `single_policy_flag` → field_name "single_policy_flag".
    `transaction_type` → field_name "Transaction Type" (the canonical
    placeholder is removed in `_transform_document` so this is the only row).

    Per-intent date / policy picks (``intent_<N>_effective_date_pick``,
    ``intent_<N>_policy_number_pick``) emit supervision rows keyed by the
    matching intent slot number. They are emitted *only* when the supervisor
    actually selected a real value (skip empty / the ``__none__`` sentinel
    used when nothing was extracted), so consumers can rely on absence to
    mean "no selection".
    """
    import re as _re

    rows = []
    intent_seen = 0
    pick_re = _re.compile(r"^intent_(\d+)_(effective_date|policy_number)_pick$")

    def _row(output_name, field_name, occurrence, choice):
        rows.append({
            "id": next_id_seed[0],
            "output_name": output_name,
            "field_name": field_name,
            "occurrence_index": occurrence,
            "page_number": 1,
            "identification_source": "supervision",
            "identification_confidence": "sure",
            "transcription": str(choice),
            "transcription_normalized": str(choice),
            "transcription_source": "supervision",
            "transcription_confidence": "sure",
            "required": False,
            "multiline": False,
            "state": "complete",
        })
        next_id_seed[0] += 1

    for d in decisions or []:
        name = d.get("decision") or ""
        choice = d.get("choice")
        if choice is None:
            continue
        # Skip placeholder sentinel emitted when no values were extracted.
        if isinstance(choice, str) and (not choice.strip() or choice == "__none__"):
            continue
        # Skip the user-facing "-- None --" dropdown option: treat as "no
        # selection" and omit from the Salesforce payload entirely.
        if choice == "None" and (
            (name.startswith("intent_") and not name.endswith("_pick"))
            or name == "transaction_type"
        ):
            continue

        m = pick_re.match(name)
        if m:
            slot = int(m.group(1))
            kind = m.group(2)
            if kind == "effective_date":
                _row("Effective Date", f"Effective Date {slot}", slot - 1, choice)
            else:
                _row("Policy Number", f"Policy Number {slot}", slot - 1, choice)
            continue

        if name.startswith("intent_") and not name.endswith("_pick"):
            intent_seen += 1
            _row("Intent", f"Intent {intent_seen}", intent_seen - 1, choice)
        elif name == "single_policy_flag":
            _row("Single Policy Flag", "single_policy_flag", 0, choice)
        elif name == "transaction_type":
            _row("Transaction Type", "Transaction Type", 0, choice)
        elif name == "multiple_transaction_type":
            if choice is None:
                continue
            if isinstance(choice, str):
                normalized = choice.strip().lower()
                if normalized in {"", "none", "null", "false", "no"}:
                    continue
            _row("Multiple Transaction Type", "Multiple Transaction Type", 0, choice)
    return rows


def _transform_document(doc, supervision_decisions=None):
    src_fields = doc.get("document_fields") or []
    flat_fields = [_flatten_field(f) for f in src_fields if isinstance(f, dict)]

    # Guarantee canonical fields present (empty-string default).
    have_names = {f["field_name"] for f in flat_fields if f.get("occurrence_index", 0) == 0}
    for canonical in EXPECTED_FIELDS:
        if canonical not in have_names:
            flat_fields.append(_empty_field(canonical))

    # Append supervision rows. Prefer decisions wired in from the supervision
    # block's `decisions` output port; fall back to post-API doc.decisions[].
    next_id = [10_000_000]
    decisions = supervision_decisions if supervision_decisions is not None else doc.get("decisions")
    supervision_rows = _decisions_to_field_rows(decisions, next_id)

    # If supervision provided a Transaction Type, drop the empty placeholder
    # so the payload has exactly one Transaction Type row per document.
    sup_field_names = {r.get("field_name") for r in supervision_rows}
    if "Transaction Type" in sup_field_names:
        flat_fields = [
            f for f in flat_fields
            if not (
                f.get("field_name") == "Transaction Type"
                and f.get("transcription_source") != "supervision"
                and not (f.get("transcription") or "").strip()
            )
        ]

    flat_fields.extend(supervision_rows)

    return {
        "id": doc.get("id"),
        "exceptions": doc.get("exceptions") or [],
        "layout_kind": doc.get("type") or doc.get("layout_kind"),
        "layout_name": doc.get("layout_name"),
        "layout_language": doc.get("layout_language") or "en",
        "layout_tags": doc.get("layout_tags") or [],
        "layout_uuid": doc.get("layout_uuid"),
        "layout_version_name": doc.get("layout_version_name"),
        "layout_version_uuid": doc.get("layout_version_uuid"),
        "metadata": doc.get("metadata") or {},
        "pages": doc.get("pages") or [],
        "status": doc.get("state") or "complete",
        "document_fields": flat_fields,
        "tables": doc.get("document_tables") or [],
        "state": doc.get("state") or "complete",
        "complete_time": doc.get("complete_time"),
    }


def _resolve_external_id(submission, submission_record):
    # Prefer the persisted submission record fetched from
    # `GET /api/v5/submissions/{id}?flat=false` (this is the only place the
    # platform exposes the caller-supplied external_id). Fall back to the
    # in-flight pipeline submission if the record lookup is unavailable.
    for src in (submission_record, submission):
        if isinstance(src, dict):
            ext = (
                src.get("external_id")
                or src.get("source_external_id")
                or (src.get("metadata") or {}).get("external_id")
                or (src.get("api_params") or {}).get("external_id")
            )
            if ext:
                return ext
    return None


def _build_payload(submission, decisions=None, submission_record=None):
    submission = submission or {}
    by_doc = _normalize_supervision_decisions(decisions)
    docs = submission.get("documents") or []
    out_docs = []
    for d in docs:
        doc_id = d.get("id") if isinstance(d, dict) else None
        per_doc = [
            dec for dec in (by_doc.get(None) or [])
            if dec.get("decision") != "transaction_type"
        ]
        per_doc.extend(by_doc.get(doc_id) or [])
        out_docs.append(_transform_document(d, supervision_decisions=per_doc))
    return {
        "id": submission.get("id"),
        "external_id": _resolve_external_id(submission, submission_record),
        "classification_review_needed": False,
        "unassigned_pages": submission.get("unassigned_pages") or [],
        "cases": submission.get("cases") or [],
        "document_folders": submission.get("document_folders") or [],
        "documents": out_docs,
    }


def process_task(
    proxy: Block, task: WFEngineTask[CustomCodeBlockProxyInputs]
) -> WFEngineTaskResult:
    return _build_payload(
        task.inputData.submission,
        task.inputData.decisions,
        task.inputData.submission_record,
    )
