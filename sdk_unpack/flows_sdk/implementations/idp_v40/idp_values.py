import enum
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from flows_sdk.blocks import IOBlock
from flows_sdk.flows import Dependency, InputDefinition, Manifest, Parameter, Triggers
from flows_sdk.implementations.idp_v40.flows_version import FLOWS_VERSION
from flows_sdk.implementations.idp_v40.licensing import (
    FeatureGatingCommonDependencies,
    LicenseGatedFeature,
    field_validation_context_not_contains_all_features,
)
from flows_sdk.utils import icon_path_to_base64, system_secret, workflow_input

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# This module contains all default values needed by an IDP flow

S3_SECRET_KEY = 's3_downloader'
OCS_SECRET_KEY = 'ocs_downloader'
HTTP_SECRET_KEY = 'http_config'
DEFAULT_IDP_CORE_IDENTIFIER = f'IDP_CORE_{FLOWS_VERSION}'
DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER = 'IDP_SUBMISSION_NOTIFY'
DEFAULT_SUBMISSION_AWARE_ON_ERROR_FLOW_IDENTIFIER = 'SUBMISSION_AWARE_ON_ERROR_FLOW'
IDP_OUTPUT_ROLE = 'idp_output'
JSON_OUTPUT_ROLE = 'json_output'
CONSECUTIVE_PAGE_BEHAVIOR_GROUP_PAGES = 'group_pages'
CONSECUTIVE_PAGE_BEHAVIOR_SPLIT_PAGES = 'split_pages'
CONSECUTIVE_PAGE_BEHAVIOR_MANUAL = 'manual'
CONSECUTIVE_PAGE_BEHAVIOR_GROUP_FILE = 'group_file'
EXACT_PERCENT_SCHEMA = {'type': 'number', 'multipleOf': 0.001, 'minimum': 0, 'maximum': 1}

ABS_SAS_TOKEN_ONLY = 'sas_token_only'
ABS_SERVICE_PRINCIPAL = 'service_principal'
ABS_MANAGED_IDENTITY = 'managed_identity'
ABS_ACCOUNT_KEY = 'account_key'

# Document Renderer Block related constants
INCHES = 'in'
MILLIMETERS = 'mm'
PDF_MIME_TYPE = 'application/pdf'
LETTER_HEIGHT_IN_INCHES = 11
LETTER_WIDTH_IN_INCHES = 8.5
LETTER_HEIGHT_IN_MM = 279.4
LETTER_WIDTH_IN_MM = 215.9
DEFAULT_QUALITY = 50


class Inputs:
    WorkflowUuid = 'workflow_uuid'
    WorkflowName = 'workflow_name'
    WorkflowVersion = 'workflow_version'
    Submission = 'submission'

    Trigger = '$trigger'


class Settings:
    LayoutReleaseUuid = 'layout_release_uuid'
    ImageCorrection = 'image_correction'

    # Submission Initialization Settings
    SubmissionBootstrapNotificationWorkflow = 'notification_workflow_initialization'
    SubmissionBootstrapS3Config = 'submission_bootstrap_s3_config'
    SubmissionBootstrapS3EndpointUrl = 'submission_bootstrap_s3_endpoint_url'
    SubmissionBootstrapOCSConfig = 'submission_bootstrap_ocs_config'
    SubmissionBootstrapHTTPConfig = 'submission_bootstrap_http_config'
    SubmissionBootstrapABSAuthType = 'submission_bootstrap_abs_auth_type'
    SubmissionBootstrapABSAccountUrl = 'submission_bootstrap_abs_account_url'
    SubmissionBootstrapABSTenantId = 'submission_bootstrap_abs_tenant_id'
    SubmissionBootstrapABSClientId = 'submission_bootstrap_abs_client_id'
    SubmissionBootstrapABSClientSecret = 'submission_bootstrap_abs_client_secret'
    SubmissionBootstrapABSAuthorityHost = 'submission_bootstrap_abs_authority_host'
    SubmissionBootstrapABSAccountName = 'submission_bootstrap_abs_account_name'
    SubmissionBootstrapABSAccountKey = 'submission_bootstrap_abs_account_key'
    # Collation Settings
    CollationDedupeFiles = 'machine_collation_dedupe_files'
    CollationRemoveFromCases = 'machine_collation_remove_from_cases'
    CollationRetentionPeriod = 'machine_collation_retention_period'
    CollationRefreshRetentionPeriod = 'machine_collation_refresh_retention_period'

    # Classification Settings
    StructuredLayoutMatchThreshold = 'structured_layout_match_threshold'
    SemiStructuredClassification = 'semi_structured_classification'
    SemiDocGroupingLogic = 'semi_doc_grouping_logic'
    SemiTargetAccuracy = 'semi_target_accuracy'
    SemiQaSampleRate = 'semi_qa_sample_rate'
    ManualNlcEnabled = 'manual_nlc_enabled'
    RotationCorrectionEnabled = 'machine_classification_rotation_correction_enabled'
    MobileProcessingEnabled = 'machine_classification_mobile_processing_enabled'
    FileTranscriptionEnabled = 'machine_classification_file_transcription_enabled'
    ManualClassificationNotificationWorkflow = 'notification_workflow_classification'
    ManualClassificationTaskRestrictions = 'manual_classification_task_restrictions'
    LayoutIdDealbreaker = 'layout_id_dealbreaker'
    LayoutIdDealbreakerBypass = 'layout_id_dealbreaker_bypass'

    # Identification Settings
    FieldIdTargetAccuracy = 'field_id_target_accuracy'
    TableIdTargetAccuracy = 'table_id_target_accuracy'
    # This enables both field and table identification
    ManualFieldIdEnabled = 'manual_field_id_enabled'
    FieldIdQaEnabled = 'field_id_qa_enabled'
    FieldIdQaSampleRate = 'field_id_qa_sample_rate'
    TableIdQaEnabled = 'table_id_qa_enabled'
    TableIdQaSampleRate = 'table_id_qa_sample_rate'
    ManualFieldIdNotificationWorkflow = 'notification_workflow_identification'
    ManualFieldIdTaskRestrictions = 'manual_identification_task_restrictions'

    # Transcription Settings
    TranscriptionModel = 'transcription_model'
    TranscriptionOverrides = 'transcription_overrides'
    FinetuningOnlyTrainedLayouts = 'finetuning_only_trained_layouts'
    ForceNormalizationErrorsToSV = 'force_normalization_errors_to_sv'
    ForceRequiredEntriesToSV = 'force_required_entries_to_sv'
    ManualTranscriptionEnabled = 'manual_transcription_enabled'
    AutoQaSamplingRateEnabled = 'auto_qa_sampling_rate_enabled'
    ManualTranscriptionNotificationWorkflow = 'notification_workflow_transcription'
    ManualTranscriptionSupervisionTranscriptionMasking = (
        'manual_transcription_supervision_transcription_masking'
    )
    ManualTranscriptionTableOutputManualReview = 'manual_transcription_table_output_manual_review'
    ManualTranscriptionAlwaysSuperviseBlankCells = (
        'manual_transcription_always_supervise_blank_cells'
    )
    ManualTranscriptionTaskRestrictions = 'manual_transcription_task_restrictions'

    StructuredTranscriptionTraining = 'structured_transcription_training'
    StructuredTranscriptionTrainingPeriod = 'structured_transcription_training_period'
    StructuredImprovedTranscrThresholdAccuracy = 'structured_improved_transcr_threshold_accuracy'

    SemiStructuredTranscriptionTraining = 'semi_structured_transcription_training'
    SemiStructuredTranscriptionTrainingPeriod = 'semi_structured_transcription_training_period'
    SemiStructuredImprovedTranscrThresholdAccuracy = (
        'semi_structured_improved_transcr_threshold_accuracy'
    )

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

    SemiStructuredTableMinTrainingRecords = 'semi_structured_table_min_training_records'
    SemiStructuredTableMaxTrainingRecords = 'semi_structured_table_max_training_records'
    SemiStructuredTableTargetAccuracy = 'semi_structured_table_target_accuracy'
    SemiStructuredTableAutomation = 'semi_structured_table_automation'
    SemiStructuredTableThreshold = 'semi_structured_table_threshold'
    SemiStructuredTableMinLegThreshold = 'semi_structured_table_min_leg_threshold'

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
    TranscriptionStructuredEntryQaSampleRate = 'structured_entry_qa_sample_rate'
    TranscriptionStructuredCheckboxQaSampleRate = 'structured_checkbox_qa_sample_rate'
    TranscriptionStructuredSignatureQaSampleRate = 'structured_signature_qa_sample_rate'
    TranscriptionSemiStructuredQaSampleRate = 'semi_structured_qa_sample_rate'
    ExcludeAutoTranscribeFieldsFromQA = 'exclude_auto_transcribe_fields_from_qa'

    TableCellTranscriptionQaEnabled = 'table_cell_transcription_qa_enabled'
    TableCellTranscriptionQaSampleRate = 'table_cell_transcription_qa_sample_rate'

    FieldTranscriptionTargetAccuracies = 'field_transcription_target_accuracies'
    ColumnTranscriptionTargetAccuracies = 'column_transcription_target_accuracies'

    # Flexible Extraction
    FlexibleExtractionNotificationWorkflow = 'notification_workflow_flexible_extraction'
    FlexibleExtractionSupervisionTranscriptionMasking = (
        'flexible_extraction_supervision_transcription_masking'
    )
    FlexibleExtractionTaskRestrictions = 'flexible_extraction_task_restrictions'

    # Document Rendering
    DocumentRenderingEnabled = 'document_rendering_enabled'
    DocumentRenderingHeight = 'document_rendering_height'
    DocumentRenderingWidth = 'document_rendering_width'
    DocumentRenderingQuality = 'document_rendering_quality'
    DocumentRenderingMimeType = 'document_rendering_mime_type'
    DocumentRenderingUnit = 'document_rendering_unit'


