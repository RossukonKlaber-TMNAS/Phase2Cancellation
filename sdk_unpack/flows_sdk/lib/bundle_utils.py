import ast
import os
import re
from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
from logging import getLogger
from pathlib import Path, PurePosixPath
from shutil import which
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Set, Union
from unicodedata import normalize
from uuid import UUID
from zipfile import ZipFile

from flows_sdk.blocks import CodeBlock, PythonBlock
from flows_sdk.flows import Flow
from flows_sdk.package_utils import json_from_dict

logger = getLogger(__name__)


def slugify(value: str) -> str:
    value = normalize('NFKC', value)
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


class EntryPointError(Exception):
    """
    Raised by FlowFile when we cannot find the entrypoint function
    that returns the top-level flow in the module of a flow.
    See FlowFile.DEFAULT_ENTRY_FUNCTIONS.
    """

    pass


class BundleError(Exception):
    """
    Parent to the Exceptions raised by BundleExporter.
    """

    pass


class FlowsNotFoundError(BundleError):
    """
    Raised by BundleExporter when we cannot find any valid flows in the specified input locations.
    """

    pass


class InputFileNotFoundError(BundleError):
    """
    Raised by BundleExporter when the specified input file of some flow does not exist.
    """

    pass


class InvalidInputFile(BundleError):
    """
    Raised by BundleExporter when the specified input file of some flow is invalid.
    E.g. it's located outside the flow directory scope or is executable.
    """

    pass


class FlowFile:
    """
    Holds information about a flow file.
    Usually constructed via from_path().
    """

    EXPORT_FUNCTION = 'export_flow'

    DEFAULT_ENTRY_FUNCTIONS = (
        'entry_point_flow',
        'entry_point_workflow',
    )

    def __init__(self, path: Path, flow: Flow):
        self.path = path
        self.name = path.stem
        self.directory = path.parents[0]
        self.flow = flow

    @classmethod
    def from_path(cls, path: Path, custom_entry_point: Optional[str] = None) -> 'FlowFile':
        """
        Parses a file and creates a FlowFile object if a flow is found inside.
        :param path: path to flow file
        :param custom_entry_point: name of custom entry point function
        """
        flow = cls._parse_file(path, custom_entry_point)
        return cls(path, flow)

    @classmethod
    def _get_default_entry_point(
        cls, ast_tree: ast.Module, custom_entry_point: Optional[str]
    ) -> Optional[str]:
        entry_points = (
            [custom_entry_point, *cls.DEFAULT_ENTRY_FUNCTIONS]
            if custom_entry_point
            else cls.DEFAULT_ENTRY_FUNCTIONS
        )
        functions = [
            func.name
            for func in ast.walk(ast_tree)
            if isinstance(func, ast.FunctionDef) and func.args.args == []
        ]
        for entry_point in entry_points:
            if entry_point in functions:
                return entry_point
        return None

    @classmethod
    def _resolve_name(cls, main_body: List[ast.stmt], name: ast.expr) -> Optional[str]:
        for item in main_body:
            if (
                isinstance(item, ast.Assign)
                and item.targets[0].id == name.id  # type: ignore[attr-defined]
            ):
                name = item.value
            if isinstance(name, ast.Call) and isinstance(name.func, ast.Name):
                return name.func.id
        return None

    @classmethod
    def _parse_entry_point(cls, ast_tree: ast.Module) -> Optional[str]:
        main_if = [
            item
            for item in ast_tree.body
            if isinstance(item, ast.If)
            and isinstance(item.test, ast.Compare)
            and isinstance(item.test.left, ast.Name)
            and item.test.left.id == '__name__'
        ]
        if len(main_if) != 1:
            return None  # either too many or too few main sections found
        arg = None
        main_body = main_if[0].body[::-1]
        for item in main_body:  # iterate over the main section to find the export_flow() call
            if (
                isinstance(item, ast.Expr)
                and isinstance(item.value, ast.Call)
                and isinstance(item.value.func, ast.Name)
                and item.value.func.id == cls.EXPORT_FUNCTION
            ):
                if item.value.args:  # find the flow argument
                    arg = item.value.args[0]
                elif item.value.keywords:
                    for kw in item.value.keywords:
                        if kw.arg == 'flow':
                            arg = kw.value
        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name):
            return arg.func.id
        if isinstance(arg, ast.Name):  # if the flow arg is a var, try to resolve it
            return cls._resolve_name(main_body, arg)
        return None

    @classmethod
    def _parse_file(cls, path: Path, custom_entry_point: Optional[str]) -> Flow:
        with open(path, 'r') as flow_file:
            ast_tree = ast.parse(flow_file.read())
        entry_point_name = cls._get_default_entry_point(
            ast_tree, custom_entry_point
        ) or cls._parse_entry_point(ast_tree)
        if entry_point_name is None:
            raise EntryPointError(
                f'No entry point found when parsing {path}: '
                'Make sure all flows have an entry_point_flow()'
                ' function that returns a Flow object.'
            )
        elif entry_point_name not in cls.DEFAULT_ENTRY_FUNCTIONS:
            logger.warning(
                '%s: Function %s() located as entry point: '
                'Please make sure your flow has an entry_point_flow() '
                'function that returns the Flow object to be exported."',
                path,
                entry_point_name,
            )
        # execute flow file and return flow
        spec = spec_from_file_location(path.stem, path)
        module = module_from_spec(spec)  # type: ignore[arg-type]
        try:
            spec.loader.exec_module(module)  # type: ignore[union-attr]
            entry_point = getattr(module, entry_point_name)
            return entry_point()
        except Exception as err:
            logger.error('%s encountered while running %s:', type(err).__name__, path)
            raise


