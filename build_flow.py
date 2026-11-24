"""Builds two HS V41 flows for the Drop Down Intent Capture POC.

Architecture (per HS team guidance):

    1. **Core subflow** (`dropdown_core.json`): standard IDP pipeline
       (classification -> identification -> transcription) followed by our
       custom supervision task that captures cancellation intents. Roles default # TODO updated endorsement to cancellation
       to ['supporting', 'idp_core'] so it can be assigned as the IDP Core
       implementation inside the wrapper.

    2. **Wrapper flow** (`dropdown_wrapper.json`): top-level entry point.
       Roles=['idp'] so HS shows the flow page with the Live toggle. Contains
       SubmissionBootstrap -> IDPCoreBlock -> SubmissionComplete. The
       IDPCoreBlock delegates to whichever subflow has role 'idp_core' that
       the user picks in HS Studio (our `dropdown_core` flow).

Import order in HS:
    1. Import `dropdown_core.json`
    2. Import `dropdown_wrapper.json`
    3. Open the wrapper -> set its IDP Core block to point to `dropdown_core`
    4. Attach Layout Release on the wrapper
    5. Toggle wrapper to Live

Run:  python build_flow.py
Output: dropdown_core.json, dropdown_wrapper.json
"""
from __future__ import annotations

import json
import sys
import copy
from datetime import datetime
from pathlib import Path
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

from flows_sdk.flows import Flow
from flows_sdk.utils import workflow_input
from flows_sdk.blocks import PythonBlock
from flows_sdk.implementations.idp_v41 import idp_blocks as ib
from flows_sdk.implementations.idp_v41 import idp_values as iv
from flows_sdk.implementations.idp_v44.idp_blocks import ManualClassificationBlock
from flows_sdk.implementations.idp_v44 import idp_blocks as v44_blocks

# Stable UUIDs so rebuilds don't churn the file (and so HS treats re-imports
# as new versions of the same flow rather than creating new flows).

CORE_FLOW_UUID = UUID("b87e2988-f94c-4642-b298-16fed14109d5") # TODO Updated from the old UUID 6113ffb0-31c5-431c-93ec-a5bb233a3672
WRAPPER_FLOW_UUID = UUID("2271e1ef-82d9-4bb6-8b60-8e7f9cf3bb4c") # TODO Updated from the old 2271e1ef-82d9-4bb6-8b60-8e7f9cf3bb4b


# --------------------------------------------------------------------------- #
# Shared constants
# --------------------------------------------------------------------------- #