@dataclass
class StructuredSamplingRates:
    entry_sampling_rate: float
    checkbox_sampling_rate: float
    signature_sampling_rate: float

    @classmethod
    def single_sampling_rate(cls, sampling_rate: float) -> 'StructuredSamplingRates':
        return cls(
            entry_sampling_rate=sampling_rate,
            checkbox_sampling_rate=sampling_rate,
            signature_sampling_rate=sampling_rate,
        )


@dataclass
class TranscriptionQaConfigData:
    auto_qa_sampling_rate_enabled: bool
    structured_sampling_rates: StructuredSamplingRates
    semi_structured_sampling_rate: float
    exclude_auto_transcribe_fields_from_qa: bool


@dataclass
class QaConfigData:
    field_id_qa_enabled: bool
    field_id_qa_sampling_ratio: float
    nlc_qa_sampling_ratio: float
    transcription_qa: Optional[TranscriptionQaConfigData]
    table_cell_transcription_qa_sample_rate: Optional[float]
    table_id_qa_enabled: bool = True
    table_id_qa_sampling_ratio: float = 0.05


@dataclass
class MachineClassificationConfig:
    nlc_enabled: bool
    nlc_target_accuracy: float
    vpc_registration_threshold: float
    layout_id_dealbreaker: Optional[bool] = False
    layout_id_dealbreaker_bypass: Optional[bool] = False


@dataclass
class SupervisionConfig:
    task_restrictions: List[str]


@dataclass
class ManualTranscriptionConfig(SupervisionConfig):
    supervision_transcription_masking: bool
    table_output_manual_review: bool
    always_supervise_blank_cells: bool


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
class SingleEntityTargetAccuracy(dict):
    source_uuid: str
    target_accuracy: float


@dataclass
class FinetuningConfig:
    STRUCTURED_TRAINING_TYPE = 'structured'
    SEMI_STRUCTURED_TRAINING_TYPE = 'semi_structured'


@dataclass
class HttpHeaderAuthorizationParams:
    authorization_header: str
    authorization_header_name: str


@dataclass
class OAuth2AuthorizationParams:
    auth_url: str
    client_id: str
    client_secret: str
    audience: str


@dataclass
class DocumentRenderingConfig:
    quality: int
    mime_type: str
    unit: str
    enabled: bool
    height: Optional[float]
    width: Optional[float]


