import ast
import hashlib
import inspect
import os
import re
import sys
from collections import defaultdict
from dataclasses import asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Set

from asttokens import asttokens

from flows_sdk.error_handling import ErrorHandling
from flows_sdk.types import CompatibilitySpec


class AutoRef:
    """
    :meta private:
    Helper class for automatically generating unique references on a per block identifier
    basis.
    A goal is to keep identifiers as stable as possible. While it is hard to achieve 100%
    stability for auto-generated names as a flow topology is changing, this implementation
    will keep blocks with non-affected identifiers consistent within the generated HSDSL json.


    For example, if we have a flow with 1x block A, 2x block B and we:

        auto_a_1   auto_b_1   auto_b_2
        ┌──────┐   ┌──────┐   ┌──────┐
        │  A   ├──►│  B   ├──►│  B   │
        └──────┘   └──────┘   └──────┘

    - add a block C anywhere
        - A and B ref names will be kept the same.
    - add a second block A after the existing block A
        - B ref names will be kept the same, 'auto_a_1' will stay the same and the new block
            will get `auto_a_2' ref name.
    - add a second block A before the existing block A
        - B ref names will be kept the same, but the newly inserted A block will get the
            existing reference 'auto_a_1' while the previous 'auto_a_1' block will have the
            'auto_a_2' reference name.

    This implementation is **not** thread-safe.
    """

    _ref_lookup: Dict[str, int]
    _prefix: str

    def __init__(
        self, references_lookup_dict: Optional[Dict[str, int]] = None, prefix: str = 'auto'
    ) -> None:
        """

        :param references_lookup_dict: dict that stores context with key identifier and value
            number of times that block has been instantiated. Used to generate unique reference
            names on a per-block-identifier basis.
            When not provided, defaults to a new empty dictionary.
        :param prefix: referance name prefix, prepended to make it easier to find out what
            reference names have been auto generated and to avoid potential common collisions
        """
        if not references_lookup_dict:
            references_lookup_dict = defaultdict(int)
        self._ref_lookup = references_lookup_dict
        self._prefix = prefix

    def for_identifier(self, identifier: str) -> str:
        """
        :param identifier: of the block to generate a reference for
        :return: a unique string in the format "auto_IDENTIFIER_unique_incrementing_counter"
            for example: "auto_submission_bootstrap_1"
        """
        self._ref_lookup[identifier] += 1
        return f'{self._prefix}_{identifier}__{self._ref_lookup[identifier]}'.lower()


global_auto_ref = AutoRef()


