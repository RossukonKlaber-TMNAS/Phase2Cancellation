from typing import Any, Dict, List, Optional, Sequence, Union

from flows_sdk.blocks import Block, IOBlock, Outputs
from flows_sdk.implementations.idp_v37.additional_values import JSON_OUTPUT_ROLE
from flows_sdk.implementations.idp_v37.idp_values import (
    IDP_SUBMISSION_NOTIFY_NAME,
    HttpHeaderAuthorizationParams,
    OAuth2AuthorizationParams,
)


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
            identifier=self.IDENTIFIER,
            reference_name=reference_name,
            input=inputs,
            title=title,
            description=description,
        )


class FullPageTranscriptionBlock(Block):
    """
    Full Page Transcription Block machine-transcribes the document pages passed to it

    Mandatory parameters:

    :param pages: list of pages that includes the raw documents that need to be transcribed

    Optional Parameters:

    :param reference_name: unique identifier within a flow, a unique one will be generated when
        not provided
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

    IDENTIFIER = 'FULL_PAGE_TRANSCRIPTION_PAGES'

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
                        'page_id': 1,
                        'data_identifier': '2afd7a67-ddee-484f-ab6b-2d292752e5ee',
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
        notification_workflow: str = IDP_SUBMISSION_NOTIFY_NAME,
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
            title='Custom Supervision',
            description='Custom Supervision',
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
                inputs['authorization_header_name'] = auth_params.authorization_header_name
            elif isinstance(auth_params, OAuth2AuthorizationParams):
                inputs['auth_url'] = auth_params.auth_url
                inputs['client_id'] = auth_params.client_id
                inputs['client_secret'] = auth_params.client_secret
                inputs['audience'] = auth_params.audience

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
