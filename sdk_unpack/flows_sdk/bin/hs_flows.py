#!/usr/bin/env python
"""
CLI tool for Flows SDK.
Provides an interface for bundling flows into zip files.
"""
import logging
from argparse import ArgumentParser, ArgumentTypeError, Namespace, RawTextHelpFormatter
from pathlib import Path

from flows_sdk.lib.bundle_utils import BundleError, BundleExporter, slugify

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def py_or_dir(value: str) -> str:
    path = Path(value)
    if path.exists() and (path.suffix == '.py' or path.is_dir()):
        return value
    raise ArgumentTypeError(f'Invalid input path "{value}": should be an existing directory or .py')


def zip_or_dir(value: str) -> str:
    path = Path(value)
    if path.is_dir():
        return value
    if path.suffix == '.zip' and path.parent.is_dir():
        return f'{path.parent / slugify(path.stem)}.zip'
    raise ArgumentTypeError(
        f'Invalid output path "{value}": should be an existing directory or a provisional .zip'
    )


def parse_args() -> Namespace:
    parser = ArgumentParser(description='Flows SDK CLI tool')
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True
    bundle = subparsers.add_parser(
        'bundle',
        help='bundle one or more flows into a zip',
        description='Bundle one or more flows into a zip file.',
        formatter_class=RawTextHelpFormatter,
    )
    bundle.add_argument(
        'input',
        nargs='+',
        type=py_or_dir,
        help='input path: either a .py flow file, or a directory containing flow files',
    )
    bundle.add_argument(
        '-o',
        '--output',
        type=zip_or_dir,
        default='.',
        help='output path: either a .zip file to create, or a directory to auto-create it in\n'
        'note: will overwrite if the file already exists\n'
        '(default: current directory)',
    )
    bundle.add_argument(
        '-c',
        '--code-extraction-policy',
        choices=['inline', 'files'],
        default='inline',
        help='policy for custom code extraction into external files:\n'
        '"inline" to keep code inline in the json\n'
        '"files" to extract code into external files\n'
        '(default: inline)',
    )
    bundle.add_argument(
        '-e',
        '--entry-point',
        help='name of the flow entry point function that returns a Flow;\n'
        'used to locate flows inside the python files\n'
        '(default: entry_point_flow, entry_point_workflow)',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == 'bundle':
        flow_exporter = BundleExporter(
            args.input, args.output, args.code_extraction_policy, args.entry_point
        )
        try:
            flow_exporter.export()
        except BundleError as err:
            logger.error(err)


if __name__ == '__main__':
    main()