# Canonical intent values. These strings are used VERBATIM as the decision
# `const` (the value persisted by Supervision and exported to Salesforce as
# `transcription_normalized`). They intentionally retain underscores and exact
# casing -- do NOT slugify/lowercase them, otherwise the underscores get
# stripped from the value that reaches Salesforce.
# Ordered mapping from const (persisted API-name sent to Salesforce) to the
# exact UI label the client provided. Keep this in the client-specified
# alphabetical order so the Supervision dropdown matches the source of truth.
# When adding a new intent, add ONE entry here; ALLOWED_INTENTS and
# INTENT_SCHEMA_ONEOF are derived from this dict so the two never drift.
# TODO Confirm the intent lists for allow lists
INTENT_LABELS: "dict[str, str]" = {
    "Account_Contact_Update": "Account Contact Update",
    "Add_Additional_Insured_Auto": "Add Additional Insured - Auto",
    "Add_Additional_Insured_Property": "Add Additional Insured - Property",
    "Add_Additional_Property_Coverage_Forms": "Add Additional Property Coverage Forms",
    "Add_Amend_Delete_Additional_Insured_DO": "Add/Amend/Delete  Additional Insured- D&O",
    "Add_Amend_Delete_Additional_Insured_EPLI": "Add/Amend/Delete  Additional Insured- EPLI",
    "Add_Amend_Delete_Additional_Insured_GL": "Add/Amend/Delete  Additional Insured- GL",
    "Add_Amend_Delete_Additional_Insured_Ot": "Add/Amend/Delete Additional Insured - Other",
    "Add_Amend_Delete_Additional_Insured_PL": "Add/Amend/Delete  Additional Insured- PL",
    "Add_Amend_Delete_Driver": "Add/Amend/Delete Driver Request",
    "Add_Amend_Delete_Med": "Add/Amend/Delete Med Mal Coverage",
    "Add_Amend_Delete_PL_Coverage": "Add/Amend/Delete PL Coverage/Limits",
    "Add_Amend_Delete_Special_Events": "Add/Amend/Delete Special Events",
    "Add_Amend_Delete_Underlying_Coverages": "Add/Amend/Delete Underlying Coverages",
    "Add_Auto": "Add Auto",
    "Add_Auto_First_Time": "Add Auto - First Time",
    "Add_Crime_First_Time": "Add Crime - First Time",
    "Add_Cyber_Coverage_Limits": "Add Cyber Coverage/Limits",
    "Add_Delete_Less_Than_10_Autos": "Add/Delete Less Than 10 Autos",
    "Add_Delete_Location_s": "Add/Delete Location(s)",
    "Add_Delete_More_Than_10_Autos": "Add/Delete More Than 10 Autos",
    "Add_GL_Only_Location": "Add GL - Only Location",
    "Add_Inland_Marine_First_Time": "Add Inland Marine - First Time",
    "Add_Location": "Add Location",
    "Add_Loss_Payee": "Add Loss Payee - Auto",
    "Add_Named_Insured": "Add Named Insured",
    "Add_DO_EPLI_Coverage_Limits": "Add D&O/EPLI Coverage/Limits",
    "Add_PL_Coverage_Limits": "Add PL Coverage/Limits",
    "Add_Professional_Liability_First_Time": "Add Professional Liability - First Time",
    "Agency_Contact_Update": "Agency Contact Update",
    "Amend_Auto": "Amend Auto",
    "Amend_Cyber_Coverage_Limits": "Amend Cyber Coverage/Limits",
    "Amend_Delete_Crime_Coverage": "Amend/Delete Crime Coverage",
    "Amend_GL": "Amend GL (Class Codes/Limits/Exposures)",
    "Amend_Mailing_Address": "Amend Mailing Address",
    "Amend_Named_Insured": "Amend Named Insured",
    "Amend_DO_EPLI_Coverage_Limits": "Amend D&O/EPLI Coverage/Limits",
    "Amend_PL_Coverage_Limits": "Amend PL Coverage/Limits",
    "Amend_Remove_Items_Coverage": "Amend/Remove Items or Coverage on Inland Marine",
    "Amend_Umbrella_Limits": "Amend Umbrella Limits",
    "Automated_Emails": "Automated Emails",
    "BME_Request": "BME Request",
    "BOP_Request": "BOP Request",
    "BOR_Request": "BOR Request",
    "Backdate_Add_Delete_Auto": "Backdate Add Auto Greater Than 60 Days",
    "Backdate_Delete_Auto_Greater_Than_60_Day": "Backdate Delete Auto Greater Than 60 Days/Total Loss",
    "Billing_Address": "Billing Address",
    "Billing_Changes_Issues": "Billing Changes/Issues",
    "Bind_Orders": "Bind Orders",
    "Bind_Orders_E_S": "Bind Orders - E&S",
    "COI": "COI",
    "Cancellation_Request": "Cancellation Request",
    "Claim_Reports": "Claim Reports",
    "Court_Commercial_Bonds": "Court and Commercial Bonds",
    "Decrease_Property_Limit": "Decrease Property Limit",
    "Delete_Auto": "Delete Auto",
    "Delete_Cyber_Coverage_Limits": "Delete Cyber Coverage/Limits",
    "Delete_DO_EPLI_Coverage_Limits": "Delete D&O/EPLI Coverage/Limits",
    "Delete_Location": "Delete Location",
    "Delete_Loss_Payee": "Delete Loss Payee - Auto",
    "Delete_Named_Insured": "Delete Named Insured",
    "Delete_PL_Coverage_Limits": "Delete PL Coverage/Limits",
    "Delete_Terrorism_Coverage": "Delete Terrorism Coverage (TRIA)",
    "Duplicate_Request": "Duplicate Request",
    "EPAC_Request": "EPAC Request",
    "ERP": "ERP",
    "Endorsement_Issued_Incorrectly": "Endorsement Issued Incorrectly",
    "Endorsement_Status_Request": "Endorsement Status Request",
    "Exceptions_All_Other": "Exceptions - All Other",
    "Flood_Request_FloodPro": "Flood Request - FloodPro",
    "Flood_Request_WNCFirst": "Flood Request - WNCFirst",
    "Increase_Property_Limit": "Increase Property Limit",
    "Loss_Run_Request": "Loss Run Request",
    "Multiple_Changes": "Multiple Changes",
    "NY_Premium_Audit": "NY Premium Audit",
    "New_Business": "New Business",
    "New_Business_E_S": "New Business - E&S",
    "PCAC_Request": "PCAC Request",
    "PCAP_Request": "PCAP Request",
    "PHBX_Request": "PHBX Request",
    "PHCV_Request": "PHCV Request",
    "PHGT_PHBT_Request": "PHGT/PHBT Request",
    "PHPA_PHPC_Request": "PHPA/PHPC Request",
    "PHPR_PHEX_Request": "PHPR/PHEX Request",
    "PHSD_Cancel_Request": "PHSD Cancel Request",
    "PHSD_General_Inquiries": "PHSD General Inquiries",
    "PHSD_Loss_Run_Request": "PHSD Loss Run Request",
    "Policy_Corrections_Other": "Policy Corrections - Other",
    "Policy_Extension": "Policy Extension",
    "Policy_Issued_Incorrectly": "Policy Issued Incorrectly",
    "RS_Request": "RS Request",
    "RapidSure_Request": "RapidSure F&W Request",
    "Remove_Additional_Insured": "Remove Additional Insured - Auto",
    "Renewal_Business": "Renewal Business",
    "Renewal_Business_E_S": "Renewal Business - E&S",
    "STEP_Request": "STEP Request",
    "Surety_Contract": "Surety Contract",
    "VB_Request": "VB Request",
}

# Derived list of const values (order preserved from INTENT_LABELS).
ALLOWED_INTENTS = list(INTENT_LABELS.keys())

# Number of intent slots rendered on the supervision screen. Kept at 2 to
# match the current production reference export; bump only after coordinating
# with the downstream Salesforce payload builder + build_salesforce_payload.py.
# TODO update INTENT_SLOTS = 1?
# INTENT_SLOTS = 2

# Real HS Studio data-type UUIDs (one per logical field, reused across slots).
# TODO If any, Update Custom Data Type if needed for Cancellation 

# REAL_DATA_TYPES = {
#     "intent":         "e19aa0b5-91e8-4f6d-a465-6cec1e8b8332",
#     "policy_number":  "7fc603ff-6ac9-4db7-92a3-c7d23f70e41f",
#     "effective_date": "ed9aa0b5-91e8-4f6d-a465-6cec1e8b8332",
# }

# DATA_IDENTIFIERS = {
#     f"{base}_{i}": REAL_DATA_TYPES[base]
#     for i in range(1, INTENT_SLOTS + 1)
#     for base in REAL_DATA_TYPES
# }

CORE_FLOW_IDENTIFIER = "CANCELLATION_CUSTOM_CORE_V44"
WRAPPER_FLOW_IDENTIFIER = "DROPDOWN_TRANSACTION_TYPE_WRAPPER"
SAAS_PYTHON_BLOCK_VERSION = PythonBlock.SupportedPythonBlockPythonVersion.PYTHON_3_14
SAAS_PYTHON_BLOCK_IDENTIFIER = "PYTHON_3_14_CODE"

# The current production supervision template is minimal (intent dropdowns +
# doc-level Transaction Type). Policy / effective-date pickers were removed
# from the UI, so these lists are intentionally empty. The PythonBlock still
# accepts them for backward-compatibility with the input contract.
# POLICY_FIELD_NAMES: list = []
# DATE_FIELD_NAMES: list = []


# --------------------------------------------------------------------------- #
# Custom Supervision template
# --------------------------------------------------------------------------- #

