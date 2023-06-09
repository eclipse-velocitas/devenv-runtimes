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
from io import TextIOWrapper

from yaspin.core import Yaspin


def registry_exists(log_output: TextIOWrapper | int = subprocess.DEVNULL) -> bool:
    """Check if the Kanto registry exists.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.

    Returns:
        bool: True if the registry exists, False if not.
    """
    return "" != str(
        subprocess.check_output(
            ["docker", "ps", "-a", "-q", "-f", "name=registry"], stderr=log_output
        ),
        "utf-8",
    )


def registry_running(log_output: TextIOWrapper | int = subprocess.DEVNULL) -> bool:
    """Check if the Kanto registry is running.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.

    Returns:
        bool: True if the registry exists, False if not.
    """
    return "true" in str(
        subprocess.check_output(
            [
                "docker",
                "container",
                "inspect",
                "-f",
                "'{{.State.Running}}'",
                "registry",
            ],
            stderr=log_output,
        ),
        "utf-8",
    )


def create_and_start_registry(log_output: TextIOWrapper | int = subprocess.DEVNULL):
    """Create and start the Kanto registry.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    subprocess.check_call(
        ["docker", "run", "-d", "-p", "12345:5000", "--name", "registry", "registry:2"],
        stdout=log_output,
        stderr=log_output,
    )


def start_registry(log_output: TextIOWrapper | int = subprocess.DEVNULL):
    """Start the Kanto registry.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    subprocess.check_call(
        ["docker", "start", "registry"],
        stdout=log_output,
        stderr=log_output,
    )


def stop_registry(log_output: TextIOWrapper | int = subprocess.DEVNULL):
    """Stop the Kanto registry.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    subprocess.check_call(
        ["docker", "stop", "registry"],
        stdout=log_output,
        stderr=log_output,
    )


def configure_controlplane(
    spinner: Yaspin, log_output: TextIOWrapper | int = subprocess.DEVNULL
):
    """Configure the Kanto control plane and display the progress
    using the given spinner.

    Args:
        spinner (Yaspin): The progress spinner to update.
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """

    status = "> Checking Kanto registry... "
    if not registry_exists(log_output):
        spinner.write(status + "starting registry.")
        create_and_start_registry(log_output)
        spinner.write(status + "started.")
    else:
        spinner.write(status + "registry already exists.")
        if registry_running(log_output):
            spinner.write(status + "registry already started.")
        else:
            spinner.write(status + "starting registry.")
            start_registry(log_output)
            spinner.write(status + "started.")


def reset_controlplane(
    spinner: Yaspin, log_output: TextIOWrapper | int = subprocess.DEVNULL
):
    """Reset the K3D control plane and display the progress
    using the given spinner.

    Args:
        spinner (Yaspin): The progress spinner to update.
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """

    status = "> Stopping Kanto registry... "
    if registry_exists(log_output):
        stop_registry(log_output)
        status = status + "stopped."
    else:
        status = status + "does not exist."
    spinner.write(status)
