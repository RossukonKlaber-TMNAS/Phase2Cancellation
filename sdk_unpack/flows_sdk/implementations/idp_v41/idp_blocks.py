from typing import Any, Dict, List, Optional, Sequence, Union

from flows_sdk.blocks import Block, IOBlock, Outputs
from flows_sdk.implementations.idp_v41.idp_values import (
    DEFAULT_IDP_CORE_IDENTIFIER,
    DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER,
    IDP_OUTPUT_ROLE,
    IdpWorkflowConfig,
    Inputs,
    Settings,
    get_idp_wf_inputs,
)
from flows_sdk.types import CompatibilitySpec
from flows_sdk.utils import workflow_input


class IDPCoreBlock(Block):
    """IDP core block includes the steps to process the passed documents into machine-readable
    output.

    Mandatory parameters:

    :parameter idp_wf_config: IdpWorkflowConfig object with all flow-level configuration settings
        for IDP

    Parameters with defaults:

    :param reference_name: unique reference name within a flow, a unique one will be generated when
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
    :param trigger: the trigger input from a connector - if not set explicitly,
        it will default to the workflow input trigger (which is where this value is normally found)
    :param layout_release_uuid: Layout Release UUID at submission creation time,
        defaults to workflow_input(Settings.LayoutReleaseUuid)
    :param s3_config: Specify Amazon S3 credentials for submission retrieval store.
        Expects a json expression: ``{"aws_access_key_id": "X", "aws_secret_access_key": "Y"}``,
        defaults to workflow_input(Settings.SubmissionBootstrapS3Config)
    :param s3_endpoint_url: Endpoint URL for S3 submission retrieval store,
        defaults to workflow_input(Settings.SubmissionBootstrapS3EndpointUrl)
    :param ocs_config: OCS Configuration for downloading submission data,
        defaults to workflow_input(Settings.SubmissionBootstrapOCSConfig)
    :param http_config:
        An optional system secret field expressing the HTTP Configuration for
        downloading submission data. The content is expected to be a json formatted as:
        ``{"username": "X", "password": "Y", "ssl_cert": "CA bundle filename"}``,
        defaults to workflow_input(Settings.SubmissionBootstrapHTTPConfig)
    :param notification_workflow: Notification flow name to run when the submission is initialized,
        defaults to workflow_input(Settings.SubmissionBootstrapNotificationWorkflow)
    :param workflow_uuid: UUID of the triggered workflow version,
        defaults to workflow_input(Inputs.WorkflowUuid)
    :param workflow_name: Name of the triggered workflow,
        defaults to workflow_input(Inputs.WorkflowName)
    :param workflow_version: Version of the triggered workflow,
        defaults to workflow_input(Inputs.WorkflowVersion)
    :param submission: Submission object

    Example usage::

        submission_bootstrap = SubmissionBootstrapBlock(reference_name='submission_bootstrap')
    """

    IDENTIFIER = 'SUBMISSION_BOOTSTRAP_2'

    def __init__(
        self,
        reference_name: Optional[str] = None,
        trigger: str = workflow_input(Inputs.Trigger),
        layout_release_uuid: str = workflow_input(Settings.LayoutReleaseUuid),
        s3_config: str = workflow_input(Settings.SubmissionBootstrapS3Config),
        s3_endpoint_url: str = workflow_input(Settings.SubmissionBootstrapS3EndpointUrl),
        ocs_config: str = workflow_input(Settings.SubmissionBootstrapOCSConfig),
        http_config: Optional[str] = workflow_input(Settings.SubmissionBootstrapHTTPConfig),
        abs_auth_type: Optional[str] = workflow_input(Settings.SubmissionBootstrapABSAuthType),
        abs_account_url: Optional[str] = workflow_input(Settings.SubmissionBootstrapABSAccountUrl),
        abs_tenant_id: Optional[str] = workflow_input(Settings.SubmissionBootstrapABSTenantId),
        abs_client_id: Optional[str] = workflow_input(Settings.SubmissionBootstrapABSClientId),
        abs_client_secret: Optional[str] = workflow_input(
            Settings.SubmissionBootstrapABSClientSecret
        ),
        abs_authority_host: Optional[str] = workflow_input(
            Settings.SubmissionBootstrapABSAuthorityHost
        ),
        abs_account_name: Optional[str] = workflow_input(
            Settings.SubmissionBootstrapABSAccountName
        ),
        abs_account_key: Optional[str] = workflow_input(Settings.SubmissionBootstrapABSAccountKey),
        notification_workflow: Optional[str] = workflow_input(
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
                '$trigger': trigger,
                'layout_release_uuid': layout_release_uuid,
                's3_config': s3_config,
                's3_endpoint_url': s3_endpoint_url,
                'ocs_config': ocs_config,
                'http_config': http_config,
                'abs_auth_type': abs_auth_type,
                'abs_account_url': abs_account_url,
                'abs_tenant_id': abs_tenant_id,
                'abs_client_id': abs_client_id,
                'abs_client_secret': abs_client_secret,
                'abs_authority_host': abs_authority_host,
                'abs_account_name': abs_account_name,
                'abs_account_key': abs_account_key,
                'notification_workflow': notification_workflow,
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
        from the case. Keep in mind this option is only relevant when adding to cases.
        Defaults to workflow_input(Settings.CollationDedupeFiles)
    :param remove_from_cases: This parameter accepts an array of JSON objects that contains
        information on how documents or pages should be removed from a pre-existing case.
        Currently, the only way to de-collate from a case is by the ids of the Documents or
        Pages within a given case, defaults to workflow_input(Settings.CollationRemoveFromCases)

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
        Defaults to workflow_input(Settings.CollationRetentionPeriod)
    :param refresh_retention_period: If ``True``, (re)applies Retention Period parameter to all
        cases passed into the block. If ``False``, only updates those without a pre-existing
        deletion date. Defaults to workflow_input(Settings.CollationRefreshRetentionPeriod)

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
                'dedupe_files': dedupe_files,
                'remove_from_cases': remove_from_cases,
                'retention_period': retention_period,
                'refresh_retention_period': refresh_retention_period,
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
        defaults to workflow_input(Settings.RotationCorrectionEnabled)
    :param mobile_processing_enabled: Improves the machine readability of photo
        captured documents,
        defaults to workflow_input(Settings.MobileProcessingEnabled)
    :param file_transcription_enabled: Improves the transcription speed of pdf files.
        Make sure that the "Image Correction" option is disabled and the pdfs you
        submit do not contain any rotated images
        defaults to workflow_input(Settings.FileTranscriptionEnabled)
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

    IDENTIFIER = 'MACHINE_CLASSIFICATION_7'

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
        layout_id_dealbreaker: str = workflow_input(Settings.LayoutIdDealbreaker),
        layout_id_dealbreaker_bypass: str = workflow_input(Settings.LayoutIdDealbreakerBypass),
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
                'rotation_correction_enabled': rotation_correction_enabled,
                'mobile_processing_enabled': mobile_processing_enabled,
                'file_transcription_enabled': file_transcription_enabled,
                'layout_id_dealbreaker': layout_id_dealbreaker,
                'layout_id_dealbreaker_bypass': layout_id_dealbreaker_bypass,
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
        defaults to workflow_input(Settings.ManualClassificationTaskRestrictions)
    :param notification_workflow: Notification flow name to run when the submission
        enters Manual Classification,
        defaults to workflow_input(Settings.ManualClassificationNotificationWorkflow)
    :param nlc_enabled: Enables workflow to manage a model for automated classification
        of semi-structured and additional layout variations,
        defaults to workflow_input(Settings.SemiStructuredClassification)
    :param nlc_target_accuracy: Classification Target Accuracy,
        defaults to workflow_input(Settings.SemiTargetAccuracy)
    :param mobile_processing_enabled: Improves the machine readability of photo
        captured document,
        defaults to workflow_input(Settings.MobileProcessingEnabled)
    :param vpc_registration_threshold: Structured pages above this threshold will be
        automatically matched to a layout variation when performing light vpc registration
        in the doc-org task,
        defaults to workflow_input(Settings.StructuredLayoutMatchThreshold)

    Example usage::

        manual_classification = ManualClassificationBlock(
            reference_name='manual_classification',
            submission=machine_classification.output('submission'),
            api_params=submission_bootstrap.output('result.api_params'),
        )
    """

    IDENTIFIER = 'MANUAL_CLASSIFICATION_5'

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
        vpc_registration_threshold: Optional[str] = workflow_input(
            Settings.StructuredLayoutMatchThreshold
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
                'notification_workflow': notification_workflow,
                'vpc_registration_threshold': vpc_registration_threshold,
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

    :param layout_release_uuid: Layout Release UUID at submission creation time,
        defaults to workflow_input(Settings.LayoutReleaseUuid)
    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
    :param manual_field_id_enabled: Enables manual identification when applicable,
        defaults to workflow_input(Settings.ManualFieldIdEnabled)
    :param force_required_missing_entries_to_sv:
        defaults to workflow_input( Settings.ForceRequiredEntriesToSV )
    :param field_id_target_accuracy: Field ID Target Accuracy,
        defaults to workflow_input(Settings.FieldIdTargetAccuracy)
    :param table_id_target_accuracy: Table ID Target Accuracy,
        defaults to workflow_input(Settings.TableIdTargetAccuracy)
    :param id_target_accuracies:
        defaults to workflow_input( Settings.IdentificationTargetAccuracies )

    Example usage::

        machine_identification = MachineIdentificationBlock(
            reference_name='machine_identification',
            submission=manual_classification.output('submission'),
            api_params=submission_bootstrap.output('result.api_params'),
        )
    """

    IDENTIFIER = 'MACHINE_IDENTIFICATION_8'

    def __init__(
        self,
        submission: Any,
        api_params: Any,
        layout_release_uuid: Any = workflow_input(Settings.LayoutReleaseUuid),
        reference_name: Optional[str] = None,
        manual_field_id_enabled: str = workflow_input(Settings.ManualFieldIdEnabled),
        force_required_missing_entries_to_sv: str = workflow_input(
            Settings.ForceRequiredEntriesToSV
        ),
        field_id_target_accuracy: str = workflow_input(Settings.FieldIdTargetAccuracy),
        table_id_target_accuracy: str = workflow_input(Settings.TableIdTargetAccuracy),
        id_target_accuracies: str = workflow_input(Settings.IdentificationTargetAccuracies),
    ) -> None:
        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input={
                'submission': submission,
                'layout_release_uuid': layout_release_uuid,
                'api_params': api_params,
                'manual_field_id_enabled': manual_field_id_enabled,
                'force_required_missing_entries_to_sv': force_required_missing_entries_to_sv,
                'field_id_target_accuracy': field_id_target_accuracy,
                'table_id_target_accuracy': table_id_target_accuracy,
                'id_target_accuracies': id_target_accuracies,
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
        defaults to workflow_input(Settings.ManualFieldIdTaskRestrictions)
    :param manual_field_id_enabled: Enables manual identification when applicable,
        defaults to workflow_input(Settings.ManualFieldIdEnabled)
    :param layout_release_uuid: Layout Release UUID at submission creation time,
        defaults to workflow_input(Settings.LayoutReleaseUuid)
    :param notification_workflow: Notification flow name to run when the submission
        enters Manual Identification,
        defaults to workflow_inputSettings.ManualFieldIdNotificationWorkflow

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
    :param force_normalization_errors_to_sv:
        defaults to workflow_input( Settings.ForceNormalizationErrorsToSV )
    :param force_required_blank_entries_to_sv:
        defaults to workflow_input( Settings.ForceRequiredEntriesToSV )
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
    :param field_target_accuracies:
        defaults to workflow_input( Settings.FieldTargetAccuracies )
    :param column_target_accuracies: Deprecated since R40.1 and will be removed in R43
        defaults to workflow_input( Settings.ColumnTargetAccuracies )

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
        force_normalization_errors_to_sv: str = workflow_input(
            Settings.ForceNormalizationErrorsToSV
        ),
        force_required_blank_entries_to_sv: str = workflow_input(Settings.ForceRequiredEntriesToSV),
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
        field_target_accuracies: str = workflow_input(Settings.FieldTranscriptionTargetAccuracies),
        column_target_accuracies: str = workflow_input(
            Settings.ColumnTranscriptionTargetAccuracies
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
                'force_normalization_errors_to_sv': force_normalization_errors_to_sv,
                'force_required_blank_entries_to_sv': force_required_blank_entries_to_sv,
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
                'field_target_accuracies': field_target_accuracies,
                'column_target_accuracies': column_target_accuracies,
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
        defaults to workflow_input(Settings.ManualTranscriptionSupervisionTranscriptionMasking)
    :param table_output_manual_review: Always generates a table transcription task if the
        layout contains a table. If disabled, a table transcription task will only be
        generated if one or more cells have transcribed values below the defined thresholds,
        defaults to workflow_input(Settings.ManualTranscriptionTableOutputManualReview)
    :param always_supervise_blank_cells: If enabled, always send blank cells in transcribed
        tables to be supervised manually, regardless of confidence
        defaults to workflow_input(Settings.ManualTranscriptionAlwaysSuperviseBlankCells)
    :param task_restrictions: Defines what users can access Supervision tasks for
        submission from a particular source or submissions matching a specific layout,
        defaults to workflow_input(Settings.ManualTranscriptionTaskRestrictions)
    :param manual_transcription_enabled: Enables manual transcription when applicable,
        defaults to workflow_input(Settings.ManualTranscriptionEnabled)
    :param notification_workflow: Notification flow name to run when the submission
        enters Manual Transcription,
        defaults to workflow_input(Settings.ManualTranscriptionNotificationWorkflow)

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
                'supervision_transcription_masking': supervision_transcription_masking,
                'table_output_manual_review': table_output_manual_review,
                'always_supervise_blank_cells': always_supervise_blank_cells,
                'notification_workflow': notification_workflow,
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
        defaults to workflow_input(Settings.FlexibleExtractionSupervisionTranscriptionMasking)
    :param task_restrictions: Defines what users can access Supervision tasks created
        by this block,
        defaults workflow_input(Settings.FlexibleExtractionTaskRestrictions)
    :param layout_release_uuid: Layout Release UUID at submission creation time,
        defaults to workflow_input(Settings.LayoutReleaseUuid)
    :param notification_workflow: Notification flow name to run when the submission
        enters Flexible Extraction,
        defaults to workflow_input(Settings.FlexibleExtractionNotificationWorkflow)

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
                'supervision_transcription_masking': supervision_transcription_masking,
                'notification_workflow': notification_workflow,
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

    **How the Reprocessing block works**

    The Reprocessing block examines whether any documents within the submission have been marked
    with an incorrect layout, and if so, redirects the submission to the classification step for
    proper classification. It does this by recursively calling the same flow or subflow with the
    same inputs and documents, but with the addition of a status key for each document to denote
    which were marked with an incorrect layout during supervision.

    .. note::
        The Reprocessing block works in tandem with the “Mark Incorrect Layout” option presented
        to users during Manual Identification, Manual Transcription, and Flexible Extraction
        supervision interfaces introduced in R38. Include the Reprocessing block in all custom
        flows in order to take advantage of this feature. The feature will remain selectable
        in supervision interfaces even if the Reprocessing block is not included in the flow.

    The initial flow run will pause execution at the Reprocessing block until the recursive flow
    has completed, at which point the initial flow will resume to finish its execution. If an
    error occurs during the execution of the recursive flow, that error will be raised to the
    Reprocessing block of the initial flow.

    .. note::
        The recursive flow run is linked with the same correlation_id as the initial flow run
        and the submission. Users can click the “View related flow runs” link on the left
        sidebar of the initial flow run to view any recursive flow runs.

    As expected, recursively calling the same flow may cause some blocks to run again, resulting
    in unnecessary work being performed, or work which doesn't gracefully handle duplications
    (non-idempotent blocks). To mitigate this, certain Hyperscience-provided blocks - including
    Submission Initialization, Machine Collation, and Machine Classification - detect when the
    submission object already contains the output from its block to avoid re-execution. It's a
    best practice to build custom blocks such that they are idempotent and reentrant; if that's
    not feasible, you can add similar logic to custom blocks which do not depend on the layout
    for the documents being processed. Common methods for handling this include:

    * Iterating through each status key within the submission.document[] collection to see if
      any documents are set to “reprocess”.

    * Inspecting if the submission object already contains a key or value explicitly defined
      by the custom code block.

    **Recommended Placement for the Reprocessing Block**

    * The Reprocessing block should not be placed before any supervision blocks which allow
      users to mark a document with an incorrect layout. These supervision blocks include
      Manual Identification, Manual Transcription and Flexible Extraction.

    * The Reprocessing block should always be placed before the SubmissionCompete Block.

    * The Reprocessing block can be used with flows which include multiple branches and
      conditionals; however, it's recommended to ensure the Reprocessing block is executed
      to honor user's selection of marking layouts incorrectly when supervising documents.

    * In general, any custom logic that is to be performed after data has been extracted from
      documents should be placed after the Reprocessing block. To avoid duplicate executions of
      this custom logic, it is recommended to separate the document processing blocks - inclusive
      of the Reprocessing block - from the custom logic. This can be handled in different ways:

        * Split the flow into separate subflows, where the Reprocessing block is in a subflow
          that does not contain the custom logic.

        * Add a decision to bypass the custom logic if the Reprocessing block was triggered.
          With this method, the recursive flow run will execute the custom logic, and the initial
          flow run will bypass the logic.

    Mandatory parameters:

    :param submission: Submission object
    """

    IDENTIFIER = 'REPROCESSING_2'

    def __init__(
        self,
        reference_name: Optional[str],
        submission: Any,
        parent_flow: str = '${workflow.definition.identifier}',
        # This name could be more generic (like workflow_input), but changing it would
        # require releasing a new version of the block and would break compatibility with
        # existing flows.
        idp_wf_config: Any = '${workflow.input}',
        trigger: Any = workflow_input(Inputs.Trigger),
        reprocessing_enabled: Union[str, bool] = workflow_input(Settings.ReprocessingEnabled),
    ):
        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            title='Reprocessing',
            description='Reprocess flow if required.',
            input={
                'reprocessing_enabled': reprocessing_enabled,
                'idp_wf_config': idp_wf_config,
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

    :param data: Optional JSON structure that extends the data used to populate the
        supervision_template. This is intended to append to the data already gathered by the IDP
        wrapper. If there are any conflicting keys, the keys in this input will take precedent.
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
        defaults to IDP_SUBMISSION_NOTIFY_NAME
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
            data={
                'documents': [
                    {
                        'id': 2,
                        'layout_uuid': 'e31c3cbf-dcea-44fd-a052-902463c6040f',
                        'layout_name': 'layout_name',
                        'page_count': 2,
                        'read_only': False,
                    }
                ]
            }
            supervision_transcription_masking=False,
        )
    """

    IDENTIFIER = 'IDP_CUSTOM_SUPERVISION_2'

    def __init__(
        self,
        submission: Any,
        task_purpose: str,
        supervision_template: Any,
        data: Optional[Dict[str, Any]] = None,
        reference_name: Optional[str] = None,
        supervision_transcription_masking: Union[str, bool] = True,
        task_restrictions: Union[str, Optional[List[Any]]] = None,
        page_ids: Union[str, List[int], None] = None,
        notification_workflow: str = DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER,
        title: Optional[str] = 'IDP Custom Supervision',
        description: Optional[str] = 'IDP Custom Supervision',
    ) -> None:
        if not task_restrictions:
            task_restrictions = []
        if not page_ids:
            page_ids = []
        if not data:
            data = {}

        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input={
                'supervision_template': supervision_template,
                'data': data,
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
    IDP Full Page Transcription Block machine-transcribes the documents contained in a submission

    Mandatory parameters:

    :param submission: submission object that includes the raw documents that need to be transcribed

    Optional Parameters:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
    :param app_metadata: used for capturing information about the flow
    :param language_family: language family to use when instantiating the underlying transcription
        model. If not provided, the system will default to `latin`. Language families are single
        word lowercase strings, e.g., `latin`, `arabic`, `korean`, `chinese`.
        You can read more about language families for your Hyperscience version in the
        Supported Languages section of the documentation
        https://help.hyperscience.com/docs/search?searchtext="Supported%20Languages"&selectedTab=2

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

    IDENTIFIER = 'FULL_PAGE_TRANSCRIPTION_SUBMISSION_2'

    def __init__(
        self,
        submission: str,
        reference_name: Optional[str] = None,
        title: str = 'Full Page Transcription (Submission)',
        description: str = 'Transcribes the documents included in a submission',
        app_metadata: Optional[List[str]] = None,
        language_family: Optional[str] = None,
    ) -> None:
        inputs: Dict[Any, Any] = {
            'submission': submission,
            'language_family': language_family,
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


class DocumentRendererBlock(Block):
    """
    Document File Generator Block renders a document into a PDF and stores it in the Blob storage.

    This block should be placed ALWAYS after a Reprocessing block (if there is any) so that it
    is not possible to have more changes in the documents' organisation.

    Mandatory parameters:

    :param submission: submission object that includes the raw documents that need to be rendered.

    Optional parameters:

    :param document_rendering_enabled: a boolean that enables or disables the document rendering.
      Default is False.
    :param document_rendering_mime_type: the mime type of the document to be generated. Default is
        'application/pdf'
    :param document_rendering_unit: the unit of the document to be generated. Default is 'inches'
    :param document_rendering_height: the height of the document to be generated. Default is 11
    :param document_rendering_width: the width of the document to be generated. Default is 8.5
    :param document_rendering_quality: Quality of pages (images) appended to the resulting document
      as a percentage (recommended 50%). Higher quality results in a larger file size for the
      generated PDF.
    :param is_reprocessing: boolean to handle execution when reprocessing
        defaults to False

    Example usage::

        # Use the output of the reprocessing block.
        reprocessing = ReprocessingBlock(reference_name='reprocessing')

        document_renderer_block = DocumentRendererBlock(
            reference_name='document_renderer',
            submission=reprocessing.output(submission),
            document_rendering_enabled=True,
            document_rendering_unit='in',
            document_rendering_width=8.5,
            document_rendering_height=11,
            document_rendering_quality=50
            is_reprocessing=reprocessing.output('is_reprocessing')
        )

        output_ref = document_renderer_block.output()

    Example content of output_ref::

        {
            'document_files': {
                [
                    {
                        'document_id': "1",
                        'blob_uuid': 'f42fc9af-b551-4403-aba6-d0eba2c41973',
                        'mime_type': 'application/pdf',
                        'height_in_mm': 279.4,
                        'width_in_mm': 215.9,
                        'quality': 50,
                    }
                ]
            },
            'submission': {
                ...
            }
        }

    """

    IDENTIFIER = 'DOCUMENT_RENDERER'

    def __init__(
        self,
        submission: str,
        is_reprocessing: Union[str, bool] = False,
        title: str = 'Document Renderer',
        description: str = 'Renders a document into a PDF',
        reference_name: Optional[str] = None,
        document_rendering_enabled: Union[bool, str] = workflow_input(
            Settings.DocumentRenderingEnabled
        ),
        document_rendering_mime_type: str = workflow_input(Settings.DocumentRenderingMimeType),
        document_rendering_unit: str = workflow_input(Settings.DocumentRenderingUnit),
        document_rendering_height: Union[str, float] = workflow_input(
            Settings.DocumentRenderingHeight
        ),
        document_rendering_width: Union[str, float] = workflow_input(
            Settings.DocumentRenderingWidth
        ),
        document_rendering_quality: Union[str, int] = workflow_input(
            Settings.DocumentRenderingQuality
        ),
    ) -> None:
        inputs = {
            'submission': submission,
            'is_reprocessing': is_reprocessing,
            'document_rendering_enabled': document_rendering_enabled,
            'document_rendering_mime_type': document_rendering_mime_type,
            'document_rendering_unit': document_rendering_unit,
            'document_rendering_height': document_rendering_height,
            'document_rendering_width': document_rendering_width,
            'document_rendering_quality': document_rendering_quality,
        }
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
    :param rotation_correction_enabled: Identifies and corrects the orientation of images.
        Enabled by default.
    :param mobile_processing_enabled: Improves the machine readability of photo captured documents.
        Disabled by default.
    :param language_family: language family to use when performing image correction.
        If not provided, the system will default to `latin`. Language families are single
        word lowercase strings, e.g., `latin`, `arabic`, `korean`, `chinese`.
        You can read more about language families for your Hyperscience version in the
        Supported Languages section of the documentation
        https://help.hyperscience.com/docs/search?searchtext="Supported%20Languages"&selectedTab=2
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
        language_family: Optional[str] = None,
        title: str = 'Image Correction (Submission)',
        description: str = 'Rotate and de-skew documents included in a submission',
        app_metadata: Optional[List[str]] = None,
    ) -> None:
        inputs: Dict[Any, Any] = {
            'submission': submission,
            'rotation_correction_enabled': rotation_correction_enabled,
            'mobile_processing_enabled': mobile_processing_enabled,
            'language_family': language_family,
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


IDP_CORE_INPUTS_MAPPING = {
    SubmissionBootstrapBlock.IDENTIFIER: {
        'submission': workflow_input('submission'),
        'notification_workflow': workflow_input('notification_workflow_initialization'),
        's3_config': workflow_input('submission_bootstrap_s3_config'),
        's3_endpoint_url': workflow_input('submission_bootstrap_s3_endpoint_url'),
        'ocs_config': workflow_input('submission_bootstrap_ocs_config'),
        'http_config': workflow_input('submission_bootstrap_http_config'),
        'abs_auth_type': workflow_input('submission_bootstrap_abs_auth_type'),
        'abs_account_url': workflow_input('submission_bootstrap_abs_account_url'),
        'abs_tenant_id': workflow_input('submission_bootstrap_abs_tenant_id'),
        'abs_client_id': workflow_input('submission_bootstrap_abs_client_id'),
        'abs_client_secret': workflow_input('submission_bootstrap_abs_client_secret'),
        'abs_authority_host': workflow_input('submission_bootstrap_abs_authority_host'),
        'abs_account_key': workflow_input('submission_bootstrap_abs_account_key'),
        'abs_account_name': workflow_input('submission_bootstrap_abs_account_name'),
        'workflow_uuid': workflow_input(Inputs.WorkflowUuid),
        'workflow_name': workflow_input(Inputs.WorkflowName),
        'workflow_version': workflow_input(Inputs.WorkflowVersion),
    },
    MachineCollationBlock.IDENTIFIER: {
        'dedupe_files': workflow_input('machine_collation_dedupe_files'),
        'remove_from_cases': workflow_input('machine_collation_remove_from_cases'),
        'retention_period': workflow_input('machine_collation_retention_period'),
        'refresh_retention_period': workflow_input('machine_collation_refresh_retention_period'),
    },
    MachineClassificationBlock.IDENTIFIER: {
        'rotation_correction_enabled': workflow_input(
            'machine_classification_rotation_correction_enabled'
        ),
        'mobile_processing_enabled': workflow_input(
            'machine_classification_mobile_processing_enabled'
        ),
        'file_transcription_enabled': workflow_input(
            'machine_classification_file_transcription_enabled'
        ),
        'layout_release_uuid': workflow_input(Settings.LayoutReleaseUuid),
        'vpc_registration_threshold': workflow_input(Settings.StructuredLayoutMatchThreshold),
        'nlc_enabled': workflow_input(Settings.SemiStructuredClassification),
        'nlc_target_accuracy': workflow_input(Settings.SemiTargetAccuracy),
        'nlc_doc_grouping_logic': workflow_input(Settings.SemiDocGroupingLogic),
    },
    ManualClassificationBlock.IDENTIFIER: {
        'notification_workflow': workflow_input('notification_workflow_classification'),
        'task_restrictions': workflow_input('manual_classification_task_restrictions'),
        'layout_release_uuid': workflow_input(Settings.LayoutReleaseUuid),
        'manual_nlc_enabled': workflow_input(Settings.ManualNlcEnabled),
        'nlc_enabled': workflow_input(Settings.SemiStructuredClassification),
        'nlc_target_accuracy': workflow_input(Settings.SemiTargetAccuracy),
        'mobile_processing_enabled': workflow_input(
            'machine_classification_mobile_processing_enabled'
        ),
    },
    MachineIdentificationBlock.IDENTIFIER: {
        'layout_release_uuid': workflow_input(Settings.LayoutReleaseUuid),
        'manual_field_id_enabled': workflow_input(Settings.ManualFieldIdEnabled),
        'force_required_missing_entries_to_sv': workflow_input(Settings.ForceRequiredEntriesToSV),
        'field_id_target_accuracy': workflow_input(Settings.FieldIdTargetAccuracy),
        'table_id_target_accuracy': workflow_input(Settings.TableIdTargetAccuracy),
        'id_target_accuracies': workflow_input(Settings.IdentificationTargetAccuracies),
    },
    ManualIdentificationBlock.IDENTIFIER: {
        'notification_workflow': workflow_input('notification_workflow_identification'),
        'task_restrictions': workflow_input('manual_identification_task_restrictions'),
        'manual_field_id_enabled': workflow_input(Settings.ManualFieldIdEnabled),
        'layout_release_uuid': workflow_input(Settings.LayoutReleaseUuid),
    },
    MachineTranscriptionBlock.IDENTIFIER: {
        'layout_release_uuid': workflow_input(Settings.LayoutReleaseUuid),
        'transcription_model': workflow_input(Settings.TranscriptionModel),
        'finetuning_only_trained_layouts': workflow_input(Settings.FinetuningOnlyTrainedLayouts),
        'force_normalization_errors_to_sv': workflow_input(Settings.ForceNormalizationErrorsToSV),
        'force_required_blank_entries_to_sv': workflow_input(Settings.ForceRequiredEntriesToSV),
        'transcription_overrides': workflow_input(Settings.TranscriptionOverrides),
        'structured_text_target_accuracy': workflow_input(Settings.StructuredTextTargetAccuracy),
        'structured_text_confidence_threshold': workflow_input(Settings.StructuredTextThreshold),
        'structured_text_acceptable_confidence': workflow_input(
            Settings.StructuredTextMinLegThreshold
        ),
        'semi_structured_text_target_accuracy': workflow_input(
            Settings.SemiStructuredTextTargetAccuracy
        ),
        'semi_structured_text_confidence_threshold': workflow_input(
            Settings.SemiStructuredTextThreshold
        ),
        'semi_structured_text_acceptable_confidence': workflow_input(
            Settings.SemiStructuredTextMinLegThreshold
        ),
        'semi_structured_table_target_accuracy': workflow_input(
            Settings.SemiStructuredTableTargetAccuracy
        ),
        'semi_structured_table_confidence_threshold': workflow_input(
            Settings.SemiStructuredTableThreshold
        ),
        'semi_structured_table_acceptable_confidence': workflow_input(
            Settings.SemiStructuredTableMinLegThreshold
        ),
        'structured_checkbox_target_accuracy': workflow_input(
            Settings.StructuredCheckboxTargetAccuracy
        ),
        'structured_checkbox_confidence_threshold': workflow_input(
            Settings.StructuredCheckboxThreshold
        ),
        'structured_checkbox_acceptable_confidence': workflow_input(
            Settings.StructuredCheckboxMinLegThreshold
        ),
        'structured_signature_target_accuracy': workflow_input(
            Settings.StructuredSignatureTargetAccuracy
        ),
        'structured_signature_confidence_threshold': workflow_input(
            Settings.StructuredSignatureThreshold
        ),
        'structured_signature_acceptable_confidence': workflow_input(
            Settings.StructuredSignatureMinLegThreshold
        ),
        'semi_structured_checkbox_target_accuracy': workflow_input(
            Settings.SemiStructuredCheckboxTargetAccuracy
        ),
        'semi_structured_checkbox_confidence_threshold': workflow_input(
            Settings.SemiStructuredCheckboxThreshold
        ),
        'semi_structured_checkbox_acceptable_confidence': workflow_input(
            Settings.SemiStructuredCheckboxMinLegThreshold
        ),
        'field_target_accuracies': workflow_input(Settings.FieldTranscriptionTargetAccuracies),
    },
    ManualTranscriptionBlock.IDENTIFIER: {
        'table_output_manual_review': workflow_input(
            'manual_transcription_table_output_manual_review'
        ),
        'supervision_transcription_masking': workflow_input(
            'manual_transcription_supervision_transcription_masking'
        ),
        'always_supervise_blank_cells': workflow_input(
            'manual_transcription_always_supervise_blank_cells'
        ),
        'task_restrictions': workflow_input('manual_transcription_task_restrictions'),
        'notification_workflow': workflow_input('notification_workflow_transcription'),
    },
    FlexibleExtractionBlock.IDENTIFIER: {
        'task_restrictions': workflow_input('flexible_extraction_task_restrictions'),
        'supervision_transcription_masking': workflow_input(
            'flexible_extraction_supervision_transcription_masking'
        ),
        'notification_workflow': workflow_input('notification_workflow_flexible_extraction'),
        'layout_release_uuid': workflow_input(Settings.LayoutReleaseUuid),
    },
    ReprocessingBlock.IDENTIFIER: {
        'trigger': workflow_input(Inputs.Trigger),
    },
    DocumentRendererBlock.IDENTIFIER: {
        'document_rendering_enabled': workflow_input(Settings.DocumentRenderingEnabled),
        'document_rendering_mime_type': workflow_input(Settings.DocumentRenderingMimeType),
        'document_rendering_unit': workflow_input(Settings.DocumentRenderingUnit),
        'document_rendering_height': workflow_input(Settings.DocumentRenderingHeight),
        'document_rendering_width': workflow_input(Settings.DocumentRenderingWidth),
        'document_rendering_quality': workflow_input(Settings.DocumentRenderingQuality),
    },
    SubmissionCompleteBlock.IDENTIFIER: {
        'nlc_qa_sampling_ratio': workflow_input(Settings.SemiQaSampleRate),
        'field_id_qa_enabled': workflow_input(Settings.FieldIdQaEnabled),
        'field_id_qa_sampling_ratio': workflow_input(Settings.FieldIdQaSampleRate),
        'table_id_qa_enabled': workflow_input(Settings.TableIdQaEnabled),
        'table_id_qa_sampling_ratio': workflow_input(Settings.TableIdQaSampleRate),
        'transcription_qa_enabled': workflow_input(Settings.TranscriptionQaEnabled),
        'transcription_structured_entry_qa_sample_rate': workflow_input(
            Settings.TranscriptionStructuredEntryQaSampleRate
        ),
        'transcription_structured_signature_qa_sample_rate': workflow_input(
            Settings.TranscriptionStructuredSignatureQaSampleRate
        ),
        'transcription_structured_checkbox_qa_sample_rate': workflow_input(
            Settings.TranscriptionStructuredCheckboxQaSampleRate
        ),
        'transcription_semi_structured_qa_sample_rate': workflow_input(
            Settings.TranscriptionSemiStructuredQaSampleRate
        ),
        'table_cell_transcription_qa_enabled': workflow_input(
            Settings.TableCellTranscriptionQaEnabled
        ),
        'table_cell_transcription_qa_sample_rate': workflow_input(
            Settings.TableCellTranscriptionQaSampleRate
        ),
        'auto_qa_sampling_rate_enabled': workflow_input(Settings.AutoQaSamplingRateEnabled),
        'exclude_auto_transcribe_fields_from_qa': workflow_input(
            Settings.ExcludeAutoTranscribeFieldsFromQA
        ),
    },
}
