import base64
import hashlib
import mimetypes
import uuid


def workflow_input(*params: str) -> str:
    assert len(params) > 0, 'At least one parameter has to be specified for workflow inputs'
    param_path = '.'.join(params)
    return f'${{workflow.input.{param_path}}}'


def triggers_output(*params: str) -> str:
    param_path = '.'.join(params)
    param_path = f'.{param_path}' if param_path else ''
    return '${triggers.output.result' + param_path + '}'


def system_setting(key: str) -> str:
    return f'${{system.settings.{key}}}'


def system_secret(key: str) -> str:
    return f'${{system.secrets.{key}}}'


def icon_path_to_base64(icon_path: str) -> str:
    """
    Reads an icon file and returns it in "data:mimetype;base64,xxx" form for putting in a manifest
    """
    with open(icon_path, 'rb') as f:
        encoded_icon = base64.b64encode(f.read()).decode('ascii')
    mimetype, _ = mimetypes.guess_type(icon_path)
    icon_base64 = f'data:{mimetype};base64,{encoded_icon}'
    return icon_base64


def str_to_deterministic_uuid_4(value: str) -> uuid.UUID:
    """
    Generates a deterministic UUID from a given string
    """
    md5_encoded = hashlib.md5(value.encode(encoding='utf-8'))
    md5_hex = md5_encoded.hexdigest()
    return uuid.UUID(hex=md5_hex, version=4)
