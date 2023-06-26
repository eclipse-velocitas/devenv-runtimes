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
import subprocess
import sys
from io import TextIOWrapper

from yaspin.core import Yaspin

from velocitas_lib import get_services, parse_service_config

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "runtime"))


def remove_container(log_output: TextIOWrapper | int = subprocess.DEVNULL):
    """Uninstall the runtime.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    subprocess.check_call(
        ["kanto-cm", "remove", "-f", "-n", "databroker"],
        stdout=log_output,
        stderr=log_output,
    )
    subprocess.check_call(
        ["kanto-cm", "remove", "-f", "-n", "mosquitto"],
        stdout=log_output,
        stderr=log_output,
    )
    subprocess.check_call(
        ["kanto-cm", "remove", "-f", "-n", "feedercan"],
        stdout=log_output,
        stderr=log_output,
    )
    subprocess.check_call(
        ["kanto-cm", "remove", "-f", "-n", "seatservice"],
        stdout=log_output,
        stderr=log_output,
    )


def undeploy_runtime(
    spinner: Yaspin, log_output: TextIOWrapper | int = subprocess.DEVNULL
):
    """Undeploy/remove the runtime and display the progress
    using the given spinner.

    Args:
        spinner (Yaspin): The progress spinner to update.
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    status = "> Undeploying runtime... "
    remove_container(log_output)
    status = status + "uninstalled!"
    spinner.write(status)
