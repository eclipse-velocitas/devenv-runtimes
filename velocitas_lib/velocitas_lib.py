# Copyright (c) 2023 Robert Bosch GmbH
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0

import inspect
import json
import os
import re
import sys
from io import TextIOWrapper
from pathlib import Path
from typing import Any


def require_env(name: str) -> str:
    """Require and return an environment variable.

    Args:
        name (str): The name of the variable.

    Raises:
        ValueError: In case the environment variable is not set.

    Returns:
        str: The value of the variable.
    """
    var = os.getenv(name)
    if not var:
        raise ValueError(f"Environment variable {name!r} not set!")
    return var


def get_workspace_dir() -> str:
    """Return the workspace directory."""
    return require_env("VELOCITAS_WORKSPACE_DIR")


def get_app_manifest() -> dict:
    return json.loads(require_env("VELOCITAS_APP_MANIFEST"))


def get_script_path() -> str:
    """Return the absolute path to the directory the invoked Python script
    is located in."""
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def get_package_path() -> Path:
    """Return the absolute path to the package directory the invoked Python
    script belongs to."""
    invoking_file_path = inspect.stack()[1].filename
    parents = Path(invoking_file_path).resolve().parents
    for parent in parents:
        if parent.is_dir() and "manifest.json" in os.listdir(parent):
            return parent

    raise FileNotFoundError(
        f"Unable to find the package path of '{invoking_file_path}'!"
    )


def get_cache_data() -> dict[str, Any]:
    """Return the data of the cache as Python object."""
    return json.loads(require_env("VELOCITAS_CACHE_DATA"))


def get_services() -> dict[str, Any]:
    """Return all specified services as Python object."""
    path = f"{get_package_path()}/runtime.json"
    variable_value = require_env("runtimeFilePath")

    if variable_value is not None:
        overwritten_path = Path(variable_value)
        if not overwritten_path.is_absolute():
            overwritten_path = Path(get_workspace_dir()).joinpath(overwritten_path)

        if overwritten_path.exists():
            path = overwritten_path
            print(f"Runtime.json path redirected to {path}")

    return json.load(
        open(
            path,
            encoding="utf-8",
        )
    )


def replace_variables(input_str: str, variables: dict[str, str]) -> str:
    """Replace all occurrences of the defined variables in the input string"""
    if "${{" not in input_str:
        return input_str
    input_str_match = re.search(r"(?<=\${{)(.*?)(?=}})", input_str)
    if input_str_match:
        input_str_value = input_str_match.group().strip()
        if input_str_value not in variables:
            raise KeyError(f"{input_str_value!r} not in {variables!r}")
        for key, value in variables.items():
            input_str = input_str.replace("${{ " + key + " }}", str(value))
        return input_str
    else:
        raise ValueError(f"{input_str!r} not in the right format")


def json_obj_to_flat_map(obj, prefix: str = "", separator: str = ".") -> dict[str, str]:
    """Flatten a JSON Object into a one dimensional dict by joining the keys
    with the specified separator."""
    result = dict[str, str]()
    if isinstance(obj, dict):
        for key, value in obj.items():
            nested_key = f"{prefix}{separator}{key}"
            result.update(json_obj_to_flat_map(value, nested_key, separator))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            nested_key = f"{prefix}{separator}{index}"
            result.update(json_obj_to_flat_map(value, nested_key, separator))
    else:
        nested_key = f"{prefix}"
        result[nested_key] = obj

    return result


def get_log_file_name(service_id: str, runtime_id: str) -> str:
    """Build the log file name for the given service and runtime.

    Args:
        service_id (str): The ID of the service to log.
        runtime_id (str): The ID of the runtime to log.

    Returns:
        str: The log file name.
    """
    return os.path.join(get_workspace_dir(), "logs", runtime_id, f"{service_id}.txt")


def create_log_file(service_id: str, runtime_id: str) -> TextIOWrapper:
    """Create a log file for the given service and runtime.

    Args:
        service_id (str): The ID of the service to log.
        runtime_id (str): The ID of the runtime to log.

    Returns:
        TextIOWrapper: The log file.
    """
    log_file_name = get_log_file_name(service_id, runtime_id)
    os.makedirs(os.path.dirname(log_file_name), exist_ok=True)
    return open(log_file_name, "w", encoding="utf-8")