# def _intent_const(intent: str) -> str:
#     """Convert a display intent ('Add/Delete Less Than 10 Autos') into a
#     stable snake_case const ('add_delete_less_than_10_autos').

#     Strategy: lowercase, replace any non-alphanumeric character with '_',
#     collapse runs of '_', and strip leading / trailing '_'. Idempotent.
#     """
#     import re
#     slug = re.sub(r"[^a-z0-9]+", "_", intent.lower())
#     return slug.strip("_")


# `const` keeps the exact underscore value (persisted by Supervision and
# exported to Salesforce); `title` is the client-approved UI label shown
# in the dropdown, sourced from INTENT_LABELS so the two never drift.
# INTENT_SCHEMA_ONEOF = [
#     {"const": "None", "title": "-- None --"},
# ] + [
#     {"const": i, "title": INTENT_LABELS[i]} for i in ALLOWED_INTENTS
# ]

# Transaction Type per-slot dropdown. `const` is the value persisted by
# Supervision (and sent to Salesforce); `title` is the label shown to the
# keyer. Consts stay CamelCase (no spaces) per client contract.
FLAT_CANCELLATION_SCHEMA_ONEOF = [
    {"const": "None", "title": "-- None --"},
    {"const": "Yes", "title": "Yes"},
    {"const": "No", "title": "No"},
]

TRANSACTION_TYPE_SCHEMA_ONEOF = [
    {"const": "None", "title": "-- None --"},
    {"const": "Cancellation", "title": "Cancellation"},
    {"const": "Endorsement", "title": "Endorsement"},
    {"const": "Exception", "title": "Exception"},
    {"const": "Combination", "title": "Combination(Cancellation and Endorsement)"},
]

# Defensive check: surface duplicate consts (different display names that
# slugify to the same const) at build time rather than silently dropping
# options in the supervision dropdown.
# _seen = set()
# for _opt in INTENT_SCHEMA_ONEOF:
#     if _opt["const"] in _seen:
#         raise SystemExit(
#             f"Duplicate intent const {_opt['const']!r} from display "
#             f"name {_opt['title']!r}. Rename the display variant in "
#             f"ALLOWED_INTENTS."
#         )
#     _seen.add(_opt["const"])

# TODO Update value in dic of return IF data in DATA_IDENTIFIERS has changed

# def _intent_slot_inputs(slot: int):
#     """Static placeholder slot inputs. The dynamic template builder
#     (PythonBlock) replaces effective_date / policy_number components per slot
#     with decision dropdowns whose options are the actual extracted values
#     from the submission. The intent decision is static (controlled list).
#     """
#     s = str(slot)
#     return [
#         # Decision component renders as a true click-to-open dropdown.
#         # Per HS docs: "Decisions, or decision components, are drop-down menus
#         # with options from a predetermined set of choices set in the JSON
#         # configuration." schema.oneOf = single-select dropdown.
#         {
#             "name": f"intent_{s}",
#             "type": "decision",
#             "title": f"Intent {s}",
#             "relation": {"type": "document"},
#             "schema": {"oneOf": INTENT_SCHEMA_ONEOF},
#         },
#         # Editable transcription of the policy field (so keyer can correct).
#         {
#             "name": f"policy_number_{s}",
#             "type": "transcription",
#             "data_identifier": DATA_IDENTIFIERS[f"policy_number_{s}"],
#             "title": f"Policy Number {s}",
#             "description": "Policy that is being modified.",
#         },
#         # Editable transcription of the effective_date field.
#         {
#             "name": f"effective_date_{s}",
#             "type": "transcription",
#             "data_identifier": DATA_IDENTIFIERS[f"effective_date_{s}"],
#             "title": f"Effective Date {s}",
#             "description": "MM/DD/YYYY",
#         },
#     ]


# --------------------------------------------------------------------------- #
# Dynamic supervision template builder (runs as a PythonBlock at flow time)
# --------------------------------------------------------------------------- #

def _build_dynamic_template(
    submission,
    
    # intent_oneof,
    # intent_slots,
    # policy_field_names,
    # date_field_names,
    hs_base_url=None,
    transaction_type_oneof=None,
    flat_cancellation_oneof=None,
):
    """Build a minimal custom-supervision template: only the per-slot Intent
    decision dropdowns. A banner row at the top renders a link back to the
    Hyperscience submission detail page so reviewers can open the source
    submission (and all attached documents) in a new tab.

    The submission and field-name inputs are accepted for backward-
    compatibility with the PythonBlock input contract but are unused.
    """

    # Resolve submission id and full link URL (defensive against missing keys).
    sub_id = None
    if isinstance(submission, dict):
        sub_id = submission.get("id") or submission.get("submission_id")
    base_url = (hs_base_url or "").rstrip("/")
    link_url = (
        f"{base_url}/submissions/{sub_id}"
        if base_url and sub_id is not None
        else None
    )

    inputs = []
    groups = []

    # Top banner: a transcription component whose visible TITLE carries the
    # full submission URL as selectable plain text. HS populates the input
    # box from ``data_identifier`` (not from ``value``), so the box itself
    # will render empty -- but the URL printed in the title is selectable
    # for copy/paste. HS still requires a well-formed UUID in
    # ``data_identifier`` even for display-only components, so we pass the
    # nil UUID.
    # Top banner: a decision component with a single "Acknowledge" option.
    # The decision component's title renders as a full-width label that
    # wraps, so we put the full submission URL in the title. The dropdown
    # below is functionally a no-op (single option, pre-selected) but is
    # the only HS component type whose label reliably wraps long text.
    # for i in range(1, intent_slots + 1):
    #     s = str(i)
    #     inputs.append({
    #         "name": f"intent_{s}",
    #         "type": "decision",
    #         "title": f"Intent {s}",
    #         "relation": {"type": "document"},
    #         "schema": {"oneOf": intent_oneof},
    #     })
    #     groups.append({"title": "", "fields": [f"intent_{s}"]})

    # Transaction Type dropdown: required reviewer selection that drives the
    # 'Transaction Type' field on the downstream Salesforce payload.
    tx_oneof = transaction_type_oneof or [
        {"const": "Cancellation", "title": "Cancellation"},
        {"const": "Endorsement", "title": "Endorsement"},
        {"const": "Exception", "title": "Exception"},
        {"const": "Combination", "title": "Combination"},
    ]
    inputs.append({
        "name": "transaction_type",
        "type": "decision",
        "title": "Transaction Type",
        "relation": {"type": "document"},
        "required": True,
        "schema": {"oneOf": tx_oneof},
    })

    inputs.append({
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
    })
 
    inputs.append({
        "name": "flat_cancellation",
        "type": "decision",
        "title": "Flat Cancellation",
        "relation": {"type": "document"},
        "schema": {"oneOf": flat_cancellation_oneof},
    })

    groups.append({"title": "", "fields": ["transaction_type", "multiple_transaction_type","flat_cancellation"]})
    

    action = {
        "name": "cancellation_transaction_type", # TODO udpate endorsement_intents to cancellation_instents?
        "display": "Cancellation Transaction Type", # TODO update Cancellation Transaction Type to Cancellation Transaction Type?
        "input": inputs,
        "ui": {"groups": groups},
    }
    if link_url:
        # Some HS UI versions render the action description prominently near
        # the task header; this is a belt-and-braces second placement for the
        # link in case the banner component is collapsed.
        action["description"] = f"Submission link: {link_url}"

    return [
        {
            "name": "three_column_template",
            "version": "1.0",
            "thumbnail": {"group_by_document": True, "group_by_case": True},
            "action": [action],
        }
    ]


