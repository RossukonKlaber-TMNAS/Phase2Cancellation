"""
README

This file contains the LicenseGatedFeature enum which is used to gate features based on the license.
It also contains utility functions to generate conditions that can be used in manifest
overrides to gate features based on licensing packages.

The LicenseGatedFeature enum, and the utility functions are necessary for the proper intended
functioning of the out-of-the-box Hyperscience blocks and flows. For example, some features may be
visible or hidden based on the license, or some fields may be enabled or disabled based on the
license.

IMPORTANT:
This file is not intended for usage by the end-users of the Flows SDK, as it may result in
unintended behaviour of flows when imported in the Hyperscience platform.
"""

from typing import Any, Dict, List

from flows_sdk.flows import Dependency
from flows_sdk.implementations.idp_v41.licensing.gated_features import LicenseGatedFeature


def field_validation_context_not_contains_all_features(
    features: List[LicenseGatedFeature],
) -> Dict[str, Any]:
    """
    Utility that returns a dictionary that can be plugged in a manifest override condition which
    checks whether all the provided features are available in the current validation context.
    """
    return build_license_gating_validation_context(condition=_not_contains_all(features))


def field_validation_context_not_contains_any_features(
    features: List[LicenseGatedFeature],
) -> Dict[str, Any]:
    """
    Utility that returns a dictionary that can be plugged in a manifest override condition which
    checks whether at least one of the provided features is available in the current
    validation context.
    """
    return build_license_gating_validation_context(condition=_not_contains_any(features))


# Utility functions to improve readability and reusability
# when building complex license gating conditions
def build_license_gating_validation_context(condition: dict[str, Any]) -> Dict[str, Any]:
    """
    Builds the final JSON schema structure for the available features with
    the provided conditions.
    """
    return {
        '$hs_validation_context': {
            'properties': {'license': {'properties': {'available_features': condition}}}
        }
    }


def _not_contains_all(features: List[LicenseGatedFeature]) -> Dict[str, Any]:
    return {'not': {'allOf': [{'contains': {'const': f.value}} for f in features]}}


def _not_contains_any(features: List[LicenseGatedFeature]) -> Dict[str, Any]:
    return {'not': {'anyOf': [{'contains': {'const': f.value}} for f in features]}}


def _feature_gating_hide_id_target_accuracies_schema(
    entry_hiding_condition: dict[str, Any],
) -> Dict[str, Any]:
    return {
        'properties': build_license_gating_validation_context(
            condition={
                'anyOf': [
                    _not_contains_all([LicenseGatedFeature.SEMI_STRUCTURED_LAYOUTS]),
                    entry_hiding_condition,
                ],
            }
        )
    }


class FeatureGatingCommonDependencies:

    _field_id_licenses = [
        LicenseGatedFeature.FIELD_LOCATOR_MODELS,
    ]
    _table_id_licenses = [
        LicenseGatedFeature.TABLE_MODELS_SINGLE,
        LicenseGatedFeature.TABLE_MODELS_MULTIPLE_NESTED,
    ]

    _field_id_license_condition = _not_contains_all(_field_id_licenses)
    _table_id_license_condition = _not_contains_any(_table_id_licenses)

    SemiStructured = [
        Dependency(
            condition={
                'properties': {
                    **field_validation_context_not_contains_all_features(
                        [LicenseGatedFeature.SEMI_STRUCTURED_LAYOUTS]
                    )
                }
            },
            override={'ui': {'hide_and_retain': True}},
        )
    ]
    FieldId = [
        Dependency(
            condition=_feature_gating_hide_id_target_accuracies_schema(
                entry_hiding_condition=_field_id_license_condition
            ),
            override={'ui': {'hide_and_retain': True}},
        )
    ]
    TableId = [
        Dependency(
            condition=_feature_gating_hide_id_target_accuracies_schema(
                entry_hiding_condition=_table_id_license_condition
            ),
            override={'ui': {'hide_and_retain': True}},
        )
    ]
    IdentificationTargetAccuraciesEnabled = [
        Dependency(
            condition=_feature_gating_hide_id_target_accuracies_schema(
                entry_hiding_condition={
                    'allOf': [
                        _field_id_license_condition,
                        _table_id_license_condition,
                    ]
                }
            ),
            override={'ui': {'hide_and_retain': True}},
        )
    ]
    NER = [
        Dependency(
            condition={
                'properties': {
                    **field_validation_context_not_contains_all_features(
                        [LicenseGatedFeature.NAMED_ENTITY_RECOGNITION]
                    )
                }
            },
            override={'computed_value': False},
        )
    ]
    CED = [
        Dependency(
            condition={
                'properties': {
                    **field_validation_context_not_contains_all_features(
                        [LicenseGatedFeature.CUSTOM_ENTITY_RECOGNITION]
                    )
                }
            },
            override={'computed_value': False},
        )
    ]
    CED_HIDDEN = [
        Dependency(
            condition={
                'properties': {
                    **field_validation_context_not_contains_all_features(
                        [
                            LicenseGatedFeature.CUSTOM_ENTITY_RECOGNITION,
                        ]
                    )
                }
            },
            override={'ui': {'hide_and_retain': True}},
        )
    ]
    DocumentRendererEnabled = Dependency(
        condition={
            'properties': {
                **field_validation_context_not_contains_all_features(
                    [LicenseGatedFeature.DOCUMENT_RENDERER]
                )
            }
        },
        override={
            'value': False,
            'ui': {
                'hide_and_retain': True,
                'warning': 'Document rendering feature is not available in your current license.',
            },
        },
    )