# TODO(FLOWS-2135): this is a duplication from common.utils
class FieldTypeByKind(enum.Enum):
    ENTRY = 'entry'
    SIGNATURE = 'signature'
    CHECKBOX = 'checkbox'
    FLEX_ENTRY = 'flex_entry'
    FLEX_CHECKBOX = 'flex_checkbox'
    FLEX_TABLE_ENTRY = 'flex_table_entry'


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
    semi_structured_table: TranscriptionConfig
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

    # Document rendering settings
    document_rendering: DocumentRenderingConfig

    notification_workflow_initialization: Optional[str] = None
    notification_workflow_classification: Optional[str] = None
    notification_workflow_identification: Optional[str] = None
    notification_workflow_transcription: Optional[str] = None
    notification_workflow_flexible_extraction: Optional[str] = None
    field_transcription_target_accuracies: Optional[list[SingleEntityTargetAccuracy]] = None
    column_transcription_target_accuracies: Optional[list[SingleEntityTargetAccuracy]] = None


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
    transcription_qa = idp_wf_config.qa_config.transcription_qa
    return {
        # this field needs to exist for releases to be assigned to this flow
        Settings.LayoutReleaseUuid: workflow_input(Settings.LayoutReleaseUuid),
        Inputs.WorkflowUuid: workflow_input(Inputs.WorkflowUuid),
        Inputs.WorkflowName: workflow_input(Inputs.WorkflowName),
        Inputs.WorkflowVersion: workflow_input(Inputs.WorkflowVersion),
        Settings.SubmissionBootstrapS3Config: system_secret(S3_SECRET_KEY),
        Settings.SubmissionBootstrapOCSConfig: system_secret(OCS_SECRET_KEY),
        Settings.SubmissionBootstrapHTTPConfig: None,
        Settings.SubmissionBootstrapNotificationWorkflow: (
            idp_wf_config.notification_workflow_initialization
        ),
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
        Settings.RotationCorrectionEnabled: idp_wf_config.rotation_correction_enabled,
        Settings.MobileProcessingEnabled: False,
        Settings.FileTranscriptionEnabled: False,
        Settings.ManualClassificationNotificationWorkflow: (
            idp_wf_config.notification_workflow_classification
        ),
        Settings.FieldIdTargetAccuracy: idp_wf_config.field_id_target_accuracy,
        Settings.TableIdTargetAccuracy: idp_wf_config.table_id_target_accuracy,
        Settings.ManualFieldIdEnabled: idp_wf_config.manual_field_id_enabled,
        Settings.ManualFieldIdNotificationWorkflow: (
            idp_wf_config.notification_workflow_identification
        ),
        Settings.FieldIdQaEnabled: idp_wf_config.qa_config.field_id_qa_enabled,
        Settings.FieldIdQaSampleRate: idp_wf_config.qa_config.field_id_qa_sampling_ratio,
        # @since v31.0 therefore no backing django model for this value
        Settings.TableIdQaEnabled: True,
        # @since v31.0 therefore no backing django model for this value
        Settings.TableIdQaSampleRate: 0.05,
        Settings.StructuredTranscriptionTraining: idp_wf_config.transcription_automation_training,
        Settings.StructuredImprovedTranscrThresholdAccuracy: (
            idp_wf_config.improved_transcription_threshold_accuracy
        ),
        Settings.StructuredTranscriptionTrainingPeriod: (
            idp_wf_config.transcription_training_legibility_period
        ),
        Settings.SemiStructuredTranscriptionTraining: (
            idp_wf_config.transcription_automation_training
            or idp_wf_config.flex_confidence_boosting_enabled
        ),
        Settings.SemiStructuredTranscriptionTrainingPeriod: (
            idp_wf_config.transcription_training_legibility_period
        ),
        Settings.SemiStructuredImprovedTranscrThresholdAccuracy: (
            idp_wf_config.improved_transcription_threshold_accuracy
        ),
        Settings.TranscriptionModel: idp_wf_config.transcription_model,
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
        Settings.SemiStructuredTableMinTrainingRecords: (
            idp_wf_config.semi_structured_table.min_samples
        ),
        Settings.SemiStructuredTableMaxTrainingRecords: (
            idp_wf_config.semi_structured_table.max_samples
        ),
        Settings.SemiStructuredTableTargetAccuracy: (
            idp_wf_config.semi_structured_table.target_accuracy
        ),
        Settings.SemiStructuredTableThreshold: (
            idp_wf_config.semi_structured_table.confidence_threshold
        ),
        Settings.SemiStructuredTableMinLegThreshold: (
            idp_wf_config.semi_structured_table.acceptable_confidence
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
        Settings.ManualTranscriptionNotificationWorkflow: (
            idp_wf_config.notification_workflow_transcription
        ),
        Settings.ManualTranscriptionSupervisionTranscriptionMasking: (
            idp_wf_config.manual_transcription_config.supervision_transcription_masking
        ),
        Settings.ManualTranscriptionTaskRestrictions: (
            idp_wf_config.manual_transcription_config.task_restrictions
        ),
        Settings.ManualTranscriptionTableOutputManualReview: (
            idp_wf_config.manual_transcription_config.table_output_manual_review
        ),
        Settings.ManualTranscriptionAlwaysSuperviseBlankCells: (
            idp_wf_config.manual_transcription_config.always_supervise_blank_cells
        ),
        Settings.TranscriptionQaEnabled: transcription_qa is not None,
        Settings.TranscriptionStructuredEntryQaSampleRate: (
            transcription_qa.structured_sampling_rates.entry_sampling_rate
            if transcription_qa is not None
            else None
        ),
        Settings.TranscriptionStructuredCheckboxQaSampleRate: (
            transcription_qa.structured_sampling_rates.checkbox_sampling_rate
            if transcription_qa is not None
            else None
        ),
        Settings.TranscriptionStructuredSignatureQaSampleRate: (
            transcription_qa.structured_sampling_rates.signature_sampling_rate
            if transcription_qa is not None
            else None
        ),
        Settings.TranscriptionSemiStructuredQaSampleRate: (
            transcription_qa.semi_structured_sampling_rate if transcription_qa is not None else None
        ),
        Settings.ExcludeAutoTranscribeFieldsFromQA: (
            transcription_qa.exclude_auto_transcribe_fields_from_qa
            if transcription_qa is not None
            else None
        ),
        # @since v32.0 therefore no backing django model for this value
        Settings.TableCellTranscriptionQaEnabled: True,
        # @since v32.0 therefore no backing django model for this value
        Settings.TableCellTranscriptionQaSampleRate: 0.05,
        Settings.FinetuningOnlyTrainedLayouts: idp_wf_config.finetuning_only_trained_layouts,
        Settings.ForceNormalizationErrorsToSV: False,
        Settings.ForceRequiredEntriesToSV: False,
        Settings.AutoQaSamplingRateEnabled: transcription_qa is not None
        and transcription_qa.auto_qa_sampling_rate_enabled,
        Settings.FlexibleExtractionNotificationWorkflow: (
            idp_wf_config.notification_workflow_flexible_extraction
        ),
        Settings.FlexibleExtractionSupervisionTranscriptionMasking: (
            idp_wf_config.flexible_extraction_config.supervision_transcription_masking
        ),
        Settings.FlexibleExtractionTaskRestrictions: (
            idp_wf_config.flexible_extraction_config.task_restrictions
        ),
        # @since v40
        Settings.DocumentRenderingEnabled: idp_wf_config.document_rendering.enabled,
        Settings.DocumentRenderingHeight: idp_wf_config.document_rendering.height,
        Settings.DocumentRenderingWidth: idp_wf_config.document_rendering.width,
        Settings.DocumentRenderingQuality: idp_wf_config.document_rendering.quality,
        Settings.DocumentRenderingMimeType: idp_wf_config.document_rendering.mime_type,
        Settings.DocumentRenderingUnit: idp_wf_config.document_rendering.unit,
        # @since v40
        Settings.FieldTranscriptionTargetAccuracies: (
            idp_wf_config.field_transcription_target_accuracies or []
        ),
        Settings.ColumnTranscriptionTargetAccuracies: (
            idp_wf_config.column_transcription_target_accuracies or []
        ),
        # @since v40
        Settings.LayoutIdDealbreaker: (
            idp_wf_config.machine_classification_config.layout_id_dealbreaker
        ),
        Settings.LayoutIdDealbreakerBypass: (
            idp_wf_config.machine_classification_config.layout_id_dealbreaker_bypass
        ),
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
        semi_structured_table=TranscriptionConfig(
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
            always_supervise_blank_cells=True,
        ),
        manual_identification_config=ManualIdentificationConfig(task_restrictions=[]),
        qa_config=QaConfigData(
            field_id_qa_sampling_ratio=0.05,
            field_id_qa_enabled=True,
            nlc_qa_sampling_ratio=0.05,
            table_id_qa_enabled=True,
            table_id_qa_sampling_ratio=0.05,
            table_cell_transcription_qa_sample_rate=0.05,
            transcription_qa=TranscriptionQaConfigData(
                auto_qa_sampling_rate_enabled=False,
                structured_sampling_rates=StructuredSamplingRates.single_sampling_rate(0.05),
                semi_structured_sampling_rate=0.05,
                exclude_auto_transcribe_fields_from_qa=False,
            ),
        ),
        transcription_model='IDP',
        finetuning_only_trained_layouts=True,
        document_rendering=DocumentRenderingConfig(
            height=11,
            width=8.5,
            quality=50,
            mime_type='application/pdf',
            unit=INCHES,
            enabled=False,
        ),
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

    # mypy pidantic errors out on redefined init
    # issue: https://github.com/pydantic/pydantic/issues/4113
    def __init__(self, blocks: Optional[Sequence[IOBlock]] = None) -> None:
        blocks = blocks or []

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


class IDPWrapperManifest(Manifest):
    """
    An adapter class making it easier to instantiate :py:class:`flows_sdk.flows.Manifest` for
    IDP wrapper flows.
    In particular, provides defaults for some fields (e.g. roles)
    but more importantly, defines all :py:class:`flows_sdk.flows.Parameter` that construct the
    Flow inputs and their UI representation (left-hand side menu in Flow studio).


    :param flow_identifier: A system-wide unique identifier for :py:class:`flows_sdk.flows.Flow`

    Example usage when instantiating an IDP flow::

        flow = Flow(
            manifest=IDPWrapperManifest(flow_identifier='FLOW_IDENTIFIER'),
            ...
        )
    """

    def __init__(self, flow_identifier: str) -> None:
        super().__init__(
            identifier=flow_identifier,
            roles=['idp'],
            input=[
                Parameter(
                    name=Settings.LayoutReleaseUuid, type='ReleaseUUID', title='Layout Release'
                ),
            ],
        )


class IDPCoreManifest(Manifest):
    """
    An adapter class making it easier to instantiate :py:class:`flows_sdk.flows.Manifest` for
    IDP Core flows.
    In particular, provides defaults for some fields (e.g. roles, output)
    but more importantly, defines all :py:class:`flows_sdk.flows.Parameter` that construct the
    Flow inputs and their UI representation (left-hand side menu in Flow studio).


    :param flow_identifier: A system-wide unique identifier for :py:class:`flows_sdk.flows.Flow`
    :param roles: 'read_only', 'supporting' and 'idp_core' are the default roles of every subflow
        that can replace the default IDP_CORE subflow inside the top-level IDP flows.
        'supporting' and 'idp_core' are mandatory roles that are necessary for all IDP Core flows.
        'supporting' ensures that the subflow will be auto-deployed together with the
        top-level IDP flow.
        'idp_core' ensures that this subflow can be selected in the UI in dropdowns which allow
        picking an alternative subflow to the default IDP_CORE subflow. If you are implementing
        a subflow that is not supposed to be a drop-in replacement for IDP_CORE, you will have to
        subclass or implement your own version of IDPCoreManifest class in order
        to remove the `idp_core` role.

    Example usage when instantiating an IDP flow::

        flow = Flow(
            manifest=IDPCoreManifest(flow_identifier='FLOW_IDENTIFIER'),
            ...
        )
    """

    def __init__(self, flow_identifier: str, roles: Optional[List[str]] = None) -> None:
        document_rendering_common_dependencies = [
            Dependency(
                condition={'properties': {Settings.DocumentRenderingEnabled: {'const': False}}},
                override={'ui': {'hidden': True}},
            ),
            Dependency(
                condition={
                    'properties': {
                        **field_validation_context_not_contains_all_features(
                            [LicenseGatedFeature.DOCUMENT_RENDERER]
                        )
                    }
                },
                override={'ui': {'hide_and_retain': True}},
            ),
        ]
        system_provided_inputs = [
            Parameter(
                name=Inputs.WorkflowUuid,
                type='string',
                title='Root workflow UUID',
                optional=True,
                ui={'hidden': True},
            ),
            Parameter(
                name=Inputs.WorkflowName,
                type='string',
                title='Root workflow name',
                optional=True,
                ui={'hidden': True},
            ),
            Parameter(
                name=Inputs.WorkflowVersion,
                type='string',
                title='Root workflow version',
                optional=True,
                ui={'hidden': True},
            ),
        ]
        submission_bootstrap_inputs = [
            Parameter(
                name='$trigger',
                title='Trigger',
                type='object',
                ui={'hidden': True},
            ),
            Parameter(
                name=Settings.SubmissionBootstrapNotificationWorkflow,
                type='FlowIdentifier',
                title='Submission Initialization Notification Flow',
                type_spec={'filter_roles': ['notifications'], 'label': 'If task needed'},
                optional=True,
                value=None,
            ),
            Parameter(
                name=Settings.SubmissionBootstrapS3Config,
                type='object',
                description='Specify Amazon S3 credentials for submission retrieval store. '
                'Expects a json expression: '
                '{"aws_access_key_id": "X", "aws_secret_access_key": "Y"}',
                title='S3 Submission Retrieval Store Configuration',
                secret=True,
                optional=True,
            ),
            Parameter(
                name=Settings.SubmissionBootstrapS3EndpointUrl,
                type='string',
                description='Endpoint URL for S3 Submission Retrieval Store. '
                'Do not use when your submission retrieval store is in a public cloud.',
                title='S3 Submission Retrieval Endpoint URL',
                optional=True,
            ),
            Parameter(
                name=Settings.SubmissionBootstrapOCSConfig,
                type='object',
                description='OCS configuration for submission retrieval store. '
                'Expects a json expression: {"host_url": "X", "username": "Y", '
                '"password": "Z", "ssl_cert": "CA bundle filename"}. '
                'ssl_cert is the CA bundle filename inside $HS_PATH/certs directory. '
                'Set it to "SKIP" to disable certificate validation.',
                title='OCS Configuration',
                secret=True,
                optional=True,
            ),
            Parameter(
                name=Settings.SubmissionBootstrapHTTPConfig,
                type='object',
                description='Specify relevant Generic Web Storage configuration variables '
                'for submission retrieval store. Expects a JSON expression: '
                '{"username": "X", "password": "Y", "ssl_cert": "CA bundle filename"}. '
                'ssl_cert is the CA bundle filename inside $HS_PATH/certs directory. '
                'Set it to "SKIP" to disable certificate validation.',
                title='Generic Web Storage (HTTP/HTTPS) Configuration',
                secret=True,
                optional=True,
            ),
            Parameter(
                name=Settings.SubmissionBootstrapABSAuthType,
                type='string',
                optional=True,
                schema={
                    'type': 'string',
                    'oneOf': [
                        {'title': 'SAS Token Only', 'const': ABS_SAS_TOKEN_ONLY},
                        {'title': 'Service Principal', 'const': ABS_SERVICE_PRINCIPAL},
                        {'title': 'Managed Identity', 'const': ABS_MANAGED_IDENTITY},
                        {'title': 'Account Key', 'const': ABS_ACCOUNT_KEY},
                    ],
                },
                description='The type of authentication to use.',
                title='Azure Blob Storage Authentication Type',
            ),
            Parameter(
                name=Settings.SubmissionBootstrapABSAccountUrl,
                type='string',
                description='The URL of the storage account.',
                title='Azure Blob Storage Account URL',
                optional=True,
                ui={'hidden': True},
                dependencies=[
                    Dependency(
                        condition={'required': [Settings.SubmissionBootstrapABSAuthType]},
                        override={
                            'ui': {'hidden': False},
                            'optional': False,
                        },
                    ),
                ],
            ),
            Parameter(
                name=Settings.SubmissionBootstrapABSTenantId,
                type='string',
                description='The tenant ID of the service principal.',
                title='Azure Blob Storage Tenant ID',
                optional=True,
                ui={'hidden': True},
                dependencies=[
                    Dependency(
                        condition={
                            'required': [Settings.SubmissionBootstrapABSAuthType],
                            'properties': {
                                Settings.SubmissionBootstrapABSAuthType: {
                                    'const': ABS_SERVICE_PRINCIPAL
                                }
                            },
                        },
                        override={'ui': {'hidden': False}},
                    ),
                ],
            ),
            Parameter(
                name=Settings.SubmissionBootstrapABSClientId,
                type='string',
                description='The client ID of the service principal or managed identity.',
                title='Azure Blob Storage Client ID',
                optional=True,
                ui={'hidden': True},
                dependencies=[
                    Dependency(
                        condition={
                            'required': [Settings.SubmissionBootstrapABSAuthType],
                            'properties': {
                                Settings.SubmissionBootstrapABSAuthType: {
                                    'enum': [ABS_SERVICE_PRINCIPAL, ABS_MANAGED_IDENTITY]
                                }
                            },
                        },
                        override={'ui': {'hidden': False}},
                    ),
                ],
            ),
            Parameter(
                name=Settings.SubmissionBootstrapABSClientSecret,
                type='string',
                description='The client secret of the service principal.',
                title='Azure Blob Storage Client Secret',
                optional=True,
                secret=True,
                ui={'hidden': True},
                dependencies=[
                    Dependency(
                        condition={
                            'required': [Settings.SubmissionBootstrapABSAuthType],
                            'properties': {
                                Settings.SubmissionBootstrapABSAuthType: {
                                    'const': ABS_SERVICE_PRINCIPAL
                                }
                            },
                        },
                        override={'ui': {'hidden': False}},
                    )
                ],
            ),
            Parameter(
                name=Settings.SubmissionBootstrapABSAuthorityHost,
                type='string',
                description='The authority host of the service principal.',
                title='Azure Blob Storage Authority Host',
                optional=True,
                ui={'hidden': True},
                dependencies=[
                    Dependency(
                        condition={
                            'required': [Settings.SubmissionBootstrapABSAuthType],
                            'properties': {
                                Settings.SubmissionBootstrapABSAuthType: {
                                    'const': ABS_SERVICE_PRINCIPAL
                                }
                            },
                        },
                        override={'ui': {'hidden': False}},
                    )
                ],
            ),
            Parameter(
                name=Settings.SubmissionBootstrapABSAccountName,
                type='string',
                description='The account name of the storage account.',
                title='Azure Blob Storage Account Name',
                optional=True,
                secret=False,
                ui={'hidden': True},
                dependencies=[
                    Dependency(
                        condition={
                            'required': [Settings.SubmissionBootstrapABSAuthType],
                            'properties': {
                                Settings.SubmissionBootstrapABSAuthType: {'const': ABS_ACCOUNT_KEY}
                            },
                        },
                        override={'ui': {'hidden': False}},
                    )
                ],
            ),
            Parameter(
                name=Settings.SubmissionBootstrapABSAccountKey,
                type='string',
                description='The account key of the storage account.',
                title='Azure Blob Storage Account Key',
                optional=True,
                secret=True,
                ui={'hidden': True},
                dependencies=[
                    Dependency(
                        condition={
                            'required': [Settings.SubmissionBootstrapABSAuthType],
                            'properties': {
                                Settings.SubmissionBootstrapABSAuthType: {'const': ABS_ACCOUNT_KEY}
                            },
                        },
                        override={'ui': {'hidden': False}},
                    )
                ],
            ),
        ]
        machine_collation_inputs = [
            Parameter(
                name='machine_collation_dedupe_files',
                type='boolean',
                value=False,
                title='Replace case data from duplicate file names',
                description=(
                    'Enabling this setting will replace case data from repeated file names within '
                    'the same case. Cases will retain data from the most recently submitted '
                    'version of a particular file. Note that this setting does not delete the old '
                    'data, it just removes it from the case. Keep in mind this option is only '
                    'relevant when adding to cases'
                ),
            ),
            Parameter(
                name='machine_collation_remove_from_cases',
                type='array',
                optional=True,
                title='Remove from Cases Information',
                ui={'hidden': True},
                description='This parameter accepts an array of JSON objects that contains '
                'information on how documents or pages should be removed from a pre-existing '
                'case. Currently, the only way to de-collate from a case is by the ids of the '
                'Documents or Pages within a given case',
            ),
            Parameter(
                name='machine_collation_retention_period',
                type='integer',
                optional=True,
                value=None,
                title='Retention Period',
                description='The number of days to retain cases after they are updated by this '
                'block. If None, no changes to the deletion date will be made.',
            ),
            Parameter(
                name='machine_collation_refresh_retention_period',
                type='boolean',
                optional=True,
                value=True,
                title='Refresh Retention Period',
                description='If True, applies Retention Period to all cases in the block. '
                'If False, only updates those without a pre-existing deletion date.',
            ),
        ]
        classification_inputs = [
            Parameter(
                name='machine_classification_rotation_correction_enabled',
                type='boolean',
                value=True,
                title='Image correction',
                description='Identifies and corrects the orientation of semi-structured images.',
            ),
            Parameter(
                name='machine_classification_mobile_processing_enabled',
                type='boolean',
                value=False,
                title='Mobile processing',
                description='Improves the machine readability of photo captured documents',
            ),
            Parameter(
                name='machine_classification_file_transcription_enabled',
                type='boolean',
                value=False,
                title='Faster PDF transcription',
                description=(
                    'Improves the transcription speed of pdf files. Make sure that '
                    'the "Image Correction" option is disabled and the pdfs you '
                    'submit do not contain any rotated images'
                ),
            ),
            Parameter(
                name=Settings.LayoutIdDealbreaker,
                type='boolean',
                value=False,
                title='Classify using Layout ID',
                description=(
                    'Forces structured document matching by Layout ID, '
                    'if present in both the document and in the structured layout'
                ),
            ),
            Parameter(
                name=Settings.LayoutIdDealbreakerBypass,
                type='boolean',
                value=False,
                title='Bypass classification by Layout ID',
                description=(
                    'Bypass validation by Layout ID'
                    " if the matched layout doesn't have a Layout ID specified"
                ),
                dependencies=[
                    Dependency(
                        condition={'properties': {Settings.LayoutIdDealbreaker: {'const': True}}},
                        override={'ui': {'hidden': False}},
                    )
                ],
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
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
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
                title='Semi-Structured Classification Target Accuracy',
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
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
                title='Semi-Structured Classification Grouping Logic',
                description=(
                    'Determines how multiple pages matched to the same layout variation in a '
                    'given submission will be handled.'
                ),
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiQaSampleRate,
                type='Percentage',
                title='Semi-Structured Classification QA Sample Rate',
                description='Defines the percentage of documents sampled for QA.',
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.ManualClassificationNotificationWorkflow,
                type='FlowIdentifier',
                value=None,
                title='Manual Classification Notification Flow',
                type_spec={'filter_roles': ['notifications'], 'label': 'If task needed'},
                optional=True,
            ),
            Parameter(
                name=Settings.ManualClassificationTaskRestrictions,
                type='TaskRestrictions',
                title='Default Task Restrictions',
                description=(
                    'Defines what users can access Supervision tasks created by this block.'
                ),
                optional=True,
            ),
        ]
        identification_inputs = [
            Parameter(
                name=Settings.FieldIdTargetAccuracy,
                type='Percentage',
                schema=EXACT_PERCENT_SCHEMA,
                title='Field Identification Target Accuracy',
                dependencies=FeatureGatingCommonDependencies.FieldId,
            ),
            Parameter(
                name=Settings.TableIdTargetAccuracy,
                type='Percentage',
                schema=EXACT_PERCENT_SCHEMA,
                title='Table Identification Target Accuracy',
                value=0.96,
                dependencies=FeatureGatingCommonDependencies.TableId,
            ),
            Parameter(
                name=Settings.ManualFieldIdEnabled,
                type='boolean',
                title='Manual Identification Supervision',
                description='Enables manual identification when applicable',
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.FieldIdQaEnabled,
                type='boolean',
                title='Field Identification Quality Assurance',
                description=(
                    'Allows users to verify the location or presence of fields on '
                    'semi-structured documents.'
                ),
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
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
                    ),
                ]
                + FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.TableIdQaEnabled,
                type='boolean',
                value=True,
                title='TABLE IDENTIFICATION QUALITY ASSURANCE',
                description='Allows users to verify the location of table cells.',
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
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
                    ),
                ]
                + FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.ManualFieldIdNotificationWorkflow,
                type='FlowIdentifier',
                value=None,
                title='Manual Identification Notification Flow',
                type_spec={'filter_roles': ['notifications'], 'label': 'If task needed'},
                optional=True,
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.ManualFieldIdTaskRestrictions,
                type='TaskRestrictions',
                title='Default Task Restrictions',
                description=(
                    'Defines what users can access Supervision tasks created by this block.'
                ),
                optional=True,
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
        ]
        general_transcription_inputs = [
            Parameter(
                name=Settings.FieldTranscriptionTargetAccuracies,
                type='FieldTranscriptionTargetAccuracies',
                title='Field Transcription Accuracy Targets',
                description='Field Transcription Accuracy Targets',
                ui={'hidden': False},
                optional=True,
                value=[],
                schema={
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'source_uuid': {'type': 'string'},
                            'target_accuracy': {'type': 'number'},
                        },
                    },
                },
            ),
            Parameter(
                name=Settings.ManualTranscriptionEnabled,
                type='boolean',
                title='Manual Transcription Supervision',
                description='Enables manual transcription when applicable',
            ),
            Parameter(
                name=Settings.TranscriptionQaEnabled,
                type='boolean',
                title='Transcription Quality Assurance',
            ),
            Parameter(
                name=Settings.AutoQaSamplingRateEnabled,
                type='boolean',
                title='Automatic QA Sample Rate',
                description='Updates QA rate daily based on submission volume.',
                value=False,
                dependencies=[
                    Dependency(
                        condition={
                            'properties': {Settings.TranscriptionQaEnabled: {'const': False}}
                        },
                        override={'ui': {'hidden': True}},
                    )
                ],
            ),
            Parameter(
                name=Settings.TranscriptionStructuredEntryQaSampleRate,
                type='Percentage',
                title='Structured Text Transcription QA Sample Rate',
                description=(
                    'Defines the percentage of structured text fields ' 'the system samples for QA.'
                ),
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
                    ),
                    Dependency(
                        condition={
                            'properties': {Settings.AutoQaSamplingRateEnabled: {'const': True}}
                        },
                        override={'ui': {'disabled': True}},
                    ),
                ],
            ),
            Parameter(
                name=Settings.TranscriptionStructuredCheckboxQaSampleRate,
                type='Percentage',
                title='Structured Checkbox Transcription QA Sample Rate',
                description=(
                    'Defines the percentage of structured checkbox fields '
                    'the system samples for QA.'
                ),
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
                    ),
                    Dependency(
                        condition={
                            'properties': {Settings.AutoQaSamplingRateEnabled: {'const': True}}
                        },
                        override={'ui': {'disabled': True}},
                    ),
                ],
            ),
            Parameter(
                name=Settings.TranscriptionStructuredSignatureQaSampleRate,
                type='Percentage',
                title='Structured Signature Transcription QA Sample Rate',
                description=(
                    'Defines the percentage of structured signature fields '
                    'the system samples for QA.'
                ),
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
                    ),
                    Dependency(
                        condition={
                            'properties': {Settings.AutoQaSamplingRateEnabled: {'const': True}}
                        },
                        override={'ui': {'disabled': True}},
                    ),
                ],
            ),
            Parameter(
                name=Settings.TranscriptionSemiStructuredQaSampleRate,
                type='Percentage',
                title='Semi-Structured Transcription QA Sample Rate',
                description=(
                    'Defines the percentage of semi-structured fields ' 'the system samples for QA.'
                ),
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
                    ),
                    Dependency(
                        condition={
                            'properties': {Settings.AutoQaSamplingRateEnabled: {'const': True}}
                        },
                        override={'ui': {'disabled': True}},
                    ),
                ]
                + FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.TableCellTranscriptionQaEnabled,
                type='boolean',
                title='Table Transcription Quality Assurance',
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
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
                ]
                + FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.TranscriptionOverrides,
                type='object',
                title='Transcription Overrides',
                optional=True,
                value={},
                ui={'hidden': True},
            ),
            Parameter(
                name=Settings.FinetuningOnlyTrainedLayouts,
                type='boolean',
                title='Finetuning only for trained layouts',
                description='Run finetuning only for trained layouts.',
            ),
            Parameter(
                name=Settings.ForceNormalizationErrorsToSV,
                type='boolean',
                value=False,
                title='Force normalization errors to Supervision',
                description=(
                    'Enable this option to ensure that fields or table cells with normalization '
                    'errors are sent to Supervision for additional human review, preventing '
                    'uncorrected errors from proceeding to downstream processing. '
                    'Available from V40.2.'
                ),
            ),
            Parameter(
                name=Settings.ForceRequiredEntriesToSV,
                type='boolean',
                value=False,
                title='Force missing/blank Fields to Supervision',
                description=(
                    'Enable this option to route fields marked as "Required" to Supervision for '
                    'review if they are missing or left blank, ensuring important data is present '
                    'in downstream processes. Available from V40.2.'
                ),
            ),
            Parameter(
                name=Settings.ExcludeAutoTranscribeFieldsFromQA,
                type='boolean',
                title='Exclude Auto-Transcribe Fields From QA',
                value=False,
            ),
            Parameter(
                name=Settings.ColumnTranscriptionTargetAccuracies,
                type='array',
                title='Column Transcription Target Accuracies',
                optional=True,
                value=[],
                ui={'hidden': True},
            ),
            # Manual Transcription Settings
            Parameter(
                name=Settings.ManualTranscriptionNotificationWorkflow,
                type='FlowIdentifier',
                value=None,
                title='Manual Transcription Notification Flow',
                type_spec={'filter_roles': ['notifications'], 'label': 'If task needed'},
                optional=True,
            ),
            Parameter(
                name=Settings.ManualTranscriptionSupervisionTranscriptionMasking,
                type='boolean',
                value=True,
                title='Supervision Transcription Masking',
                description=(
                    'Prevents users from inputting invalid characters during'
                    ' Supervision Transcription tasks.'
                ),
            ),
            Parameter(
                name=Settings.ManualTranscriptionTableOutputManualReview,
                type='boolean',
                value=False,
                title='Table Output Manual Review',
                description=(
                    'Always generates a table transcription task if the layout '
                    'contains a table. If disabled, a table transcription task will '
                    'only be generated if one or more cells have transcribed values '
                    'below the defined thresholds.'
                ),
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.ManualTranscriptionAlwaysSuperviseBlankCells,
                type='boolean',
                value=True,
                title='Create Manual Transcription Task For Tables With Blank Cells',
                description=(
                    'If enabled, always send blank cells in transcribed tables to be '
                    'supervised manually, regardless of confidence.'
                ),
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.ManualTranscriptionTaskRestrictions,
                type='TaskRestrictions',
                title='Default Task Restrictions',
                description=(
                    'Defines what users can access Supervision tasks created by this block.'
                ),
                optional=True,
            ),
            Parameter(
                name=Settings.TranscriptionModel,
                type='string',
                title='Transcription Model',
                description='The transcription model that will be used for this flow',
                ui={'hidden': True},
            ),
        ]
        structured_document_transcription_inputs = [
            Parameter(
                name=Settings.StructuredTranscriptionTraining,
                type='TranscriptionAutomationTraining',
                schema={
                    'type': 'boolean',
                    'training_type': FinetuningConfig.STRUCTURED_TRAINING_TYPE,
                },
                value=True,
                title='Transcription Automation Training',
                description=(
                    'Uses QA data for on-premise machine learning'
                    ' to improve transcription automation.'
                ),
            ),
            Parameter(
                name=Settings.StructuredTranscriptionTrainingPeriod,
                type='integer',
                schema={'type': 'integer', 'minimum': 0},
                value=30,
                title='Period of records to use',
                ui={'prefix': 'Past', 'suffix': 'days'},
                dependencies=[
                    Dependency(
                        condition={
                            'properties': {
                                Settings.StructuredTranscriptionTraining: {'const': False}
                            }
                        },
                        override={
                            'ui': {
                                'na_reason': (
                                    'Not applied when Transcription Automation Training'
                                    ' is disabled.'
                                )
                            }
                        },
                    )
                ],
            ),
            Parameter(
                name=Settings.StructuredImprovedTranscrThresholdAccuracy,
                type='boolean',
                value=True,
                title='Improved threshold accuracy',
                dependencies=[
                    Dependency(
                        condition={
                            'properties': {
                                Settings.StructuredTranscriptionTraining: {'const': False}
                            }
                        },
                        override={
                            'ui': {
                                'na_reason': (
                                    'Not applied when Transcription Automation Training'
                                    ' is disabled.'
                                )
                            }
                        },
                    )
                ],
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
                type='TranscriptionTargetAccuracy',
                schema={
                    **EXACT_PERCENT_SCHEMA,
                    'entity_type': FieldTypeByKind.ENTRY.value,
                    'min_training_records_prop': Settings.StructuredTextMinTrainingRecords,
                    'training_period_prop': Settings.StructuredTranscriptionTrainingPeriod,
                },
                title='Structured Text Target Accuracy',
                value=0.95,
            ),
            Parameter(
                name=Settings.StructuredTextAutomation,
                type='TranscriptionAutomation',
                schema={
                    **EXACT_PERCENT_SCHEMA,
                    'entity_type': FieldTypeByKind.ENTRY.value,
                    'target_accuracy_prop': Settings.StructuredTextTargetAccuracy,
                    'min_training_records_prop': Settings.StructuredTextMinTrainingRecords,
                    'training_period_prop': Settings.StructuredTranscriptionTrainingPeriod,
                },
                title='Structured Text Automation',
                description=(
                    'This number shows the amount of automation you will get based on the '
                    'target accuracy.'
                ),
                value=0,
                ui={'disabled': True},
            ),
            Parameter(
                name=Settings.StructuredTextThreshold,
                type='TranscriptionThreshold',
                schema={
                    'type': 'number',
                    'minimum': 0,
                    'maximum': 1,
                    'entity_type': FieldTypeByKind.ENTRY.value,
                    'target_accuracy_prop': Settings.StructuredTextTargetAccuracy,
                    'training_period_prop': Settings.StructuredTranscriptionTrainingPeriod,
                },
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
                type='TranscriptionTargetAccuracy',
                schema={
                    **EXACT_PERCENT_SCHEMA,
                    'entity_type': FieldTypeByKind.CHECKBOX.value,
                    'min_training_records_prop': Settings.StructuredCheckboxMinTrainingRecords,
                    'training_period_prop': Settings.StructuredTranscriptionTrainingPeriod,
                },
                title='Structured Checkbox Target Accuracy',
                value=0.95,
            ),
            Parameter(
                name=Settings.StructuredCheckboxAutomation,
                type='TranscriptionAutomation',
                schema={
                    **EXACT_PERCENT_SCHEMA,
                    'entity_type': FieldTypeByKind.CHECKBOX.value,
                    'target_accuracy_prop': Settings.StructuredCheckboxTargetAccuracy,
                    'min_training_records_prop': Settings.StructuredCheckboxMinTrainingRecords,
                    'training_period_prop': Settings.StructuredTranscriptionTrainingPeriod,
                },
                title='Structured Checkbox Automation',
                description=(
                    'This number shows the amount of automation you will get based on the '
                    'target accuracy.'
                ),
                value=0,
                ui={'disabled': True},
            ),
            Parameter(
                name=Settings.StructuredCheckboxThreshold,
                type='TranscriptionThreshold',
                schema={
                    'type': 'number',
                    'minimum': 0,
                    'maximum': 1,
                    'entity_type': FieldTypeByKind.CHECKBOX.value,
                    'target_accuracy_prop': Settings.StructuredCheckboxTargetAccuracy,
                    'training_period_prop': Settings.StructuredTranscriptionTrainingPeriod,
                },
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
                type='TranscriptionTargetAccuracy',
                schema={
                    **EXACT_PERCENT_SCHEMA,
                    'entity_type': FieldTypeByKind.SIGNATURE.value,
                    'min_training_records_prop': Settings.StructuredSignatureMinTrainingRecords,
                    'training_period_prop': Settings.StructuredTranscriptionTrainingPeriod,
                },
                title='Structured Signature Target Accuracy',
                value=0.95,
            ),
            Parameter(
                name=Settings.StructuredSignatureAutomation,
                type='TranscriptionAutomation',
                schema={
                    **EXACT_PERCENT_SCHEMA,
                    'entity_type': FieldTypeByKind.SIGNATURE.value,
                    'target_accuracy_prop': Settings.StructuredSignatureTargetAccuracy,
                    'min_training_records_prop': Settings.StructuredSignatureMinTrainingRecords,
                    'training_period_prop': Settings.StructuredTranscriptionTrainingPeriod,
                },
                title='Structured Signature Automation',
                description=(
                    'This number shows the amount of automation you will get based on the '
                    'target accuracy.'
                ),
                value=0,
                ui={'disabled': True},
            ),
            Parameter(
                name=Settings.StructuredSignatureThreshold,
                type='TranscriptionThreshold',
                schema={
                    'type': 'number',
                    'minimum': 0,
                    'maximum': 1,
                    'entity_type': FieldTypeByKind.SIGNATURE.value,
                    'target_accuracy_prop': Settings.StructuredSignatureTargetAccuracy,
                    'training_period_prop': Settings.StructuredTranscriptionTrainingPeriod,
                },
                title='Structured Signature Threshold',
                value=0.99,
            ),
            Parameter(
                name=Settings.StructuredSignatureMinLegThreshold,
                type='number',
                schema={'type': 'number', 'minimum': 0, 'maximum': 1},
                title='Structured Signature Minimum Legibility Threshold',
            ),
        ]
        semistructured_document_transcription_inputs = [
            Parameter(
                name=Settings.SemiStructuredTranscriptionTraining,
                type='TranscriptionAutomationTraining',
                schema={
                    'type': 'boolean',
                    'training_type': FinetuningConfig.SEMI_STRUCTURED_TRAINING_TYPE,
                },
                value=True,
                title='Transcription Automation Training',
                description=(
                    'Uses QA data for on-premise machine learning'
                    ' to improve transcription automation.'
                ),
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredTranscriptionTrainingPeriod,
                type='integer',
                schema={'type': 'integer', 'minimum': 0},
                value=30,
                title='Period of records to use',
                ui={'prefix': 'Past', 'suffix': 'days'},
                dependencies=[
                    Dependency(
                        condition={
                            'properties': {
                                Settings.SemiStructuredTranscriptionTraining: {'const': False}
                            }
                        },
                        override={
                            'ui': {
                                'na_reason': (
                                    'Not applied when Transcription Automation Training'
                                    ' is disabled.'
                                )
                            }
                        },
                    )
                ]
                + FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredImprovedTranscrThresholdAccuracy,
                type='boolean',
                value=True,
                title='Improved threshold accuracy',
                dependencies=[
                    Dependency(
                        condition={
                            'properties': {
                                Settings.SemiStructuredTranscriptionTraining: {'const': False}
                            }
                        },
                        override={
                            'ui': {
                                'na_reason': (
                                    'Not applied when Transcription Automation Training'
                                    ' is disabled.'
                                )
                            }
                        },
                    )
                ]
                + FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredTextMinTrainingRecords,
                type='integer',
                schema={'type': 'integer', 'minimum': 0},
                title='Semi-Structured Text Min Training Records',
                value=2000,
                ui={'hidden': True},
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredTextMaxTrainingRecords,
                type='integer',
                schema={'type': 'integer', 'minimum': 0},
                title='Semi-Structured Text Max Training Records',
                value=50000,
                ui={'hidden': True},
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredTextTargetAccuracy,
                type='TranscriptionTargetAccuracy',
                schema={
                    **EXACT_PERCENT_SCHEMA,
                    'entity_type': FieldTypeByKind.FLEX_ENTRY.value,
                    'min_training_records_prop': Settings.SemiStructuredTextMinTrainingRecords,
                    'training_period_prop': Settings.SemiStructuredTranscriptionTrainingPeriod,
                },
                title='Semi-Structured Text Target Accuracy',
                value=0.95,
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredTextAutomation,
                type='TranscriptionAutomation',
                schema={
                    **EXACT_PERCENT_SCHEMA,
                    'entity_type': FieldTypeByKind.FLEX_ENTRY.value,
                    'target_accuracy_prop': Settings.SemiStructuredTextTargetAccuracy,
                    'min_training_records_prop': Settings.SemiStructuredTextMinTrainingRecords,
                    'training_period_prop': Settings.SemiStructuredTranscriptionTrainingPeriod,
                },
                title='Semi-Structured Text Automation',
                description=(
                    'This number shows the amount of automation you will get based on the '
                    'target accuracy.'
                ),
                value=0,
                ui={'disabled': True},
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredTextThreshold,
                type='TranscriptionThreshold',
                schema={
                    'type': 'number',
                    'minimum': 0,
                    'maximum': 1,
                    'entity_type': FieldTypeByKind.FLEX_ENTRY.value,
                    'target_accuracy_prop': Settings.SemiStructuredTextTargetAccuracy,
                    'training_period_prop': Settings.SemiStructuredTranscriptionTrainingPeriod,
                },
                title='Semi-Structured Text Threshold',
                value=0.52,
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredTextMinLegThreshold,
                type='number',
                schema={'type': 'number', 'minimum': 0, 'maximum': 1},
                title='Semi-Structured Text Minimum Legibility Threshold',
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredTableMinTrainingRecords,
                type='integer',
                schema={'type': 'integer', 'minimum': 0},
                title='Table Min Training Records',
                value=2000,
                ui={'hidden': True},
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredTableMaxTrainingRecords,
                type='integer',
                schema={'type': 'integer', 'minimum': 0},
                title='Table Max Training Records',
                value=50000,
                ui={'hidden': True},
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredTableTargetAccuracy,
                type='TranscriptionTargetAccuracy',
                schema={
                    **EXACT_PERCENT_SCHEMA,
                    'entity_type': FieldTypeByKind.FLEX_TABLE_ENTRY.value,
                    'min_training_records_prop': Settings.SemiStructuredTableMinTrainingRecords,
                    'training_period_prop': Settings.SemiStructuredTranscriptionTrainingPeriod,
                },
                title='Table Target Accuracy',
                value=0.95,
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredTableAutomation,
                type='TranscriptionAutomation',
                schema={
                    **EXACT_PERCENT_SCHEMA,
                    'entity_type': FieldTypeByKind.FLEX_TABLE_ENTRY.value,
                    'target_accuracy_prop': Settings.SemiStructuredTableTargetAccuracy,
                    'min_training_records_prop': Settings.SemiStructuredTableMinTrainingRecords,
                    'training_period_prop': Settings.SemiStructuredTranscriptionTrainingPeriod,
                },
                title='Table Automation',
                description=(
                    'This number shows the amount of automation you will get based on the '
                    'target accuracy.'
                ),
                value=0,
                ui={'disabled': True},
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredTableThreshold,
                type='TranscriptionThreshold',
                schema={
                    'type': 'number',
                    'minimum': 0,
                    'maximum': 1,
                    'entity_type': FieldTypeByKind.FLEX_TABLE_ENTRY.value,
                    'target_accuracy_prop': Settings.SemiStructuredTableTargetAccuracy,
                    'training_period_prop': Settings.SemiStructuredTranscriptionTrainingPeriod,
                },
                title='Table Threshold',
                value=0.52,
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredTableMinLegThreshold,
                type='number',
                schema={'type': 'number', 'minimum': 0, 'maximum': 1},
                title='Table Minimum Legibility Threshold',
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredCheckboxMinTrainingRecords,
                type='integer',
                schema={'type': 'integer', 'minimum': 0},
                title='Semi-Structured Checkbox Min Training Records',
                value=2000,
                ui={'hidden': True},
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredCheckboxMaxTrainingRecords,
                type='integer',
                schema={'type': 'integer', 'minimum': 0},
                title='Semi-Structured Checkbox Max Training Records',
                value=50000,
                ui={'hidden': True},
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredCheckboxTargetAccuracy,
                type='TranscriptionTargetAccuracy',
                schema={
                    **EXACT_PERCENT_SCHEMA,
                    'entity_type': FieldTypeByKind.FLEX_CHECKBOX.value,
                    'min_training_records_prop': (
                        Settings.SemiStructuredCheckboxMinTrainingRecords
                    ),
                    'training_period_prop': Settings.SemiStructuredTranscriptionTrainingPeriod,
                },
                title='Semi-Structured Checkbox Target Accuracy',
                value=0.95,
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredCheckboxAutomation,
                type='TranscriptionAutomation',
                schema={
                    **EXACT_PERCENT_SCHEMA,
                    'entity_type': FieldTypeByKind.FLEX_CHECKBOX.value,
                    'target_accuracy_prop': Settings.SemiStructuredCheckboxTargetAccuracy,
                    'min_training_records_prop': (
                        Settings.SemiStructuredCheckboxMinTrainingRecords
                    ),
                    'training_period_prop': Settings.SemiStructuredTranscriptionTrainingPeriod,
                },
                title='Semi-Structured Checkbox Automation',
                description=(
                    'This number shows the amount of automation you will get based on the '
                    'target accuracy.'
                ),
                value=0,
                ui={'disabled': True},
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredCheckboxThreshold,
                type='TranscriptionThreshold',
                schema={
                    'type': 'number',
                    'minimum': 0,
                    'maximum': 1,
                    'entity_type': FieldTypeByKind.FLEX_CHECKBOX.value,
                    'target_accuracy_prop': Settings.SemiStructuredCheckboxTargetAccuracy,
                    'training_period_prop': Settings.SemiStructuredTranscriptionTrainingPeriod,
                },
                title='Semi-Structured Checkbox Threshold',
                value=0.56,
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
            Parameter(
                name=Settings.SemiStructuredCheckboxMinLegThreshold,
                type='number',
                schema={'type': 'number', 'minimum': 0, 'maximum': 1},
                title='Semi-Structured Checkbox Minimum Legibility Threshold',
                dependencies=FeatureGatingCommonDependencies.SemiStructured,
            ),
        ]
        flexible_extraction_inputs = [
            Parameter(
                name=Settings.FlexibleExtractionNotificationWorkflow,
                type='FlowIdentifier',
                value=None,
                title='Flexible Extraction Notification Flow',
                type_spec={'filter_roles': ['notifications'], 'label': 'If task needed'},
                optional=True,
            ),
            Parameter(
                name=Settings.FlexibleExtractionSupervisionTranscriptionMasking,
                type='boolean',
                value=True,
                title='Flexible Extraction Transcription Masking',
                description=(
                    'Prevents users from inputting invalid characters during'
                    ' the Flexible Extraction task.'
                ),
            ),
            Parameter(
                name=Settings.FlexibleExtractionTaskRestrictions,
                type='TaskRestrictions',
                title='Default Task Restrictions',
                description=(
                    'Defines what users can access Supervision tasks created by this block.'
                ),
                optional=True,
            ),
        ]
        document_rendering_inputs = [
            Parameter(
                name=Settings.DocumentRenderingEnabled,
                type='boolean',
                title='Document Rendering Enabled',
                description='Enable document rendering',
                value=False,
                ui={
                    'warning': (
                        'Enabling document rendering will result in a higher compute utilization '
                        'and require more storage for storing all documents.'
                    )
                },
                dependencies=[FeatureGatingCommonDependencies.DocumentRendererEnabled],
            ),
            Parameter(
                name=Settings.DocumentRenderingMimeType,
                type='string',
                value=PDF_MIME_TYPE,
                title='Rendered Document Format',
                schema={
                    'type': 'string',
                    'oneOf': [
                        {
                            'title': 'PDF',
                            'const': 'application/pdf',
                        }
                    ],
                },
                description=(
                    'Format in which the document will be rendered. Currently only PDF is '
                    'supported.'
                ),
                # At the moment, there is only one option available, so we hide it.
                # If more options are added, this should be removed and
                # `dependencies=[document_rendering_common_dependency]` should be added.
                ui={'hidden': True},
                dependencies=document_rendering_common_dependencies,
            ),
            Parameter(
                name=Settings.DocumentRenderingUnit,
                type='number',
                title='Document Measurement Unit',
                description='Unit of measurement for the document rendering.',
                schema={
                    'type': 'string',
                    'oneOf': [
                        {
                            'title': 'Inches',
                            'const': INCHES,
                        },
                        {
                            'title': 'Millimeters',
                            'const': MILLIMETERS,
                        },
                    ],
                },
                value=INCHES,
                dependencies=document_rendering_common_dependencies,
            ),
            Parameter(
                name=Settings.DocumentRenderingWidth,
                type='number',
                title='Document Width',
                description='Width of the rendered document.',
                schema={'type': 'number', 'minimum': 0, 'maximum': 600},
                dependencies=document_rendering_common_dependencies
                + [
                    Dependency(
                        condition={
                            'properties': {Settings.DocumentRenderingUnit: {'const': INCHES}}
                        },
                        override={'value': LETTER_WIDTH_IN_INCHES},
                    ),
                    Dependency(
                        condition={
                            'properties': {Settings.DocumentRenderingUnit: {'const': MILLIMETERS}}
                        },
                        override={'value': LETTER_WIDTH_IN_MM},
                    ),
                ],
                optional=True,
                value=LETTER_WIDTH_IN_INCHES,
            ),
            Parameter(
                name=Settings.DocumentRenderingHeight,
                type='number',
                title='Document Height',
                description='Height of the rendered document.',
                schema={'type': 'number', 'minimum': 0, 'maximum': 600},
                dependencies=document_rendering_common_dependencies
                + [
                    Dependency(
                        condition={
                            'properties': {Settings.DocumentRenderingUnit: {'const': INCHES}}
                        },
                        override={'value': LETTER_HEIGHT_IN_INCHES},
                    ),
                    Dependency(
                        condition={
                            'properties': {Settings.DocumentRenderingUnit: {'const': MILLIMETERS}}
                        },
                        override={'value': LETTER_HEIGHT_IN_MM},
                    ),
                ],
                optional=True,
                value=LETTER_HEIGHT_IN_INCHES,
            ),
            Parameter(
                name=Settings.DocumentRenderingQuality,
                type='integer',
                title='Quality',
                description='Quality of pages (images) appended to the resulting document as a '
                'percentage (recommended 50%). Higher quality results in a larger '
                'file size for the generated PDF.',
                schema={'type': 'number', 'minimum': 5, 'maximum': 100},
                value=DEFAULT_QUALITY,
                optional=True,
                dependencies=document_rendering_common_dependencies,
            ),
        ]

        if not roles:
            roles = ['read_only', 'supporting', 'idp_core']
        mandatory_roles = {'supporting', 'idp_core'}
        roles = list(set(roles) | mandatory_roles)

        super().__init__(
            identifier=flow_identifier,
            roles=roles,
            enable_overrides=True,
            input=[
                Parameter(
                    name=Settings.LayoutReleaseUuid, type='ReleaseUUID', title='Layout Release'
                ),
                *system_provided_inputs,
                *submission_bootstrap_inputs,
                *machine_collation_inputs,
                *classification_inputs,
                *identification_inputs,
                *general_transcription_inputs,
                *structured_document_transcription_inputs,
                *semistructured_document_transcription_inputs,
                *flexible_extraction_inputs,
                *document_rendering_inputs,
            ],
            ui={
                'icon': icon_path_to_base64(os.path.join(BASE_DIR, 'icon.png')),
                'groups': [
                    {
                        'title': 'Submission Bootstrap',
                        'fields': [
                            Settings.SubmissionBootstrapNotificationWorkflow,
                            Settings.SubmissionBootstrapS3Config,
                            Settings.SubmissionBootstrapS3EndpointUrl,
                            Settings.SubmissionBootstrapOCSConfig,
                            Settings.SubmissionBootstrapHTTPConfig,
                            Settings.SubmissionBootstrapABSAuthType,
                            Settings.SubmissionBootstrapABSAccountUrl,
                            Settings.SubmissionBootstrapABSTenantId,
                            Settings.SubmissionBootstrapABSClientId,
                            Settings.SubmissionBootstrapABSClientSecret,
                            Settings.SubmissionBootstrapABSAuthorityHost,
                            Settings.SubmissionBootstrapABSAccountKey,
                            Settings.SubmissionBootstrapABSAccountName,
                        ],
                    },
                    {
                        'title': 'Collation',
                        'fields': [
                            Settings.CollationDedupeFiles,
                            Settings.CollationRetentionPeriod,
                            Settings.CollationRefreshRetentionPeriod,
                        ],
                    },
                    {
                        'title': 'Classification',
                        'fields': [
                            Settings.StructuredLayoutMatchThreshold,
                            Settings.SemiStructuredClassification,
                            Settings.ManualNlcEnabled,
                            Settings.SemiTargetAccuracy,
                            Settings.SemiDocGroupingLogic,
                            Settings.SemiQaSampleRate,
                            Settings.RotationCorrectionEnabled,
                            Settings.MobileProcessingEnabled,
                            Settings.FileTranscriptionEnabled,
                            Settings.ManualClassificationNotificationWorkflow,
                            Settings.ManualClassificationTaskRestrictions,
                            Settings.LayoutIdDealbreaker,
                            Settings.LayoutIdDealbreakerBypass,
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
                            Settings.ManualFieldIdNotificationWorkflow,
                            Settings.ManualFieldIdTaskRestrictions,
                        ],
                    },
                    {
                        'title': 'General Transcription',
                        'fields': [
                            Settings.FieldTranscriptionTargetAccuracies,
                            Settings.ManualTranscriptionEnabled,
                            Settings.TranscriptionQaEnabled,
                            Settings.AutoQaSamplingRateEnabled,
                            Settings.TranscriptionStructuredEntryQaSampleRate,
                            Settings.TranscriptionStructuredCheckboxQaSampleRate,
                            Settings.TranscriptionStructuredSignatureQaSampleRate,
                            Settings.TranscriptionSemiStructuredQaSampleRate,
                            Settings.TableCellTranscriptionQaEnabled,
                            Settings.TableCellTranscriptionQaSampleRate,
                            Settings.TranscriptionOverrides,
                            Settings.FinetuningOnlyTrainedLayouts,
                            Settings.ExcludeAutoTranscribeFieldsFromQA,
                            Settings.ManualTranscriptionNotificationWorkflow,
                            Settings.ManualTranscriptionTaskRestrictions,
                            Settings.ManualTranscriptionSupervisionTranscriptionMasking,
                            Settings.ManualTranscriptionTableOutputManualReview,
                            Settings.ManualTranscriptionAlwaysSuperviseBlankCells,
                            Settings.ForceNormalizationErrorsToSV,
                            Settings.ForceRequiredEntriesToSV,
                        ],
                    },
                    {
                        'title': 'Structured Document Transcription',
                        'fields': [
                            Settings.StructuredTranscriptionTraining,
                            Settings.StructuredTranscriptionTrainingPeriod,
                            Settings.StructuredImprovedTranscrThresholdAccuracy,
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
                        ],
                    },
                    {
                        'title': 'Semi-Structured Document Transcription',
                        'fields': [
                            Settings.SemiStructuredTranscriptionTraining,
                            Settings.SemiStructuredTranscriptionTrainingPeriod,
                            Settings.SemiStructuredImprovedTranscrThresholdAccuracy,
                            Settings.SemiStructuredTextMinTrainingRecords,
                            Settings.SemiStructuredTextMaxTrainingRecords,
                            Settings.SemiStructuredTextTargetAccuracy,
                            Settings.SemiStructuredTextAutomation,
                            Settings.SemiStructuredTextThreshold,
                            Settings.SemiStructuredTextMinLegThreshold,
                            Settings.SemiStructuredTableMinTrainingRecords,
                            Settings.SemiStructuredTableMaxTrainingRecords,
                            Settings.SemiStructuredTableTargetAccuracy,
                            Settings.SemiStructuredTableAutomation,
                            Settings.SemiStructuredTableThreshold,
                            Settings.SemiStructuredTableMinLegThreshold,
                            Settings.SemiStructuredCheckboxMinTrainingRecords,
                            Settings.SemiStructuredCheckboxMaxTrainingRecords,
                            Settings.SemiStructuredCheckboxTargetAccuracy,
                            Settings.SemiStructuredCheckboxAutomation,
                            Settings.SemiStructuredCheckboxThreshold,
                            Settings.SemiStructuredCheckboxMinLegThreshold,
                        ],
                    },
                    {
                        'title': 'Flexible Extraction',
                        'fields': [
                            Settings.FlexibleExtractionNotificationWorkflow,
                            Settings.FlexibleExtractionSupervisionTranscriptionMasking,
                            Settings.FlexibleExtractionTaskRestrictions,
                        ],
                    },
                    {
                        'title': 'Document Rendering',
                        'fields': [
                            Settings.DocumentRenderingEnabled,
                            Settings.DocumentRenderingMimeType,
                            Settings.DocumentRenderingUnit,
                            Settings.DocumentRenderingWidth,
                            Settings.DocumentRenderingHeight,
                            Settings.DocumentRenderingQuality,
                        ],
                    },
                ],
            },
            output=[
                Parameter(
                    name='submission',
                    type='Submission',
                    title='Submission',
                    description='The processed submission',
                )
            ],
        ),