# def _single_policy_decision():
#     """Document-level checkboxes for policy scope.
#     Multi-select (anyOf) renders each option as a checkbox."""
#     return {
#         "name": "single_policy_flag",
#         "type": "decision",
#         "title": "Do all intents apply to a single policy?",
#         "relation": {"type": "document"},
#         "schema": {
#             "anyOf": [
#                 {"const": "yes", "title": "Yes - single policy"},
#                 {"const": "no", "title": "No - multiple policies"},
#             ]
#         },
#     }

# def _multiple_transaction_type_decision():
#     """Optional document-level yes/no decision for whether there are
#     multiple transaction types in the submission. This is a supported
#     dropdown-style choice in HS v41 and should be treated as 'None' when
#     unset or no to avoid sending a blank/false indicator downstream."""
#     return {
#         "name": "multiple_transaction_type",
#         "type": "decision",
#         "title": "Multiple Transaction Type",
#         "relation": {"type": "document"},
#         "schema": {
#             "oneOf": [
#                 {"const": "True", "title": "True"},
#                 {"const": "False", "title": "False"},
#             ]
#         },
#     }


# def _supervision_template():
#     inputs = [_single_policy_decision()]
#     groups = [
#         {
#             "title": "Policy Scope",
#             "fields": ["single_policy_flag", "multiple_transaction_type"],
#         }
#     ]
#     for i in range(1, INTENT_SLOTS + 1):
#         inputs.extend(_intent_slot_inputs(i))
#         groups.append(
#             {
#                 "title": f"Intent #{i}",
#                 "fields": [
#                     f"intent_{i}",
#                     f"policy_number_{i}",
#                     f"effective_date_{i}",
#                 ],
#             }
#         )

#     inputs.append({
#         "name": "transaction_type",
#         "type": "decision",
#         "title": "Transaction Type",
#         "relation": {"type": "document"},
#         "required": True,
#         "schema": {"oneOf": TRANSACTION_TYPE_SCHEMA_ONEOF},
#     })
#     inputs.append(_multiple_transaction_type_decision())
#     groups.append({
#         "title": "",
#         "fields": ["transaction_type", "multiple_transaction_type"],
#     })

#     return [
#         {
#             "name": "three_column_template",
#             "version": "1.0",
#             "thumbnail": {
#                 "group_by_document": True,
#                 "group_by_case": True,
#             },
#             "action": [
#                 {
#                     "name": "endorsement_intents", # TODO update endorsement_intents to cancellation_intents
#                     "display": "Endorsement Intents", # TODO update Endorsement Intents to Cancellation Intents
#                     "input": inputs,
#                     "ui": {"groups": groups},
#                 }
#             ],
#         }
#     ]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _sanitize_top_input(d):
    """Replace self-referential ``${workflow.input.X}`` strings with None so HS
    treats them as user-fillable rather than trying to resolve them at the
    flow level (which causes 'Invalid value for field data type' errors).
    """
    out = {}
    for k, v in d.items():
        if isinstance(v, str) and v.startswith("${workflow.input."):
            out[k] = None
        else:
            out[k] = v
    return out


# --------------------------------------------------------------------------- #
# Core subflow: standard IDP pipeline + custom supervision
# --------------------------------------------------------------------------- #

