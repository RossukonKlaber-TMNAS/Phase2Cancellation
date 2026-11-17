from typing import Any, Dict, List, Optional, Sequence, Union

from flows_sdk.blocks import Block, IOBlock, Outputs
from flows_sdk.implementations.idp_v38.idp_values import (
    DEFAULT_IDP_CORE_IDENTIFIER,
    DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER,
    IDP_OUTPUT_ROLE,
    OCS_SECRET_KEY,
    S3_SECRET_KEY,
    IdpWorkflowConfig,
    Inputs,
    Settings,
    extract_config,
    get_idp_wf_inputs,
)
from flows_sdk.types import CompatibilitySpec
from flows_sdk.utils import system_secret, workflow_input


class IDPCoreBlock(Block):
    """IDP core block includes the steps to process the passed documents into machine-readable
    output.

    Mandatory parameters:

    :parameter idp_wf_config: IdpWorkflowConfig object with all flow-level configuration settings
        for IDP

    Parameters with defaults:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
    :param compatibility_spec: defines a filter for flows that could be selected in the UI in place
        of "IDP Core" for the block. Defaults to flows with the role 'idp_core'. The user will be
        able to pick any flow that matches the compatibility_spec. This serves to make upgrading
        to a new compatible version of "IDP Core" (e.g. IDP_CORE_V39) easier in future releases.
    :param identifier: The identifier of the flow. Defaults to the IDP_CORE_VXX identifier of the
        out-of-the-box flow that comes with the system.
    :param additional_inputs: Dictionary containing key-value pairs that will be added to the
        inputs of the block. If a key is contained in the default inputs, its value will be
        overwritten by the value provided here. You generally do not need to provide
        additional_inputs, unless you are creating a custom derivative of the IDP_CODE_Vxx flow
        and are modifying or extending the list of inputs it accepts.

    Example usage::

        idp_core = IDPCoreBlock(idp_wf_config=idp_wf_config)
    """

    # REFERENCE_NAME should be "__idp_core__" to preserve core platform functionality
    # related to layouts and releases that looks for this specific name.
    # Do not change it even if you are creating custom versions of IDPCoreBlock.
    REFERENCE_NAME = '__idp_core__'

    def __init__(
        self,
        idp_wf_config: IdpWorkflowConfig,
        reference_name: Optional[str] = REFERENCE_NAME,
        title: str = 'Start Document Processing Subflow',
        description: str = 'Calls the Document Processing Subflow with the specified settings.',
        compatibility_spec: Optional[CompatibilitySpec] = CompatibilitySpec(
            filter_roles=['idp_core']
        ),
        identifier: str = DEFAULT_IDP_CORE_IDENTIFIER,
        additional_inputs: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not additional_inputs:
            additional_inputs = {}
        default_inputs = get_idp_wf_inputs(idp_wf_config)

        super().__init__(
            identifier=identifier,
            reference_name=reference_name,
            title=title,
            description=description,
            input={
                **default_inputs,
                **additional_inputs,
                '$trigger': workflow_input(Inputs.Trigger),
            },
            compatibility_spec=compatibility_spec,
        )


class SubmissionBootstrapBlock(Block):
    """Submission bootstrap block initializes the submission object and prepares external images
    or other submission data if needed.
    **This block should be called at the START of every flow** that
    uses blocks included in the library.

    Parameters with defaults:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
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

    IDENTIFIER = 'SUBMISSION_BOOTSTRAP_2'

    def __init__(
        self,
        reference_name: Optional[str] = None,
        layout_release_uuid: str = workflow_input(Settings.LayoutReleaseUuid),
        s3_config: str = workflow_input(Settings.SubmissionBootstrapS3Config),
        s3_endpoint_url: str = workflow_input(Settings.SubmissionBootstrapS3EndpointUrl),
        ocs_config: str = workflow_input(Settings.SubmissionBootstrapOCSConfig),
        http_config: Optional[str] = workflow_input(Settings.SubmissionBootstrapHTTPConfig),
        notification_workflow: str = workflow_input(
            Settings.SubmissionBootstrapNotificationWorkflow
        ),
        workflow_uuid: str = workflow_input(Inputs.WorkflowUuid),
        workflow_name: str = workflow_input(Inputs.WorkflowName),
        workflow_version: str = workflow_input(Inputs.WorkflowVersion),
        submission: Any = workflow_input(Inputs.Submission),
    ) -> None:
        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input={
                '$trigger': workflow_input(Inputs.Trigger),
                'layout_release_uuid': layout_release_uuid,
                's3_config': s3_config or system_secret(S3_SECRET_KEY),
                's3_endpoint_url': s3_endpoint_url,
                'ocs_config': ocs_config or system_secret(OCS_SECRET_KEY),
                'http_config': http_config,
                'notification_workflow': notification_workflow
                or DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER,
                'workflow_uuid': workflow_uuid,
                'workflow_name': workflow_name,
                'workflow_version': workflow_version,
                'submission': submission,
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
    """Machine collation block groups files, documents and pages (from the submission) into cases.

    Mandatory parameters:

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

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
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

    :param retention_period: The number of days to retain cases after they are updated by this
        block. If passed ``None``, no changes to the deletion date will be made.
        By default, this value is ``None``
    :param refresh_retention_period: If ``True``, (re)applies Retention Period parameter to all
        cases passed into the block. If ``False``, only updates those without a pre-existing
        deletion date. By default, this value is ``True``

    Example usage::

        machine_collation = MachineCollationBlock(
            reference_name='machine_collation',
            submission=submission_bootstrap.output('result.submission'),
            cases=submission_bootstrap.output('result.api_params.cases'),
            dedupe_files=True,
            remove_from_cases=custom_supervision.output('remove_from_cases')
        )
    """

    IDENTIFIER = 'MACHINE_COLLATION_2'

    def __init__(
        self,
        submission: Any,
        cases: Any,
        dedupe_files: Union[bool, str] = workflow_input(Settings.CollationDedupeFiles),
        refresh_retention_period: Union[bool, str] = workflow_input(
            Settings.CollationRefreshRetentionPeriod
        ),
        remove_from_cases: Optional[Any] = workflow_input(Settings.CollationRemoveFromCases),
        retention_period: Optional[Union[int, str]] = workflow_input(
            Settings.CollationRetentionPeriod
        ),
        reference_name: Optional[str] = None,
    ) -> None:
        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input={
                'submission': submission,
                'cases': cases,
                'dedupe_files': dedupe_files or False,
                'remove_from_cases': remove_from_cases,
                'retention_period': retention_period,
                'refresh_retention_period': refresh_retention_period or True,
            },
            title='Machine Collation',
            description='Group files, documents, and pages into cases',
        )


class MachineClassificationBlock(Block):
    """Machine classification block automatically matches documents to structured,
    semi-structured or additional layouts

    Mandatory parameters:

    :param submission: Submission object
    :param api_params:

    Parameters with defaults:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
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

    IDENTIFIER = 'MACHINE_CLASSIFICATION_5'

    def __init__(
        self,
        submission: Any,
        api_params: Any,
        reference_name: Optional[str] = None,
        rotation_correction_enabled: Union[bool, str] = workflow_input(
            Settings.RotationCorrectionEnabled
        ),
        mobile_processing_enabled: Union[bool, str] = workflow_input(
            Settings.MobileProcessingEnabled
        ),
        file_transcription_enabled: Union[bool, str] = workflow_input(
            Settings.FileTranscriptionEnabled
        ),
        layout_release_uuid: str = workflow_input(Settings.LayoutReleaseUuid),
        vpc_registration_threshold: str = workflow_input(Settings.StructuredLayoutMatchThreshold),
        nlc_enabled: str = workflow_input(Settings.SemiStructuredClassification),
        nlc_target_accuracy: str = workflow_input(Settings.SemiTargetAccuracy),
        nlc_doc_grouping_logic: str = workflow_input(Settings.SemiDocGroupingLogic),
    ) -> None:
        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input={
                'layout_release_uuid': layout_release_uuid,
                'submission': submission,
                'api_params': api_params,
                'vpc_registration_threshold': vpc_registration_threshold,
                'nlc_enabled': nlc_enabled,
                'nlc_target_accuracy': nlc_target_accuracy,
                'nlc_doc_grouping_logic': nlc_doc_grouping_logic,
                'rotation_correction_enabled': rotation_correction_enabled or True,
                'mobile_processing_enabled': mobile_processing_enabled or False,
                'file_transcription_enabled': file_transcription_enabled or False,
            },
            title='Machine Classification',
            description='Automatically classify documents',
        )


