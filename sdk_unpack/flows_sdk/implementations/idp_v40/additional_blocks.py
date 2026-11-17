from typing import Any, Dict, List, Literal, Optional, Sequence, Union

from flows_sdk.blocks import Block, IOBlock, Outputs
from flows_sdk.implementations.idp_v40.additional_values import JSON_OUTPUT_ROLE
from flows_sdk.implementations.idp_v40.idp_values import (
    DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER,
    HttpHeaderAuthorizationParams,
    Inputs,
    OAuth2AuthorizationParams,
)
from flows_sdk.utils import workflow_input


class JSONOutputsBlock(Outputs):
    """Output block allows users to send JSON data extracted by an IDP flow to other systems
    for downstream processing
    Mandatory parameters:

    :param inputs: Used by the UI to automatically pre-populate the input of
        newly added blocks. Extended in this class to include ``'enabled': True``
        to visualize an enabled/disabled trigger that is controllable via Flow Studio.

    Usage when parameters are to be defined in Flow Studio::

        outputs = JSONOutputBlock(
            inputs={'result': }
        )
    """

    def __init__(self, inputs: Dict[str, Any], blocks: Optional[Sequence[IOBlock]] = None) -> None:
        if not blocks:
            blocks = []

        super().__init__(
            reference_name='json_outputs',
            title='JSON Outputs',
            description='Send JSON submission data to external systems',
            role_filter=[JSON_OUTPUT_ROLE],
            input_template=inputs,
            blocks=blocks,
        )


