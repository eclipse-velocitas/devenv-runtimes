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
import pytest
import sys

from velocitas_lib import (
    get_app_manifest,
    get_cache_data,
    get_script_path,
    get_workspace_dir,
    json_obj_to_flat_map,
    replace_variables,
    require_env,
)


@pytest.fixture()
def set_test_env_var() -> str:
    os.environ["TEST"] = "test"
    return os.environ["TEST"]


@pytest.fixture()
def set_velocitas_workspace_dir() -> str:
    os.environ["VELOCITAS_WORKSPACE_DIR"] = "/test/vehicle-app-workspace"
    return os.environ["VELOCITAS_WORKSPACE_DIR"]


@pytest.fixture()
def set_app_manifest() -> str:
    app_manifest = {"vehicleModel": {"src": "test"}}
    os.environ["VELOCITAS_APP_MANIFEST"] = json.dumps(app_manifest)
    return os.environ["VELOCITAS_APP_MANIFEST"]


@pytest.fixture()
def set_velocitas_cache_data() -> str:
    cache_data_mock = {"testPropA": "testValueA", "testPropB": "testValueB"}
    os.environ["VELOCITAS_CACHE_DATA"] = json.dumps(cache_data_mock)
    return os.environ["VELOCITAS_CACHE_DATA"]


def test_require_env__env_var_set__returns_env_value(set_test_env_var):
    assert require_env("TEST") == "test"


def test_require_env__env_var_not_set__raises_ValueError():
    with pytest.raises(ValueError):
        require_env("TEST_ENV_NOT_SET") == "test"


def test_get_workspace_dir__returns_workspace_dir_path(set_velocitas_workspace_dir):
    assert get_workspace_dir() == "/test/vehicle-app-workspace"


def test_get_app_manifest__app_manifest_set__returns_app_manifest_data(
    set_app_manifest,
):
    assert get_app_manifest()["vehicleModel"]["src"] == "test"


def test_get_app_manifest__missing_key__raises_KeyError(set_app_manifest):
    with pytest.raises(KeyError):
        get_app_manifest()["vehicleModel"]["srcs"] == "test"


def test_get_app_manifest__no_app_manifest__raises_ValueError():
    os.environ["VELOCITAS_APP_MANIFEST"] = ""
    with pytest.raises(ValueError):
        get_app_manifest()


def test_get_script_path__returns_script_path():
    assert get_script_path() == os.path.dirname(os.path.realpath(sys.argv[0]))


def test_get_cache_data__returns_cache_data(set_velocitas_cache_data):
    assert get_cache_data()["testPropA"] == "testValueA"
    assert get_cache_data()["testPropB"] == "testValueB"


def test_replace_variables__returns_correct_resolved_string():
    input_str_a = "${{ test.string.a }}"
    input_str_b = "/test/${{ test.string.b }}/test"
    variables_to_replace = {
        "test.string.a": "testA",
        "test.string.b": "testB",
    }
    assert (
        replace_variables(input_str_a, variables_to_replace)
        == variables_to_replace["test.string.a"]
    )
    assert (
        replace_variables(input_str_b, variables_to_replace)
        == f'/test/{variables_to_replace["test.string.b"]}/test'
    )


def test_replace_variables__variable_not_defined__raises_KeyError():
    with pytest.raises(KeyError):
        input_str_a = "${{ test.string.a }}"
        variables_to_replace = {
            "test.string.b": "testB",
        }
        replace_variables(input_str_a, variables_to_replace)


def test_json_obj_to_flat_map__returns_replaced_cache_data_with_separator(
    set_velocitas_cache_data,
):
    separator = "test.separator"
    cache_data_with_keys_to_replace = json_obj_to_flat_map(get_cache_data(), separator)
    assert cache_data_with_keys_to_replace[f"{separator}.testPropA"] == "testValueA"
    assert cache_data_with_keys_to_replace[f"{separator}.testPropB"] == "testValueB"
