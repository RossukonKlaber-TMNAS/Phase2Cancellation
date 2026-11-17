from typing import Any, Dict, List, Optional, Sequence, Union

from flows_sdk.blocks import Block, IOBlock, Outputs
from flows_sdk.implementations.idp_v33.idp_values import (
    IDP_OUTPUT_ROLE,
    IDP_SUBMISSION_NOTIFY_NAME,
    OCS_SECRET_KEY,
    S3_SECRET_KEY,
    HttpHeaderAuthorizationParams,
    Inputs,
    OAuth2AuthorizationParams,
    Settings,
)
from flows_sdk.utils import system_secret, workflow_input


class SubmissionBootstrapBlock(Block):
    """Submission bootstrap block initializes the submission object and prepares external images
    or other submission data if needed.

    **This block should be called at the START of every flow** that
    uses blocks included in the ``flows_sdk.implementations.idp_v33`` library.

    Mandatory parameters:

    :param reference_name: unique identifier within a flow

    Parameters with defaults:

    :param layout_release_uuid: Layout Release UUID at submission creation time,
        defaults to workflow_input(Settings.LayoutReleaseUuid)
    :param s3_config: Specify Amazon S3 credentials for submission retrieval store.
        Expects a json expression: ``{"aws_access_key_id": "X", "aws_secret_access_key": "Y"}``,
        defaults to system_secret(S3_SECRET_KEY)
    :param s3_endpoint_url: Endpoint URL for S3 submission retrieval store, defaults to None
    :param ocs_config: OCS Configuration for downloading submission data,
        defaults to system_secret(OCS_SECRET_KEY)
    :param http_config:
        An optional system secret field expressing the HTTP Configuration for
        downloading submission data. The content is expected to be a json formatted as:
        ``{"username": "X", "password": "Y", "ssl_cert": "CA bundle filename"}``,
        defaults to None
    :param notification_workflow: Notification flow name to run when the submission is initialized,
        defaults to IDP_SUBMISSION_NOTIFY_NAME
    :param workflow_uuid: UUID of the triggered workflow version,
        defaults to workflow_input(Inputs.WorkflowUuid)
    :param workflow_name: Name of the triggered workflow,
        defaults to workflow_input(Inputs.WorkflowName)
    :param workflow_version: Version of the triggered workflow,
        defaults to workflow_input(Inputs.WorkflowVersion)

    Example usage::

        submission_bootstrap = SubmissionBootstrapBlock(reference_name='submission_bootstrap')

    """

    def __init__(
        self,
        reference_name: Optional[str] = None,
        layout_release_uuid: str = workflow_input(Settings.LayoutReleaseUuid),
        s3_config: str = system_secret(S3_SECRET_KEY),
        s3_endpoint_url: Optional[str] = None,
        ocs_config: str = system_secret(OCS_SECRET_KEY),
        http_config: Optional[str] = None,
        notification_workflow: str = IDP_SUBMISSION_NOTIFY_NAME,
        workflow_uuid: str = workflow_input(Inputs.WorkflowUuid),
        workflow_name: str = workflow_input(Inputs.WorkflowName),
        workflow_version: str = workflow_input(Inputs.WorkflowVersion),
    ) -> None:
        super().__init__(
            identifier='SUBMISSION_BOOTSTRAP_2',
            reference_name=reference_name,
            input={
                '$trigger': workflow_input(Inputs.Trigger),
                'layout_release_uuid': layout_release_uuid,
                's3_config': s3_config,
                's3_endpoint_url': s3_endpoint_url,
                'ocs_config': ocs_config,
                'http_config': http_config,
                'notification_workflow': notification_workflow,
                'workflow_uuid': workflow_uuid,
                'workflow_name': workflow_name,
                'workflow_version': workflow_version,
            },
            title='Submission Initialization',
            description='Initialize submission and, if necessary, fetch and prepare '
            'external images or other submission data',
        )

    def output(self, key: Optional[str] = None) -> str:
        """
        Submission bootstrap ends with a CodeBlock, which nests the actual outputs under
        the 'result' key. This method overrides the default output in the same manner that
        :py:class:`flows_sdk.blocks.Routing.CodeBlock` does for convenience.

        :param key: Optionally provide a key to directly get a nested property.
            When not provided, the entire 'result' will be returned.

            For example, we have::

                {
                    "result": {
                        "a": {
                            "b": 42
                        }
                    }
                }

            - skipping the key ``output()` will return ``{"a": {"b": 42}}``
            - calling with ``output("a")`` will result in ``{"b": 42}``
            - calling with ``output("a.b")`` will return ``42``
        :return: the value under the provided key
        """
        return super().output('result' + ('' if not key else '.' + key))


class MachineCollationBlock(Block):
    """Machine collation block groups files, documents and pages (from the submission) into cases

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param submission: Submission object
    :param cases: This parameter accepts an array of JSON objects that contain information on
        how Cases should be created. There are two ways to collate a case: by the filenames
        specified in the current Submission, or by the ids of the Documents or Pages submitted
        in previous submissions.

        This parameter follows the given format::

            {
                'cases': [
                    'external_case_id': 'HS-1',
                    'filename': 'file1.pdf',
                    'documents': [42],
                    'pages': [43]
                ]
            }

    Parameters with defaults:

    :param dedupe_files: Enabling this setting will replace case data from repeated file names
        within the same case. Cases will retain data from the most recently submitted version of
        a particular file. Note that this setting does not delete the old data, it just removes it
        from the case. Keep in mind this option is only relevant when adding to cases
    :param remove_from_cases: This parameter accepts an array of JSON objects that contains
        information on how documents or pages should be removed from a pre-existing case.
        Currently, the only way to de-collate from a case is by the ids of the Documents or
        Pages within a given case

        This parameter follows the given format::

            {
                'remove_from_cases': [
                    'external_case_id': 'HS-1',
                    'documents': [42],
                    'pages': [43]
                ]
            }

    Example usage::

        machine_collation = MachineCollationBlock(
            reference_name='machine_collation',
            submission=submission_bootstrap.output('result.submission'),
            cases=submission_bootstrap.output('result.api_params.cases'),
            dedupe_files=True,
            remove_from_cases=custom_supervision.output('remove_from_cases')
        )

    """

    def __init__(
        self,
        submission: Any,
        cases: Any,
        dedupe_files: bool = False,
        remove_from_cases: Optional[Any] = None,
        reference_name: Optional[str] = None,
    ) -> None:

        super().__init__(
            identifier='MACHINE_COLLATION_2',
            reference_name=reference_name,
            input={
                'submission': submission,
                'cases': cases,
                'dedupe_files': dedupe_files,
                'remove_from_cases': remove_from_cases,
            },
            title='Machine Collation',
            description='Group files, documents, and pages into cases',
        )