class ImageCorrectionBlock(Block):
    """
    Image Correction Block rotates and de-skews tilted/skewed images so that they are more
    transcription-friendly
    Mandatory parameters:

    :param pages: list of page object that includes the raw documents that need to be
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
        You can read more about language families in the Supported Languages section of the
        documentation
        https://help.hyperscience.com/v40/docs/supported-languages
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

    IDENTIFIER = 'IMAGE_CORRECTION_PAGES'

    def __init__(
        self,
        pages: str,
        reference_name: Optional[str] = None,
        rotation_correction_enabled: bool = True,
        mobile_processing_enabled: bool = False,
        language_family: Optional[str] = None,
        title: str = 'Image Correction (Pages)',
        description: str = 'Rotate and de-skew documents',
        app_metadata: Optional[List[str]] = None,
    ) -> None:
        inputs: Dict[Any, Any] = {
            'pages': pages,
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


class FullPageTranscriptionBlock(Block):
    """
    Full Page Transcription Block machine-transcribes the documents contained in a submission

    Mandatory parameters:

    :param pages: list of pages that includes the raw documents that need to be transcribed

    Optional Parameters:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
    :param language_family: language family to use when instantiating the underlying transcription
        model. If not provided, the system will default to `latin`. Language families are single
        word lowercase strings, e.g., `latin`, `arabic`, `korean`, `chinese`.
        You can read more about language families in the Supported Languages section of the
        documentation
        https://help.hyperscience.com/v40/docs/supported-languages
    :param app_metadata: used for capturing information about the flow

    Example usage::

        # This is one way to obtain the submission object (using SubmissionBootstrapBlock)
        submission_bootstrap = SubmissionBootstrapBlock(reference_name='submission_bootstrap')
        # FullPageTranscriptionBlock transcribes the documents contained in the submission object
        fpt_block = FullPageTranscriptionBlock(
            reference_name='fpt',
            submission=submission_bootstrap.output(submission.unassigned_pages),
        )
        # reference to the output of FullPageTranscriptionBlock which can be passed as input to the
        # next block. For more information on output() and output references, please take a look at
        # class Block and its output() method
        output_ref = fpt_block.output()
    """

    IDENTIFIER = 'FULL_PAGE_TRANSCRIPTION_PAGES_2'

    def __init__(
        self,
        pages: str,
        reference_name: Optional[str] = None,
        title: str = 'Full Page Transcription (Pages)',
        description: str = 'Transcribes documents',
        language_family: Optional[str] = None,
        app_metadata: Optional[List[str]] = None,
    ) -> None:
        inputs: Dict[Any, Any] = {
            'pages': pages,
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


class CustomSupervisionBlock(Block):
    """The CustomSupervisionBlock uses a JSON schema as a form builder to create customer-driven
    UIs for Supervision tasks.

    Mandatory parameters:

    :param submission: Submission object
    :param task_purpose: the custom task name that's given to all supervision tasks that run
        through a particular instance of a custom supervision block. This can be used to filter
        tasks in the task queue.
    :param data: JSON structure that supplies the data used to populated the supervision_template
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
    :param notification_workflow: Notification flow name to run when the submission
        enters Custom Supervision,
        defaults to IDP_SUBMISSION_NOTIFY_NAME
    :param title: UI-visible title of the block. Defaults to 'IDP Custom Supervision'
    :type title: Optional[str]
    :param description: Description of the block. Both useful for documentation purpose and visible
            to users in the Flow studio. Defaults to 'IDP Custom Supervision'
    :type description: Optional[str]

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
                'fields': [
                    {
                        'id': 967,
                        'uuid': 'fe8d4e7a-a82c-448c-85a1-0a3cbbe53b61',
                        'value': '111-22-3333',
                        'page_id': 15,
                        'layout_field_id': '2afd7a67-ddee-484f-ab6b-2d292752e5ee',
                        'validation_overridden': False,
                        'bounding_box': [
                            0.09360783305186686,
                            0.25792617589433436,
                            0.6358913805295097,
                            0.28862414740388187,
                        ],
                        'occurrence_index': 1,
                    },
                ],
                'template_fields': [
                    {
                        'uuid': '2afd7a67-ddee-484f-ab6b-2d292752e5ee',
                        'notes': '',
                        'type': 'entry',
                        'data_type_uuid': 'b600a4e4-758f-4c4b-a2f4-cbb5dd870a0c',
                        'name': 'SSN',
                    },
                ],
                'pages': [
                    {
                        'id': 15,
                        'file_page_number': 1,
                        'document_page_number': 1,
                        'image_url': '/image/2ed3d989-b64a-44bd-a9fb-6e0dcc5ccdb8',
                        'form_id': 2,
                        'submission_id': 1,
                        'external_case_ids': [],
                        'read_only': False,
                        'filename': '1 page.pdf',
                        'form_page_id': 1
                    },
                ],
                'documents': [
                    {
                        'id': 2,
                        'layout_uuid': 'e31c3cbf-dcea-44fd-a052-902463c6040f',
                        'layout_name': 'layout_name',
                        'page_count': 2,
                        'read_only': False,
                    },
                ],
                'cases': [],
                'selected_choices': [],
            },
            supervision_transcription_masking=False,
        )
    """

    IDENTIFIER = 'CUSTOM_SUPERVISION_2'

    def __init__(
        self,
        submission: Any,
        task_purpose: str,
        data: Any,
        supervision_template: Any,
        reference_name: Optional[str] = None,
        supervision_transcription_masking: bool = True,
        task_restrictions: Optional[List[Any]] = None,
        notification_workflow: str = DEFAULT_IDP_SUBMISSION_NOTIFY_IDENTIFIER,
        title: Optional[str] = 'Custom Supervision',
        description: Optional[str] = 'Custom Supervision',
    ) -> None:
        if not task_restrictions:
            task_restrictions = []

        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input={
                'supervision_template': supervision_template,
                'submission': submission,
                'task_purpose': task_purpose,
                'data': data,
                'task_restrictions': task_restrictions,
                'supervision_transcription_masking': supervision_transcription_masking,
                'notification_workflow': notification_workflow,
            },
            title=title,
            description=description,
        )


class SoapRequestBlock(Block):
    """Soap Block allows user to perform SOAP requests
    Mandatory parameters:

    :param method: SOAP method to invoke
    :param endpoint: absolute url including schema to HTTP endpoint for this request

    Optional Parameters:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
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

    IDENTIFIER = 'SOAP_REQ'

    def __init__(
        self,
        method: str,
        reference_name: Optional[str] = None,
        endpoint: str = '',
        body_namespace: Optional[str] = None,
        headers_namespace: Optional[str] = None,
        headers: Optional[Dict[Any, Any]] = None,
        params: Optional[Dict[Any, Any]] = None,
        use_wsdl: bool = False,
        wsdl_uri: Optional[str] = '',
        wsdl_service_name: Optional[str] = '',
        wsdl_port_name: Optional[str] = '',
        title: str = 'HTTP REST Block',
        description: str = 'HTTP REST block',
    ) -> None:
        inputs: Dict[Any, Any] = {
            'method': method,
            'endpoint': endpoint,
            'use_wsdl': use_wsdl,
            'wsdl_uri': wsdl_uri,
            'wsdl_service_name': wsdl_service_name,
            'wsdl_port_name': wsdl_port_name,
        }
        if body_namespace is not None:
            inputs['body_namespace'] = body_namespace
        if headers_namespace is not None:
            inputs['headers_namespace'] = headers_namespace
        if headers is not None:
            inputs['headers'] = headers
        if params is not None:
            inputs['params'] = params

        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input=inputs,
            title=title,
            description=description,
        )


