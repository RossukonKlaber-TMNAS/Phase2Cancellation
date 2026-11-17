from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from flows_sdk.blocks import IOBlock
from flows_sdk.flows import Dependency, InputDefinition, Manifest, Parameter, Triggers
from flows_sdk.utils import system_setting

# This module contains all default values needed by an IDP flow

LAYOUT_RELEASE_KEY = 'layout_release_uuid'
S3_SECRET_KEY = 's3_downloader'
OCS_SECRET_KEY = 'ocs_downloader'
IDP_SUBMISSION_NOTIFY_NAME = 'IDP_SUBMISSION_NOTIFY_V32'
IDP_OUTPUT_ROLE = 'idp_output'
CONSECUTIVE_PAGE_BEHAVIOR_GROUP_PAGES = 'group_pages'
CONSECUTIVE_PAGE_BEHAVIOR_SPLIT_PAGES = 'split_pages'
CONSECUTIVE_PAGE_BEHAVIOR_MANUAL = 'manual'
CONSECUTIVE_PAGE_BEHAVIOR_GROUP_FILE = 'group_file'
EXACT_PERCENT_SCHEMA = {'type': 'number', 'multipleOf': 0.001, 'minimum': 0, 'maximum': 1}


class Inputs:
    WorkflowUuid = 'workflow_uuid'
    WorkflowName = 'workflow_name'
    WorkflowVersion = 'workflow_version'

    Trigger = '$trigger'


class Settings:
    LayoutReleaseUuid = 'layout_release_uuid'
    ImageCorrection = 'image_correction'

    # Classification Settings
    StructuredLayoutMatchThreshold = 'structured_layout_match_threshold'
    SemiStructuredClassification = 'semi_structured_classification'
    SemiDocGroupingLogic = 'semi_doc_grouping_logic'
    SemiTargetAccuracy = 'semi_target_accuracy'
    SemiQaSampleRate = 'semi_qa_sample_rate'
    ManualNlcEnabled = 'manual_nlc_enabled'

    # Identification Settings
    FieldIdTargetAccuracy = 'field_id_target_accuracy'
    TableIdTargetAccuracy = 'table_id_target_accuracy'
    # This enables both field and table identification
    ManualFieldIdEnabled = 'manual_field_id_enabled'
    FieldIdQaEnabled = 'field_id_qa_enabled'
    FieldIdQaSampleRate = 'field_id_qa_sample_rate'
    TableIdQaEnabled = 'table_id_qa_enabled'
    TableIdQaSampleRate = 'table_id_qa_sample_rate'

    # Transcription Settings
    TranscriptionAutomationTraining = 'transcription_automation_training'
    TranscriptionTrainingLegibilityPeriod = 'transcription_training_legibility_period'
    TranscriptionModel = 'transcription_model'
    ImprovedTranscriptionThresholdAccuracy = 'improved_transcription_threshold_accuracy'
    FinetuningOnlyTrainedLayouts = 'finetuning_only_trained_layouts'
    ManualTranscriptionEnabled = 'manual_transcription_enabled'
    SemiTranscriptionConfBoost = 'semi_transcription_conf_boost'

    StructuredTextMinTrainingRecords = 'structured_text_min_training_records'
    StructuredTextMaxTrainingRecords = 'structured_text_max_training_records'
    StructuredTextTargetAccuracy = 'structured_text_target_accuracy'
    StructuredTextAutomation = 'structured_text_automation'
    StructuredTextThreshold = 'structured_text_threshold'
    StructuredTextMinLegThreshold = 'structured_min_leg_threshold'

    SemiStructuredTextMinTrainingRecords = 'semi_structured_text_min_training_records'
    SemiStructuredTextMaxTrainingRecords = 'semi_structured_text_max_training_records'
    SemiStructuredTextTargetAccuracy = 'semi_structured_text_target_accuracy'
    SemiStructuredTextAutomation = 'semi_structured_text_automation'
    SemiStructuredTextThreshold = 'semi_structured_text_threshold'
    SemiStructuredTextMinLegThreshold = 'semi_structured_min_leg_threshold'

    StructuredCheckboxMinTrainingRecords = 'structured_checkbox_min_training_records'
    StructuredCheckboxMaxTrainingRecords = 'structured_checkbox_max_training_records'
    StructuredCheckboxTargetAccuracy = 'structured_checkbox_target_accuracy'
    StructuredCheckboxAutomation = 'structured_checkbox_automation'
    StructuredCheckboxThreshold = 'structured_checkbox_threshold'
    StructuredCheckboxMinLegThreshold = 'checkbox_min_leg_threshold'

    StructuredSignatureMinTrainingRecords = 'structured_signature_min_training_records'
    StructuredSignatureMaxTrainingRecords = 'structured_signature_max_training_records'
    StructuredSignatureTargetAccuracy = 'structured_signature_target_accuracy'
    StructuredSignatureAutomation = 'structured_signature_automation'
    StructuredSignatureThreshold = 'structured_signature_threshold'
    StructuredSignatureMinLegThreshold = 'signature_min_leg_threshold'

    SemiStructuredCheckboxMinTrainingRecords = 'semi_structured_checkbox_min_training_records'
    SemiStructuredCheckboxMaxTrainingRecords = 'semi_structured_checkbox_max_training_records'
    SemiStructuredCheckboxTargetAccuracy = 'semi_structured_checkbox_target_accuracy'
    SemiStructuredCheckboxAutomation = 'semi_structured_checkbox_automation'
    SemiStructuredCheckboxThreshold = 'semi_structured_checkbox_threshold'
    SemiStructuredCheckboxMinLegThreshold = 'semi_structured_checkbox_min_leg_threshold'

    TranscriptionQaEnabled = 'qa'
    TranscriptionQaSampleRate = 'qa_sample_rate'

    TableCellTranscriptionQaEnabled = 'table_cell_transcription_qa_enabled'
    TableCellTranscriptionQaSampleRate = 'table_cell_transcription_qa_sample_rate'