def build_core_flow() -> Flow:
    bootstrap = ib.SubmissionBootstrapBlock(reference_name="submission_bootstrap")

    machine_classification = ib.MachineClassificationBlock(
        reference_name="machine_classification",
        submission=bootstrap.output("submission"),
        api_params=bootstrap.output("api_params"),
    )

    manual_classification = ManualClassificationBlock(
        reference_name="manual_classification",
        submission=machine_classification.output("submission"),
        api_params=bootstrap.output("api_params"),
    )

    machine_identification = ib.MachineIdentificationBlock(
        reference_name="machine_identification",
        submission=manual_classification.output("submission"),
        api_params=bootstrap.output("api_params"),
        manual_field_id_enabled=False,
    )

    manual_identification = ib.ManualIdentificationBlock(
        reference_name="manual_identification",
        submission=machine_identification.output("submission"),
        api_params=bootstrap.output("api_params"),
        manual_field_id_enabled=False,
    )

    machine_transcription = ib.MachineTranscriptionBlock(
        reference_name="machine_transcription",
        submission=manual_identification.output("submission"),
        api_params=bootstrap.output("api_params"),
    )

    manual_transcription = ib.ManualTranscriptionBlock(
        reference_name="manual_transcription",
        submission=machine_transcription.output("submission"),
        api_params=bootstrap.output("api_params"),
    )
    build_template = PythonBlock(
            reference_name="build_supervision_template",
            code=_build_dynamic_template,
            python_version=SAAS_PYTHON_BLOCK_VERSION,
            code_input={
                "submission": manual_transcription.output("submission"),
                # "intent_oneof": INTENT_SCHEMA_ONEOF,
                # "intent_slots": INTENT_SLOTS,

                # Identify policy / effective-date fields by their layout field
                # *name* (case-insensitive, zero-width-space tolerant). Names are
                # stable across HS environments; UUIDs are not. Add any layout
                # variants your tenant uses here.
                # "policy_field_names": POLICY_FIELD_NAMES,
                # "date_field_names": DATE_FIELD_NAMES,
                # Base URL of the HS tenant; used by the runtime template to
                # render a copyable link back to the submission detail page.
                "hs_base_url": "${workflow.input.hs_base_url}",
                "transaction_type_oneof": TRANSACTION_TYPE_SCHEMA_ONEOF,
                "flat_cancellation_oneof": FLAT_CANCELLATION_SCHEMA_ONEOF,
            },
        )
    
    transaction_supervision = ib.IdpCustomSupervisionBlock(
        reference_name="transaction_supervision",
        submission=manual_transcription.output("submission"),
        task_purpose="capture_transcription",
        supervision_template=build_template.output(),
    )

    def _merge_outputs(submission: dict, decisions: dict) -> dict:
        # Extract selected decision choices into a clean dictionary (e.g., {"transaction_type": "Cancellation"})
        extracted_decisions = {}
        for item in decisions.get("selected_choices", []):
            dc = item.get("decision_choice", {})
            decision_name = dc.get("decision", {}).get("name")
            choice_name = dc.get("choice", {}).get("name")
            if decision_name:
                extracted_decisions[decision_name] = choice_name

        # Attach to submission external_metadata (or inject into a specific document's fields)
        # metadata = submission.get("external_metadata") or {}
        # metadata["custom_decisions"] = extracted_decisions
        # metadata["raw_decisions"] = decisions
        # submission["external_metadata"] = metadata

        submission["custom_decisions"] = decisions

        return submission

    merge_outputs = PythonBlock(
        reference_name="merge_outputs",
        code=_merge_outputs,
        python_version=SAAS_PYTHON_BLOCK_VERSION,
        code_input={
            "submission": transaction_supervision.output("submission"),
            "decisions": transaction_supervision.output("decisions"),
        },
    )

    complete = ib.SubmissionCompleteBlock(
        reference_name="complete",
        submission=merge_outputs.output(),
    )
    #     payload={
    #     "submission": transaction_supervision.output("submission"),
    #     "decisions": transaction_supervision.output("decisions"),
    # },
    """
    # Dynamic supervision-template builder: reads extracted dates/policies
        # from the upstream submission and produces a supervision_template
        # whose per-slot date / policy dropdowns list the actual extracted values.
        build_template = PythonBlock(
            reference_name="build_supervision_template",
            code=_build_dynamic_template,
            python_version=SAAS_PYTHON_BLOCK_VERSION,
            code_input={
                "submission": manual_transcription.output("submission"),
                "intent_oneof": INTENT_SCHEMA_ONEOF,
                "intent_slots": INTENT_SLOTS,
                # Identify policy / effective-date fields by their layout field
                # *name* (case-insensitive, zero-width-space tolerant). Names are
                # stable across HS environments; UUIDs are not. Add any layout
                # variants your tenant uses here.
                "policy_field_names": POLICY_FIELD_NAMES,
                "date_field_names": DATE_FIELD_NAMES,
                # Base URL of the HS tenant; used by the runtime template to
                # render a copyable link back to the submission detail page.
                "hs_base_url": "${workflow.input.hs_base_url}",
                "transaction_type_oneof": TRANSACTION_TYPE_SCHEMA_ONEOF,
            },
        )
        intent_supervision = ib.IdpCustomSupervisionBlock(
            reference_name="intent_supervision",
            submission=manual_transcription.output("submission"),
            task_purpose="capture_intents",
            supervision_template=build_template.output(),
        )
        complete = ib.SubmissionCompleteBlock(
            reference_name="complete",
            submission=intent_supervision.output("submission"),
        )
      
    """
    
    # Default IDPCoreManifest roles are ['supporting', 'idp_core'] which is
    # exactly what we want for a subflow.
    return Flow(
        uuid=CORE_FLOW_UUID,
        owner_email="flows.sdk@hyperscience.com",
        title="Cancellation Custom Core Flow_V44",
        description=(
            "IDP Core subflow: standard pipeline (classification -> "
            "identification -> transcription) + custom supervision that "
            "captures cancellation transaction type per document." # TODO updated endorsement to cancellation
        ),
        manifest=iv.IDPCoreManifest(flow_identifier=CORE_FLOW_IDENTIFIER),
        blocks=[
            bootstrap,
            machine_classification,
            manual_classification,
            machine_identification,
            manual_identification,
            machine_transcription,
            manual_transcription,
            build_template,
            transaction_supervision,
            merge_outputs,
            complete,
        ],
        input=_sanitize_top_input(iv.get_idp_wf_inputs(iv.get_idp_wf_config())),
    )


# --------------------------------------------------------------------------- #
# Wrapper flow: top-level, delegates to the core subflow
# --------------------------------------------------------------------------- #

