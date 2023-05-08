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

import json
import os
import re
import sys


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


def get_cache_data():
    """Return the data of the cache as Python object."""
    return json.loads(require_env("VELOCITAS_CACHE_DATA"))


def get_services():
    """Return all specified services as Python object."""
    return json.load(open(f"{get_script_path()}/../../runtime.json", encoding="utf-8"))


def replace_variables(input_str: str, variables: dict[str, str]) -> str:
    """Replace all occurrences of the defined variables in the input string"""
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