@dataclass
class QaConfigData:
    transcription_qa_sampling_ratio: float
    field_id_qa_sampling_ratio: float
    transcription_qa_enabled: bool
    field_id_qa_enabled: bool
    nlc_qa_sampling_ratio: float
    table_id_qa_enabled: bool = True
    table_id_qa_sampling_ratio: float = 0.05
    table_cell_transcription_qa_enabled: bool = True
    table_cell_transcription_qa_sample_rate: float = 0.05


@dataclass
class MachineClassificationConfig:
    nlc_enabled: bool
    nlc_target_accuracy: float
    vpc_registration_threshold: float


@dataclass
class SupervisionConfig:
    task_restrictions: List[str]


@dataclass
class ManualTranscriptionConfig(SupervisionConfig):
    supervision_transcription_masking: bool
    table_output_manual_review: bool


@dataclass
class ManualIdentificationConfig(SupervisionConfig):
    pass


@dataclass
class FlexibleExtractionConfig(SupervisionConfig):
    supervision_transcription_masking: bool


@dataclass
class TranscriptionConfig:
    min_samples: int
    max_samples: int
    target_accuracy: float
    confidence_threshold: float
    acceptable_confidence: float


@dataclass
class HttpHeaderAuthorizationParams:
    authorization_header: str


@dataclass
class OAuth2AuthorizationParams:
    auth_url: str
    client_id: str
    client_secret: str
    audience: str


@dataclass
class IdpWorkflowConfig:
    """
    Convenience dataclass outlining all flow-level config values for IDP.
    """

    # Workflow level configs
    rotation_correction_enabled: bool
    document_grouping_logic: str
    qa_config: QaConfigData
    manual_document_organization_enabled: bool

    # Transcription settings
    transcription_automation_training: bool
    transcription_training_legibility_period: int
    transcription_model: str
    manual_transcription_enabled: bool
    finetuning_only_trained_layouts: bool
    flex_confidence_boosting_enabled: bool
    improved_transcription_threshold_accuracy: bool
    structured_text: TranscriptionConfig
    semi_structured_text: TranscriptionConfig
    structured_checkbox: TranscriptionConfig
    structured_signature: TranscriptionConfig
    semi_structured_checkbox: TranscriptionConfig

    # Identification settings
    field_id_target_accuracy: float
    table_id_target_accuracy: float

    manual_field_id_enabled: bool

    machine_classification_config: MachineClassificationConfig
    manual_transcription_config: ManualTranscriptionConfig
    manual_identification_config: ManualIdentificationConfig
    flexible_extraction_config: FlexibleExtractionConfig


