# Copyright (c) 2023-2024 Contributors to the Eclipse Foundation
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

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from run_service import main  # noqa: E402


@pytest.fixture()
def set_env_vars():
    os.environ["runtimeFilePath"] = "./runtime.json"
    os.environ["VELOCITAS_PACKAGE_DIR"] = "."
    os.environ["VELOCITAS_WORKSPACE_DIR"] = "."
    os.environ["VELOCITAS_CACHE_DATA"] = '{"vspec_file_path":""}'
    os.environ["mockFilePath"] = "mock.py"


def test_run_service__invalid_service_id__prints_available_services(
    capsys, set_env_vars
):
    main("foo_bar_baz")

    captured = capsys.readouterr()
    assert (
        captured.out
        == """runtime.json path redirected to runtime.json
Error: Service with id 'foo_bar_baz' not defined
Available services:
 * 'mqtt-broker'
 * 'vehicledatabroker'
 * 'mockservice'
"""
    )
