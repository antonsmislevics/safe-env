import os
from tabulate import tabulate
import yaml
from pydantic import BaseModel
from typing import List, Any, Dict


def obj_to_dict(item: Any) -> Dict:
    if isinstance(item, BaseModel):
        item_dict = item.dict()
    elif isinstance(item, dict):
        item_dict = item
    else:
        item_dict = item.__dict__
    return item_dict


def print_table(items: List[Any], fields: List[str], headers: List[str], tablefmt:str = "pretty", sort_by_field_index: int = None) -> str:
    table = []
    for item in items:
        item_dict = obj_to_dict(item)
        record = list([item_dict[x] for x in fields])
        table.append(record)
    
    if not(sort_by_field_index is None):
        table = sorted(table, key=lambda x: x[sort_by_field_index])

    return tabulate(table, headers=headers, tablefmt=tablefmt)


def print_yaml(item: Any, unset=False) -> str:
    item_dict = obj_to_dict(item)
    if unset:
        for key, value in item_dict.items():
            item_dict[key] = ""
    obj_yaml = yaml.dump(item_dict, default_flow_style=False, sort_keys=False)
    return obj_yaml


def _escape_bash_value(value: str):
    return value.replace("\\", "\\\\").replace("$", "\\$").replace("\"", "\\\"")


def _escape_powershell_value(value: str):
    return value.replace("\"", "\"\"").replace("$", "`$")


def _escape_cmd_value(value: str):
    return value.replace("\"", "\"\"")


def print_env_export_script_bash(item: Any, unset=False) -> str:
    # TODO: check if escaping value is correct
    item_dict = obj_to_dict(item)
    script_parts = [f"export {key}=\"{'' if unset else _escape_bash_value(value)}\"" for (key, value) in item_dict.items()]
    return ";".join(script_parts)


def print_env_export_script_powershell(item: Any, unset=False) -> str:
    # TODO: check if escaping value is correct
    item_dict = obj_to_dict(item)
    script_parts = [f"$env:{key}=\"{'' if unset else _escape_powershell_value(value)}\"" for (key, value) in item_dict.items()]
    return ";".join(script_parts)


def print_env_export_script_cmd(item: Any, unset=False) -> str:
    # TODO: check if escaping value is correct
    item_dict = obj_to_dict(item)
    script_parts = [f"set \"{key}={'' if unset else _escape_cmd_value(value)}\"" for (key, value) in item_dict.items()]
    return ";".join(script_parts)


def print_docker_env_content(item: Any, unset=False) -> str:
    # TODO: unset is not used currently
    item_dict = obj_to_dict(item)
    script_parts = [f"{key}=${{{key}}}" for (key, value) in item_dict.items()]
    return os.linesep.join(script_parts)