class MachineClassificationBlock(Block):
    """Machine classification block automatically matches documents to structured,
    semi-structured or additional layouts

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param submission: Submission object
    :param api_params:

    Parameters with defaults:

    :param rotation_correction_enabled: Identifies and corrects the orientation of
        semi-structured images,
        defaults to True
    :param mobile_processing_enabled: Improves the machine readability of photo
        captured documents,
        defaults to False
    :param layout_release_uuid: Layout Release UUID at submission creation time,
        defaults to workflow_input(Settings.LayoutReleaseUuid)
    :param vpc_registration_threshold: Structured pages above this threshold will be
        automatically matched to a layout variation,
        defaults to workflow_input(Settings.StructuredLayoutMatchThreshold)
    :param nlc_enabled: Enables workflow to manage a model for automated classification
        of semi-structured and additional layout variations,
        defaults to workflow_input(Settings.SemiStructuredClassification)
    :param nlc_target_accuracy: defaults to workflow_input(Settings.SemiTargetAccuracy)
    :param nlc_doc_grouping_logic: Logic to handle multiple pages matched to the same
        layout variationin a given submission,
        defaults to workflow_input(Settings.SemiDocGroupingLogic)

    Example usage::

        machine_classification = MachineClassificationBlock(
            reference_name='machine_classification',
            submission=case_collation.output('submission'),
            api_params=submission_bootstrap.output('result.api_params'),
            rotation_correction_enabled=idp_wf_config.rotation_correction_enabled,
        )

    """

    def __init__(
        self,
        submission: Any,
        api_params: Any,
        reference_name: Optional[str] = None,
        rotation_correction_enabled: bool = True,
        mobile_processing_enabled: bool = False,
        layout_release_uuid: str = workflow_input(Settings.LayoutReleaseUuid),
        vpc_registration_threshold: str = workflow_input(Settings.StructuredLayoutMatchThreshold),
        nlc_enabled: str = workflow_input(Settings.SemiStructuredClassification),
        nlc_target_accuracy: str = workflow_input(Settings.SemiTargetAccuracy),
        nlc_doc_grouping_logic: str = workflow_input(Settings.SemiDocGroupingLogic),
    ) -> None:
        super().__init__(
            identifier='MACHINE_CLASSIFICATION_2',
            reference_name=reference_name,
            input={
                'submission': submission,
                'api_params': api_params,
                'layout_release_uuid': layout_release_uuid,
                'vpc_registration_threshold': vpc_registration_threshold,
                'nlc_enabled': nlc_enabled,
                'nlc_target_accuracy': nlc_target_accuracy,
                'nlc_doc_grouping_logic': nlc_doc_grouping_logic,
                'rotation_correction_enabled': rotation_correction_enabled,
                'mobile_processing_enabled': mobile_processing_enabled,
            },
            title='Machine Classification',
            description='Automatically classify documents',
        )


class ManualClassificationBlock(Block):
    """Manual classification block allows keyers to manually match submissions to their layouts.
    Keyers may perform manual classification if machine classification cannot automatically
    match a submission to a layout with high confidence

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param submission: Submission object
    :param api_params:

    Parameters with defaults:

    :param layout_release_uuid: Layout Release UUID at submission creation time,
        defaults to workflow_input(Settings.LayoutReleaseUuid)
    :param manual_nlc_enabled: Enables manual classification when applicable,
        defaults to workflow_input(Settings.ManualNlcEnabled)
    :param task_restrictions: Defines what users can access Supervision tasks created
        by this block,
        defaults to None
    :param notification_workflow: Notification flow name to run when the submission
        enters Manual Classification,
        defaults to IDP_SUBMISSION_NOTIFY_NAME

    Example usage::

        manual_classification = ManualClassificationBlock(
            reference_name='manual_classification',
            submission=machine_classification.output('submission'),
            api_params=submission_bootstrap.output('result.api_params'),
        )

    """

    def __init__(
        self,
        submission: Any,
        api_params: Any,
        reference_name: Optional[str] = None,
        layout_release_uuid: str = workflow_input(Settings.LayoutReleaseUuid),
        manual_nlc_enabled: str = workflow_input(Settings.ManualNlcEnabled),
        task_restrictions: Optional[List[Any]] = None,
        notification_workflow: str = IDP_SUBMISSION_NOTIFY_NAME,
    ) -> None:
        if task_restrictions is None:
            task_restrictions = []
        super().__init__(
            identifier='MANUAL_CLASSIFICATION_2',
            reference_name=reference_name,
            input={
                'layout_release_uuid': layout_release_uuid,
                'manual_nlc_enabled': manual_nlc_enabled,
                'task_restrictions': task_restrictions,
                'api_params': api_params,
                'submission': submission,
                'notification_workflow': notification_workflow,
            },
            title='Manual Classification',
            description='Manually classify documents that could not be automatically classified',
        )


class MachineIdentificationBlock(Block):
    """Machine identification automatically identify fields and tables in the submission

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param submission: Submission object
    :param api_params:

    Parameters with defaults:

    :param manual_field_id_enabled: Enables manual identification when applicable,
        defaults to workflow_input(Settings.ManualFieldIdEnabled)
    :param field_id_target_accuracy: Field ID Target Accuracy,
        defaults to workflow_input(Settings.FieldIdTargetAccuracy)
    :param table_id_target_accuracy: Table ID Target Accuracy,
        defaults to workflow_input(Settings.TableIdTargetAccuracy)

    Example usage::

        machine_identification = MachineIdentificationBlock(
            reference_name='machine_identification',
            submission=manual_classification.output('submission'),
            api_params=submission_bootstrap.output('result.api_params'),
        )

    """

    def __init__(
        self,
        submission: Any,
        api_params: Any,
        reference_name: Optional[str] = None,
        manual_field_id_enabled: str = workflow_input(Settings.ManualFieldIdEnabled),
        field_id_target_accuracy: str = workflow_input(Settings.FieldIdTargetAccuracy),
        table_id_target_accuracy: str = workflow_input(Settings.TableIdTargetAccuracy),
    ) -> None:
        super().__init__(
            identifier='MACHINE_IDENTIFICATION_3',
            reference_name=reference_name,
            input={
                'submission': submission,
                'api_params': api_params,
                'manual_field_id_enabled': manual_field_id_enabled,
                'field_id_target_accuracy': field_id_target_accuracy,
                'table_id_target_accuracy': table_id_target_accuracy,
            },
            title='Machine Identification',
            description='Automatically locate fields on semi-structured documents',
        )


class ManualIdentificationBlock(Block):
    """Manual identification allows keyers to complete field identification or table identification
    tasks, where they draw bounding boxes around the contents of certain fields, table columns
    or table rows. This identification process ensures that the system will be able to
    transcribe the correct content in the upcoming transcription process

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param submission: Submission object
    :param api_params:

    Parameters with defaults:

    :param task_restrictions: Defines what users can access Supervision tasks created
        by this block,
        defaults to []
    :param manual_field_id_enabled: Enables manual identification when applicable,
        defaults to workflow_input(Settings.ManualFieldIdEnabled)
    :param layout_release_uuid: Layout Release UUID at submission creation time,
        defaults to workflow_input(Settings.LayoutReleaseUuid)
    :param notification_workflow: Notification flow name to run when the submission
        enters Manual Identification,
        defaults to IDP_SUBMISSION_NOTIFY_NAME

    Example usage::

        manual_identification = ManualIdentificationBlock(
            reference_name='manual_identification',
            submission=machine_identification.output('submission'),
            api_params=submission_bootstrap.output('result.api_params'),
            task_restrictions=idp_wf_config.manual_identification_config.task_restrictions,
        )

    """

    def __init__(
        self,
        submission: Any,
        api_params: Any,
        reference_name: Optional[str] = None,
        task_restrictions: Optional[List[Any]] = None,
        manual_field_id_enabled: str = workflow_input(Settings.ManualFieldIdEnabled),
        layout_release_uuid: str = workflow_input(Settings.LayoutReleaseUuid),
        notification_workflow: str = IDP_SUBMISSION_NOTIFY_NAME,
    ) -> None:
        if task_restrictions is None:
            task_restrictions = []
        super().__init__(
            identifier='MANUAL_IDENTIFICATION_3',
            reference_name=reference_name,
            input={
                'submission': submission,
                'api_params': api_params,
                'manual_field_id_enabled': manual_field_id_enabled,
                'layout_release_uuid': layout_release_uuid,
                'notification_workflow': notification_workflow,
                'task_restrictions': task_restrictions,
            },
            title='Manual Identification',
            description='Manually locate fields on semi-structured documents that '
            'could not be automatically located',
        )


