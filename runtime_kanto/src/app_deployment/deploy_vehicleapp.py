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

from velocitas_lib import create_log_file, get_app_manifest
from velocitas_lib.docker import (
    is_docker_image_build_locally,
    push_docker_image_to_registry,
)
from velocitas_lib.services import get_service_port
from yaspin import yaspin

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app_deployment"))
from build_vehicleapp import build_vehicleapp  # noqa: E402


def is_vehicleapp_installed(
    app_name: str,
    log_output: TextIOWrapper | int = subprocess.DEVNULL,
) -> bool:
    """Return whether the runtime is installed or not.

    Args:
        app_name (str): App name
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    return (
        subprocess.call(
            ["kanto-cm", "get", "-n", app_name],
            stdout=log_output,
            stderr=log_output,
        )
        == 0
    )


def remove_vehicleapp(
    app_name: str, log_output: TextIOWrapper | int = subprocess.DEVNULL
):
    """Uninstall VehicleApp container

    Args:
        app_name (str): App name to remove container for
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    subprocess.call(
        ["kanto-cm", "remove", "-f", "-n", app_name],
        stdout=log_output,
        stderr=log_output,
    )


def create_container(
    app_name: str, log_output: TextIOWrapper | int = subprocess.DEVNULL
):
    """Create kanto container

    Args:
        app_name (str): App name for container creation
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    middleware_type = "native"
    app_registry = "localhost:12345"
    vdb_port = get_service_port("vehicledatabroker")
    vdb_address = "grpc://127.0.0.1"
    mqtt_port = get_service_port("mqtt-broker")
    mqtt_address = "mqtt://127.0.0.1"

    subprocess.check_call(
        [
            "kanto-cm",
            "create",
            "--i",
            "--t",
            "--network",
            "host",
            "--e",
            f"SDV_MIDDLEWARE_TYPE={middleware_type}",
            "--e",
            f"SDV_VEHICLEDATABROKER_ADDRESS={vdb_address}:{vdb_port}",
            "--e",
            f"SDV_MQTT_ADDRESS={mqtt_address}:{mqtt_port}",
            "-n",
            app_name,
            f"{app_registry}/{app_name}:local",
        ],
        stdout=log_output,
        stderr=log_output,
    )


def start_container(
    app_name: str, log_output: TextIOWrapper | int = subprocess.DEVNULL
):
    """Start VehicleApp container

    Args:
        app_name (str): App name for container start
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """

    subprocess.check_call(
        [
            "kanto-cm",
            "start",
            "-n",
            app_name,
        ],
        stdout=log_output,
        stderr=log_output,
    )


def deploy_vehicleapp():
    """Deploy VehicleApp docker image via kanto-cm
    and display the progress using a given spinner."""

    print("Hint: Log files can be found in your workspace's logs directory")
    log_output = create_log_file("deploy-vapp", "runtime_kanto")
    with yaspin(text="Deploying VehicleApp...", color="cyan") as spinner:
        try:
            app_name = get_app_manifest()["name"].lower()

            if not is_docker_image_build_locally(app_name):
                spinner.write("Cannot find vehicle app image...")
                spinner.stop()
                build_vehicleapp()

            spinner.start()
            push_docker_image_to_registry(app_name, log_output)
            status = f"> Pushing {app_name} docker image to registry done!"
            spinner.write(status)

            status = "> Removing old vehicleapp..."
            if is_vehicleapp_installed(app_name, log_output):
                remove_vehicleapp(app_name, log_output)
                spinner.write(f"{status} done!")
            else:
                spinner.write(f"{status} vehicleapp not yet installed.")

            create_container(app_name, log_output)
            start_container(app_name, log_output)
            spinner.write(f"> Deploying vehicleapp container for {app_name}... done!")
            spinner.ok("✅")
        except Exception as err:
            log_output.write(str(err))
            spinner.fail("💥")


if __name__ == "__main__":
    deploy_vehicleapp()
