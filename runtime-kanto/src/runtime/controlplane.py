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
from io import TextIOWrapper
from typing import List

from yaspin.core import Yaspin

from velocitas_lib import get_package_path, require_env


def registry_exists(log_output: TextIOWrapper | int = subprocess.DEVNULL) -> bool:
    """Check if the Kanto registry exists.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.

    Returns:
        bool: True if the registry exists, False if not.
    """
    return


def create_registry(log_output: TextIOWrapper | int = subprocess.DEVNULL):
    """Create the Kanto registry.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """


def delete_registry(log_output: TextIOWrapper | int = subprocess.DEVNULL):
    """Delete the Kanto registry.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """


def append_proxy_var_if_set(proxy_args: List[str], var_name: str):  # noqa: U100
    """Append the specified environment variable setting to the passed list,
    if the variable exists in the calling environment

    Args:
        proxy_args (List[str]): List to append to
        var_name (str): Enironment variable to append if existing
    """
    var_content = os.getenv(var_name)
    if var_content:
        proxy_args += ["-e", f"{var_name}={var_content}@server:0"]



def configure_controlplane(
    spinner: Yaspin, log_output: TextIOWrapper | int = subprocess.DEVNULL
):
    """Configure the K3D control plane and display the progress
    using the given spinner.

    Args:
        spinner (Yaspin): The progress spinner to update.
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """

    status = "> Checking Kanto registry... "
    if not registry_exists(log_output):
        create_registry(log_output)
        status = status + "created."
    else:
        status = status + "registry already exists."
    spinner.write(status)


def reset_controlplane(
    spinner: Yaspin, log_output: TextIOWrapper | int = subprocess.DEVNULL
):
    """Reset the K3D control plane and display the progress
    using the given spinner.

    Args:
        spinner (Yaspin): The progress spinner to update.
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """

    status = "> Checking Kanto registry... "
    if registry_exists(log_output):
        delete_registry(log_output)
        status = status + "uninstalled."
    else:
        status = status + "does not exist."
    spinner.write(status)