class MachineTranscriptionBlock(Block):
    """Machine transcription automatically transcribes the content of your submission

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param submission: Submission object
    :param api_params:

    Parameters with defaults:

    :param layout_release_uuid: Layout Release UUID at submission creation time,
        defaults to workflow_input(Settings.LayoutReleaseUuid)
    :param transcription_automation_training:
        defaults to workflow_input( Settings.TranscriptionAutomationTraining )
    :param transcription_model: The transcription model that will be used for this flow,
        defaults to workflow_input(Settings.TranscriptionModel)
    :param flex_confidence_boosting_enabled: Boosts semi-structured transcription confidence
        for repeated values.,
        defaults to workflow_input(Settings.SemiTranscriptionConfBoost)
    :param finetuning_only_trained_layouts:
        defaults to workflow_input( Settings.FinetuningOnlyTrainedLayouts )
    :param structured_text_target_accuracy:
        defaults to workflow_input( Settings.StructuredTextTargetAccuracy )
    :param structured_text_confidence_threshold:
        defaults to workflow_input( Settings.StructuredTextThreshold )
    :param structured_text_acceptable_confidence:
        defaults to workflow_input( Settings.StructuredTextMinLegThreshold )
    :param semi_structured_text_target_accuracy:
        defaults to workflow_input( Settings.SemiStructuredTextTargetAccuracy )
    :param semi_structured_text_confidence_threshold:
        defaults to workflow_input( Settings.SemiStructuredTextThreshold )
    :param semi_structured_text_acceptable_confidence:
        defaults to workflow_input( Settings.SemiStructuredTextMinLegThreshold )
    :param structured_checkbox_target_accuracy:
        defaults to workflow_input( Settings.StructuredCheckboxTargetAccuracy )
    :param structured_checkbox_confidence_threshold:
        defaults to workflow_input( Settings.StructuredCheckboxThreshold )
    :param structured_checkbox_acceptable_confidence:
        defaults to workflow_input( Settings.StructuredCheckboxMinLegThreshold )
    :param structured_signature_target_accuracy:
        defaults to workflow_input( Settings.StructuredSignatureTargetAccuracy )
    :param structured_signature_confidence_threshold:
        defaults to workflow_input( Settings.StructuredSignatureThreshold )
    :param structured_signature_acceptable_confidence:
        defaults to workflow_input( Settings.StructuredSignatureMinLegThreshold )
    :param semi_structured_checkbox_target_accuracy:
        defaults to workflow_input( Settings.SemiStructuredCheckboxTargetAccuracy )
    :param semi_structured_checkbox_confidence_threshold:
        defaults to workflow_input( Settings.SemiStructuredCheckboxThreshold )
    :param semi_structured_checkbox_acceptable_confidence:
        defaults to workflow_input( Settings.SemiStructuredCheckboxMinLegThreshold )

    Example usage::

        machine_transcription = MachineTranscriptionBlock(
            reference_name='machine_transcription',
            submission=manual_identification.output('submission'),
            api_params=submission_bootstrap.output('result.api_params'),
        )

    """

    def __init__(
        self,
        submission: Any,
        api_params: Any,
        reference_name: Optional[str] = None,
        layout_release_uuid: str = workflow_input(Settings.LayoutReleaseUuid),
        transcription_automation_training: str = workflow_input(
            Settings.TranscriptionAutomationTraining
        ),
        transcription_model: str = workflow_input(Settings.TranscriptionModel),
        flex_confidence_boosting_enabled: str = workflow_input(Settings.SemiTranscriptionConfBoost),
        finetuning_only_trained_layouts: str = workflow_input(
            Settings.FinetuningOnlyTrainedLayouts
        ),
        structured_text_target_accuracy: str = workflow_input(
            Settings.StructuredTextTargetAccuracy
        ),
        structured_text_confidence_threshold: str = workflow_input(
            Settings.StructuredTextThreshold
        ),
        structured_text_acceptable_confidence: str = workflow_input(
            Settings.StructuredTextMinLegThreshold
        ),
        semi_structured_text_target_accuracy: str = workflow_input(
            Settings.SemiStructuredTextTargetAccuracy
        ),
        semi_structured_text_confidence_threshold: str = workflow_input(
            Settings.SemiStructuredTextThreshold
        ),
        semi_structured_text_acceptable_confidence: str = workflow_input(
            Settings.SemiStructuredTextMinLegThreshold
        ),
        semi_structured_table_target_accuracy: str = workflow_input(
            Settings.SemiStructuredTableTargetAccuracy
        ),
        semi_structured_table_confidence_threshold: str = workflow_input(
            Settings.SemiStructuredTableThreshold
        ),
        semi_structured_table_acceptable_confidence: str = workflow_input(
            Settings.SemiStructuredTableMinLegThreshold
        ),
        structured_checkbox_target_accuracy: str = workflow_input(
            Settings.StructuredCheckboxTargetAccuracy
        ),
        structured_checkbox_confidence_threshold: str = workflow_input(
            Settings.StructuredCheckboxThreshold
        ),
        structured_checkbox_acceptable_confidence: str = workflow_input(
            Settings.StructuredCheckboxMinLegThreshold
        ),
        structured_signature_target_accuracy: str = workflow_input(
            Settings.StructuredSignatureTargetAccuracy
        ),
        structured_signature_confidence_threshold: str = workflow_input(
            Settings.StructuredSignatureThreshold
        ),
        structured_signature_acceptable_confidence: str = workflow_input(
            Settings.StructuredSignatureMinLegThreshold
        ),
        semi_structured_checkbox_target_accuracy: str = workflow_input(
            Settings.SemiStructuredCheckboxTargetAccuracy
        ),
        semi_structured_checkbox_confidence_threshold: str = workflow_input(
            Settings.SemiStructuredCheckboxThreshold
        ),
        semi_structured_checkbox_acceptable_confidence: str = workflow_input(
            Settings.SemiStructuredCheckboxMinLegThreshold
        ),
    ) -> None:
        # black does not honor the max 100 line long rule for k:v pairs like below
        # fmt: off
        super().__init__(
            identifier='MACHINE_TRANSCRIPTION_4',
            reference_name=reference_name,
            input={
                'layout_release_uuid': layout_release_uuid,
                'submission': submission,
                'api_params': api_params,
                'transcription_automation_training': transcription_automation_training,
                'transcription_model': transcription_model,
                'flex_confidence_boosting_enabled': flex_confidence_boosting_enabled,
                'finetuning_only_trained_layouts': finetuning_only_trained_layouts,
                'structured_text_target_accuracy': structured_text_target_accuracy,
                'structured_text_confidence_threshold': structured_text_confidence_threshold,
                'structured_text_acceptable_confidence': structured_text_acceptable_confidence,
                'semi_structured_text_target_accuracy': semi_structured_text_target_accuracy,
                'semi_structured_text_confidence_threshold':
                    semi_structured_text_confidence_threshold,
                'semi_structured_text_acceptable_confidence':
                    semi_structured_text_acceptable_confidence,
                'semi_structured_table_target_accuracy':
                    semi_structured_table_target_accuracy,
                'semi_structured_table_confidence_threshold':
                    semi_structured_table_confidence_threshold,
                'semi_structured_table_acceptable_confidence':
                    semi_structured_table_acceptable_confidence,
                'structured_checkbox_target_accuracy': structured_checkbox_target_accuracy,
                'structured_checkbox_confidence_threshold':
                    structured_checkbox_confidence_threshold,
                'structured_checkbox_acceptable_confidence':
                    structured_checkbox_acceptable_confidence,
                'structured_signature_target_accuracy': structured_signature_target_accuracy,
                'structured_signature_confidence_threshold':
                    structured_signature_confidence_threshold,
                'structured_signature_acceptable_confidence':
                    structured_signature_acceptable_confidence,
                'semi_structured_checkbox_target_accuracy':
                    semi_structured_checkbox_target_accuracy,
                'semi_structured_checkbox_confidence_threshold':
                    semi_structured_checkbox_confidence_threshold,
                'semi_structured_checkbox_acceptable_confidence':
                    semi_structured_checkbox_acceptable_confidence,
            },
            title='Machine Transcription',
            description='Automatically transcribe fields',
        )
        # fmt: on