def get_idp_wf_inputs(idp_wf_config: IdpWorkflowConfig) -> Dict[str, Any]:
    """
    A helper function that maps the values provided by an ``IdpWorkflowConfig`` to their
    corresponding IDP keys.

    :param idp_wf_config: with static values to be filled.

    :return: a dictionary with filled static values, compatible with IDP flows.

    Example usage with default values::

        flow = Flow(
            input=get_idp_wf_inputs(get_idp_wf_config()),
            ...
        )


    Example usage::

        Example usage when instantiating an IDP flow with custom parameters::

        flow = Flow(
            input=get_idp_wf_inputs({an instance of IdpWorkflowConfig}),
            ...
        )


    """
    return {
        Settings.LayoutReleaseUuid: system_setting(LAYOUT_RELEASE_KEY),
        Settings.StructuredLayoutMatchThreshold: (
            idp_wf_config.machine_classification_config.vpc_registration_threshold
        ),
        Settings.SemiStructuredClassification: (
            idp_wf_config.machine_classification_config.nlc_enabled
        ),
        Settings.SemiTargetAccuracy: (
            idp_wf_config.machine_classification_config.nlc_target_accuracy
        ),
        Settings.ManualNlcEnabled: idp_wf_config.manual_document_organization_enabled,
        Settings.SemiDocGroupingLogic: idp_wf_config.document_grouping_logic,
        Settings.SemiQaSampleRate: idp_wf_config.qa_config.nlc_qa_sampling_ratio,
        Settings.FieldIdTargetAccuracy: idp_wf_config.field_id_target_accuracy,
        Settings.TableIdTargetAccuracy: idp_wf_config.table_id_target_accuracy,
        Settings.ManualFieldIdEnabled: idp_wf_config.manual_field_id_enabled,
        Settings.FieldIdQaEnabled: idp_wf_config.qa_config.field_id_qa_enabled,
        Settings.FieldIdQaSampleRate: idp_wf_config.qa_config.field_id_qa_sampling_ratio,
        # @since v31.0 therefore no backing django model for this value
        Settings.TableIdQaEnabled: True,
        # @since v31.0 therefore no backing django model for this value
        Settings.TableIdQaSampleRate: 0.05,
        Settings.TranscriptionAutomationTraining: idp_wf_config.transcription_automation_training,
        Settings.TranscriptionTrainingLegibilityPeriod: (
            idp_wf_config.transcription_training_legibility_period
        ),
        Settings.TranscriptionModel: idp_wf_config.transcription_model,
        Settings.ImprovedTranscriptionThresholdAccuracy: (
            idp_wf_config.improved_transcription_threshold_accuracy
        ),
        Settings.StructuredTextMinTrainingRecords: idp_wf_config.structured_text.min_samples,
        Settings.StructuredTextMaxTrainingRecords: idp_wf_config.structured_text.max_samples,
        Settings.StructuredTextTargetAccuracy: idp_wf_config.structured_text.target_accuracy,
        Settings.StructuredTextThreshold: idp_wf_config.structured_text.confidence_threshold,
        Settings.StructuredTextMinLegThreshold: idp_wf_config.structured_text.acceptable_confidence,
        Settings.SemiStructuredTextMinTrainingRecords: (
            idp_wf_config.semi_structured_text.min_samples
        ),
        Settings.SemiStructuredTextMaxTrainingRecords: (
            idp_wf_config.semi_structured_text.max_samples
        ),
        Settings.SemiStructuredTextTargetAccuracy: (
            idp_wf_config.semi_structured_text.target_accuracy
        ),
        Settings.SemiStructuredTextThreshold: (
            idp_wf_config.semi_structured_text.confidence_threshold
        ),
        Settings.SemiStructuredTextMinLegThreshold: (
            idp_wf_config.semi_structured_text.acceptable_confidence
        ),
        Settings.StructuredCheckboxMinTrainingRecords: (
            idp_wf_config.structured_checkbox.min_samples
        ),
        Settings.StructuredCheckboxMaxTrainingRecords: (
            idp_wf_config.structured_checkbox.max_samples
        ),
        Settings.StructuredCheckboxTargetAccuracy: (
            idp_wf_config.structured_checkbox.target_accuracy
        ),
        Settings.StructuredCheckboxThreshold: (
            idp_wf_config.structured_checkbox.confidence_threshold
        ),
        Settings.StructuredCheckboxMinLegThreshold: (
            idp_wf_config.structured_checkbox.acceptable_confidence
        ),
        Settings.StructuredSignatureMinTrainingRecords: (
            idp_wf_config.structured_signature.min_samples
        ),
        Settings.StructuredSignatureMaxTrainingRecords: (
            idp_wf_config.structured_signature.max_samples
        ),
        Settings.StructuredSignatureTargetAccuracy: (
            idp_wf_config.structured_signature.target_accuracy
        ),
        Settings.StructuredSignatureThreshold: (
            idp_wf_config.structured_signature.confidence_threshold
        ),
        Settings.StructuredSignatureMinLegThreshold: (
            idp_wf_config.structured_signature.acceptable_confidence
        ),
        Settings.SemiStructuredCheckboxMinTrainingRecords: (
            idp_wf_config.semi_structured_checkbox.min_samples
        ),
        Settings.SemiStructuredCheckboxMaxTrainingRecords: (
            idp_wf_config.semi_structured_checkbox.max_samples
        ),
        Settings.SemiStructuredCheckboxTargetAccuracy: (
            idp_wf_config.semi_structured_checkbox.target_accuracy
        ),
        Settings.SemiStructuredCheckboxThreshold: (
            idp_wf_config.semi_structured_checkbox.confidence_threshold
        ),
        Settings.SemiStructuredCheckboxMinLegThreshold: (
            idp_wf_config.semi_structured_checkbox.acceptable_confidence
        ),
        Settings.ManualTranscriptionEnabled: idp_wf_config.manual_transcription_enabled,
        Settings.SemiTranscriptionConfBoost: idp_wf_config.flex_confidence_boosting_enabled,
        Settings.TranscriptionQaEnabled: idp_wf_config.qa_config.transcription_qa_enabled,
        Settings.TranscriptionQaSampleRate: idp_wf_config.qa_config.transcription_qa_sampling_ratio,
        # @since v32.0 therefore no backing django model for this value
        Settings.TableCellTranscriptionQaEnabled: True,
        # @since v32.0 therefore no backing django model for this value
        Settings.TableCellTranscriptionQaSampleRate: 0.05,
        Settings.FinetuningOnlyTrainedLayouts: idp_wf_config.finetuning_only_trained_layouts,
    }


def get_idp_wf_config() -> IdpWorkflowConfig:
    """
    A helper function that instantiates an ``IdpWorkflowConfig`` pre-filled with default values.
    ``IdpWorkflowConfig`` is the container class for defining flow-level settings.

    :return: a valid, fully constructed IdpWorkflowConfig instance

    Example usage when instantiating an IDP flow::

        flow = Flow(
            input=get_idp_wf_inputs(get_idp_wf_config()),
            ...
        )

    """
    return IdpWorkflowConfig(
        manual_document_organization_enabled=False,
        rotation_correction_enabled=True,
        field_id_target_accuracy=0.95,
        table_id_target_accuracy=0.96,
        transcription_automation_training=False,
        transcription_training_legibility_period=30,
        flex_confidence_boosting_enabled=False,
        improved_transcription_threshold_accuracy=True,
        structured_text=TranscriptionConfig(
            min_samples=5000,
            max_samples=50000,
            target_accuracy=0.95,
            confidence_threshold=0.52,
            acceptable_confidence=0.1,
        ),
        semi_structured_text=TranscriptionConfig(
            min_samples=2000,
            max_samples=50000,
            target_accuracy=0.95,
            confidence_threshold=0.52,
            acceptable_confidence=0.1,
        ),
        structured_checkbox=TranscriptionConfig(
            min_samples=2000,
            max_samples=50000,
            target_accuracy=0.95,
            confidence_threshold=0.56,
            acceptable_confidence=0.5,
        ),
        structured_signature=TranscriptionConfig(
            min_samples=2000,
            max_samples=50000,
            target_accuracy=0.95,
            confidence_threshold=0.99,
            acceptable_confidence=0.5,
        ),
        semi_structured_checkbox=TranscriptionConfig(
            min_samples=2000,
            max_samples=50000,
            target_accuracy=0.95,
            confidence_threshold=0.56,
            acceptable_confidence=0.5,
        ),
        manual_field_id_enabled=True,
        manual_transcription_enabled=True,
        machine_classification_config=MachineClassificationConfig(
            nlc_enabled=True, nlc_target_accuracy=0.99, vpc_registration_threshold=0.6
        ),
        document_grouping_logic='group_pages',
        flexible_extraction_config=FlexibleExtractionConfig(
            task_restrictions=[], supervision_transcription_masking=True
        ),
        manual_transcription_config=ManualTranscriptionConfig(
            task_restrictions=[],
            supervision_transcription_masking=True,
            table_output_manual_review=False,
        ),
        manual_identification_config=ManualIdentificationConfig(task_restrictions=[]),
        qa_config=QaConfigData(
            transcription_qa_sampling_ratio=0.05,
            field_id_qa_sampling_ratio=0.05,
            transcription_qa_enabled=True,
            field_id_qa_enabled=True,
            nlc_qa_sampling_ratio=0.05,
            table_id_qa_enabled=True,
            table_id_qa_sampling_ratio=0.05,
            table_cell_transcription_qa_enabled=True,
            table_cell_transcription_qa_sample_rate=0.05,
        ),
        transcription_model='IDP',
        finetuning_only_trained_layouts=True,
    )


