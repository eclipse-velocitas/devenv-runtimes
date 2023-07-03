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

import subprocess
import json

BASE_COMMAND_RUNTIME = "velocitas exec runtime-kanto"
BASE_COMMAND_DEPLOYMENT = "velocitas exec deployment-kanto"


def check_container_is_running(container_name: str) -> bool:
    """Return whether the container is running or not.

    Args:
        app_name (str): App name
    """
    return json.loads((
        subprocess.run(
            ["kanto-cm", "get", "-n", container_name], stdout=subprocess.PIPE
        )
    ).stdout.decode('utf-8'))['state']['running']


def run_command(command: str) -> bool:
    return subprocess.check_call(command.split(" ")) == 0


def test_scripts_run_successfully():
    assert run_command(f"{BASE_COMMAND_RUNTIME} install-deps")
    assert run_command(f"{BASE_COMMAND_RUNTIME} up")
    assert run_command(f"{BASE_COMMAND_DEPLOYMENT} build-vehicleapp")
    assert run_command(f"{BASE_COMMAND_DEPLOYMENT} deploy-vehicleapp")
    assert check_container_is_running('mosquitto')
    assert check_container_is_running('seatservice')
    assert check_container_is_running('databroker')
    assert check_container_is_running('feedercan')
    assert check_container_is_running('sampleapp')
    assert run_command(f"{BASE_COMMAND_RUNTIME} down")