class ManualTranscriptionBlock(Block):
    """Manual transcription lets your keyers manually enter the text found in fields or tables
    that could not be automatically transcribed

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param submission: Submission object
    :param api_params:

    Parameters with defaults:

    :param supervision_transcription_masking: Prevents users from inputting invalid
        characters during Supervision Transcription tasks,
        defaults to True
    :param table_output_manual_review: Always generates a table transcription task if the
        layout contains a table. If disabled, a table transcription task will only be
        generated if one or more cells have transcribed values below the defined thresholds,
        defaults to False
    :param task_restrictions: Defines what users can access Supervision tasks for
        submission from a particular source or submissions matching a specific layout,
        defaults to []
    :param manual_transcription_enabled: Enables manual transcription when applicable,
        defaults to workflow_input(Settings.ManualTranscriptionEnabled)
    :param notification_workflow: Notification flow name to run when the submission
        enters Manual Transcription,
        defaults to IDP_SUBMISSION_NOTIFY_NAME

    Example usage::

        manual_transcription = ManualTranscriptionBlock(
            reference_name='manual_transcription',
            submission=machine_transcription.output('submission'),
            api_params=submission_bootstrap.output('result.api_params'),
            supervision_transcription_masking=(
                idp_wf_config.manual_transcription_config.supervision_transcription_masking
            ),
            table_output_manual_review=(
                idp_wf_config.manual_transcription_config.table_output_manual_review
            ),
            task_restrictions=idp_wf_config.manual_transcription_config.task_restrictions,
        )

    """

    def __init__(
        self,
        submission: Any,
        api_params: Any,
        reference_name: Optional[str] = None,
        supervision_transcription_masking: bool = True,
        table_output_manual_review: bool = False,
        task_restrictions: Optional[List[Any]] = None,
        manual_transcription_enabled: str = workflow_input(Settings.ManualTranscriptionEnabled),
        notification_workflow: str = IDP_SUBMISSION_NOTIFY_NAME,
    ) -> None:
        if not task_restrictions:
            task_restrictions = []

        super().__init__(
            identifier='MANUAL_TRANSCRIPTION_3',
            reference_name=reference_name,
            input={
                'submission': submission,
                'api_params': api_params,
                'task_restrictions': task_restrictions,
                'manual_transcription_enabled': manual_transcription_enabled,
                'supervision_transcription_masking': supervision_transcription_masking,
                'table_output_manual_review': table_output_manual_review,
                'notification_workflow': notification_workflow,
            },
            title='Manual Transcription',
            description='Manually transcribe fields that could not be automatically transcribed',
        )


class FlexibleExtractionBlock(Block):
    """Flexible extraction manually transcribes fields marked for review

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param submission: Submission object
    :param api_params:

    Parameters with defaults:

    :param supervision_transcription_masking: Prevents users from inputting invalid
        characters during the Flexible Extraction task,
        defaults to True
    :param task_restrictions: Defines what users can access Supervision tasks created
        by this block,
        defaults to []
    :param layout_release_uuid: Layout Release UUID at submission creation time,
        defaults to workflow_input(Settings.LayoutReleaseUuid)
    :param notification_workflow: Notification flow name to run when the submission
        enters Flexible Extraction,
        defaults to IDP_SUBMISSION_NOTIFY_NAME

    Example usage::

        flexible_extraction = FlexibleExtractionBlock(
            reference_name='flexible_extraction',
            submission=manual_transcription.output('submission'),
            api_params=submission_bootstrap.output('result.api_params'),
            supervision_transcription_masking=(
                idp_wf_config.flexible_extraction_config.supervision_transcription_masking
            ),
            task_restrictions=idp_wf_config.flexible_extraction_config.task_restrictions,
        )

    """

    def __init__(
        self,
        submission: Any,
        api_params: Any,
        reference_name: Optional[str] = None,
        supervision_transcription_masking: bool = True,
        task_restrictions: Optional[List[Any]] = None,
        layout_release_uuid: str = workflow_input(Settings.LayoutReleaseUuid),
        notification_workflow: str = IDP_SUBMISSION_NOTIFY_NAME,
    ) -> None:
        if not task_restrictions:
            task_restrictions = []

        super().__init__(
            identifier='FLEXIBLE_EXTRACTION_2',
            reference_name=reference_name,
            input={
                'layout_release_uuid': layout_release_uuid,
                'api_params': api_params,
                'submission': submission,
                'task_restrictions': task_restrictions,
                'supervision_transcription_masking': supervision_transcription_masking,
                'notification_workflow': notification_workflow,
            },
            title='Flexible Extraction',
            description='Manually transcribe fields marked for review',
        )