class ApiParams:
    Restrictions = 'restrictions'
    GoalTimeRule = 'goal_time_rule'
    LayoutUuid = 'layout_uuid'
    FallbackLayoutUuid = 'fallback_layout_uuid'
    SourceRoutingTagCommaSeparated = 'source_routing_tag_comma_separated'
    MachineOnly = 'machine_only'
    SingleDocumentPerPage = 'single_document_per_page'
    Cases = 'cases'


class IDPTriggers(Triggers):
    """
    An adapter class making it easier to instantiate :py:class:`flows_sdk.flows.Triggers` for
    IDP flows.
    In particular, provides defaults for some fields (e.g. title, description, reference_name)
    and defines `api_params_manifest` with IDP specific parameters.

    :param blocks: :py:class:`flows_sdk.blocks.IOBlock` s to be included as triggers for
        an IDP Flow.
        Optional, defaults to an empty list.

    Example usage when instantiating an IDP flow::

        folder_listener = IOBlock(...)
        flow = Flow(
            triggers=IDPTriggers([folder_listener]),
            ...
        )

    """

    def __init__(self, blocks: Optional[Sequence[IOBlock]] = None) -> None:
        if not blocks:
            blocks = []

        super().__init__(
            title='Inputs',
            description='Ingest submission data from an external source, '
            'and trigger submission processing',
            reference_name='triggers',
            blocks=blocks,
            api_params_manifest=InputDefinition(
                input=[
                    Parameter(
                        name=ApiParams.Restrictions,
                        type='TaskRestrictions',
                        title='Task Restrictions',
                        description=(
                            'Supervision tasks for submissions created via this input '
                            'connection will only be accessible to users associated with '
                            'the specified Task Restrictions.'
                        ),
                        optional=True,
                        value=[],
                    ),
                    Parameter(
                        name=ApiParams.GoalTimeRule,
                        type='GoalTimeRule',
                        title='Submission Processing Deadline',
                        description=(
                            'Dynamic processing deadline for submissions '
                            'coming via this connection.'
                            'This will impact how manual tasks get prioritized in the Work Queue.'
                        ),
                        optional=True,
                        value=None,
                    ),
                    Parameter(
                        name=ApiParams.LayoutUuid,
                        type='LayoutUUID',
                        title='Layout UUID',
                        description=(
                            "The UUID of a Semi-Structured layout that\'s part of an "
                            'active release can be specified. When specified, all '
                            'submitted pages in the request will be matched to it and '
                            'machine page classification will be skipped.'
                        ),
                        optional=True,
                        value=None,
                    ),
                    Parameter(
                        name=ApiParams.FallbackLayoutUuid,
                        type='LayoutUUID',
                        title='Fallback Layout UUID',
                        description=(
                            "The UUID of a Semi-Structured layout that\'s part of an "
                            'active release can be specified. When specified only pages '
                            'that are not matched to a live Structured layout in the '
                            'request will be matched to the specified Semi-structured '
                            'layout.'
                        ),
                        optional=True,
                        value=None,
                    ),
                    Parameter(
                        name=ApiParams.SourceRoutingTagCommaSeparated,
                        type='string',
                        title='Source Tags',
                        description=(
                            'Comma-separated values. Source tags can be used to filter what '
                            'status change notifications are sent to each output connection.'
                        ),
                        optional=True,
                        value=None,
                    ),
                    Parameter(
                        name=ApiParams.MachineOnly,
                        type='boolean',
                        title='Machine Only',
                        description='Process the submission using an automated flow only.',
                        value=False,
                    ),
                    Parameter(
                        name=ApiParams.SingleDocumentPerPage,
                        type='boolean',
                        title='Single Document Per Page',
                        description=(
                            'This parameter only applies to semi-structured documents. '
                            'Force the creation of separate documents for each uploaded '
                            'page in each file. For example, a single PNG image will '
                            'produce a single document while a 3-page PDF file will '
                            'always produce 3 separate documents under this scheme. '
                            "It takes precedence over the flow's settings. "
                            'By default, PNG and JPG files that match the same layout '
                            'are combined into one document while only consecutive pages '
                            'in a single PDF, TFF, or XPS matching the same layout will '
                            'be grouped into the same document.'
                        ),
                        value=False,
                    ),
                ],
                ui={
                    'groups': [
                        {
                            'title': 'Submission Processing Settings',
                            'fields': [
                                ApiParams.Restrictions,
                                ApiParams.GoalTimeRule,
                                ApiParams.LayoutUuid,
                                ApiParams.FallbackLayoutUuid,
                                ApiParams.SourceRoutingTagCommaSeparated,
                                ApiParams.MachineOnly,
                                ApiParams.SingleDocumentPerPage,
                            ],
                        }
                    ]
                },
            ),
        )


