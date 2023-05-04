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
import sys
import json
from velocitas_lib import (
    require_env,
    get_workspace_dir,
    get_app_manifest,
    get_script_path,
    get_cache_data,
    replace_variables,
    json_obj_to_flat_map,
)

cache_data_mock = {"testPropA": "testValueA", "testPropB": "testValueB"}
app_manifest = {"vehicleModel": {"src": "test"}}

os.environ["TEST"] = "test"
os.environ["VELOCITAS_WORKSPACE_DIR"] = "/tmp/vehicle-app-workspace"
os.environ["VELOCITAS_APP_MANIFEST"] = json.dumps(app_manifest)
os.environ["VELOCITAS_CACHE_DATA"] = json.dumps(cache_data_mock)


def test_require_env():
    assert require_env("TEST") == "test"


def test_get_workspace_dir():
    assert get_workspace_dir() == "/tmp/vehicle-app-workspace"


def test_get_app_manifest():
    assert get_app_manifest() == app_manifest
    assert get_app_manifest()["vehicleModel"]["src"] == "test"


def test_get_script_path():
    assert get_script_path() == os.path.dirname(os.path.realpath(sys.argv[0]))


def test_get_cache_data():
    assert get_cache_data() == cache_data_mock
    assert get_cache_data()["testPropA"] == "testValueA"
    assert get_cache_data()["testPropB"] == "testValueB"


def test_replace_variables():
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


def test_json_obj_to_flat_map():
    separator = "test.separator"
    cache_data_with_keys_to_replace = json_obj_to_flat_map(get_cache_data(), separator)
    assert cache_data_with_keys_to_replace[f"{separator}.testPropA"] == "testValueA"
    assert cache_data_with_keys_to_replace[f"{separator}.testPropB"] == "testValueB"
