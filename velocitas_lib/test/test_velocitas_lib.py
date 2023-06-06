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
import sys
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from velocitas_lib import (
    get_app_manifest,
    get_cache_data,
    get_package_path,
    get_script_path,
    get_services,
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


@pytest.fixture()
def mock_filesystem(fs: FakeFilesystem) -> FakeFilesystem:
    fs.add_real_file(os.path.join(Path(__file__).resolve().parents[2], "manifest.json"))
    return fs


def test_require_env__env_var_set__returns_env_value(set_test_env_var):  # type: ignore
    assert require_env("TEST") == "test"


def test_require_env__env_var_not_set__raises_ValueError():
    with pytest.raises(ValueError):
        require_env("TEST_ENV_NOT_SET")


def test_get_workspace_dir__returns_workspace_dir_path(set_velocitas_workspace_dir):  # type: ignore
    assert get_workspace_dir() == "/test/vehicle-app-workspace"


def test_get_app_manifest__app_manifest_set__returns_app_manifest_data(
    set_app_manifest,
):
    assert get_app_manifest()["vehicleModel"]["src"] == "test"


def test_get_app_manifest__missing_key__raises_KeyError(set_app_manifest):  # type: ignore
    with pytest.raises(KeyError):
        get_app_manifest()["vehicleModel"]["srcs"]


def test_get_app_manifest__no_app_manifest__raises_ValueError():
    os.environ["VELOCITAS_APP_MANIFEST"] = ""
    with pytest.raises(ValueError):
        get_app_manifest()


def test_get_script_path__returns_script_path():
    assert get_script_path() == os.path.dirname(os.path.realpath(sys.argv[0]))


def test_get_package_path__returns_package_path():
    assert get_package_path() == Path(__file__).resolve().parents[2]


def test_get_cache_data__returns_cache_data(set_velocitas_cache_data):  # type: ignore
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


def test_replace_variables__no_replacement_in_input_str__returns_input_str():
    input_str_a = "test.string.a"
    input_str_b = "/test/test.string.b/test"
    input_str_c = "testImage:testVersion"
    input_str_d = "url.com/owner/repo/service:version"
    variables_to_replace = {
        "test.string.a": "testA",
        "test.string.b": "testB",
    }
    assert replace_variables(input_str_a, variables_to_replace) == input_str_a
    assert replace_variables(input_str_b, variables_to_replace) == input_str_b
    assert replace_variables(input_str_c, variables_to_replace) == input_str_c
    assert replace_variables(input_str_d, variables_to_replace) == input_str_d


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


def test_get_services__no_overwrite_provided__returns_default_services(
    mock_filesystem: FakeFilesystem,
):
    os.environ["runtimeFilePath"] = "runtime.json"
    mock_filesystem.create_file(
        f"{get_package_path()}/runtime.json", contents='[ { "id": "service1" } ]'
    )

    all_services = get_services()

    assert len(all_services) == 1
    assert all_services[0]["id"] == "service1"


def test_get_services__overwrite_provided__returns_overwritten_services(
    mock_filesystem: FakeFilesystem,
):
    os.environ["runtimeFilePath"] = "runtime.json"

    mock_filesystem.create_file(
        f"{get_package_path()}/runtime.json", contents='[ { "id": "service1" } ]'
    )
    mock_filesystem.create_file(
        f"{get_workspace_dir()}/runtime.json",
        contents='[ { "id": "my-custom-service" } ]',
    )

    all_services = get_services()

    assert len(all_services) == 1
    assert all_services[0]["id"] == "my-custom-service"