class IDPManifest(Manifest):
    """
    An adapter class making it easier to instantiate :py:class:`flows_sdk.flows.Manifest` for
    IDP flows.
    In particular, provides defaults for some fields (e.g. roles, identifier)
    but more importantly, defines all py:class:`flows_sdk.flows.Parameter` that construct the
    Flow inputs and their UI representation (left-hand side menu in Flow studio).

    :param flow_identifier: A system-wide unique identifier for :py:class:`flows_sdk.flows.Flow`

    Example usage when instantiating an IDP flow::

        flow = Flow(
            manifest=IDPManifest(flow_identifier='FLOW_IDENTIFIER'),
            ...
        )

    """

    def __init__(self, flow_identifier: str) -> None:
        transcription_automation_training_dependency = Dependency(
            condition={'properties': {Settings.TranscriptionAutomationTraining: {'const': False}}},
            override={
                'ui': {
                    'na_reason': 'Not applied when Transcription Automation Training is disabled.'
                }
            },
        )

        super().__init__(
            identifier=flow_identifier,
            roles=['idp'],
            enable_overrides=True,
            input=[
                Parameter(
                    name=Settings.LayoutReleaseUuid,
                    type='ReleaseUUID',
                    title='Layout Release',
                    ui={'hidden': True},
                ),
                Parameter(
                    name=Settings.StructuredLayoutMatchThreshold,
                    type='number',
                    schema={'type': 'number', 'minimum': 0, 'maximum': 1},
                    title='Structured Layout Match Threshold',
                    description=(
                        'Matches structured layouts above this threshold to a layout variation '
                        'automatically. Pages below this threshold will be sent to Document '
                        'Classification, if enabled. If disabled, such pages will be marked as '
                        '"No Layout Variation Found."'
                    ),
                ),
                Parameter(
                    name=Settings.SemiStructuredClassification,
                    type='boolean',
                    title='Semi-Structured Classification',
                    description=(
                        'Enables workflow to manage a model for automated classification of '
                        'semi-structured and additional layout variations.'
                    ),
                ),
                Parameter(
                    name=Settings.ManualNlcEnabled,
                    type='boolean',
                    title='Manual Classification Supervision',
                    description='Enables manual classification when applicable',
                ),
                Parameter(
                    name=Settings.SemiTargetAccuracy,
                    schema=EXACT_PERCENT_SCHEMA,
                    type='Percentage',
                    title='Semi-Structured Target Accuracy',
                ),
                Parameter(
                    name=Settings.SemiDocGroupingLogic,
                    type='string',
                    schema={
                        'type': 'string',
                        'oneOf': [
                            {
                                'title': 'Consecutive pages as a document',
                                'const': CONSECUTIVE_PAGE_BEHAVIOR_GROUP_PAGES,
                            },
                            {
                                'title': 'Consecutive pages as separate documents',
                                'const': CONSECUTIVE_PAGE_BEHAVIOR_SPLIT_PAGES,
                            },
                            {
                                'title': 'Manual review of consecutive pages',
                                'const': CONSECUTIVE_PAGE_BEHAVIOR_MANUAL,
                            },
                        ],
                    },
                    title='Semi-Structured Grouping Logic',
                    description=(
                        'Determines how multiple pages matched to the same layout variation in a '
                        'given submission will be handled.'
                    ),
                ),
                Parameter(
                    name=Settings.SemiQaSampleRate,
                    type='Percentage',
                    title='Semi-Structured QA Sample Rate',
                    description='Defines the percentage of documents sampled for QA.',
                ),
                Parameter(
                    name=Settings.FieldIdTargetAccuracy,
                    type='Percentage',
                    schema=EXACT_PERCENT_SCHEMA,
                    title='Field Identification Target Accuracy',
                ),
                Parameter(
                    name=Settings.TableIdTargetAccuracy,
                    type='Percentage',
                    schema=EXACT_PERCENT_SCHEMA,
                    title='Table Identification Target Accuracy',
                    value=0.96,
                ),
                Parameter(
                    name=Settings.ManualFieldIdEnabled,
                    type='boolean',
                    title='Manual Identification Supervision',
                    description='Enables manual identification when applicable',
                ),
                Parameter(
                    name=Settings.FieldIdQaEnabled,
                    type='boolean',
                    title='Field Identification Quality Assurance',
                    description=(
                        'Allows users to verify the location or presence of fields on '
                        'semi-structured documents.'
                    ),
                ),
                Parameter(
                    name=Settings.FieldIdQaSampleRate,
                    type='Percentage',
                    title='Field Identification QA Sample Rate',
                    description='Defines the percentage of documents the system samples for QA.',
                    dependencies=[
                        Dependency(
                            condition={'properties': {Settings.FieldIdQaEnabled: {'const': False}}},
                            override={
                                'ui': {
                                    'na_reason': (
                                        'Not applied when Field Identification Quality Assurance'
                                        ' is disabled.'
                                    )
                                }
                            },
                        )
                    ],
                ),
                Parameter(
                    name=Settings.TableIdQaEnabled,
                    type='boolean',
                    value=True,
                    title='TABLE IDENTIFICATION QUALITY ASSURANCE',
                    description='Allows users to verify the location of table cells.',
                ),
                Parameter(
                    name=Settings.TableIdQaSampleRate,
                    type='Percentage',
                    value=0.05,
                    title='TABLE IDENTIFICATION QA SAMPLE RATE',
                    description='Defines the percentage of tables the system samples for QA.',
                    dependencies=[
                        Dependency(
                            condition={'properties': {Settings.TableIdQaEnabled: {'const': False}}},
                            override={
                                'ui': {
                                    'na_reason': (
                                        'Not applied when Table Identification Quality Assurance'
                                        ' is disabled.'
                                    )
                                }
                            },
                        )
                    ],
                ),
                Parameter(
                    name=Settings.TranscriptionAutomationTraining,
                    type='TranscriptionAutomationTraining',
                    schema={'type': 'boolean'},
                    value=True,
                    title='Transcription Automation Training',
                    description=(
                        'Uses QA data for on-premise machine learning'
                        ' to improve transcription automation.'
                    ),
                ),
                Parameter(
                    name=Settings.TranscriptionTrainingLegibilityPeriod,
                    type='integer',
                    schema={'type': 'integer', 'minimum': 0},
                    value=30,
                    title='Periods of records to use',
                    ui={'prefix': 'Past', 'suffix': 'days'},
                    dependencies=[transcription_automation_training_dependency],
                ),
                Parameter(
                    name=Settings.ImprovedTranscriptionThresholdAccuracy,
                    type='boolean',
                    value=True,
                    title='Improved threshold accuracy',
                    dependencies=[transcription_automation_training_dependency],
                ),
                Parameter(
                    name=Settings.StructuredTextMinTrainingRecords,
                    type='integer',
                    schema={'type': 'integer', 'minimum': 0},
                    title='Structured Text Min Training Records',
                    value=2000,
                    ui={'hidden': True},
                ),
                Parameter(
                    name=Settings.StructuredTextMaxTrainingRecords,
                    type='integer',
                    schema={'type': 'integer', 'minimum': 0},
                    title='Structured Text Max Training Records',
                    value=50000,
                    ui={'hidden': True},
                ),
                Parameter(
                    name=Settings.StructuredTextTargetAccuracy,
                    type='Percentage',
                    schema=EXACT_PERCENT_SCHEMA,
                    title='Structured Text Target Accuracy',
                    value=0.95,
                    dependencies=[transcription_automation_training_dependency],
                ),
                Parameter(
                    name=Settings.StructuredTextAutomation,
                    type='Percentage',
                    schema=EXACT_PERCENT_SCHEMA,
                    title='Structured Text Automation',
                    description=(
                        'This number shows the amount of automation you will get based on the '
                        'target accuracy.'
                    ),
                    value=0,
                    ui={'disabled': True},
                    dependencies=[transcription_automation_training_dependency],
                ),
                Parameter(
                    name=Settings.StructuredTextThreshold,
                    type='number',
                    schema={'type': 'number', 'minimum': 0, 'maximum': 1},
                    title='Structured Text Threshold',
                    value=0.52,
                ),
                Parameter(
                    name=Settings.StructuredTextMinLegThreshold,
                    type='number',
                    schema={'type': 'number', 'minimum': 0, 'maximum': 1},
                    title='Structured Text Minimum Legibility Threshold',
                ),
                Parameter(
                    name=Settings.SemiStructuredTextMinTrainingRecords,
                    type='integer',
                    schema={'type': 'integer', 'minimum': 0},
                    title='Semi-Structured Text Min Training Records',
                    value=2000,
                    ui={'hidden': True},
                ),
                Parameter(
                    name=Settings.SemiStructuredTextMaxTrainingRecords,
                    type='integer',
                    schema={'type': 'integer', 'minimum': 0},
                    title='Semi-Structured Text Max Training Records',
                    value=50000,
                    ui={'hidden': True},
                ),
                Parameter(
                    name=Settings.SemiStructuredTextTargetAccuracy,
                    type='Percentage',
                    schema=EXACT_PERCENT_SCHEMA,
                    title='Semi-Structured Text Target Accuracy',
                    value=0.95,
                    dependencies=[transcription_automation_training_dependency],
                ),
                Parameter(
                    name=Settings.SemiStructuredTextAutomation,
                    type='Percentage',
                    schema=EXACT_PERCENT_SCHEMA,
                    title='Semi-Structured Text Automation',
                    description=(
                        'This number shows the amount of automation you will get based on the '
                        'target accuracy.'
                    ),
                    value=0,
                    ui={'disabled': True},
                    dependencies=[transcription_automation_training_dependency],
                ),
                Parameter(
                    name=Settings.SemiStructuredTextThreshold,
                    type='number',
                    schema={'type': 'number', 'minimum': 0, 'maximum': 1},
                    title='Semi-Structured Text Threshold',
                    value=0.52,
                ),
                Parameter(
                    name=Settings.SemiStructuredTextMinLegThreshold,
                    type='number',
                    schema={'type': 'number', 'minimum': 0, 'maximum': 1},
                    title='Semi-Structured Text Minimum Legibility Threshold',
                ),
                Parameter(
                    name=Settings.StructuredCheckboxMinTrainingRecords,
                    type='integer',
                    schema={'type': 'integer', 'minimum': 0},
                    title='Structured Checkbox Min Training Records',
                    value=2000,
                    ui={'hidden': True},
                ),
                Parameter(
                    name=Settings.StructuredCheckboxMaxTrainingRecords,
                    type='integer',
                    schema={'type': 'integer', 'minimum': 0},
                    title='Structured Checkbox Max Training Records',
                    value=50000,
                    ui={'hidden': True},
                ),
                Parameter(
                    name=Settings.StructuredCheckboxTargetAccuracy,
                    type='Percentage',
                    schema=EXACT_PERCENT_SCHEMA,
                    title='Structured Checkbox Target Accuracy',
                    value=0.95,
                    dependencies=[transcription_automation_training_dependency],
                ),
                Parameter(
                    name=Settings.StructuredCheckboxAutomation,
                    type='Percentage',
                    schema=EXACT_PERCENT_SCHEMA,
                    title='Structured Checkbox Automation',
                    description=(
                        'This number shows the amount of automation you will get based on the '
                        'target accuracy.'
                    ),
                    value=0,
                    ui={'disabled': True},
                    dependencies=[transcription_automation_training_dependency],
                ),
                Parameter(
                    name=Settings.StructuredCheckboxThreshold,
                    type='number',
                    schema={'type': 'number', 'minimum': 0, 'maximum': 1},
                    title='Structured Checkbox Threshold',
                    value=0.56,
                ),
                Parameter(
                    name=Settings.StructuredCheckboxMinLegThreshold,
                    type='number',
                    schema={'type': 'number', 'minimum': 0, 'maximum': 1},
                    title='Structured Checkbox Minimum Legibility Threshold',
                ),
                Parameter(
                    name=Settings.StructuredSignatureMinTrainingRecords,
                    type='integer',
                    schema={'type': 'integer', 'minimum': 0},
                    title='Structured Signature Min Training Records',
                    value=2000,
                    ui={'hidden': True},
                ),
                Parameter(
                    name=Settings.StructuredSignatureMaxTrainingRecords,
                    type='integer',
                    schema={'type': 'integer', 'minimum': 0},
                    title='Structured Signature Max Training Records',
                    value=50000,
                    ui={'hidden': True},
                ),
                Parameter(
                    name=Settings.StructuredSignatureTargetAccuracy,
                    type='Percentage',
                    schema=EXACT_PERCENT_SCHEMA,
                    title='Structured Signature Target Accuracy',
                    value=0.95,
                    dependencies=[transcription_automation_training_dependency],
                ),
                Parameter(
                    name=Settings.StructuredSignatureAutomation,
                    type='Percentage',
                    schema=EXACT_PERCENT_SCHEMA,
                    title='Structured Signature Automation',
                    description=(
                        'This number shows the amount of automation you will get based on the '
                        'target accuracy.'
                    ),
                    value=0,
                    ui={'disabled': True},
                    dependencies=[transcription_automation_training_dependency],
                ),
                Parameter(
                    name=Settings.StructuredSignatureThreshold,
                    type='number',
                    schema={'type': 'number', 'minimum': 0, 'maximum': 1},
                    title='Structured Signature Threshold',
                    value=0.99,
                ),
                Parameter(
                    name=Settings.StructuredSignatureMinLegThreshold,
                    type='number',
                    schema={'type': 'number', 'minimum': 0, 'maximum': 1},
                    title='Structured Signature Minimum Legibility Threshold',
                ),
                Parameter(
                    name=Settings.SemiStructuredCheckboxMinTrainingRecords,
                    type='integer',
                    schema={'type': 'integer', 'minimum': 0},
                    title='Semi-Structured Checkbox Min Training Records',
                    value=2000,
                    ui={'hidden': True},
                ),
                Parameter(
                    name=Settings.SemiStructuredCheckboxMaxTrainingRecords,
                    type='integer',
                    schema={'type': 'integer', 'minimum': 0},
                    title='Semi-Structured Checkbox Max Training Records',
                    value=50000,
                    ui={'hidden': True},
                ),
                Parameter(
                    name=Settings.SemiStructuredCheckboxTargetAccuracy,
                    type='Percentage',
                    schema=EXACT_PERCENT_SCHEMA,
                    title='Semi-Structured Checkbox Target Accuracy',
                    value=0.95,
                    dependencies=[transcription_automation_training_dependency],
                ),
                Parameter(
                    name=Settings.SemiStructuredCheckboxAutomation,
                    type='Percentage',
                    schema=EXACT_PERCENT_SCHEMA,
                    title='Semi-Structured Checkbox Automation',
                    description=(
                        'This number shows the amount of automation you will get based on the '
                        'target accuracy.'
                    ),
                    value=0,
                    ui={'disabled': True},
                    dependencies=[transcription_automation_training_dependency],
                ),
                Parameter(
                    name=Settings.SemiStructuredCheckboxThreshold,
                    type='number',
                    schema={'type': 'number', 'minimum': 0, 'maximum': 1},
                    title='Semi-Structured Checkbox Threshold',
                    value=0.56,
                ),
                Parameter(
                    name=Settings.SemiStructuredCheckboxMinLegThreshold,
                    type='number',
                    schema={'type': 'number', 'minimum': 0, 'maximum': 1},
                    title='Semi-Structured Checkbox Minimum Legibility Threshold',
                ),
                Parameter(
                    name=Settings.SemiTranscriptionConfBoost,
                    type='boolean',
                    title='Semi-Structured Transcription Confidence Boost',
                ),
                Parameter(
                    name=Settings.TranscriptionQaEnabled,
                    type='boolean',
                    title='Transcription Quality Assurance',
                ),
                Parameter(
                    name=Settings.TranscriptionQaSampleRate,
                    type='Percentage',
                    title='Transcription QA Sample Rate',
                    description='Defines the percentage of fields the system samples for QA.',
                    dependencies=[
                        Dependency(
                            condition={
                                'properties': {Settings.TranscriptionQaEnabled: {'const': False}}
                            },
                            override={
                                'ui': {
                                    'na_reason': (
                                        'Not applied when Transcription Quality Assurance'
                                        ' is disabled.'
                                    )
                                }
                            },
                        )
                    ],
                ),
                Parameter(
                    name=Settings.TableCellTranscriptionQaEnabled,
                    type='boolean',
                    title='Table Transcription Quality Assurance',
                ),
                Parameter(
                    name=Settings.TableCellTranscriptionQaSampleRate,
                    type='Percentage',
                    title='Table Transcription QA Sample Rate',
                    description=(
                        'Defines the percentage of cells the system samples for QA. This '
                        'value is likely to be lower than "Transcription QA Sample Rate" since'
                        'there are more table cells than fields on any given page.'
                    ),
                    dependencies=[
                        Dependency(
                            condition={
                                'properties': {
                                    Settings.TableCellTranscriptionQaEnabled: {'const': False}
                                }
                            },
                            override={
                                'ui': {
                                    'na_reason': (
                                        'Not applied when Table Transcription Quality Assurance'
                                        ' is disabled.'
                                    )
                                }
                            },
                        )
                    ],
                ),
                Parameter(
                    name=Settings.ManualTranscriptionEnabled,
                    type='boolean',
                    title='Manual Transcription Supervision',
                    description='Enables manual transcription when applicable',
                ),
                Parameter(
                    name=Settings.TranscriptionModel,
                    type='string',
                    title='Transcription Model',
                    description='The transcription model that will be used for this flow',
                    ui={'hidden': True},
                ),
                Parameter(
                    name=Settings.FinetuningOnlyTrainedLayouts,
                    type='boolean',
                    title='Finetuning only for trained layouts',
                    description=('Run finetuning only for trained layouts.'),
                ),
            ],
            ui={
                'groups': [
                    {
                        'title': 'Classification',
                        'fields': [
                            Settings.StructuredLayoutMatchThreshold,
                            Settings.SemiStructuredClassification,
                            Settings.ManualNlcEnabled,
                            Settings.SemiTargetAccuracy,
                            Settings.SemiDocGroupingLogic,
                            Settings.SemiQaSampleRate,
                        ],
                    },
                    {
                        'title': 'Identification',
                        'fields': [
                            Settings.FieldIdTargetAccuracy,
                            Settings.TableIdTargetAccuracy,
                            Settings.ManualFieldIdEnabled,
                            Settings.FieldIdQaEnabled,
                            Settings.FieldIdQaSampleRate,
                            Settings.TableIdQaEnabled,
                            Settings.TableIdQaSampleRate,
                        ],
                    },
                    {
                        'title': 'General Transcription',
                        'fields': [
                            Settings.TranscriptionAutomationTraining,
                            Settings.TranscriptionTrainingLegibilityPeriod,
                            Settings.ImprovedTranscriptionThresholdAccuracy,
                            Settings.ManualTranscriptionEnabled,
                            Settings.TranscriptionQaEnabled,
                            Settings.TranscriptionQaSampleRate,
                            Settings.TableCellTranscriptionQaEnabled,
                            Settings.TableCellTranscriptionQaSampleRate,
                        ],
                    },
                    {
                        'title': 'Structured Document Transcription',
                        'fields': [
                            Settings.StructuredTextMinTrainingRecords,
                            Settings.StructuredTextMaxTrainingRecords,
                            Settings.StructuredTextTargetAccuracy,
                            Settings.StructuredTextAutomation,
                            Settings.StructuredTextThreshold,
                            Settings.StructuredTextMinLegThreshold,
                            Settings.StructuredCheckboxMinTrainingRecords,
                            Settings.StructuredCheckboxMaxTrainingRecords,
                            Settings.StructuredCheckboxTargetAccuracy,
                            Settings.StructuredCheckboxAutomation,
                            Settings.StructuredCheckboxThreshold,
                            Settings.StructuredCheckboxMinLegThreshold,
                            Settings.StructuredSignatureMinTrainingRecords,
                            Settings.StructuredSignatureMaxTrainingRecords,
                            Settings.StructuredSignatureTargetAccuracy,
                            Settings.StructuredSignatureAutomation,
                            Settings.StructuredSignatureThreshold,
                            Settings.StructuredSignatureMinLegThreshold,
                            Settings.FinetuningOnlyTrainedLayouts,
                        ],
                    },
                    {
                        'title': 'Semi-Structured Document Transcription',
                        'fields': [
                            Settings.SemiStructuredTextMinTrainingRecords,
                            Settings.SemiStructuredTextMaxTrainingRecords,
                            Settings.SemiStructuredTextTargetAccuracy,
                            Settings.SemiStructuredTextAutomation,
                            Settings.SemiStructuredTextThreshold,
                            Settings.SemiStructuredTextMinLegThreshold,
                            Settings.SemiStructuredCheckboxMinTrainingRecords,
                            Settings.SemiStructuredCheckboxMaxTrainingRecords,
                            Settings.SemiStructuredCheckboxTargetAccuracy,
                            Settings.SemiStructuredCheckboxAutomation,
                            Settings.SemiStructuredCheckboxThreshold,
                            Settings.SemiStructuredCheckboxMinLegThreshold,
                            Settings.SemiTranscriptionConfBoost,
                        ],
                    },
                ]
            },
            output=[
                Parameter(
                    name='submission',
                    type='Submission',
                    title='Submission',
                    description='The processed submission',
                )
            ],
        )