class SubmissionCompleteBlock(Block):
    """Submission complete block finalizes submission processing and updates reporting data.

    **This block should be called at the END of every flow** that
    uses blocks included in the ``flows_sdk.implementations.idp_v33`` library.
    The block requires both the ``submission`` object and a ``payload`` to be passed in.

    Mandatory parameters:

    :param reference_name: unique identifier within a flow.
    :param submission: Submission object
    :param payload: Object to pass to downstream systems

    Parameters with defaults:

    :param nlc_qa_sampling_ratio: Defines the percentage of documents sampled for
        Classification QA,
        defaults to workflow_input(Settings.SemiQaSampleRate)
    :param field_id_qa_enabled:
        defaults to workflow_input(Settings.FieldIdQaEnabled)
    :param field_id_qa_sampling_ratio: Defines the percentage of documents sampled for
        Identification QA,
        defaults to workflow_input(Settings.FieldIdQaSampleRate)
    :param table_id_qa_enabled: Allows users to verify the location of table cells,
        defaults to workflow_input(Settings.TableIdQaEnabled)
    :param table_id_qa_sampling_ratio: Defines the percentage of tables the
        system samples for QA,
        defaults to workflow_input(Settings.TableIdQaSampleRate)
    :param transcription_qa_enabled:
        defaults to workflow_input(Settings.TranscriptionQaEnabled)
    :param transcription_qa_sampling_ratio: Defines the percentage of fields sampled for
        Transcription QA,
        defaults to workflow_input(Settings.TranscriptionQaSampleRate)
    :param table_cell_transcription_qa_enabled:
        defaults to workflow_input(Settings.TableCellTranscriptionQaEnabled)
    :param table_cell_transcription_qa_sample_rate: Defines the percentage of cells the
        system samples for QA. This value is likely to be lower than
        “Transcription QA Sample Rate” since there are more table cells than fields
        on any given page,
        defaults to workflow_input(Settings.TableCellTranscriptionQaSampleRate)

    Example usage::

        submission_complete = SubmissionCompleteBlock(
            reference_name='complete_submission',
            submission=flexible_extraction.output('submission')
        )

    """

    def __init__(
        self,
        submission: str,
        reference_name: Optional[str] = None,
        nlc_qa_sampling_ratio: Union[str, int] = workflow_input(Settings.SemiQaSampleRate),
        field_id_qa_enabled: Union[str, bool] = workflow_input(Settings.FieldIdQaEnabled),
        field_id_qa_sampling_ratio: Union[str, int] = workflow_input(Settings.FieldIdQaSampleRate),
        table_id_qa_enabled: Union[str, bool] = workflow_input(Settings.TableIdQaEnabled),
        table_id_qa_sampling_ratio: Union[str, int] = workflow_input(Settings.TableIdQaSampleRate),
        transcription_qa_enabled: Union[str, bool] = workflow_input(
            Settings.TranscriptionQaEnabled
        ),
        transcription_qa_sampling_ratio: Union[str, int] = workflow_input(
            Settings.TranscriptionQaSampleRate
        ),
        table_cell_transcription_qa_enabled: Union[str, bool] = workflow_input(
            Settings.TableCellTranscriptionQaEnabled
        ),
        table_cell_transcription_qa_sample_rate: Union[str, int] = workflow_input(
            Settings.TableCellTranscriptionQaSampleRate
        ),
        payload: Any = None,
    ) -> None:
        inputs = {
            'submission': submission,
            'nlc_qa_sampling_ratio': nlc_qa_sampling_ratio,
            'field_id_qa_enabled': field_id_qa_enabled,
            'field_id_qa_sampling_ratio': field_id_qa_sampling_ratio,
            'table_id_qa_enabled': table_id_qa_enabled,
            'table_id_qa_sampling_ratio': table_id_qa_sampling_ratio,
            'transcription_qa_enabled': transcription_qa_enabled,
            'transcription_qa_sampling_ratio': transcription_qa_sampling_ratio,
            'table_cell_transcription_qa_enabled': table_cell_transcription_qa_enabled,
            'table_cell_transcription_qa_sample_rate': table_cell_transcription_qa_sample_rate,
        }

        if payload is not None:
            inputs['payload'] = payload

        super().__init__(
            identifier='SUBMISSION_COMPLETE_3',
            reference_name=reference_name,
            input=inputs,
            title='Complete',
            description='Finalize submission processing and update reporting data',
        )


class IDPOutputsBlock(Outputs):
    """Output block allows users to send data extracted by an IDP flow to other systems
    for downstream processing

    Mandatory parameters:

    :param inputs: Used by the UI to automatically pre-populate the input of
        newly added blocks. Extended in this class to include ``'enabled': True``
        to visualize an enabled/disabled trigger that is controllable via Flow Studio.

    Usage when parameters are to be defined in Flow Studio::

        outputs = IDPOutputBlock(
            inputs={'submission': submission_bootstrap.output('result.submission')}
        )

    """

    def __init__(self, inputs: Dict[str, Any], blocks: Optional[Sequence[IOBlock]] = None) -> None:
        if not blocks:
            blocks = []

        super().__init__(
            reference_name='outputs',
            title='Outputs',
            description='Send submission data to external systems',
            role_filter=[IDP_OUTPUT_ROLE],
            input_template={**inputs, 'enabled': True},
            blocks=blocks,
        )


class DatabaseAccessBlock(Block):
    """Database Block allows user to access and perform queries on the specified database

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param db_type: database type (mssql, oracle, postgres)
    :param host: URL/IP address of the server database is hosted on
    :param database: database name
    :param username: database username
    :param password: database password
    :param query: parameterized query

    Optional parameters:

    :param port: database port number
    :param options: dictionary of additional connection string options
    :param query_params: dictionary of values for query placeholders
    :param timeout: timeout in seconds (mssql and postgres only)

    Example usage::

        # minimum viable instantiation, the rest of the fields can later be added in the UI
        db_lookup = DatabaseAccessBlock(
            reference_name='db_lookup',
            title='Database Lookup',
            description='Perform database lookup',
        )

        # note that storing password in plain text form is not recommended
        # password can later be entered in the UI or defined as a flow secret.
        db_lookup = DatabaseAccessBlock(
            reference_name='db_lookup',
            title='Database Lookup',
            description='Perform database lookup',
            db_type='mssql',
            database='cars',
            host='example.com',
            username='user',
            # we recommend skipping the password field or defining it as a system secret
            # e.g. system_secret('{your_secret_identifier}') (both allow for secret input via. UI)
            password='pw'
            port=1433,
            timeout=200,
            query='SELECT * from CAR',
        )

        # reference to the output of DBAccessBlock which can be passed as input to the next block
        # for more information on output() and output references, please take a look at class Block
        # and its output() method
        output_ref = db_lookup.output()

        # content of output_ref:
        {
            "result": [
                {
                    "id": 1,
                    "brand": "Aston Martin",
                    "model": "Vanquish"
                },
                {
                    "id": 2,
                    "brand": "Jaguar",
                    "model": "XE 2018"
                }
            ]
        }

    Database output for the same query (SELECT * FROM CAR)

    .. image:: ../media/images/db_access_query_example.png



    """

    def __init__(
        self,
        reference_name: Optional[str] = None,
        db_type: str = '',
        database: str = '',
        host: str = '',
        username: str = '',
        password: str = '',
        query: str = '',
        port: Optional[int] = None,
        options: Optional[Dict[Any, Any]] = None,
        timeout: Optional[int] = None,
        query_params: Optional[Dict[Any, Any]] = None,
        title: str = 'DB Block',
        description: str = 'DB access block',
    ) -> None:

        inputs: Dict[Any, Any] = {
            'db_type': db_type,
            'database': database,
            'host': host,
            'username': username,
            'password': password,
            'query': query,
        }
        if port is not None:
            inputs['port'] = port
        if options is not None:
            inputs['options'] = options
        if timeout is not None:
            inputs['timeout'] = timeout
        if query_params is not None:
            inputs['query_params'] = query_params

        super().__init__(
            identifier='DB_ACCESS',
            reference_name=reference_name,
            title=title,
            description=description,
            input=inputs,
        )