class Block:
    """Base structure representing an executable within a Hyperscience deployment.
    Available blocks depend on the version of the underlying Hyperscience platform,
    but additional blocks may have also been manually installed. Check out :doc:`idp` for
    example blocks used for the Document Processing flow that comes with V32.

    :param reference_name: unique identifier on a per-Flow basis, used to identify the concrete
        block within a Flow (e.g., in order to reference the outputs of a concrete block)
    :param identifier: block implementation that will be used at runtime
        (e.g., `MACHINE_CLASSIFICATION`). Multiple blocks with same identifier
        can be present in a Flow.
    :param input: key-value dict being passed during execution of the Block.
        Can both have static values or various dynamic values (e.g., output from a previously
        executed block, see :py:meth:`flows_sdk.blocks.Block.output`). Most blocks have mandatory
        inputs, depending on their identifier. For example::

                {
                    'a': 42,
                    'b': 'foo',
                    'c': some_previous_block.output(),
                    'd': another_previous_block.output('nested.path')
                }

    :param title: UI-visible title of the block.
    :param description: Description of the block. Both useful for documentation purpose and visible
            to users in the Flow studio.
    :param error_handling: The error handling policy that will be applied to this block.
    :param compatibility_spec: What flows or blocks can this block be changed with on the UI.
            "filter_roles" param takes a list of strings that represent roles.
            "filter_schema" param is a JSON schema, that allows for more intricate filtering.
            "label" represents the UI label in FlowStudio
    """

    def __init__(
        self,
        identifier: str,
        reference_name: Optional[str] = None,
        input: Optional[Dict[str, Any]] = None,  # pylint: disable=W0622
        title: Optional[str] = None,
        description: Optional[str] = None,
        error_handling: Optional[ErrorHandling] = None,
        compatibility_spec: Optional[CompatibilitySpec] = None,
    ) -> None:
        if error_handling and error_handling.on_error_flow:
            raise NotImplementedError('On error flow currently not supported for blocks')
        if reference_name is None:
            reference_name = global_auto_ref.for_identifier(identifier)

        self._reference_name = reference_name
        self._identifier = identifier
        self._input = input
        self._title = title
        self._description = description
        self._error_handling = error_handling
        self._compatibility_spec = compatibility_spec

    def output(self, key: Optional[str] = None) -> str:
        """Used to reference the output of a block that has already been executed.
        For example, if we have a Flow with two blocks, the second can reference
        the output of the first as part of its inputs.

        :param key: When not provided, the entire output of the referenced block will be
            passed along. When provided, will pass a concrete key from the output
            (e.g. for an output like ``{"a": 42}``, calling ``output()`` will pass it
            as a dictionary, while calling ``output("a")`` will pass ``42``.)
        :type key: Optional[str]
        :return: a string-formatted reference that will be unpacked to a value during runtime.
        :rtype: str

        For example::

            a = Block(...)
            b = Block(
                ...,
                input = {
                    'foo': a.output('bar')
                }
            )

        """
        if key:
            return '${%s.output.%s}' % (self._reference_name, key)
        else:
            return '${%s.output}' % (self._reference_name)

    def with_error_handling(self, error_handling: ErrorHandling) -> 'Block':
        """
        Adds the provided error handling section to this block.

        Available in v36 and later.
        """
        if error_handling.on_error_flow:
            raise NotImplementedError('On error flow currently not supported for blocks')
        # Added this method so that we don't need to propagate the error_handling argument
        # to the constructors of all subclasses
        self._error_handling = error_handling
        return self

    def _render_self(self) -> Dict[str, Any]:
        """Dictionary representation of the Block.

        :return: the instance as a serializable dictionary.
        :rtype: Dict[str, Any]
        """

        r: Dict[str, Any] = {'identifier': self._identifier, 'reference_name': self._reference_name}
        if self._input is not None:
            r['input'] = self._input
        if self._title is not None:
            r['title'] = self._title
        if self._description is not None:
            r['description'] = self._description
        if self._error_handling is not None:
            r['error_handling'] = asdict(self._error_handling)
        if self._compatibility_spec is not None:
            r['compatibility_spec'] = asdict(
                self._compatibility_spec,
                dict_factory=CompatibilitySpec.compatibility_spec_dict_factory,
            )

        return r

    def render(self) -> List[Dict[str, Any]]:
        """:meta private: Dictionary representation of the Block as a single element within a list.

        :return: List with a single element - the instance as a serializable dictionary.
        :rtype: List[Dict[str, Any]]
        """
        return [self._render_self()]