def build_wrapper_flow() -> Flow:
    idp_wf_config = iv.get_idp_wf_config()

    # IDPCoreBlock delegates to whichever flow has role 'idp_core' that the
    # user selects in HS Studio. We default the identifier to our core flow
    # so it picks up correctly on import; users can switch via the UI.
    #
    # IDPCoreBlock by default does NOT pass `submission` to the subflow, but
    # the subflow's SubmissionBootstrapBlock reads ${workflow.input.submission}.
    # Without it the subflow fails with "NoneType has no attribute 'get'".
    # Pass it explicitly via additional_inputs.
    idp_core = ib.IDPCoreBlock(
        idp_wf_config=idp_wf_config,
        identifier=CORE_FLOW_IDENTIFIER,
        additional_inputs={
            iv.Inputs.Submission: workflow_input(iv.Inputs.Submission),
        },
    )

    # We need a top-level (roles=['idp']) flow that ALSO declares all the
    # IDP workflow inputs in its manifest (so HS forwards trigger/submission
    # and all settings into the subflow). Neither IDPWrapperManifest (declares
    # only layout_release_uuid) nor IDPCoreManifest (forces supporting/idp_core
    # roles) does both. Workaround: build with IDPCoreManifest (full parameter
    # set) and patch roles + add a 'submission' parameter post-render.
    return Flow(
        uuid=WRAPPER_FLOW_UUID,
        owner_email="flows.sdk@hyperscience.com",
        title="Cancellation Automation Dev Sample - PERF TEST",
        description=(
            "Top-level wrapper for the Cancellation Custom Core Flow. "
            "Delegates document processing + Transaction Type supervision to the "
            "DROPDOWN_TRANSACTION_TYPE_CORE subflow."
        ),
        manifest=iv.IDPCoreManifest(flow_identifier=WRAPPER_FLOW_IDENTIFIER),
        blocks=[idp_core],
        input=_sanitize_top_input(iv.get_idp_wf_inputs(idp_wf_config)),
    )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def _wrapper_triggers():
    """A 'triggers' section is required for top-level (idp) flows so HS knows
    to expose an input connector and populate $trigger / submission. Without
    it, submissions never reach the bootstrap block and downstream tasks
    crash with 'NoneType has no attribute get'.

    Replicates the standard IDP input connector manifest used by stock IDP
    flows so users can upload via the HS UI / API.
    """
    return {
        "title": "Inputs",
        "description": (
            "Ingest submission data from an external source, and trigger "
            "submission processing"
        ),
        "reference_name": "triggers",
        "api_params_manifest": {
            "input": [
                {
                    "name": "restrictions",
                    "type": "TaskRestrictions",
                    "title": "Task Restrictions",
                    "description": (
                        "Supervision tasks for submissions created via this "
                        "input connection will only be accessible to users "
                        "associated with the specified Task Restrictions."
                    ),
                    "value": [],
                    "optional": True,
                },
                {
                    "name": "goal_time_rule",
                    "type": "GoalTimeRule",
                    "title": "Submission Processing Deadline",
                    "description": (
                        "Dynamic processing deadline for submissions coming "
                        "via this connection. This will impact how manual "
                        "tasks get prioritized in the Work Queue."
                    ),
                    "value": None,
                    "optional": True,
                },
                {
                    "name": "layout_uuid",
                    "type": "LayoutUUID",
                    "title": "Layout UUID",
                    "description": (
                        "The UUID of a Semi-Structured layout that's part of "
                        "an active release can be specified. When specified, "
                        "all submitted pages in the request will be matched "
                        "to it and machine page classification will be "
                        "skipped."
                    ),
                    "value": None,
                    "optional": True,
                },
                {
                    "name": "fallback_layout_uuid",
                    "type": "LayoutUUID",
                    "title": "Fallback Layout UUID",
                    "description": (
                        "The UUID of a Semi-Structured layout that's part of "
                        "an active release can be specified. When specified "
                        "only pages that are not matched to a live Structured "
                        "layout in the request will be matched to the "
                        "specified Semi-structured layout."
                    ),
                    "value": None,
                    "optional": True,
                },
                {
                    "name": "source_routing_tag_comma_separated",
                    "type": "string",
                    "title": "Source Tags",
                    "description": (
                        "Comma-separated values. Source tags can be used to "
                        "filter what status change notifications are sent to "
                        "each output connection."
                    ),
                    "value": None,
                    "optional": True,
                },
                {
                    "name": "machine_only",
                    "type": "boolean",
                    "title": "Machine Only",
                    "description": (
                        "Process the submission using an automated flow only."
                    ),
                    "value": False,
                },
                {
                    "name": "single_document_per_page",
                    "type": "boolean",
                    "title": "Single Document Per Page",
                    "description": (
                        "Force creation of separate documents for each "
                        "uploaded page in each file."
                    ),
                    "value": False,
                },
            ],
            "ui": {
                "groups": [
                    {
                        "title": "Submission Processing Settings",
                        "fields": [
                            "restrictions",
                            "goal_time_rule",
                            "layout_uuid",
                            "fallback_layout_uuid",
                            "source_routing_tag_comma_separated",
                            "machine_only",
                            "single_document_per_page",
                        ],
                    }
                ]
            },
        },
        "blocks": [],
    }


def _write(flow: Flow, filename: str, role_override: list | None = None,
           extra_inputs: list | None = None,
           inject_triggers: bool = False) -> Path:
    rendered = flow.render()
    if role_override is not None:
        rendered["manifest"]["roles"] = role_override
    else:
        # Sort default roles for deterministic output across rebuilds.
        rendered["manifest"]["roles"] = sorted(rendered["manifest"].get("roles", []))
    if extra_inputs:
        existing_names = {p.get("name") for p in rendered["manifest"].get("input", [])}
        for p in extra_inputs:
            if p["name"] not in existing_names:
                rendered["manifest"].setdefault("input", []).append(p)
    if inject_triggers and "triggers" not in rendered:
        rendered["triggers"] = _wrapper_triggers()
    out_path = Path(__file__).with_name(filename)
    out_path.write_text(json.dumps(rendered, indent=2), encoding="utf-8")
    return out_path

# def build_core_with_intent_catalog(core: dict) -> dict:
#     """Generate a core object from its structure and the Python intent catalog.

#     Flow structure and unrelated settings are retained from the supplied core
#     export. The intent list is generated from INTENT_LABELS. The input mapping
#     is never mutated.
#     """
#     candidate = copy.deepcopy(core)
#     """
#     if candidate.get("title") != "Endorsement Custom Core Flow_V41":
#         raise ValueError("Input is not the expected Endorsement core flow.")
#     """
   
#     if candidate.get("title") != "Cancellation Custom Core Flow_V44":
#         raise ValueError("Input is not the expected Cancellation core flow.")