class BaseHttpRestBlock(Block):
    """
    :meta private:

    Base HttpRest block to be reused by internal and external divergent interface implementations
    """

    def __init__(
        self,
        method: str,
        reference_name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None,
        sdm_app_endpoint: Optional[str] = None,
        authorization_type: Optional[str] = None,
        handled_error_codes: Optional[List[Union[int, str]]] = None,
        auth_params: Optional[
            Union[HttpHeaderAuthorizationParams, OAuth2AuthorizationParams]
        ] = None,
        title: str = 'HTTP REST Block',
        description: str = 'HTTP REST block',
    ) -> None:

        assert endpoint or sdm_app_endpoint, 'An endpoint or an sdm_app_endpoint must be specified'

        inputs: Dict[Any, Any] = {'method': method}
        if endpoint is not None:
            inputs['endpoint'] = endpoint
        if sdm_app_endpoint is not None:
            inputs['sdm_app_endpoint'] = sdm_app_endpoint
        if headers is not None:
            inputs['headers'] = headers
        if params is not None:
            inputs['params'] = params
        if payload is not None:
            inputs['payload'] = payload
        if json is not None:
            inputs['json'] = json
        if authorization_type is not None:
            inputs['authorization_type'] = authorization_type
        if handled_error_codes is not None:
            inputs['handled_error_codes'] = handled_error_codes
        if auth_params is not None:
            if isinstance(auth_params, HttpHeaderAuthorizationParams):
                inputs['authorization_header'] = auth_params.authorization_header
            elif isinstance(auth_params, OAuth2AuthorizationParams):
                inputs['auth_url'] = auth_params.auth_url
                inputs['client_id'] = auth_params.client_id
                inputs['client_secret'] = auth_params.client_secret
                inputs['audience'] = auth_params.audience

        super().__init__(
            identifier='HTTP_REST',
            title=title,
            description=description,
            reference_name=reference_name,
            input=inputs,
        )


class HttpRestBlock(BaseHttpRestBlock):
    """Http Rest Block allows user to perform HTTP requests

    Mandatory parameters:

    :param method: HTTP method to use
    :param endpoint: absolute url including schema to HTTP endpoint for this request

    Optional Parameters:

    :param reference_name: unique identifier within a flow
    :param headers: HTTP headers to use
    :param params: key-value pair used as query parameters in the request
    :param payload: key-value pair to be used as x-www-form-urlencoded data.
        Mutually exclusive with json
    :param json: key-value pair to be used as json data. Mutually exclusive
        with payload
    :param authorization_type: authorization type (none, http_header,
        oauth_2_client_credentials)
    :param handled_error_codes: specify HTTP error codes that will not fail
        the task, allowing for wildcards with the 'x' char. Example: [400, \"5xx\"]
    :param auth_params: authorization parameters to be passed when the authorization_type
        is set to "http_header" or "oauth_2_client_credentials"


    Example usage::

        # minimum viable instantiation, the rest of the fields can later be added in the UI
        http_rest_block = HttpRestBlock(
            reference_name='http_request',
            title='Http Request',
            description='Perform http request',
            method='GET',
        )

        http_rest_block = HttpRestBlock(
            reference_name='http_request',
            title='Http Request',
            description='Perform http request',
            method='GET',
            endpoint='https://sheets.googleapis.com/v4/spreadsheets/example',
        )

        # reference to the output of HttpRestBlock which can be passed as input to the next block
        # for more information on output() and output references, please take a look at class Block
        # and its output() method
        output_ref = http_rest_block.output()
    """

    def __init__(
        self,
        method: str,
        endpoint: str,
        reference_name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        authorization_type: Optional[str] = None,
        handled_error_codes: Optional[List[Union[int, str]]] = None,
        auth_params: Optional[
            Union[HttpHeaderAuthorizationParams, OAuth2AuthorizationParams]
        ] = None,
        title: str = 'HTTP REST Block',
        description: str = 'HTTP REST block',
    ) -> None:
        super().__init__(
            method=method,
            reference_name=reference_name,
            headers=headers,
            params=params,
            payload=payload,
            json=json,
            endpoint=endpoint,
            authorization_type=authorization_type,
            handled_error_codes=handled_error_codes,
            auth_params=auth_params,
            title=title,
            description=description,
        )


class HyperscienceRestApiBlock(BaseHttpRestBlock):
    """Make HTTP requests to the Hyperscience platform APIs.
    This block will automatically take care of prepending the base url and will include
    the appropriate authentication headers with the request.

    Mandatory parameters:

    :param method: HTTP method to use, e.g. 'GET', 'POST', etc.
    :param app_endpoint: relative url, beginning with a forward slash, to an HTTP endpoint
        served by the Hyperscience platform. For reference on the available endpoints, check out
        https://docs.hyperscience.com/.
        Absolute URLs that include a hostname are allowed only if the flow has received them
        as part of the response of a previous API request that the flow has made.
        Do not hardcode the hostname of the Hyperscience instance in your flow definitions as
        they will not work when you run the flows on another instance,
        or if the hostname changes.
        For making requests to external systems, use the HttpRestBlock or a library like "requests".

    Optional Parameters:

    :param reference_name: unique identifier within a flow
    :param headers: HTTP headers to use
    :param params: key-value pair used as query parameters in the request
    :param payload: key-value pair to be used as x-www-form-urlencoded data.
        Mutually exclusive with json
    :param json: key-value pair to be used as json data. Mutually exclusive
        with payload
    :param handled_error_codes: specify HTTP error codes that will not fail
        the task, allowing for wildcards with the 'x' char. Example: [400, \"5xx\"]

    Example usage::

        hs_rest_block = HyperscienceRestApiBlock(
            reference_name='http_request',
            app_endpoint='/api/healthcheck',
            method='GET',
        )

    """

    def __init__(
        self,
        method: str,
        app_endpoint: str,
        reference_name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        handled_error_codes: Optional[List[Union[int, str]]] = None,
        title: str = 'Hyperscience HTTP REST Block',
        description: str = 'Hyperscience HTTP REST block',
    ) -> None:
        super().__init__(
            method=method,
            reference_name=reference_name,
            headers=headers,
            params=params,
            payload=payload,
            json=json,
            sdm_app_endpoint=app_endpoint,
            authorization_type=None,
            handled_error_codes=handled_error_codes,
            title=title,
            description=description,
        )