class BaseHttpRestBlock(Block):
    """
    :meta private:
    Base HttpRest block to be reused by internal and external divergent interface implementations
    """

    IDENTIFIER = 'HTTP_REST'

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
        endpoint_secrets: Optional[str] = None,
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
        if endpoint_secrets is not None:
            inputs['endpoint_secrets'] = endpoint_secrets
        if auth_params is not None:
            if isinstance(auth_params, HttpHeaderAuthorizationParams):
                inputs['authorization_header'] = auth_params.authorization_header
                inputs['authorization_header_name'] = auth_params.authorization_header_name
            elif isinstance(auth_params, OAuth2AuthorizationParams):
                inputs['auth_url'] = auth_params.auth_url
                inputs['client_id'] = auth_params.client_id
                inputs['client_secret'] = auth_params.client_secret
                inputs['audience'] = auth_params.audience
            else:
                raise ValueError(
                    'auth_params must be of type HttpHeaderAuthorizationParams '
                    'or OAuth2AuthorizationParams'
                )

        super().__init__(
            identifier=self.IDENTIFIER,
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

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
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

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
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


class DatabaseAccessBlock(Block):
    """Database Block allows user to access and perform queries on the specified database
    Mandatory parameters:

    :param db_type: database type (mssql, oracle, postgres)
    :param host: URL/IP address of the server database is hosted on
    :param database: database name
    :param username: database username
    :param password: database password
    :param query: parameterized query

    Optional parameters:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
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

    IDENTIFIER = 'DB_ACCESS'

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
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            title=title,
            description=description,
            input=inputs,
        )


class LlamaBlock(Block):
    """Text generation using the Llama 2 model by Meta.

    This block utilizes Llama 2 by Meta. Llama 2 is licensed under the LLAMA 2 Community License
    (https://ai.meta.com/llama/license/). By using the Llama Block, you acknowledge that you have
    received a copy of the LLAMA 2 Community License.

    Note: This block is still experimental and not ready for production use.

    Mandatory parameters:

    :param model_id: UUID, identifier of the asset with the ML model.
        Model assets are not part of the Hypersicence bundle and must first be downloaded and
        imported into the system before they can be used. Please contact your Hyperscience
        representative to discuss the usecase and the appropriate model and to get instructions on
        downloading the models.
        Once downloaded, here are the available model asset UUIDs:
        b3da05c7-061c-4a58-af6d-4c905d2e618f - Llama 2, 13B, 8-bit quantized
    :param prompt: The prompt to generate text from. Use a CodeBlock ahead of the LlamaBlock in
        order to build the prompt. The context window of the model is limited to 4096 tokens.
        If the prompt has more tokens, the block would return an error. The total input and output
        length also cannot exceed 4096 tokens, which means that if the input is too long, the output
        may be truncated. Also see tokenize_only for a more detailed explanation of how to handle
        longer texts.

    Optional parameters:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
    :param consent: Has the business user read and acknowledged the Llama 2 legal notice.
        Unless the flow would be used in CI automation, this should be set to False so that a
        business user can read and acknowledge the notice in the Hyperscience UI. Setting this
        to True in the Python definition of the flow is also treated as acknowledgement of the
        notice on behalf of the entity that will be using the flow.
    :param tokenize_only: In the context of LLMs, tokens correspond roughly to words, partial words
        and punctuation. A rough way to compute the number of tokens in a text is
        number_of_tokens = 1.25 * number_of_words. The Llama block works with a context window
        of 4096 tokens. If a longer prompt is passed in, it would return an error. Also, if the
        prompt is shorter, but still close to 4096, the output may be truncated.
        Since the length of the prompt in tokens cannot be known ahead of time, sometimes the flow
        may need to make dynamic decisions whether to pass the text to the Llama block, or to
        split it into multiple chunks, or to use some alternative method for processing it (e.g. a
        custom supervision manual task).
        The tokenize_only option enables flows to take such dynamic decisions based on the length
        of the prompt in tokens.
        The default is false - it instructs the block to run the ML model inference over the
        prompt, i.e. to generate a text response.
        When true is passed, the model will simply tokenize the prompt without running inference
        and return the list of tokens - this will work regardless of the length of the prompt.
        A subsequent Decision task can then route longer prompts to an alternative path in the
        flow, while routing shorter prompts to the LlamaBlock for actual text generation.
    :param predict_extra_kwargs: Extra keyword arguments used for model inference.
        (Used to fine-tune the model prediction. Not recommended to change this unless you know
        what you are doing)

    Example usage::

        llama = LlamaBlock(
            reference_name='llama',
            model_id='b3da05c7-061c-4a58-af6d-4c905d2e618f',
            prompt='${previous_block.output.llama_prompt}',
        )
    """

    IDENTIFIER = 'LLAMA'

    def __init__(
        self,
        model_id: str,
        prompt: str,
        reference_name: Optional[str] = None,
        consent: Optional[bool] = False,
        tokenize_only: Optional[bool] = False,
        predict_extra_kwargs: Optional[Dict[Any, Any]] = None,
        title: str = 'Llama Text Generation',
        description: str = 'Text generation using the Llama 2 model',
    ) -> None:
        if predict_extra_kwargs is None:
            predict_extra_kwargs = {}

        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input={
                'model_id': model_id,
                'prompt': prompt,
                'consent': consent,
                'tokenize_only': tokenize_only,
                'predict_extra_kwargs': predict_extra_kwargs,
            },
            title=title,
            description=description,
        )


class EntityRecognitionBlock(Block):
    """
    Entity Recognition Block detects entities of different types within the documents contained
    in a submission

    This block requires the output of the Full Page Transcription Block as input data.

    Mandatory parameters:

    :param pages: list of pages that includes the raw documents with the transcribed information
        from the FPT block
    :param regex_map: a map that specifies different regex patterns that the block should look for,
        a default one is present
    :param keyword_map: a map that specifies different keyword patterns that the block should look
        for, a default one is present

    Optional Parameters:

    :param enhanced_output: a boolean flag that enables toggling between simple and enhanced
        output formats. Default value is False.
    :param ner_enabled: a boolean flag that enables or disables Named Entity Recognition.
        Default value is True.
    :param ced_enabled: a boolean flag that enables or disables Custom Entity Detection.
        Default value is True.
    :param signature_enabled: a boolean flag that enables or disables Signature Detection.
        Default value is True.
    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided

    Example usage::

        # This is one way to obtain the submission object (using SubmissionBootstrapBlock)
        submission_bootstrap = SubmissionBootstrapBlock(reference_name='submission_bootstrap')

        # EntityRecognitionBlock detects entities within the documents contained in the submission
        entity_recognition_block = EntityRecognitionBlock(
            reference_name='entity_recognition',
            pages=submission_bootstrap.output(submission.unassigned_pages),
            regex_map=DEFAULT_PII_REGEX_MAP,
            keyword_map=DEFAULT_PII_KEYWORD_MAP,
            enhanced_output=False,
        )

        # reference to the output of EntityRecognitionBlock which can be passed as input to the
        # next block. For more information on output() and output references, please take a look at
        # class Block and its output() method
        output_ref = entity_recognition_block.output()

    Example content of output_ref::

        {
            "documents": [
                {
                    "file_uuid": "da2c6117-43c4-4b30-84c4-cdc59cc3fa4f",
                    "entities": [
                        {
                            "text": "John Smith",
                            "type": "Person Name",
                            "positions": [
                                [0.5, 0.1, 0.55, 0.13],
                                [0.6, 0.2, 0.65, 0.23],
                                [0.7, 0.3, 0.75, 0.33],
                            ],
                            "page_ids": [0, 0, 1],
                            "origin": "NER",
                        },
                        {
                            "text": "<SIGNED>",
                            "type": "signature",
                            "positions": [[0.701171875, 0.732421875, 0.92578125, 0.8681640625]],
                            "page_ids": [0],
                            "origin": "Signature",
                        },
                    ]
                },
                {
                    "file_uuid": "4aa38f84-e5af-4cdc-ba5c-edd60f0a6b89",
                    "entities": [
                        ...
                    ]
                }
            ],
            "redaction_annotations": {
                "ner": [ ... ],
                "ced": [ ... ],
            }
        }
    """

    IDENTIFIER = 'ENTITY_RECOGNITION'

    def __init__(
        self,
        pages: str,
        regex_map: Optional[Dict[str, str]] = None,
        keyword_map: Optional[Dict[str, List[str]]] = None,
        enhanced_output: bool = False,
        ner_enabled: bool = True,
        ced_enabled: bool = True,
        signature_enabled: bool = True,
        reference_name: Optional[str] = None,
        title: str = 'Entity Recognition',
        description: str = 'Recognizes entities of different types in documents',
    ) -> None:
        inputs: Dict[Any, Any] = {
            'pages': pages,
            'regex_map': regex_map,
            'keyword_map': keyword_map,
            'enhanced_output': enhanced_output,
            'ner_enabled': ner_enabled,
            'ced_enabled': ced_enabled,
            'signature_enabled': signature_enabled,
        }

        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input=inputs,
            title=title,
            description=description,
        )


class FileFilterBlock(Block):
    """
    Available from V40.2

    File Filter Block filters out unwanted files from the input of a flow

    This block is meant to be placed at the start of the flow/subflow -
    BEFORE the SubmissionBootstrapBlock, not after it.
    It requires the output of a connector (e.g. Email Listener) or an API submission
    as input data, and its output is meant to be consumed by a SubmissionBootstrapBlock.

    Mandatory parameters:

        This block has no strictly required parameters - all of its filters are optional.

    Optional Parameters:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
    :param trigger: the trigger input from a connector - if not set explicitly,
        it will default to the workflow input trigger (which is where this value is normally found)
    :param filter_type: a discrete value, either "ALL_FILES" or "IMAGES_ONLY". Determines
        what kind of files the filters will be applied to. Default value is "ALL_FILES".
        If set to "IMAGES_ONLY", all filtering options will be applied only to images, other files
        will pass through.
    :param minimum_image_width: image width in pixels - half of the image dimension filter.
        Any image with less width than configured here will be filtered out.
        Defaults to None (will do nothing).
    :param minimum_image_height: image height in pixels - second half of the image dimension filter.
        Any image with less height than configured here will be filtered out.
        Defaults to None (will do nothing).
    :param minimum_file_size_kb: represents the file size filter. Any file whose disk size is less
        than this number (in KB) will be filtered out. May be fractional.
        Defaults to None (will do nothing).
    :param file_extensions_action: a discrete value, either "ALLOW", "DENY" or "NONE".
        Represents the function of the file extension filter.
        "ALLOW" means we only allow the configured file extensions.
        "DENY" means we only deny the configured file extensions.
        "NONE" means no file extension filtering takes place.
        Defaults to "NONE"
    :param file_extensions: a list of strings, representing the file extensions
        used for file extension filtering.
        Expected if file_extensions_action is not "NONE".
        Otherwise, defaults to None (will do nothing).
    :param file_extensions_other: a comma separated list of file extensions
        used for file extension filtering.
        Meant for adding extra extensions that are not available in the pre-defined list.
        Optional, defaults to None (will do nothing). However, it is expected
        in case the `file_extensions` parameter contains "other".

    Example usage::

        # File Filter Block filters out unwanted files from the input of a flow
        file_filter_block = FileFilterBlock(
            # trigger: str = workflow_input(Inputs.Trigger),  # usually not necessary to set this
            reference_name='file_filter',
            filter_type='ALL_FILES',
            minimum_image_width=500,
            minimum_image_height=500,
            minimum_file_size_kb=2.5,
            file_extensions_action='ALLOW',
            file_extensions=['pdf', 'png'],
            file_extensions_other='jpg,svg,txt',
        )

        # reference to the output of FileFilterBlock which can be passed as input to the
        # next block (a SubmissionBootstrapBlock)
        output_ref = file_filter_block.output('result.filtered_trigger')
        submission_bootstrap = SubmissionBootstrapBlock(trigger=output_ref)

    Example content of output_ref::

        {
            "payload": {
                "blob_storage_files": [
                    {
                        "uuid": "db58606e-32f9-42c9-a0bc-ed9848ff247a",
                    }
                ],
                "filtered_files": [
                    {
                        "uuid": "db58606e-32f9-42c9-a0bc-ed9848ff246e",
                        "filtered_by": [
                            "file_size_filter"
                        ]
                    },
                ]
            }
        }
    """

    IDENTIFIER = 'FILE_FILTER'

    def __init__(
        self,
        trigger: str = workflow_input(Inputs.Trigger),
        filter_type: Literal['ALL_FILES', 'IMAGES_ONLY'] = 'ALL_FILES',
        minimum_image_width: Optional[int] = None,
        minimum_image_height: Optional[int] = None,
        minimum_file_size_kb: Optional[float] = None,
        file_extensions_action: Literal['NONE', 'ALLOW', 'DENY'] = 'NONE',
        file_extensions: Optional[list] = None,
        file_extensions_other: Optional[str] = None,
        reference_name: Optional[str] = None,
        title: str = 'File Filter',
        description: str = 'Filters out unwanted files from the input of a flow',
    ) -> None:
        inputs: Dict[Any, Any] = {
            '$trigger': trigger,
            'filter_type': filter_type,
            'minimum_image_width': minimum_image_width,
            'minimum_image_height': minimum_image_height,
            'minimum_file_size_kb': minimum_file_size_kb,
            'file_extensions_action': file_extensions_action,
            'file_extensions': file_extensions,
            'file_extensions_other': file_extensions_other,
        }

        super().__init__(
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input=inputs,
            title=title,
            description=description,
        )
