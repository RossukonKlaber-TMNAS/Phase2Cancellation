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

from enum import IntEnum, unique

MAX_LANGUAGE_GATED_FEATURE_CODE = 1000


@unique
class LicenseGatedFeature(IntEnum):
    #  LANGUAGE FEATURES
    #
    # The first 1001 codes are reserved for languages.
    # 0 means “All Languages” and then each language has a code within the 1-1000 range.
    LANGUAGE_ALL = 0
    # Any new language should be added both here and in Salesforce. These languages are used in the
    # LANGUAGE_CHOICES from the language field of Template model.
    LANGUAGE_EN = 1
    LANGUAGE_FR = 2
    LANGUAGE_DE = 3
    LANGUAGE_ES = 4
    LANGUAGE_NL = 5
    LANGUAGE_IT = 6
    LANGUAGE_AR = 7
    LANGUAGE_PT = 8
    LANGUAGE_CH = 9
    LANGUAGE_JA = 10
    LANGUAGE_KO = 11
    LANGUAGE_KO_EN = 12
    LANGUAGE_PO = 13
    LANGUAGE_ET = 14
    LANGUAGE_CS = 15
    LANGUAGE_SK = 16
    LANGUAGE_LT = 17
    LANGUAGE_LV = 18
    LANGUAGE_TR = 19
    LANGUAGE_RU = 20
    LANGUAGE_KK = 21
    LANGUAGE_HE = 22
    LANGUAGE_BG = 23
    LANGUAGE_TH = 24
    # The maximum language code is 1000 (MAX_LANGUAGE_GATED_FEATURE_CODE = 1000)

    # OTHER FEATURES
    #
    ADVANCED_SLA_MANAGEMENT = 1001
    CUSTOM_SUPERVISION = 1002
    SEMI_STRUCTURED_LAYOUTS = 1003
    CLASSIFICATION_TRAINING_DATA_MANAGEMENT = 1004
    IDENTIFICATION_TRAINING_DATA_MANAGEMENT = 1005
    NAMED_ENTITY_RECOGNITION = 1006
    FIELD_LOCATOR_MODELS = 1007
    TABLE_MODELS_SINGLE = 1008
    TEXT_CLASSIFICATION = 1009
    CUSTOM_ENTITY_RECOGNITION = 1010
    ENTERPRISE_SYSTEM_CONNECTORS = 1011
    CUSTOM_FLOWS = 1012
    FLOW_AUTO_RETRY_POLICIES = 1013
    ON_ERROR_FLOWS = 1014
    CUSTOM_CODE_BLOCKS = 1015
    KNOWLEDGE_STORE = 1016
    CASE_MANAGEMENT = 1017
    TABLE_MODELS_MULTIPLE_NESTED = 1018
    UNSTRUCTURED_LAYOUTS = 1019
    LARGE_LANGUAGE_MODELS = 1020
    DOCUMENT_RENDERER = 1021