class ManualClassificationBlock(Block):
    """Manual classification block allows keyers to manually match submissions to their layouts.
    Keyers may perform manual classification if machine classification cannot automatically
    match a submission to a layout with high confidence

    Mandatory parameters:

    :param submission: Submission object
    :param api_params:

    Parameters with defaults:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
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

    IDENTIFIER = 'MANUAL_CLASSIFICATION_2'

    def __init__(
        self,
        submission: Any,
        api_params: Any,
        reference_name: Optional[str] = None,
        layout_release_uuid: str = workflow_input(Settings.LayoutReleaseUuid),
        manual_nlc_enabled: str = workflow_input(Settings.ManualNlcEnabled),
        task_restrictions: Optional[Union[List[Any], str]] = workflow_input(
            Settings.ManualClassificationTaskRestrictions
        ),
        notification_workflow: str = workflow_input(
            Settings.ManualClassificationNotificationWorkflow
        ),
        nlc_enabled: Optional[Union[bool, str]] = workflow_input(
            Settings.SemiStructuredClassification
        ),
        nlc_target_accuracy: Optional[Union[float, str]] = workflow_input(
            Settings.SemiTargetAccuracy
        ),
        mobile_processing_enabled: Optional[Union[bool, str]] = workflow_input(
            Settings.MobileProcessingEnabled
        ),
    ) -> None:
        if task_restrictions is None:
            task_restrictions = []
        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input={
                'layout_release_uuid': layout_release_uuid,
                'manual_nlc_enabled': manual_nlc_enabled,
                'task_restrictions': task_restrictions,
                'api_params': api_params,
                'submission': submission,
                'notification_workflow': notification_workflow
                or DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER,
                'nlc_enabled': nlc_enabled or True,
                'nlc_target_accuracy': nlc_target_accuracy or 0.99,
                'mobile_processing_enabled': mobile_processing_enabled or False,
            },
            title='Manual Classification',
            description='Manually classify documents that could not be automatically classified',
        )


class MachineIdentificationBlock(Block):
    """Machine identification automatically identify fields and tables in the submission

    Mandatory parameters:

    :param submission: Submission object
    :param api_params:

    Parameters with defaults:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
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

    IDENTIFIER = 'MACHINE_IDENTIFICATION_6'

    def __init__(
        self,
        submission: Any,
        api_params: Any,
        layout_release_uuid: Any = workflow_input(Settings.LayoutReleaseUuid),
        reference_name: Optional[str] = None,
        manual_field_id_enabled: str = workflow_input(Settings.ManualFieldIdEnabled),
        field_id_target_accuracy: str = workflow_input(Settings.FieldIdTargetAccuracy),
        table_id_target_accuracy: str = workflow_input(Settings.TableIdTargetAccuracy),
    ) -> None:
        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input={
                'submission': submission,
                'layout_release_uuid': layout_release_uuid,
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

    :param submission: Submission object
    :param api_params:

    Parameters with defaults:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
    :param task_restrictions: Defines what users can access Supervision tasks created
        by this block,
        defaults to []
    :param manual_field_id_enabled: Enables manual identification when applicable,
        defaults to workflow_input(Settings.ManualFieldIdEnabled)
    :param layout_release_uuid: Layout Release UUID at submission creation time,
        defaults to workflow_input(Settings.LayoutReleaseUuid)
    :param notification_workflow: Notification flow name to run when the submission
        enters Manual Identification,
        defaults to DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER

    Example usage::

        manual_identification = ManualIdentificationBlock(
            reference_name='manual_identification',
            submission=machine_identification.output('submission'),
            api_params=submission_bootstrap.output('result.api_params'),
            task_restrictions=idp_wf_config.manual_identification_config.task_restrictions,
        )
    """

    IDENTIFIER = 'MANUAL_IDENTIFICATION_5'

    def __init__(
        self,
        submission: Any,
        api_params: Any,
        reference_name: Optional[str] = None,
        task_restrictions: Optional[Union[List[Any], str]] = workflow_input(
            Settings.ManualFieldIdTaskRestrictions
        ),
        manual_field_id_enabled: str = workflow_input(Settings.ManualFieldIdEnabled),
        layout_release_uuid: str = workflow_input(Settings.LayoutReleaseUuid),
        notification_workflow: str = workflow_input(Settings.ManualFieldIdNotificationWorkflow),
    ) -> None:
        if task_restrictions is None:
            task_restrictions = []
        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input={
                'submission': submission,
                'api_params': api_params,
                'manual_field_id_enabled': manual_field_id_enabled,
                'layout_release_uuid': layout_release_uuid,
                'notification_workflow': notification_workflow
                or DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER,
                'task_restrictions': task_restrictions,
            },
            title='Manual Identification',
            description='Manually locate fields on semi-structured documents that '
            'could not be automatically located',
        )


class MachineTranscriptionBlock(Block):
    """Machine transcription automatically transcribes the content of your submission

    Mandatory parameters:

    :param submission: Submission object
    :param api_params:

    Parameters with defaults:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
    :param layout_release_uuid: Layout Release UUID at submission creation time,
        defaults to workflow_input(Settings.LayoutReleaseUuid)
    :param transcription_model: The transcription model that will be used for this flow,
        defaults to workflow_input(Settings.TranscriptionModel)
    :param finetuning_only_trained_layouts:
        defaults to workflow_input( Settings.FinetuningOnlyTrainedLayouts )
    :param transcription_overrides:
        defaults to workflow_input( Settings.TranscriptionOverrides )
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

    IDENTIFIER = 'MACHINE_TRANSCRIPTION_9'

    def __init__(
        self,
        submission: Any,
        api_params: Any,
        reference_name: Optional[str] = None,
        layout_release_uuid: str = workflow_input(Settings.LayoutReleaseUuid),
        transcription_model: str = workflow_input(Settings.TranscriptionModel),
        finetuning_only_trained_layouts: str = workflow_input(
            Settings.FinetuningOnlyTrainedLayouts
        ),
        transcription_overrides: str = workflow_input(Settings.TranscriptionOverrides),
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
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input={
                'layout_release_uuid': layout_release_uuid,
                'submission': submission,
                'api_params': api_params,
                'transcription_model': transcription_model,
                'finetuning_only_trained_layouts': finetuning_only_trained_layouts,
                'transcription_overrides': transcription_overrides,
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

    :param submission: Submission object
    :param api_params:

    Parameters with defaults:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
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
        defaults to DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER

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

    IDENTIFIER = 'MANUAL_TRANSCRIPTION_5'

    def __init__(
        self,
        submission: Any,
        api_params: Any,
        reference_name: Optional[str] = None,
        supervision_transcription_masking: Union[bool, str] = workflow_input(
            Settings.ManualTranscriptionSupervisionTranscriptionMasking
        ),
        table_output_manual_review: Union[bool, str] = workflow_input(
            Settings.ManualTranscriptionTableOutputManualReview
        ),
        always_supervise_blank_cells: Union[bool, str] = workflow_input(
            Settings.ManualTranscriptionAlwaysSuperviseBlankCells
        ),
        task_restrictions: Optional[Union[List[Any], str]] = workflow_input(
            Settings.ManualTranscriptionTaskRestrictions
        ),
        manual_transcription_enabled: str = workflow_input(Settings.ManualTranscriptionEnabled),
        notification_workflow: str = workflow_input(
            Settings.ManualTranscriptionNotificationWorkflow
        ),
        title: str = 'Manual Transcription',
        description: str = 'Manually transcribe fields that could not be automatically transcribed',
    ) -> None:
        if not task_restrictions:
            task_restrictions = []

        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input={
                'submission': submission,
                'api_params': api_params,
                'task_restrictions': task_restrictions,
                'manual_transcription_enabled': manual_transcription_enabled,
                'supervision_transcription_masking': supervision_transcription_masking or True,
                'table_output_manual_review': table_output_manual_review or False,
                'always_supervise_blank_cells': always_supervise_blank_cells or True,
                'notification_workflow': notification_workflow
                or DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER,
            },
            title=title,
            description=description,
        )


class FlexibleExtractionBlock(Block):
    """Flexible extraction manually transcribes fields marked for review

    Mandatory parameters:

    :param submission: Submission object
    :param api_params:

    Parameters with defaults:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
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
        defaults to DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER

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

    IDENTIFIER = 'FLEXIBLE_EXTRACTION_4'

    def __init__(
        self,
        submission: Any,
        api_params: Any,
        reference_name: Optional[str] = None,
        supervision_transcription_masking: Optional[Union[bool, str]] = workflow_input(
            Settings.FlexibleExtractionSupervisionTranscriptionMasking
        ),
        task_restrictions: Optional[Union[List[Any], str]] = workflow_input(
            Settings.FlexibleExtractionTaskRestrictions
        ),
        layout_release_uuid: str = workflow_input(Settings.LayoutReleaseUuid),
        notification_workflow: str = workflow_input(
            Settings.FlexibleExtractionNotificationWorkflow
        ),
    ) -> None:
        if not task_restrictions:
            task_restrictions = []

        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input={
                'layout_release_uuid': layout_release_uuid,
                'api_params': api_params,
                'submission': submission,
                'task_restrictions': task_restrictions,
                'supervision_transcription_masking': supervision_transcription_masking or True,
                'notification_workflow': notification_workflow
                or DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER,
            },
            title='Flexible Extraction',
            description='Manually transcribe fields marked for review',
        )


class ReprocessingBlock(Block):
    """Reprocessing block enables a second extraction attempt if documents were initially
    confidently mis-classified by the machine. When an end-user specifies that a document layout
    is incorrect during Manual Identification, Manual Transcription, or Flexible Extraction, the
    flow will reach the Reprocessing block which will mark correctly classified documents as
    "complete" status, and misclassified documents with "reprocess" status will be processed in a
    second execution of the flow. This block should be placed before the SubmissionCompleteBlock
    to enable reprocessing.

    Mandatory parameters:

    :param submission: Submission object
    """

    IDENTIFIER = 'REPROCESSING'

    def __init__(
        self,
        reference_name: Optional[str],
        submission: Any,
        parent_flow: str = '${workflow.definition.identifier}',
        idp_wf_config: Any = None,
        trigger: Any = workflow_input(Inputs.Trigger),
    ):
        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            title='Reprocessing',
            description='Reprocess flow if required.',
            input={
                'idp_wf_config': idp_wf_config or extract_config(),
                'trigger': trigger,
                'submission': submission,
                'parent_flow': parent_flow,
            },
        )


class SubmissionCompleteBlock(Block):
    """Submission complete block finalizes submission processing and updates reporting data.
    **This block should be called at the END of every flow** that
    uses blocks included in the ``flows_sdk.implementations.idp_v34`` library.
    The block requires both the ``submission`` object and a ``payload`` to be passed in.

    Mandatory parameters:

    :param submission: Submission object
    :param payload: Object to pass to downstream systems

    Parameters with defaults:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
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
    :param exclude_auto_transcribe_fields_from_qa: Defines fields that are marked as auto-transcribe
        in layout should be excluded from QA or not.
        defaults to workflow_input(Settings.ExcludeAutoTranscribeFieldsFromQA)
    :param is_reprocessing: boolean to handle execution when reprocessing
        defaults to False

    Example usage::

        submission_complete = SubmissionCompleteBlock(
            reference_name='complete_submission',
            submission=flexible_extraction.output('submission')
        )
    """

    IDENTIFIER = 'SUBMISSION_COMPLETE_4'

    def __init__(
        self,
        submission: str,
        is_reprocessing: Union[str, bool] = False,
        reference_name: Optional[str] = None,
        nlc_qa_sampling_ratio: Union[str, int] = workflow_input(Settings.SemiQaSampleRate),
        field_id_qa_enabled: Union[str, bool] = workflow_input(Settings.FieldIdQaEnabled),
        field_id_qa_sampling_ratio: Union[str, int] = workflow_input(Settings.FieldIdQaSampleRate),
        table_id_qa_enabled: Union[str, bool] = workflow_input(Settings.TableIdQaEnabled),
        table_id_qa_sampling_ratio: Union[str, int] = workflow_input(Settings.TableIdQaSampleRate),
        transcription_qa_enabled: Union[str, bool] = workflow_input(
            Settings.TranscriptionQaEnabled
        ),
        transcription_structured_entry_qa_sample_rate: Union[str, float] = workflow_input(
            Settings.TranscriptionStructuredEntryQaSampleRate
        ),
        transcription_structured_signature_qa_sample_rate: Union[str, float] = workflow_input(
            Settings.TranscriptionStructuredSignatureQaSampleRate
        ),
        transcription_structured_checkbox_qa_sample_rate: Union[str, float] = workflow_input(
            Settings.TranscriptionStructuredCheckboxQaSampleRate
        ),
        transcription_semi_structured_qa_sample_rate: Union[str, float] = workflow_input(
            Settings.TranscriptionSemiStructuredQaSampleRate
        ),
        table_cell_transcription_qa_enabled: Union[str, bool] = workflow_input(
            Settings.TableCellTranscriptionQaEnabled
        ),
        table_cell_transcription_qa_sample_rate: Union[str, int] = workflow_input(
            Settings.TableCellTranscriptionQaSampleRate
        ),
        auto_qa_sampling_rate_enabled: Union[str, bool] = workflow_input(
            Settings.AutoQaSamplingRateEnabled
        ),
        exclude_auto_transcribe_fields_from_qa: Union[str, bool] = workflow_input(
            Settings.ExcludeAutoTranscribeFieldsFromQA
        ),
        payload: Any = None,
    ) -> None:
        inputs = {
            'submission': submission,
            'is_reprocessing': is_reprocessing,
            'nlc_qa_sampling_ratio': nlc_qa_sampling_ratio,
            'field_id_qa_enabled': field_id_qa_enabled,
            'field_id_qa_sampling_ratio': field_id_qa_sampling_ratio,
            'table_id_qa_enabled': table_id_qa_enabled,
            'table_id_qa_sampling_ratio': table_id_qa_sampling_ratio,
            'transcription_qa_enabled': transcription_qa_enabled,
            'transcription_structured_entry_qa_sample_rate': (
                transcription_structured_entry_qa_sample_rate
            ),
            'transcription_structured_checkbox_qa_sample_rate': (
                transcription_structured_checkbox_qa_sample_rate
            ),
            'transcription_structured_signature_qa_sample_rate': (
                transcription_structured_signature_qa_sample_rate
            ),
            'transcription_semi_structured_qa_sample_rate': (
                transcription_semi_structured_qa_sample_rate
            ),
            'table_cell_transcription_qa_enabled': table_cell_transcription_qa_enabled,
            'table_cell_transcription_qa_sample_rate': table_cell_transcription_qa_sample_rate,
            'auto_qa_sampling_rate_enabled': auto_qa_sampling_rate_enabled,
            'exclude_auto_transcribe_fields_from_qa': exclude_auto_transcribe_fields_from_qa,
        }

        if payload is not None:
            inputs['payload'] = payload

        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input=inputs,
            title='Complete',
            description='Finalize submission processing and update reporting data',
        )


class SetTransformedOutputBlock(Block):
    """
    Set Transformed Output block sets the transformed output for the provided submission. This can
    later be used to send the transformed data downstream using output blocks. For more information
    see https://docs.hyperscience.com/#retrieving-transformed-submissions.

    Mandatory parameters:

    :param submission: Submission object
    :param transformed_output: Object that will be set as the transformed output for this submission
    """

    IDENTIFIER = 'SET_TRANSFORMED_OUTPUT'

    def __init__(
        self, submission: str, transformed_output: str, reference_name: Optional[str] = None
    ) -> None:
        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input={'submission': submission, 'transformed_output': transformed_output},
            title='Set Transformed Output',
            description='Sets the transformed output for the provided submission',
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


class IdpCustomSupervisionBlock(Block):
    """An IDP wrapper for the Custom Supervision block. It has the same functionality,
    but handles reading/writing data from the IDP database.

    Mandatory parameters:

    :param submission: Submission object
    :param task_purpose: the custom task name that's given to all supervision tasks that run
        through a particular instance of a custom supervision block. This can be used to filter
        tasks in the task queue.
    :param supervision_template: JSON used for configuration of the Custom Supervision Task.

    Parameters with defaults:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
    :param supervision_transcription_masking: Prevents users from inputting invalid
        characters during the Custom Supervision task,
        defaults to True
    :param task_restrictions: Defines what users can access Supervision tasks created
        by this block,
        defaults to []
    :param page_ids: This is an optional parameter. If left empty, the IDP wrapper will, by
        default, pull in all pages in the submission. Adding a list of page IDs will override
        the default list of pages.
        defaults to []
    :param notification_workflow: Notification flow name to run when the submission
        enters Custom Supervision (which is called within the IDP Custom Supervision block),
        defaults to DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER
    :param title: UI-visible title of the block. Defaults to 'IDP Custom Supervision'
    :type title: Optional[str]
    :param description: Description of the block. Both useful for documentation purpose and visible
            to users in the Flow studio. Defaults to 'IDP Custom Supervision'
    :type description: Optional[str]

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
                                    'data_identifier': '2afd7a67-ddee-484f-ab6b-2d292752e5ee',
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

    IDENTIFIER = 'IDP_CUSTOM_SUPERVISION_2'

    def __init__(
        self,
        submission: Any,
        task_purpose: str,
        supervision_template: Any,
        reference_name: Optional[str] = None,
        supervision_transcription_masking: bool = True,
        task_restrictions: Optional[List[Any]] = None,
        page_ids: Optional[List[int]] = None,
        notification_workflow: str = DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER,
        title: Optional[str] = 'IDP Custom Supervision',
        description: Optional[str] = 'IDP Custom Supervision',
    ) -> None:
        if not task_restrictions:
            task_restrictions = []
        if not page_ids:
            page_ids = []

        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input={
                'supervision_template': supervision_template,
                'task_purpose': task_purpose,
                'submission': submission,
                'task_restrictions': task_restrictions,
                'supervision_transcription_masking': supervision_transcription_masking,
                'page_ids': page_ids,
                'notification_workflow': notification_workflow,
            },
            title=title,
            description=description,
        )


class IDPFullPageTranscriptionBlock(Block):
    """
    IDP Full Page Transcription Block machine-transcribes the unassigned pages in a submission

    Mandatory parameters:

    :param submission: submission object that includes the raw documents that need to be transcribed

    Optional Parameters:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
    :param app_metadata: used for capturing information about the flow

    Example usage::

        # This is one way to obtain the submission object (using SubmissionBootstrapBlock)
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

    IDENTIFIER = 'FULL_PAGE_TRANSCRIPTION_SUBMISSION'

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
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input=inputs,
            title=title,
            description=description,
        )


class IDPImageCorrectionBlock(Block):
    """
    IDP Image Correction Block rotates and de-skews tilted/skewed images so that they are more
    transcription-friendly

    Mandatory parameters:

    :param submission: submission object that includes the raw documents that need to be
        image-corrected

    Optional Parameters:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
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

    IDENTIFIER = 'IMAGE_CORRECTION_SUBMISSION'

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
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input=inputs,
            title=title,
            description=description,
        )