#     builders = [
#         block for block in candidate.get("blocks", [])
#         if block.get("reference_name") == "build_supervision_template"
#     ]
#     print("builders : ",builders)
#     if len(builders) != 1:
#         raise ValueError(
#             "Expected exactly one build_supervision_template block."
#         )

#     builder_data = builders[0].get("input", {}).get("data", {})

#     if not isinstance(builder_data, dict) or "transaction_type_oneof" not in builder_data:
#         raise ValueError(
#             "Core supervision builder does not contain transaction_type_oneof."
#         )

#     # existing_options = builder_data["transaction_type_oneof"]
#     # source_options = {
#     #     option["const"]: option for option in INTENT_SCHEMA_ONEOF
#     # }
#     # existing_consts = [option.get("const") for option in existing_options]
#     # if len(existing_consts) != len(set(existing_consts)):
#     #     raise ValueError("Baseline intent catalog contains duplicate const values.")
#     # if set(existing_consts) != set(source_options):
#     #     raise ValueError(
#     #         "Baseline and Python intent catalogs contain different const values; "
#     #         "refusing to add or remove options in a label-only change."
#     #     )
#     # Keep the exported UI order stable while sourcing each display title from
#     # the canonical Python catalog.
#     # builder_data["intent_oneof"] = [
#     #     {**copy.deepcopy(option), "title": source_options[option["const"]]["title"]}
#     #     for option in existing_options
#     # ]

#     return candidate

# def regenerate_core_intents(
#     source_core_path: Path,
# ) -> Path:
#     """Regenerate the selected core artifact's intent options in place.

#     The selected core provides the existing flow structure; Python source
#     provides the generated intent labels and values. The wrapper is untouched.
#     """
#     source_path = source_core_path.resolve()
#     baseline = json.loads(source_path.read_text(encoding="utf-8"))
#     generated = build_core_with_intent_catalog(baseline)
#     source_path.write_text(json.dumps(generated, indent=2), encoding="utf-8")
#     return source_path

def _recompile_python_block_identifiers(flow: dict) -> int:
    """Set pre-3.14 Python blocks to the V44 SaaS Python 3.14 identifier."""
    changed = 0
    unsupported_identifiers = {
        "PYTHON_CODE",
        "PYTHON_3_11_CODE",
        "PYTHON_3_12_CODE",
        "PYTHON_3_13_CODE",
    }

    def visit(blocks):
        nonlocal changed
        if not isinstance(blocks, list):
            return
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if block.get("identifier") in unsupported_identifiers:
                block["identifier"] = SAAS_PYTHON_BLOCK_IDENTIFIER
                print("identifier : ",block["identifier"])
                changed += 1
            visit(block.get("blocks"))
            for branch in block.get("branches", []):
                if isinstance(branch, dict):
                    visit(branch.get("blocks"))

    visit(flow.get("blocks"))
    return changed

def build_core_with_supported_manual_classification(core: dict) -> dict:
    import copy

    upgraded = copy.deepcopy(core)
    nodes = [block for block in upgraded.get("blocks", [])
             if block.get("reference_name") == "manual_classification"]
    if len(nodes) != 1:
        raise ValueError("Expected exactly one manual_classification node.")
    node = nodes[0]
    if node.get("identifier") not in {"MANUAL_CLASSIFICATION_5", "MANUAL_CLASSIFICATION_7"}:
        raise ValueError("Unexpected manual classification block identifier.")
    node["identifier"] = ManualClassificationBlock.IDENTIFIER
    node["input"].setdefault("nlc_metadata", None)
    return upgraded

def build_core_with_supported_supervision(core: dict) -> dict:
    import copy

    upgraded = copy.deepcopy(core)
    replacements = {
        "MANUAL_IDENTIFICATION_5": v44_blocks.ManualIdentificationBlock.IDENTIFIER,
        "MANUAL_TRANSCRIPTION_5": v44_blocks.ManualTranscriptionBlock.IDENTIFIER,
        "IDP_CUSTOM_SUPERVISION_2": v44_blocks.IdpCustomSupervisionBlock.IDENTIFIER,
    }

    def visit(blocks):
        for block in blocks:
            identifier = block.get("identifier")
            if identifier in replacements:
                block["identifier"] = replacements[identifier]
            if block.get("identifier") == v44_blocks.ManualTranscriptionBlock.IDENTIFIER:
                defaults = {
                    "address_parsing_enabled": False,
                    "address_parser_api_provider": "none",
                    "address_parser_api_key": None,
                    "address_parser_api_options": None,
                }
                for key, value in defaults.items():
                    block["input"].setdefault(key, value)
            visit(block.get("blocks", []))
            for branch in block.get("branches", []):
                visit(branch.get("blocks", []))

    visit(upgraded.get("blocks", []))
    return upgraded

def regenerate_supported_manual_classification(core_path: Path, *, supervision: bool = False) -> Path:
    core_path = core_path.resolve()
    core = json.loads(core_path.read_text(encoding="utf-8"))
    upgraded = (build_core_with_supported_supervision(core) if supervision
                else build_core_with_supported_manual_classification(core))
    if upgraded == core:
        return core_path
    backup_dir = Path(__file__).resolve().parent / "archive" / "flow_exports"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with ZipFile(backup_dir / f"manual_classification_backup_{stamp}.zip", "w", ZIP_DEFLATED) as backup:
        backup.write(core_path, core_path.name)
    core_temp = core_path.with_suffix(core_path.suffix + ".tmp")
    try:
        core_temp.write_text(json.dumps(upgraded, indent=2), encoding="utf-8")
        core_temp.replace(core_path)
    finally:
        core_temp.unlink(missing_ok=True)
    return core_path