class BundleExporter:
    """
    Bundling utility for flows SDK.
    Parses flows and exports them into a .zip file.
    :param input_paths:
        List of .zip or directory paths to find flows in.
    :param output_path:
        A provisional .zip or existent directory path to write output to.
    :param code_policy:
        Policy for extracting code from Custom Code Blocks.
        Strictly 'inline' or 'files'.
    :param entry_point:
        Optional name of entry point function to look for in flow files.
        Defaults are entry_point_flow() and entry_point_workflow().
    """

    CODE_BLOCK_IDENTIFIERS = [
        CodeBlock.IDENTIFIER,
        PythonBlock.SupportedPythonBlockPythonVersion.PYTHON_3_9.value,
        PythonBlock.SupportedPythonBlockPythonVersion.PYTHON_3_11.value,
    ]

    def __init__(
        self,
        input_paths: List[Union[str, Path]],
        output_path: Union[str, Path],
        code_policy: str,
        entry_point: Optional[str] = None,
    ) -> None:
        self._input_paths = input_paths
        self._output_path = output_path
        self._code_policy = code_policy
        self._custom_entry_point = entry_point

    def _zipfile_path(self, flow_titles: List[str]) -> Path:
        path = Path(self._output_path)
        if path.is_dir():
            if len(flow_titles) == 1:
                return path / f'{slugify(flow_titles[0])}.zip'
            return path / f'flows-{datetime.now().strftime("%Y%m%d_%H%M")}.zip'
        elif path.suffix == '.zip':
            return path
        raise ValueError(f'Output path {path} should be a .zip or a directory.')

    @staticmethod
    def _extract_code(block: Dict[str, Any], flow_file: FlowFile, zip_file: ZipFile) -> None:
        ast_tree = ast.parse(block['input']['code'])
        if (  # check if lambda
            ast_tree.body
            and len(ast_tree.body) == 1
            and isinstance(ast_tree.body[0], ast.Expr)
            and isinstance(ast_tree.body[0].value, ast.Lambda)
        ):
            return
        # generate script filepath
        file_path = Path('files') / f'{block["reference_name"]}-{flow_file.flow.uuid}.py'
        # store script file and link it
        zip_file.writestr(str(file_path), block['input']['code'])
        block['input']['script_ref'] = f'file:/{PurePosixPath(file_path)}'
        # delete inline code
        del block['input']['code']

    @staticmethod
    def _is_executable(filepath: Path) -> bool:
        if os.name == 'posix':
            return which(filepath) is not None
        elif os.name == 'nt':  # windows
            path_ext_default = '.COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.MSC'
            path_ext = os.environ.get('PATHEXT', path_ext_default)
            ext = path_ext.lower().split(';')
            if filepath.suffix.lower() in ext:
                return True
            return False
        raise RuntimeError(f'Unreachable: os.name is {os.name}.')  # somehow on JavaOS

    def _validate_input_file(self, path: Path, flow_file: FlowFile) -> None:
        relative_path = path.relative_to(flow_file.directory)
        if not path.is_file():
            raise InputFileNotFoundError(
                f'Failed to parse {flow_file.name}.py: Input file {path} does not exist.'
            )
        if flow_file.directory.resolve() not in path.resolve().parents:
            raise InvalidInputFile(
                f'Failed to parse {flow_file.name}.py: Input file {relative_path} is '
                f'out of scope - please make sure it is within the respective flow directory.'
            )
        if self._is_executable(path):
            raise InvalidInputFile(
                f'Failed to parse {flow_file.name}.py: Input file {relative_path} is an '
                'executable - please make sure the flow does not include executable input files. '
                f'(If you still want this file: on unix you can chmod -x it; '
                'on windows you can modify the %PATHEXT% environment variable)'
            )

    def _extract_input_file(
        self, dsl_obj: Dict[str, Any], input_name: str, flow_file: FlowFile, zip_file: ZipFile
    ) -> None:
        file_path = dsl_obj['input'][input_name]
        full_path = flow_file.directory / Path(file_path)
        # parse and validate file path
        if Path(file_path).parts[0] == 'file:':
            full_path = flow_file.directory / Path(file_path).relative_to('file:')
        self._validate_input_file(full_path, flow_file)
        # generate file path
        ref_name = dsl_obj.get('reference_name', 'root')
        new_filename = f'{full_path.stem}-{input_name}-{ref_name}-{flow_file.flow.uuid}'
        new_path = Path('files') / f'{new_filename}{full_path.suffix}'
        # store file and link it
        zip_file.write(str(full_path), str(new_path))
        dsl_obj['input'][input_name] = f'file:/{PurePosixPath(new_path)}'

    def _traverse_and_extract(
        self, root: Any, flow_file: FlowFile, file_inputs: Set[str], zip_file: ZipFile
    ) -> Any:
        """
        Traverse the dsl recursively, extracting custom code and input files into the zip.
        """
        if isinstance(root, list):
            return [
                self._traverse_and_extract(item, flow_file, file_inputs, zip_file) for item in root
            ]
        if isinstance(root, dict):
            if (
                self._code_policy == 'files'
                and root.get('identifier') in self.CODE_BLOCK_IDENTIFIERS
            ):
                self._extract_code(root, flow_file, zip_file)
            if 'input' in root and isinstance(root['input'], dict):
                for name in root['input'].keys():
                    if name in file_inputs:
                        self._extract_input_file(root, name, flow_file, zip_file)
            return {
                key: self._traverse_and_extract(value, flow_file, file_inputs, zip_file)
                for key, value in root.items()
            }
        return root

    def _process_code_and_files(self, flow_file: FlowFile, zip_file: ZipFile) -> Dict[str, Any]:
        dsl = flow_file.flow.render()
        file_inputs = set()
        for flow_input in dsl.get('manifest', {}).get('input', []):
            if flow_input.get('type') == 'File':
                file_inputs.add(flow_input['name'])
        return self._traverse_and_extract(dsl, flow_file, file_inputs, zip_file)

    def _collect_python_files(self) -> Set[Path]:
        result = set()
        for path_name in self._input_paths:
            path = Path(path_name)
            if path.is_file() and path.suffix == '.py':
                result.add(path)
            elif path.is_dir():
                for file in path.rglob('*.py'):
                    result.add(file)
            else:
                raise ValueError(f'Input path {path} should be a .py or a directory.')
        return result

    def _export(self, zip_path: Path) -> List[str]:
        """
        Renders flows into a zip along with any code/files as needed.
        """
        any_failed = False
        bundled: Dict[UUID, str] = {}
        with ZipFile(zip_path, 'w') as zip_file:
            for file_path in sorted(self._collect_python_files()):
                try:
                    flow_file = FlowFile.from_path(file_path, self._custom_entry_point)
                except EntryPointError as err:
                    logger.warning(err)
                    continue
                except SyntaxError as err:
                    logger.error('Error when parsing %s: %s', file_path, err)
                    any_failed = True
                    continue
                uuid = flow_file.flow.uuid
                if uuid in bundled:
                    logger.error(
                        'Unable to process flows with identical UUID: "%s" and "%s" Make sure .',
                        flow_file.flow.title,
                        bundled[uuid],
                    )
                    any_failed = True
                    continue
                try:
                    dsl = self._process_code_and_files(flow_file, zip_file)
                except BundleError as err:
                    logger.error(err)
                    any_failed = True
                    continue
                json_path = Path('flows') / f'{flow_file.name}-{flow_file.flow.uuid}.json'
                zip_file.writestr(str(json_path), json_from_dict(dsl))
                logger.info('"%s" bundled from %s.', flow_file.flow.title, flow_file.path)
                bundled[uuid] = flow_file.flow.title
        if any_failed:
            raise BundleError('Failed to bundle flow(s) due to errors.')
        if len(bundled) == 0:
            raise FlowsNotFoundError(
                f'No valid flows were found in the input locations {self._input_paths}.'
            )
        return list(bundled.values())

    def export(self) -> None:
        """
        Main entrypoint of the BundleExporter class.
        Wraps _export(), ensuring we only write to a non-temporary location in case of success.
        """
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / 'flows.temp.zip'
            bundled_titles = self._export(temp_path)
            real_path = self._zipfile_path(bundled_titles)
            temp_path.replace(real_path)
            logger.info('Successfully bundled %s flow(s) into %s.', len(bundled_titles), real_path)