class SoapRequestBlock(Block):
    """Soap Block allows user to perform SOAP requests

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param method: SOAP method to invoke
    :param endpoint: absolute url including schema to HTTP endpoint for this request

    Optional Parameters:

    :param body_namespace: SOAP request body namespace url
    :param headers_namespace: SOAP request headers namespace url
    :param headers: SOAP headers to use
    :param params: key-value pair used as query parameters in the request to be
        inserted as SOAP body

    Example usage::

        # minimum viable instantiation, the rest of the fields can later be added in the UI
        soap_block = SoapRequestBlock(
            reference_name='soap_request',
            title='Soap Request',
            description='Perform soap request',
            method='ExampleMethod',
        )

        soap_block = SoapRequestBlock(
            reference_name='soap_request',
            title='Soap Request',
            description='Perform soap request',
            method='ExampleMethod',
            endpoint='http://example.org/abc.wso',
            body_namespace='http://www.example.org/abc.countryinfo',
            params={'example': 'stuff'},
            headers={}
        )

        # reference to the output of SoapRequestBlock which can be passed as input to the next block
        # for more information on output() and output references, please take a look at class Block
        # and its output() method
        output_ref = soap_block.output()
    """

    def __init__(
        self,
        method: str,
        reference_name: Optional[str] = None,
        endpoint: str = '',
        body_namespace: Optional[str] = None,
        headers_namespace: Optional[str] = None,
        headers: Optional[Dict[Any, Any]] = None,
        params: Optional[Dict[Any, Any]] = None,
        title: str = 'HTTP REST Block',
        description: str = 'HTTP REST block',
    ) -> None:

        inputs: Dict[Any, Any] = {'method': method, 'endpoint': endpoint}
        if body_namespace is not None:
            inputs['body_namespace'] = body_namespace
        if headers_namespace is not None:
            inputs['headers_namespace'] = headers_namespace
        if headers is not None:
            inputs['headers'] = headers
        if params is not None:
            inputs['params'] = params

        super().__init__(
            identifier='SOAP_REQ',
            reference_name=reference_name,
            input=inputs,
            title=title,
            description=description,
        )


class CustomSupervisionBlock(Block):
    """The CustomSupervisionBlock uses a JSON schema as a form builder to create customer-driven
    UIs for Supervision tasks.

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param submission: Submission object
    :param task_purpose: the custom task name that's given to all supervision tasks that run
        through a particular instance of a custom supervision block. This can be used to filter
        tasks in the task queue.
    :param data: JSON structure that supplies the data used to populated the supervision_template
    :param supervision_template: JSON used for configuration of the Custom Supervision Task.

    Parameters with defaults:

    :param supervision_transcription_masking: Prevents users from inputting invalid
        characters during the Custom Supervision task,
        defaults to True
    :param task_restrictions: Defines what users can access Supervision tasks created
        by this block,
        defaults to []

    Example usage::

        custom_supervision = CustomSupervisionBlock(
            reference_name='custom_supervision',
            submission=manual_transcription.output('submission'),
            task_purpose='make_custom_decision',
            supervision_template=[
                {
                    'name': 'three_column_template',
                    'version': '1.0',
                    'thumbnail': {
                        'group_by_document': True,
                        'group_by_case': True,
                    },
                    'action': [
                        {
                            'name': 'my_tab',
                            'display': 'SSN Info',
                            'input': [
                                {
                                    'name': 'ssn_field',
                                    'type': 'transcription',
                                    'layout_field_id': '2afd7a67-ddee-484f-ab6b-2d292752e5ee',
                                    'title': 'SSN',
                                },
                            ],
                            'ui': {
                                'groups': [
                                    {
                                        'title': 'My Group',
                                        'fields': ['ssn_field'],
                                    },
                                ],
                            },
                        },
                    ],
                },
            ],
            data={
                'fields': [
                    {
                        'id': 967,
                        'uuid': 'fe8d4e7a-a82c-448c-85a1-0a3cbbe53b61',
                        'value': '111-22-3333',
                        'page_id': 1,
                        'layout_field_id': '2afd7a67-ddee-484f-ab6b-2d292752e5ee',
                        'validation_overridden': false,
                        'bounding_box': [
                            0.09360783305186686,
                            0.25792617589433436,
                            0.6358913805295097,
                            0.28862414740388187,
                        ],
                        'occurence_index': 1,
                    },
                ],
                'template_fields': [
                    {
                        'uuid': '2afd7a67-ddee-484f-ab6b-2d292752e5ee',
                        'notes': '',
                        'type': 'entry',
                        'data_type_uuid': 'b600a4e4-758f-4c4b-a2f4-cbb5dd870a0c',
                        'name': 'SSN',
                        'n_occurences': 1,
                    },
                ],
                'pages': [
                    {
                        'id': 15,
                        'file_page_number': 1,
                        'document_page_number': 1,  // Optional
                        'image_url': '/image/6e55fa86-a36b-4178-8db1-3a514621d4c1',
                        'form_id': 2,
                        'submission_id': 3,
                        'external_case_ids': [
                            'HS-27',
                        ],
                        'read_only': False,
                        'filename': 'filename.pdf',
                    },
                ],
                'documents': [
                    {
                        'id': 2,
                        'layout_uuid': 'e31c3cbf-dcea-44fd-a052-902463c6040f',
                        'layout_name': 'layout_name',
                        'page_count': 2,
                        'read_only': false,
                    },
                ],
                'cases': [],
                'selected_choices': [],
            },
            supervision_transcription_masking=False,
        )

    """

    def __init__(
        self,
        submission: Any,
        task_purpose: str,
        data: Any,
        supervision_template: Any,
        reference_name: Optional[str] = None,
        supervision_transcription_masking: bool = True,
        task_restrictions: Optional[List[Any]] = None,
    ) -> None:
        if not task_restrictions:
            task_restrictions = []

        super().__init__(
            identifier='CUSTOM_SUPERVISION',
            reference_name=reference_name,
            input={
                'supervision_template': supervision_template,
                'submission': submission,
                'task_purpose': task_purpose,
                'data': data,
                'task_restrictions': task_restrictions,
                'supervision_transcription_masking': supervision_transcription_masking,
            },
            title='Custom Supervision',
            description='Custom Supervision',
        )


class IdpCustomSupervisionBlock(Block):
    """An IDP wrapper for the Custom Supervision block. It has the same functionality,
    but handles reading/writing data from the IDP database.

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param submission: Submission object
    :param task_purpose: the custom task name that's given to all supervision tasks that run
        through a particular instance of a custom supervision block. This can be used to filter
        tasks in the task queue.
    :param supervision_template: JSON used for configuration of the Custom Supervision Task.

    Parameters with defaults:

    :param supervision_transcription_masking: Prevents users from inputting invalid
        characters during the Custom Supervision task,
        defaults to True
    :param task_restrictions: Defines what users can access Supervision tasks created
        by this block,
        defaults to []
    :param page_ids: A list of page ids to include. This should not be used. The IDP wrapper should
        handle pulling in all pages in the submission.
        defaults to []

    Example usage::

        idp_custom_supervision = IdpCustomSupervisionBlock(
            reference_name='idp_custom_supervision',
            submission=manual_transcription.output('submission'),
            task_purpose='make_custom_decision',
            supervision_template=[
                {
                    'name': 'three_column_template',
                    'version': '1.0',
                    'thumbnail': {
                        'group_by_document': True,
                        'group_by_case': True,
                    },
                    'action': [
                        {
                            'name': 'my_tab',
                            'display': 'SSN Info',
                            'input': [
                                {
                                    'name': 'ssn_field',
                                    'type': 'transcription',
                                    'layout_field_id': '2afd7a67-ddee-484f-ab6b-2d292752e5ee',
                                    'title': 'SSN',
                                },
                            ],
                            'ui': {
                                'groups': [
                                    {
                                        'title': 'My Group',
                                        'fields': ['ssn_field'],
                                    },
                                ],
                            },
                        },
                    ],
                },
            ],
            supervision_transcription_masking=False,
        )

    """

    def __init__(
        self,
        submission: Any,
        task_purpose: str,
        supervision_template: Any,
        reference_name: Optional[str] = None,
        supervision_transcription_masking: bool = True,
        task_restrictions: Optional[List[Any]] = None,
        page_ids: Optional[List[int]] = None,
    ) -> None:
        if not task_restrictions:
            task_restrictions = []
        if not page_ids:
            page_ids = []

        super().__init__(
            identifier='IDP_CUSTOM_SUPERVISION',
            reference_name=reference_name,
            input={
                'supervision_template': supervision_template,
                'task_purpose': task_purpose,
                'submission': submission,
                'task_restrictions': task_restrictions,
                'supervision_transcription_masking': supervision_transcription_masking,
                'page_ids': page_ids,
            },
            title='IDP Custom Supervision',
            description='IDP Custom Supervision',
        )