def migrate_saas_v44_python_runtime(
    core_path: Path,
    wrapper_path: Path,
    backup_dir: Path | None = None,
    additional_paths: list[Path] | None = None,
) -> tuple[Path, Path, int]:
    """Recompile pre-3.14 Python block identifiers in one export set.

    A timestamped rollback ZIP is created before active exports are replaced.
    Other block identifiers and flow structure are left unchanged.
    """
    core_path = core_path.resolve()
    wrapper_path = wrapper_path.resolve()
    if core_path == wrapper_path:
        raise ValueError("Core and wrapper paths must be different files.")

    core = json.loads(core_path.read_text(encoding="utf-8"))
    wrapper = json.loads(wrapper_path.read_text(encoding="utf-8"))
    # if core.get("title") != "Endorsement Custom Core Flow_V41":
    #     raise ValueError("Core source is not Endorsement Custom Core Flow_V41.")
    # if not str(wrapper.get("title", "")).startswith("Endorsement Automation"):
    #         raise ValueError("Wrapper source is not an Endorsement Automation flow.")
    if core.get("title") != "Cancellation Custom Core Flow_V44":
            raise ValueError("Core source is not Cancellation Custom Core Flow_V44.")
    if not str(wrapper.get("title", "")).startswith("Cancellation Automation"):
        raise ValueError("Wrapper source is not an Cancellation Automation flow.")

    flows = {core_path: core, wrapper_path: wrapper}
    for path in additional_paths or []:
        path = path.resolve()
        if path in flows:
            raise ValueError("Additional flow paths must be distinct from core and wrapper paths.")
        flows[path] = json.loads(path.read_text(encoding="utf-8"))

    total = sum(_recompile_python_block_identifiers(flow) for flow in flows.values())
    if total == 0:
        return core_path, wrapper_path, 0

    backup_dir = backup_dir or Path(__file__).resolve().parent / "archive" / "flow_exports"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"saas_v44_python_runtime_backup_{stamp}.zip"
    with ZipFile(backup_path, "w", ZIP_DEFLATED) as backup:
        for path in flows:
            backup.write(path, path.name)

    temp_paths = []
    try:
        for path, flow in flows.items():
            temp_path = path.with_suffix(path.suffix + ".tmp")
            temp_path.write_text(json.dumps(flow, indent=2), encoding="utf-8")
            temp_paths.append((temp_path, path))
        for temp_path, path in temp_paths:
            temp_path.replace(path)
    finally:
        for temp_path, _ in temp_paths:
            temp_path.unlink(missing_ok=True)

    return core_path, wrapper_path, total

def main() -> None:
    if sys.argv[1:]:
        import argparse

        parser = argparse.ArgumentParser(description="Build Hyperscience flows")
        # parser.add_argument("--core-intents-only", action="store_true")
        parser.add_argument("--supported-manual-classification", action="store_true")
        parser.add_argument("--supported-supervision", action="store_true")
        parser.add_argument("--core-source", type=Path, required=True)
        parser.add_argument("--saas-v44-python-runtime", action="store_true")
        parser.add_argument("--wrapper-source", type=Path)
        parser.add_argument("--additional-flow-source", action="append", type=Path, default=[])
        args = parser.parse_args()
        if args.supported_supervision:
            print(f"Updated core: {regenerate_supported_manual_classification(args.core_source, supervision=True)}")
            return
        if args.supported_manual_classification:
            print(f"Updated core: {regenerate_supported_manual_classification(args.core_source)}")
            return
        if args.saas_v44_python_runtime:
            if args.wrapper_source is None:
                parser.error("--wrapper-source is required with --saas-v44-python-runtime")
            core_path, wrapper_path, block_count = migrate_saas_v44_python_runtime(
                args.core_source, args.wrapper_source,
                additional_paths=args.additional_flow_source,
            )
            if block_count:
                print(f"Recompiled {block_count} Python block(s) to {SAAS_PYTHON_BLOCK_IDENTIFIER}.")
                print("A rollback ZIP was saved under archive/flow_exports.")
            else:
                print(f"Core and wrapper already use {SAAS_PYTHON_BLOCK_IDENTIFIER}; no files changed.")
            print(f"Core: {core_path}")
            print(f"Wrapper: {wrapper_path}")
            return
        # if not args.core_intents_only:
        #     parser.error("Use --core-intents-only or --saas-v44-python-runtime with options")
        if args.core_source is None:
            parser.error("--core-source must identify the approved core baseline JSON")
    
        # core_path = regenerate_core_intents(args.core_source)
        # print(f"Regenerated the single selected core flow: {core_path}")
        
        print("The wrapper was not regenerated.")
        return

    core_path = _write(
        build_core_flow(),
        "dropdown_core.json",
        # Strip 'read_only' so HS UI lets us edit settings (e.g. toggle
        # Manual Identification Supervision) on the core flow directly.
        # 'supporting' + 'idp_core' are mandatory for IDPCoreManifest.
        role_override=["supporting", "idp_core"],
        extra_inputs=[
            # Core's bootstrap reads ${workflow.input.submission}, so the
            # subflow manifest must declare it (otherwise HS reports
            # "Input key submission not present in dropdown_transaction_type_core
            # manifest" when the wrapper passes it down).
            {
                "name": "submission",
                "type": "object",
                "title": "Submission",
                "optional": True,
            }
        ],
    )
    # Wrapper: force top-level roles + ensure 'submission' is declared as a
    # manifest input so HS routes the submission object into the subflow.
    wrapper_path = _write(
        build_wrapper_flow(),
        "dropdown_wrapper.json",
        role_override=["idp"],
        extra_inputs=[
            {
                "name": "submission",
                "type": "object",
                "title": "Submission",
                "optional": True,
            }
        ],
        inject_triggers=True,
    )

    print(f"Wrote {core_path.name}    (subflow,   roles=[supporting, idp_core])")
    print(f"Wrote {wrapper_path.name} (top-level, roles=[idp])")
    print()
    print("Import order in HS:")
    print("  1. Import dropdown_core.json")
    print("  2. Import dropdown_wrapper.json")
    print("  3. Open the wrapper -> 'Start Document Processing Subflow' block ->")
    print("     pick 'Drop Down Transaction Type Capture - Core' as IDP Core")
    print("  4. Attach Layout Release on the wrapper, then toggle Live")
    print()
    print("Custom supervision data identifiers (already created in HS Studio):")
    # for k, v in DATA_IDENTIFIERS.items():
    #     print(f"  {k:24s} -> {v}")


if __name__ == "__main__":
    main()
