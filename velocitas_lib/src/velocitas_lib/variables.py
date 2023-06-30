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

import os
import re
from typing import Dict

from velocitas_lib import get_cache_data, get_package_path


def json_obj_to_flat_map(obj, prefix: str = "", separator: str = ".") -> Dict[str, str]:
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


class ProjectVariables:
    def __init__(self, env: Dict[str, str] = os.environ):
        self.__build_variables_map(env)

    def __build_variables_map(self, env: Dict[str, str]):
        variables: Dict[str, str] = {}
        variables.update(json_obj_to_flat_map(get_cache_data(), "builtin.cache"))
        variables.update(env)
        variables["builtin.package_dir"] = get_package_path()
        self._variables = variables

    def replace_occurrences(self, input_str: str) -> str:
        """Replace all occurrences of the defined variables in the input string"""
        if "${{" not in input_str:
            return input_str
        input_str_match = re.search(r"(?<=\${{)(.*?)(?=}})", input_str)
        if input_str_match:
            input_str_value = input_str_match.group().strip()
            if input_str_value not in self._variables:
                raise KeyError(f"{input_str_value!r} not in {self._variables!r}")
            for key, value in self._variables.items():
                input_str = input_str.replace("${{ " + key + " }}", str(value))
            return input_str
        else:
            raise ValueError(f"{input_str!r} not in the right format")