class IDPFullPageTranscriptionBlock(Block):
    """**This block is available on 33.0.1 or later**

    IDP Full Page Transcription Block machine-transcribes the unassigned pages in a submission

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param submission: submission object that includes the raw documents that need to be transcribed

    Optional Parameters:

    :param app_metadata: used for capturing information about the flow

    Example usage::

        # This is one way to obtain the submission object (using SUbmissionBootstrapBlock)
        submission_bootstrap = SubmissionBootstrapBlock(reference_name='submission_bootstrap')
        # IDPFullPageTranscriptionBlock transcribes the documents contained in the submission object
        idp_fpt_block = IDPFullPageTranscriptionBlock(
            reference_name='idp_fpt',
            submission=submission_bootstrap.output(),
        )
        # reference to the output of IDPFullPageTranscriptionBlock which can be passed as input to
        # the next block. For more information on output() and output references, please take a
        # look at class Block and its output() method
        output_ref = idp_fpt_block.output()
    """

    def __init__(
        self,
        submission: str,
        reference_name: Optional[str] = None,
        title: str = 'Full Page Transcription (Submission)',
        description: str = 'Transcribes the documents included in a submission',
        app_metadata: Optional[List[str]] = None,
    ) -> None:

        inputs: Dict[Any, Any] = {'submission': submission}
        if app_metadata is not None:
            inputs['app_metadata'] = app_metadata

        super().__init__(
            identifier='FULL_PAGE_TRANSCRIPTION_SUBMISSION',
            reference_name=reference_name,
            input=inputs,
            title=title,
            description=description,
        )


class IDPImageCorrectionBlock(Block):
    """**This block is available on 33.0.1 or later**

    IDP Image Correction Block rotates and de-skews tilted/skewed images so that they are more
    transcription-friendly

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param submission: submission object that includes the raw documents that need to be
        image-corrected

    Optional Parameters:

    :param app_metadata: used for capturing information about the flow

    Example usage::

        # This is one way to obtain the submission object (using SubmissionBootstrapBlock)
        submission_bootstrap = SubmissionBootstrapBlock(reference_name='submission_bootstrap')
        # IDPImageCorrectionBlock takes in the submission object and outputs in the same format with
        # its images
        idp_image_correct_block = IDPImageCorrectionBlock(
            reference_name='idp_image_correct',
            submission=submission_bootstrap.output(),
        )
        # reference to the output of IDPImageCorrectionBlock which can be passed as input to the
        # next block. For more information on output() and output references, please take a look at
        # class Block and its output() method
        output_ref = idp_image_correct_block.output()
    """

    def __init__(
        self,
        submission: str,
        reference_name: Optional[str] = None,
        rotation_correction_enabled: bool = True,
        mobile_processing_enabled: bool = False,
        title: str = 'Image Correction (Submission)',
        description: str = 'Rotate and de-skew documents included in a submission',
        app_metadata: Optional[List[str]] = None,
    ) -> None:

        inputs: Dict[Any, Any] = {
            'submission': submission,
            'rotation_correction_enabled': rotation_correction_enabled,
            'mobile_processing_enabled': mobile_processing_enabled,
        }
        if app_metadata is not None:
            inputs['app_metadata'] = app_metadata

        super().__init__(
            identifier='IMAGE_CORRECTION_SUBMISSION',
            reference_name=reference_name,
            input=inputs,
            title=title,
            description=description,
        )


class FullPageTranscriptionBlock(Block):
    """**This block is available on 33.0.1 or later**

    Full Page Transcription Block machine-transcribes the document pages passed to it

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param pages: list of pages that includes the raw documents that need to be transcribed

    Optional Parameters:

    :param app_metadata: used for capturing information about the flow

    Example usage::

        # This is one way to obtain the submission object (using SubmissionBootstrapBlock)
        submission_bootstrap = SubmissionBootstrapBlock(reference_name='submission_bootstrap')
        # FullPageTranscriptionBlock transcribes the documents contained in the submission object
        fpt_block = FullPageTranscriptionBlock(
            reference_name='fpt',
            submission=submission_bootstrap.output(),
        )
        # reference to the output of FullPageTranscriptionBlock which can be passed as input to the
        # next block. For more information on output() and output references, please take a look at
        # class Block and its output() method
        output_ref = fpt_block.output()
    """

    def __init__(
        self,
        pages: str,
        reference_name: Optional[str] = None,
        title: str = 'Full Page Transcription (Pages)',
        description: str = 'Transcribes documents',
        app_metadata: Optional[List[str]] = None,
    ) -> None:

        inputs: Dict[Any, Any] = {'pages': pages}
        if app_metadata is not None:
            inputs['app_metadata'] = app_metadata

        super().__init__(
            identifier='FULL_PAGE_TRANSCRIPTION_PAGES',
            reference_name=reference_name,
            input=inputs,
            title=title,
            description=description,
        )


class ImageCorrectionBlock(Block):
    """**This block is available on 33.0.1 or later**

    Image Correction Block rotates and de-skews tilted/skewed images so that they are more
    transcription-friendly

    Mandatory parameters:

    :param reference_name: unique identifier within a flow
    :param pages: list of page object that includes the raw documents that need to be
        image-corrected

    Optional Parameters:

    :param app_metadata: used for capturing information about the flow

    Example usage::

        # This is one way to obtain the submission object (using SubmissionBootstrapBlock)
        submission_bootstrap = SubmissionBootstrapBlock(reference_name='submission_bootstrap')
        # ImageCorrectionBlock takes in the submission object and outputs in the same format with
        # its images
        image_correct_block = ImageCorrectionBlock(
            reference_name='image_correct',
            pages=submission_bootstrap.output(submission.unassigned_pages),
        )
        # reference to the output of IDPImageCorrectionBlock which can be passed as input to the
        # next block. For more information on output() and output references, please take a look
        # at class Block and its output() method
        output_ref = image_correct_block.output()
    """

    def __init__(
        self,
        pages: str,
        reference_name: Optional[str] = None,
        rotation_correction_enabled: bool = True,
        mobile_processing_enabled: bool = False,
        title: str = 'Image Correction (Pages)',
        description: str = 'Rotate and de-skew documents',
        app_metadata: Optional[List[str]] = None,
    ) -> None:

        inputs: Dict[Any, Any] = {
            'pages': pages,
            'rotation_correction_enabled': rotation_correction_enabled,
            'mobile_processing_enabled': mobile_processing_enabled,
        }
        if app_metadata is not None:
            inputs['app_metadata'] = app_metadata

        super().__init__(
            identifier='IMAGE_CORRECTION_PAGES',
            reference_name=reference_name,
            input=inputs,
            title=title,
            description=description,
        )
