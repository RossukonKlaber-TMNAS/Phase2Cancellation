import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic.json import pydantic_encoder

from flows_sdk.flows import Flow


def json_from_dict(flow_dict: Dict[str, Any]) -> str:
    return json.dumps(flow_dict, indent=2, default=pydantic_encoder) + '\n'


def export_flow(flow: Flow, filename: Optional[str] = None, location: str = '.') -> None:

    if filename:
        with open(Path(location) / f'{filename}.json', 'w') as f:
            f.write(json_from_dict(flow.render()))
    else:
        sys.stdout.write(json_from_dict(flow.render()))