class BaseCodeBlock(Block):
    _asts: Dict[bytes, asttokens.ASTTokens] = {}
    _system_arguments = ('_hs_task', '_hs_block_instance')

    def __init__(
        self,
        code: Callable,
        identifier: str,
        reference_name: Optional[str] = None,
        input: Optional[Dict[str, Any]] = None,  # pylint: disable=W0622
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        super().__init__(identifier, reference_name, input, title, description)
        self.code_fn: Callable = code

    def output(self, key: Optional[str] = None) -> str:
        """
        CodeBlock nests the actual result returned from the provided function under
        the 'result' key. This method overrides the default output, removing the need
        to always prepend 'result' when calling CodeBlock.output(...)

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

    @staticmethod
    def _format_code(
        code: Callable, inputs: Optional[Dict[str, Any]], additional_imports: str = ''
    ) -> str:
        params = set(inspect.signature(code).parameters.keys())
        BaseCodeBlock._validate_params(
            BaseCodeBlock._get_block_inputs(params), (inputs or {}).get('data', {})
        )
        if code.__name__ == '<lambda>':
            return BaseCodeBlock._get_short_lambda_source(code)
        else:
            return BaseCodeBlock._generate_code_from_template(code, params, additional_imports)

    @staticmethod
    def _get_short_lambda_source(lambda_func: Callable) -> str:
        """
        Return the source of a (short) lambda function.
        If it's impossible to obtain, returns None.
        Slightly refactored from: http://disq.us/p/1vq0bes
        """

        if lambda_func.__name__ != '<lambda>':
            raise ValueError(f'Expected lambda, got {lambda_func}')

        # Parse the whole file and find the AST node of the condition lambda.
        # This is necessary, since condition.__code__ gives us only a line number
        # which is too vague to find the lambda node.
        lines, lambda_lineno = inspect.findsource(lambda_func)

        full_source = ''.join(lines)
        atok = BaseCodeBlock._parse_source(full_source)

        lambdas_on_same_line = []
        for node in ast.walk(atok.tree):  # type: ignore[arg-type]
            if isinstance(node, ast.Lambda) and node.lineno - 1 == lambda_lineno:
                lambdas_on_same_line.append(node)

        if not lambdas_on_same_line:
            raise Exception(
                f'Lambda not found at line {lambda_lineno} of {inspect.getsourcefile(lambda_func)}'
            )
        # We don't support it, because inspect only tells us which line the lambda was defined, but
        # not where on the line. So there is no way to tell which of the 2+ lambdas it is.
        if len(lambdas_on_same_line) > 1:
            raise NotImplementedError(
                f'More than 1 lambda found on line {lambda_lineno} '
                f'of {inspect.getsourcefile(lambda_func)}'
            )

        lambda_node = lambdas_on_same_line[0]
        at_lambda_node = atok.get_token(lambda_node.lineno, lambda_node.col_offset)
        start = at_lambda_node.startpos
        end = lambda_node.last_token.endpos  # type: ignore[attr-defined]
        return full_source[start:end]

    @classmethod
    def _parse_source(cls, code: str) -> asttokens.ASTTokens:
        h = hashlib.sha256(code.encode('utf-8')).digest()
        if h not in cls._asts:
            cls._asts[h] = asttokens.ASTTokens(code, parse=True)
        return cls._asts[h]

    @staticmethod
    def _get_block_inputs(function_arguments: Set[str]) -> Set[str]:
        """
        Given the names of the arguments of a CCB function returns the names of the actual
        block inputs discarding system arguments.
        """
        block_inputs = set(function_arguments)
        # discard kwargs, can't be passed as an input
        block_inputs.discard('kwargs')
        # discard system arguments, they don't need to be passed as inputs
        return block_inputs - set(BaseCodeBlock._system_arguments)

    @staticmethod
    def _validate_params(params: Set[str], inputs: Dict[str, Any]) -> None:
        assert params.issubset(
            inputs.keys()
        ), 'code signature cannot be satisfied by the provided input params: {} vs {}'.format(
            params, inputs.keys()
        )

    @staticmethod
    def _generate_code_from_template(
        fn: Callable, params: Set[str], additional_imports: str = ''
    ) -> str:
        template = """
from typing import Any, Dict, List, Tuple
from blocks.base_python_block import WFEngineTaskResult
from blocks.types import BlockInputs
{imports}

# Used to deserialize json inputs by the CCB
class CustomCodeBlockProxyInputs(BlockInputs):
{block_inputs_schema}

{real_function_def}

{function_invocation}
"""
        fn_source = inspect.getsource(fn)
        fn_indent = inspect.indentsize(fn_source)
        fn_dedent = '\n'.join(
            [
                line[fn_indent:]
                for line in fn_source.split('\n')
                if not line[fn_indent:].startswith('@')
            ]
        )
        # a bit ugly, but we should handle empty schema as well
        input_class_fields = BaseCodeBlock._get_block_inputs(params)
        if input_class_fields:
            block_inputs_schema = '\n'.join(
                f'    {param}: Any' for param in sorted(input_class_fields)
            )
        else:
            block_inputs_schema = '    pass'

        system_arguments = BaseCodeBlock._build_system_arguments(params)
        if system_arguments:
            imports = f'from flows_sdk.types import *\n{additional_imports}'
            function_invocation_template = """
def process_task_flows_sdk_types(
    _hs_block_instance: HsBlockInstance, _hs_task: HsTask, input_data: CustomCodeBlockProxyInputs
) -> WFEngineTaskResult:
    return {real_function_name}(**input_data.dict(){system_arguments})
"""
        else:
            # this case exists entirely for backward compatibility, the new version is capable
            # of running without system arguments but if we always use the above template the
            # generated code would not run on older versions of the code blocks
            imports = (
                f'from blocks.base_python_block import Block, WFEngineTask\n{additional_imports}'
            )
            function_invocation_template = """
def process_task(
    proxy: Block, task: WFEngineTask[CustomCodeBlockProxyInputs]
) -> WFEngineTaskResult:
    return {real_function_name}(**task.inputData.dict())
"""

        return template.format(
            real_function_def=fn_dedent,
            block_inputs_schema=block_inputs_schema,
            imports=imports,
            function_invocation=function_invocation_template.format(
                real_function_name=fn.__name__, system_arguments=system_arguments
            ),
        )

    @staticmethod
    def _build_system_arguments(params: Set[str]) -> str:
        """
        Builds a list of arguments that will be mapped to system variables defined in the code
        template that encloses the user defined function. Whether these arguments are referenced
        in the function definition is evaluated at flow compile time but the actual objects are
        created and injected at runtime by the block.
        """
        return ''.join(
            [f', {arg}={arg}' for arg in BaseCodeBlock._system_arguments if arg in params]
        )


class PythonBlock(BaseCodeBlock):
    """Python Blocks are a special type of block that can run custom Python code on
    the Hyperscience Platform. Code will be serialized, then, as part of a flow run,
    executed on an isolated environment. By default, users can only utilize packages that
    are part of the Python Standard Library. To access third-party Python packages,
    users need to follow these
    :ref:`instructions <pages/python_packages:Managing Third-Party Python Packages>`
    to have them installed on the Hyperscience Platform.

    Lambda functions are executed in the context of the execution engine itself
    (less overhead, but cannot be scaled)
    Code functions are executed in a dedicated container (more overhead, can scale horizontally)

    The PythonBlock can be compiled to blocks that run on different Python versions. There are
    several ways to modify the behavior.

    By default, the Python version of the PythonBlock will be set based on the Python version of
    the current Python virtual environment. For example, if the current virtual environment uses
    Python 3.11, the PythonBlock will be compiled to a Python 3.11 block. If the version is not
    supported, it would default to Python 3.9 block.

    To override the default behavior controlled by the virtual environment, an environment
    variable - `HS_PYTHON_CODE_BLOCK_PYTHON_VERSION` - can be set. All blocks would be compiled to
    use the Python version dictated by that variable. It can be set to `3.9`, `3.11` or `3.12`.

    To enable more fine-grained control over the Python version of the block, `python_version`
    parameter can be explicitly set to each `PythonBlock` instance using one of the available values
    in the :py:class:`flows_sdk.blocks.PythonBlock.SupportedPythonBlockPythonVersion` enum.

    - **Python Block version modifier precedence**

        `virtual env version` < `HS_PYTHON_CODE_BLOCK_PYTHON_VERSION` env var <
        specific `python_version` argument to PythonBlock

    Python version examples:

    Default behaviour, given a virtual environment based off Python 3.9::

        PythonBlock(
            reference_name='ref_name', code=lambda x, y: x + y, code_input={'x': 0, 'y': 1}
        )

        produces:

        {
            "identifier": "PYTHON_CODE",
            "reference_name": "ref_name",
            "input": {"data": {"x": 0, "y": 1}, "code": "lambda x, y: x + y"}
        }

    Default behaviour, given a virtual environment based off Python 3.11::

        PythonBlock(
            reference_name='ref_name', code=lambda x, y: x + y, code_input={'x': 0, 'y': 1}
        )

        produces:

        {
            "identifier": "PYTHON_3_11_CODE",
            "reference_name": "ref_name",
            "input": {"data": {"x": 0, "y": 1}, "code": "lambda x, y: x + y"}
        }

    `HS_PYTHON_CODE_BLOCK_PYTHON_VERSION` is set to `3.11`. Virtual environment Python version
    is ignored::

        PythonBlock(
            reference_name='ref_name', code=lambda x, y: x + y, code_input={'x': 0, 'y': 1}
        )

        produces:

        {
            "identifier": "PYTHON_3_11_CODE",
            "reference_name": "ref_name",
            "input": {"data": {"x": 0, "y": 1}, "code": "lambda x, y: x + y"}
        }

    `HS_PYTHON_CODE_BLOCK_PYTHON_VERSION` is set to `3.9`, but `python_version` is set
    to `3.11` in the block instance. Virtual environment Python version is ignored::

        PythonBlock(
            reference_name='ref_name',
            code=lambda x, y: x + y,
            code_input={'x': 0, 'y': 1},
            python_version=PythonBlock.SupportedPythonBlockPythonVersion.PYTHON_3_11
        )

        produces:

        {
            "identifier": "PYTHON_3_11_CODE",
            "reference_name": "ref_name",
            "input": {"data": {"x": 0, "y": 1}, "code": "lambda x, y: x + y"}
        }


    Example usage with a code function::

        def code_fn(a_static_input: int, a_dynamic_input: str) -> str:
            import regex # third party python package
            return 'found' if regex.search(r'Hello|Hi', 'HelloWorld') else 'not found'

        function_ccb = PythonBlock(
            reference_name='example_function_ccb',
            code=code_fn,
            code_input={
                'a_static_input': 42,
                'a_dynamic_input': some_previous_block.output('path.to.value')
            },
        )

    Example usage with a lambda::

        lambda_ccb = PythonBlock(
            reference_name='example_lambda_ccb',
            code=lambda a_static_input, a_dynamic_input: {
                'foo': f'prefix_{a_dynamic_input}',
                'bar': 5 + a_static_input
            },
            code_input={
                'a_static_input': 42,
                'a_dynamic_input': some_previous_block.output('path.to.value')
            },
        )

    .. _instructions: /pages/python_packages.html
    """

    class SupportedPythonBlockPythonVersion(str, Enum):
        """
        Describes which versions of Pyhon can be passed to the `python_version`
        argument of PythonCode.
        """

        PYTHON_3_9 = 'PYTHON_CODE'
        """DEPRECATED from version 40+ due to end-of-life of Python 3.9"""

        PYTHON_3_11 = 'PYTHON_3_11_CODE'
        """Available since version 39.1"""

        PYTHON_3_12 = 'PYTHON_3_12_CODE'
        """Available since version 41.0"""

        def __str__(self) -> str:
            return self.value

    _python_version_to_block_identifier_map = {
        SupportedPythonBlockPythonVersion.PYTHON_3_9: 'PYTHON_CODE',
        SupportedPythonBlockPythonVersion.PYTHON_3_11: 'PYTHON_3_11_CODE',
        SupportedPythonBlockPythonVersion.PYTHON_3_12: 'PYTHON_3_12_CODE',
    }

    _python_version_to_enum = {
        '3.9': SupportedPythonBlockPythonVersion.PYTHON_3_9,
        '3.11': SupportedPythonBlockPythonVersion.PYTHON_3_11,
        '3.12': SupportedPythonBlockPythonVersion.PYTHON_3_12,
    }

    _venv_python_version = f'{sys.version_info.major}.{sys.version_info.minor}'
    _DEFAULT_PYTHON_VERSION = _python_version_to_enum.get(
        _venv_python_version, SupportedPythonBlockPythonVersion.PYTHON_3_9
    )

    def __init__(
        self,
        code: Callable,
        reference_name: Optional[str] = None,
        code_input: Optional[Dict[str, Any]] = None,
        input: Optional[Dict[str, Any]] = None,  # pylint: disable=W0622
        title: Optional[str] = None,
        description: Optional[str] = None,
        python_version: Optional[SupportedPythonBlockPythonVersion] = None,
    ) -> None:
        inputs = {**(input or {}), 'data': code_input or {}}
        # explicitly provided python_version overrides external settings
        if python_version:
            identifier = python_version
        else:
            target_python_version = os.environ.get('HS_PYTHON_CODE_BLOCK_PYTHON_VERSION', '')
            identifier = self._python_version_to_enum.get(
                target_python_version, self._DEFAULT_PYTHON_VERSION
            )

        super().__init__(
            code=code,
            reference_name=reference_name,
            identifier=identifier.value,
            input={**inputs, 'code': self._format_code(code, inputs)},
            title=title,
            description=description,
        )


class CodeBlock(BaseCodeBlock):
    """DEPRECATED from 34.0.1+ going forward, please use :py:class:`flows_sdk.blocks.PythonBlock`
    instead

    Code Blocks are a special type of block that can run custom Python code on
    the Hyperscience Platform. Code will be serialized, then, as part of a flow run,
    executed on an isolated environment. It will not have access
    to dependencies outside of basic ones like the Python Standard Library.

    Lambda functions are executed in the context of the execution engine itself
    (less overhead, but cannot be scaled)
    Code functions are executed in a dedicated container (more overhead, can scale horizontally)

    Example usage with a code function::

        def code_fn(a_static_input: int, a_dynamic_input: str) -> str:
            return f'Hello {code_block_input_param}'

        function_ccb = CodeBlock(
            reference_name='example_function_ccb',
            code=code_fn,
            code_input={
                'a_static_input': 42,
                'a_dynamic_input': some_previous_block.output('path.to.value')
            },
        )

    Example usage with a lambda::

        lambda_ccb = CodeBlock(
            reference_name='example_lambda_ccb',
            code=lambda a_static_input, a_dynamic_input: {
                'foo': f'prefix_{a_dynamic_input}',
                'bar': 5 + a_static_input
            },
            code_input={
                'a_static_input': 42,
                'a_dynamic_input': some_previous_block.output('path.to.value')
            },
        )

    """

    IDENTIFIER = 'CUSTOM_CODE'

    def __init__(
        self,
        code: Callable,
        reference_name: Optional[str] = None,
        code_input: Optional[Dict[str, Any]] = None,
        input: Optional[Dict[str, Any]] = None,  # pylint: disable=W0622
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        inputs = {**(input or {}), 'data': code_input or {}}
        super().__init__(
            code=code,
            reference_name=reference_name,
            identifier=self.IDENTIFIER,
            input={**inputs, 'code': self._format_code(code, inputs)},
            title=title,
            description=description,
        )


class _Branch:
    def __init__(
        self, blocks: Sequence[Block], label: Optional[str] = None, output: Optional[str] = None
    ):
        assert len(blocks) > 0 or output, 'Empty branch - at least one block or output is required'
        self.blocks = blocks
        self.label = label
        self.output = output

    def render(self) -> Dict[str, Any]:
        """:meta private:"""
        r: Dict[str, Any] = {'blocks': [element for b in self.blocks for element in b.render()]}
        if self.label is not None:
            r['label'] = self.label
        if self.output is not None:
            r['output'] = self.output
        return r


class Fork(Block):
    """Fork is a system block that is used to schedule other
    blocks for parallel execution.

    While all branches of a Fork will be scheduled for parallel execution,
    the tasks within a branch itself will be executed serially.

    The output of a Fork is a dictionary with key: identifier of the output block from each branch
    and value: the output from that block

    :param reference_name: unique identifier on a per-Flow basis
    :type reference_name: str
    :param branches: A sequence of branches, that will be scheduled for parallel execution.
    :type branches: Sequence[Fork.Branch]
    :param title: UI-visible title of the block.
    :type title: Optional[str]
    :param description: Description of the block. Both useful for documentation purpose and visible
            to users in the Flow studio.
    :type description: Optional[str]


    .. include:: ../../../samples/fork/fork_flow.py
        :literal:

    """

    class Branch(_Branch):
        """A collection of Blocks that will be serially scheduled for execution.

        :param blocks: A sequence of Blocks that will be executed as part of that Fork.Branch.
            Should contain at least one.
        :type blocks: Sequence[Block]
        :param label: UI-visible text lable of the branch.
        :type label: Optional[str]
        :param output: Reference name of the Block which will be used as the output of the entire
            branch. When not provided, the output of the last block of the branch will be treated
            as the branch output.
        :type output: Optional[str]
        """

        pass

    def __init__(
        self,
        reference_name: str,
        branches: Sequence['Fork.Branch'],
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        assert len(branches) > 0, 'Fork requires at least a single branch'

        super().__init__(
            reference_name=reference_name,
            identifier='STATIC_FORK',
            title=title,
            description=description,
        )
        self._branches = branches

    def _render_self(self) -> Dict[str, Any]:
        base = super()._render_self()
        base['branches'] = [br.render() for br in self._branches]
        return base


class Routing(Block):
    """Routing is a system Block that executes only
    the blocks in one of its branches that meets a condition.
    Similar in concept to a `switch..case` or an `if/else` construction.

    :param reference_name: [description]
    :param decision: [description]
    :param branches: [description]
    :param default_branch: [description], defaults to None
    :param title: [description], defaults to None
    :param description: [description], defaults to None

    .. include:: ../../../samples/routing/routing_flow.py
        :literal:

    """

    class Branch(_Branch):
        """[summary]

        :param case: case that must be matched in order for this branch to be scheduled for
            execution.
        :type case: str
        :param blocks: sequence of blocks to be executed as part of this branch
        :type blocks: Sequence[Block]
        :param label: UI-visible text lable of the branch
        :type label: Optional[str]
        :param output: Reference name of the Block which will be used as the output of the entire
            branch. When not provided, the output of the last block of the branch will be treated
            as the branch output.
        :type output: Optional[str]
        """

        def __init__(
            self,
            case: str,
            blocks: Sequence[Block],
            label: Optional[str] = None,
            output: Optional[str] = None,
        ):
            super().__init__(blocks=blocks, label=label, output=output)
            self.case = case

        def render(self) -> Dict[str, Any]:
            """:meta private:"""
            return {**super().render(), 'case': self.case}

    class DefaultBranch(_Branch):
        """Same as :py:class:`flows_sdk.blocks.Routing.Branch`, but without a case.
        DefaultBranch is optionally provided and executed as a fallback when there is no
        matching case from other branches.
        """

        pass

    def __init__(
        self,
        decision: str,
        branches: Sequence['Routing.Branch'],
        reference_name: Optional[str] = None,
        default_branch: Optional['Routing.DefaultBranch'] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        assert (
            len(branches) > 0 or default_branch is not None
        ), 'Routing requires at lease a single branch'
        super().__init__(
            reference_name=reference_name,
            identifier='ROUTING',
            title=title,
            description=description,
        )
        self._decision = decision
        self._branches = branches
        self._default_branch = default_branch

    def _render_self(self) -> Dict[str, Any]:
        base = super()._render_self()
        rendered_branches = [br.render() for br in self._branches]
        if self._default_branch is not None:
            rendered_branches.append(self._default_branch.render())
        base['branches'] = rendered_branches
        base['decision'] = self._decision
        return base


class IOBlock(Block):
    """A Block that has the additional boolean property `enabled`.
    Used for Triggers and Outputs where enabled can be triggered via the Flow Studio UI
    and is considered during processing (e.g. only enabled Triggers can initiate Flow execution).

    See :py:class:`flows_sdk.blocks.Block` for description of the inherited parameters.

    :param enabled: on-off state of the Block.
        Visualized as a checkbox and taken into account during processing.
    :type enabled: bool
    """

    def __init__(
        self,
        identifier: str,
        enabled: bool,
        reference_name: Optional[str] = None,
        input: Optional[Dict[str, Any]] = None,  # pylint: disable=W0622
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        super().__init__(
            reference_name=reference_name,
            identifier=identifier,
            input=input,
            title=title,
            description=description,
        )
        self._enabled = enabled

    def _render_self(self) -> Dict[str, Any]:
        return {**super()._render_self(), 'enabled': self._enabled}


class Outputs(Block):
    """Outputs is a special block-section meant to provide an easy way for users to configure
    Flow output connections through the UI. They contain a list of output blocks, that can
    optionally be filtered by role and define an input template that will wire these blocks'
    inputs automatically after the user adds them.


    :param reference_name: unique identifier on a per-Flow basis, used to identify the
        concrete block within a Flow (e.g., in order to reference the outputs of a concrete block)
    :param role_filter: Serves as an instruction to the UI for what blocks are allowed in
        this output section, since not all output blocks will be suitable for all flows.
        UI will allow adding only blocks that have all listed roles.
        If empty, blocks with any role will be allowed.
    :param input_template: Used by the UI to automatically pre-populate the input of
        newly added blocks. Thus the Flow designer can define the wiring of output blocks
        to the results from previous blocks in the Flow, while allowing the user
        to add or remove output blocks via the UI.
    :param blocks: List of output IOBlocks for sending results to external systems.
        Can be empty, since the outputs within an Outputs section are editable in Flow studio.
    :param title: UI-visible title of the block.
    :param description: Description of the block. Both useful for documentation purpose and visible
            to users in the Flow studio.
    """

    def __init__(
        self,
        role_filter: List[str],
        input_template: Dict[str, Any],
        blocks: Sequence[IOBlock],
        reference_name: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        super().__init__(
            reference_name=reference_name,
            identifier='OUTPUTS',
            title=title,
            description=description,
        )
        self._role_filter = role_filter
        self._input_template = input_template
        self._blocks = blocks

    def _render_self(self) -> Dict[str, Any]:
        # sanity check that all blocks renders as single HS DSL element
        rendered_blocks = []
        for block in self._blocks:
            rendered = block.render()
            assert len(rendered) == 1, 'IOBlock should render to single HS DSL element'
            rendered_blocks.append(rendered[0])

        return {
            **super()._render_self(),
            'role_filter': self._role_filter,
            'input_template': self._input_template,
            'blocks': rendered_blocks,
        }


class Foreach(Block):
    """
    **Available in v35 and later.**

    Foreach is a system block that can be used to run a given task for each item in a collection.
    The task is represented by a block and the collection is dynamically generated at runtime - can
    be a flow input or the output of a previous block.
    The block that will run for each item in the collection is called a "template" and supports
    special syntax for referencing the basic foreach loop concepts:

    - ``${foreach_reference_name.item}`` - to access the current item. Syntax like
      ${foreach_reference_name.item.nested_prop} is also supported.
    - ``${foreach_reference_name.index}`` - to access the index of the current item, 0-based

    At runtime Foreach dynamically generates blocks by applying the template to each item in the
    collection. The generated blocks are executed in parallel.
    The output of the Foreach block is a list that contains the outputs of the dynamically created
    blocks in the same order as the input collection.

    :param items: reference to the list of items to which the template will be applied
    :param template: the block to run for each item in the provided collection
    :param reference_name: unique identifier of the block in the flow. Note that unlike in other
            blocks here the reference_name is not optional as it is needed to refer to the items
            of the collection in the template
    :param title: UI-visible title of the block.
    :param description: Description of the block. Both useful for documentation purposes and
            visible to users in the Flow studio.

    .. include:: ../../../samples/foreach/foreach_flow.py
        :literal:
    """

    def __init__(
        self,
        items: str,
        template: Block,
        reference_name: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        assert reference_name, (
            'reference_name is required in the Foreach block because it is used to refer to '
            'the items of the collection in the template. See the examples for details.'
        )
        super().__init__(
            reference_name=reference_name,
            identifier='FOREACH',
            title=title,
            description=description,
        )
        self._items = items
        self._template = template

    def _render_self(self) -> Dict[str, Any]:
        rendered_template = self._template._render_self()
        # if the reference name of the template is static add the foreach index at the end
        template_ref_name = rendered_template['reference_name']
        if re.search(r'\${%s\.[\w.-]+}' % self._reference_name, template_ref_name) is None:
            rendered_template['reference_name'] += '_${%s.index}' % self._reference_name
        return {**super()._render_self(), 'items': self._items, 'template': rendered_template}

    def output(self, key: Optional[str] = None) -> str:
        # the actual list output is nested in a result dict because it is created
        # using a LAMBDA_PYTHON block
        return super().output('result' + ('' if not key else '.' + key))
