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

# flake8: noqa: U100 unused argument (because of pytest.fixture)

import json
import os

import pytest

from velocitas_lib import get_cache_data, get_package_path
from velocitas_lib.variables import ProjectVariables, json_obj_to_flat_map


@pytest.fixture()
def set_test_env_var():
    os.environ["VELOCITAS_CACHE_DATA"] = '{"cache_key":"cache_value"}'


@pytest.fixture()
def set_velocitas_cache_data() -> str:
    cache_data_mock = {"testPropA": "testValueA", "testPropB": "testValueB"}
    os.environ["VELOCITAS_CACHE_DATA"] = json.dumps(cache_data_mock)
    return os.environ["VELOCITAS_CACHE_DATA"]


def test_replace_occurrences__returns_correct_resolved_string(set_test_env_var):
    input_str_a = "${{ test.string.a }}"
    input_str_b = "/test/${{ test.string.b }}/test"

    variables_to_replace = {
        "test.string.a": "testA",
        "test.string.b": "testB",
    }

    variables = ProjectVariables(variables_to_replace)
    assert (
        variables.replace_occurrences(input_str_a)
        == variables_to_replace["test.string.a"]
    )
    assert (
        variables.replace_occurrences(input_str_b)
        == f'/test/{variables_to_replace["test.string.b"]}/test'
    )


def test_replace_occurrences__variable_not_defined__raises_KeyError(set_test_env_var):
    with pytest.raises(KeyError):
        input_str_a = "${{ test.string.a }}"
        variables_to_replace = {
            "test.string.b": "testB",
        }
        ProjectVariables(variables_to_replace).replace_occurrences(input_str_a)


def test_replace_occurrences__no_replacement_in_input_str__returns_input_str(
    set_test_env_var,
):
    input_str_a = "test.string.a"
    input_str_b = "/test/test.string.b/test"
    input_str_c = "testImage:testVersion"
    input_str_d = "url.com/owner/repo/service:version"
    variables_to_replace = {
        "test.string.a": "testA",
        "test.string.b": "testB",
    }

    variables = ProjectVariables(variables_to_replace)
    assert variables.replace_occurrences(input_str_a) == input_str_a
    assert variables.replace_occurrences(input_str_b) == input_str_b
    assert variables.replace_occurrences(input_str_c) == input_str_c
    assert variables.replace_occurrences(input_str_d) == input_str_d


def test_replace_occurrences__builtins_provided(set_test_env_var):
    variables = ProjectVariables({})

    assert (
        variables.replace_occurrences(
            "This is the package path: '${{ builtin.package_dir }}'"
        )
        == f"This is the package path: {get_package_path().__str__()!r}"
    )


def test_json_obj_to_flat_map__obj_is_dict__returns_replaced_cache_data_with_separator(
    set_velocitas_cache_data,  # type: ignore
):
    separator = "test.separator"
    cache_data_with_keys_to_replace = json_obj_to_flat_map(get_cache_data(), separator)
    assert cache_data_with_keys_to_replace[f"{separator}.testPropA"] == "testValueA"
    assert cache_data_with_keys_to_replace[f"{separator}.testPropB"] == "testValueB"


def test_json_obj_to_flat_map__obj_is_list__returns_replaced_cache_data_with_separator(
    set_velocitas_cache_data,  # type: ignore
):
    separator = "test.separator"
    cache_data_with_keys_to_replace = json_obj_to_flat_map(
        list(get_cache_data()), separator
    )
    assert cache_data_with_keys_to_replace[f"{separator}.0"] == "testPropA"
    assert cache_data_with_keys_to_replace[f"{separator}.1"] == "testPropB"


def test_json_obj_to_flat_map__obj_is_str__returns_replaced_cache_data_with_separator(
    set_velocitas_cache_data,  # type: ignore
):
    separator = "test.separator"
    cache_data_with_keys_to_replace = json_obj_to_flat_map("test", separator)
    assert cache_data_with_keys_to_replace[f"{separator}"] == "test"
