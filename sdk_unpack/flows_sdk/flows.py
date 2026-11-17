from collections import defaultdict
from dataclasses import asdict
from typing import Any, ClassVar, Dict, List, Optional, Sequence
from uuid import UUID

from pydantic import BaseModel, Field, root_validator, validator

from flows_sdk.blocks import Block, IOBlock
from flows_sdk.error_handling import ErrorHandling
from flows_sdk.utils import str_to_deterministic_uuid_4


class _BaseModel(BaseModel):
    """
    :meta private:
    By default, when exporting to json, pydantic will include nulls for fields that were not
    specified. We do not want this when converting to HSDSL:
    - null is a valid value in some cases e.g. for field default "value" property, so not specified
    is treated differently from specified, but null
    - generally our convention is that if a field is included in the json, it must have a valid
    value, and for many properties - e.g. schema, title, etc. - null is not an allowed value.
    Hence we specify exclude_unset.
    We also use by_alias, as we have to use an alias for the "schema" field in Parameter.
    """

    def dict(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        kwargs.setdefault('by_alias', True)
        kwargs.setdefault('exclude_unset', True)
        return super().dict(*args, **kwargs)


class Dependency(_BaseModel):
    condition: Dict[str, Any]
    override: Dict[str, Any]


class Parameter(_BaseModel):
    """
    Defines an input parameter of a block or a flow.
    """

    name: str
    """Must be a valid Python identifier"""
    type: str
    """Json-schema-like type (e.g. string, integer, number, array, object...)
    Between Hyperscience platform versions there are also extensions like:

    - Percentage (number between 0 and 1)
    - UUID (string in UUID format or null)
    - MultilineText (string, but represented as multiline text box in Flow studio)

    Depending on the Hyperscience version, other supported types may also exist,
    some of which allow for specific rendering in UI.
    """
    type_spec: Optional[Dict[str, Any]] = None
    """
    An optional object property that further specifies (or "specializes") the type, in ways that
    cannot be achieved via the `schema` property. Its exact format is specific to the specific type
    used. If specified must conform to whatever the `type_spec` format specific to the chosen
    `type` is.

    .. collapse:: File input flow that uses type_spec

        This flow uses `type_spec` to limit the types of files that can be selected for the file
        input.

        .. include:: ../../../samples/file_input/file_input_flow.py
           :literal:
    """
    title: Optional[str] = None
    """UI-visible representation of the field name"""
    description: Optional[str] = None
    """UI-visible description of the field"""
    value: Any = None
    """Optional default value of the field,
        used when its value is not specified explicitly in the inputs"""
    optional: bool = False
    """True when the field can be omitted, False when it is mandatory.
        The default value is False, i.e. if the `optional` flag is not specified,
        the field will be considered mandatory."""
    secret: Optional[bool] = None
    """UI-hint that the field should be presented as a secret (hidden symbols)
    rather than plain text."""

    json_schema: Optional[Dict[str, Any]] = Field(alias='schema', default=None)
    """Defines a format for the field using the JSON Schema specification
        (https://json-schema.org/understanding-json-schema/).
        Field values will be validated against this format when a flow is imported or edited."""
    ui: Optional[Dict[str, Any]] = None
    """Presentation-related customizations for the field"""
    dependencies: Optional[List[Dependency]] = None
    """Internal mechanism for describing dependencies between fields (e.g. show A when B is checked,
    hide A when B is unchecked)"""


class InputDefinition(_BaseModel):
    """Declaratively defines what parameters are expected, usually part of a Manifest."""

    input: List[Parameter]
    """All parameters that are part of this definition"""
    ui: Optional[Dict[str, Any]] = None
    """Presentation-related customizations for how fields are grouped together.
    ui['groups'] defines how fields are grouped together in the UI and specifies the group titles.
    groups are optional - if omitted, every input field is listed in the "default" group.
    If any fields are not included in any group, then they are shown as part of the "default"
    group of non-nested fields.

    example::

        ui: {
            groups: [
            {
                title: 'Group 1',
                fields: [
                    'layout_release_uuid',
                    'policy',
                ],
            },
            {
                title: 'Group 2',
                fields: ['accuracy'],
            },
            ]
        }"""

    @validator('input')
    @classmethod
    def _validate_input(cls, v: List[Parameter]) -> List[Parameter]:
        """validates that all parameters have unique names."""
        cls._check_for_duplicate_parameter_names('Duplicate input names', v)
        return v

    @classmethod
    def _check_for_duplicate_parameter_names(
        cls, error_message: str, parameters: List[Parameter]
    ) -> None:
        counts: Dict[str, int] = defaultdict(int)
        duplicates = set()
        for param in parameters:
            counts[param.name] += 1
            if counts[param.name] > 1:
                duplicates.add(param.name)
        if duplicates:
            raise ValueError(error_message, duplicates)


class Manifest(InputDefinition):
    """Describes how the Flow studio should present the Flow/Block.
    The parameters are displayed in the Flow studio and can be futher customized into sections via.
    the `ui` section.

    Inputs are used both for visualization and for validation - for example, in the
    :py:class:`flows_sdk.flows.Flow` manifest ``.input``, if a string is passed for a parameter
    defined as number in the manifest, the user will be prompted to

    Here is an example of how the manifest is visualized on the Flow level with
    :py:class:`flows_sdk.flows.Parameter` groupped under *Classification* and *Identification*

    .. image:: ../media/images/flow_settings.png
      :width: 250

    example::

        Manifest(
            identifier='CUSTOM_FLOW',
            input=[
                Parameter(
                    name='setting_a',
                    type='string',
                    title='Setting A',
                    value=''
                ),
                Parameter(
                    name='setting_b',
                    type='number',
                    title='Setting B',
                    value=42
                ),
                Parameter(
                    name='setting_c',
                    type='string',
                    title='Setting C',
                    value=''
                ),
            ],
            ui={
                'groups': [
                    {
                        'title': 'Groupped Settings',
                        'fields': [
                            'setting_a',
                            'setting_b',
                        ],
                    },
                ]
            }
        )
    """

    identifier: str
    """Globally-unique identifier of the block/flow. By convention - all capital snake-case witn
    an optional numeric suffix (e.g., ``HELLO_FLOW_2``)"""
    roles: List[str] = []
    """Allows for "tagging" blocks/flows, used by internal features."""
    output: Optional[List[Parameter]] = []
    """Documents the outputs of the block/flow. For the time being, used for documentation
    purposes only."""
    enable_overrides: Optional[bool] = None
    """UI representation of overrides if present.
    This requires additional API calls and should generally be set to True only when overrides
    are defined
    Advanced functionality, contact Hyperscience if you think you need it!"""

    @validator('output')
    @classmethod
    def _validate_output(cls, v: List[Parameter]) -> List[Parameter]:
        cls._check_for_duplicate_parameter_names('Duplicate output names', v)
        return v


class Triggers(_BaseModel):
    class Config:
        arbitrary_types_allowed = True

    title: str
    """User-facing title"""
    description: Optional[str] = None
    """User-facing description"""
    reference_name: str
    """unique reference on a per-Flow basis"""
    api_params_manifest: Optional[InputDefinition] = None
    """[deprecated] Defines a shared inputs between all Triggers. Will be replaced in r33+"""
    role_filter: Optional[List[str]] = None
    """Lists the roles that blocks used within this triggers section should have.
    Blocks should have all listed roles to be compatible. If empty, blocks with any role can be
    used."""
    blocks: List[IOBlock]
    """List of trigger blocks used to initiate the Flow. Can be empty and is modifiable by the
    Flow studio."""
    processing_block: Optional[Block] = None
    """[deprecated] A block that is executed after the Flow is triggered, but before other
    blocks in the Flow. Instead, add a block in the Flow itself."""

    def render(self) -> Dict[str, Any]:
        """:meta private:"""
        r = super().dict()
        # replace the blocks with rendered content
        if self.blocks:
            r['blocks'] = [el for block in self.blocks for el in block.render()]
        # TODO: the processing block has no place in triggers section. It's here
        # only in order to hide SUBMISSION_BOOTSTRAP in the UI !!!
        if self.processing_block:
            rendered = self.processing_block.render()
            assert len(rendered) == 1
            r['processing_block'] = rendered[0]
        return r


class Flow(_BaseModel):
    """Flow is the top-level construct describing the type and order of various components.

    Sample usage::

        Flow(
            title='Flow title', # UI visible and editable title
            description='Flow description' # UI visible and editable description
            blocks=[ccb], # sequence of blocks in order
            owner_email='flows.sdk@hyperscience.com',
            manifest=Manifest(identifier='HELLO_FLOW', input=[hello_input_param]),
            uuid=UUID('2e3ab564-fcf5-41fb-a573-4bc2fd153b6d'),
            input={'hello_input': 'World'},
        )

    """

    _ZERO_UUID: ClassVar[UUID] = UUID(int=0)

    class Config:
        arbitrary_types_allowed = True

    uuid: UUID = _ZERO_UUID
    """Unique identifier of the Flow. If not provided, one will be deterministically
    generated based on the value of `manifest.identifier`. Note that if manually setting the uuid,
    a new one should be used every time `manifest.identifier` changes.
    """
    owner_email: str
    """An email address where the creator of the Flow can be reached.
    This field is purely informative metadata, it does not control any permissions or
    behaviours in the system. The intended use is for the flow developer to define it in
    the Flows SDK-based definition of the flow. It is read-only in the UI because business users
    will mostly be using this for information purposes and will not usually need to change it.
    If necessary, they may still change this by exporting, editing the json of the flow,
    and reimporting.
    """
    title: str
    """User-visible and editable title, does not have to be unique."""
    manifest: Manifest
    blocks: Sequence[Block] = []
    """Sequence of Blocks to be scheduled for execution when the Flow is triggered."""
    input: Dict[str, Any] = {}
    """Key-value pairs for top-level inputs of the flow. Their types / UI representations are part
    of the Manifest."""
    description: Optional[str] = None
    """User-editable description of what the Flow is used for."""
    triggers: Optional[Triggers] = None
    """Trigger blocks that initiate the Flow."""
    output: Optional[Dict[str, str]] = None

    variables: Optional[Dict[str, Any]] = None

    error_handling: Optional[ErrorHandling] = None
    """Error handling policies for the flow."""

    @root_validator(pre=True)
    def generate_uuid_when_not_provided(  # pylint: disable=no-self-argument
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a deterministic UUID based on manifest.identifier if one is not provided.
        We use _ZERO_UUID as an anchor value to ensure that the type of `uuid` is kept as UUID
        instead of Optional[UUID], as some pieces of code might rely on the value being a valid
        UUID instead of Null that gets rendered to a valid UUID.
        """
        if values.get('uuid', cls._ZERO_UUID) == cls._ZERO_UUID:
            values['uuid'] = str_to_deterministic_uuid_4(values['manifest'].identifier)
        return values

    def render(self) -> Dict[str, Any]:
        """:meta private:"""

        dsl = {
            'metadata': {'file_type': 'workflow_dsl', 'schema_version': 2},
            'uuid': str(self.uuid),
            'owner_email': self.owner_email,
            'title': self.title,
            'manifest': self.manifest.dict(),
            'blocks': [el for block in self.blocks for el in block.render()],
            'input': {},  # must be present, even if empty
        }
        if self.description is not None:
            dsl['description'] = self.description
        if self.triggers is not None:
            dsl['triggers'] = self.triggers.render()
        if self.input is not None:
            dsl['input'] = self.input
        if self.output is not None:
            dsl['output'] = self.output
        if self.variables is not None:
            dsl['variables'] = self.variables
        if self.error_handling is not None:
            dsl['error_handling'] = asdict(self.error_handling)

        return dsl
