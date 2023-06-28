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

from build_vehicleapp import build_vehicleapp
from yaspin import yaspin

from velocitas_lib import (
    create_log_file,
    get_app_manifest,
    get_script_path,
    require_env,
    is_docker_image_build_locally,
    push_docker_image_to_registry
)


def is_vehicleapp_installed(
    log_output: TextIOWrapper | int = subprocess.DEVNULL,
) -> bool:
    """Return whether the runtime is installed or not.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    return (
        subprocess.call(
            ["helm", "status", "vapp-chart"],
            stdout=log_output,
            stderr=log_output,
        )
        == 0
    )


def uninstall_vehicleapp(log_output: TextIOWrapper | int = subprocess.DEVNULL):
    """Uninstall VehicleApp helm chart

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    subprocess.check_call(
        ["helm", "uninstall", "vapp-chart", "--wait"],
        stdout=log_output,
        stderr=log_output,
    )


def install_vehicleapp(
    app_name: str, log_output: TextIOWrapper | int = subprocess.DEVNULL
):
    """Install VehicleApp helm chart

    Args:
        app_name (str): App name to install
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    app_port = require_env("vehicleAppPort")
    app_registry = "k3d-registry.localhost:12345"
    script_path = get_script_path()
    helm_config_path = script_path + "/config/helm"

    subprocess.check_call(
        [
            "helm",
            "install",
            "vapp-chart",
            helm_config_path,
            "--values",
            f"{helm_config_path}/values.yaml",
            "--set",
            f"imageVehicleApp.repository={app_registry}/{app_name}",
            "--set",
            f"imageVehicleApp.name={app_name}",
            "--set",
            f"imageVehicleApp.daprAppid={app_name}",
            "--set",
            f"imageVehicleApp.daprPort={app_port}",
            "--wait",
            "--timeout",
            "60s",
            "--debug",
        ],
        stdout=log_output,
        stderr=log_output,
    )


def deploy_vehicleapp():
    """Deploy VehicleApp docker image via helm to k3d cluster
    and display the progress using a given spinner."""

    print("Hint: Log files can be found in your workspace's logs directory")
    log_output = create_log_file("deploy-vapp", "runtime-k3d")
    with yaspin(text="Deploying VehicleApp...", color="cyan") as spinner:
        try:
            app_name = get_app_manifest()["name"].lower()

            if not is_docker_image_build_locally(app_name):
                spinner.write("Cannot find vehicle app image...")
                spinner.stop()
                build_vehicleapp()

            spinner.start()
            push_docker_image_to_registry(app_name, log_output)
            status = f"> Pushing {app_name} docker image to k3d registry done!"
            spinner.write(status)

            status = "> Uninstalling vapp-chart..."
            if is_vehicleapp_installed(log_output):
                uninstall_vehicleapp(log_output)
                spinner.write(f"{status} done!")
            else:
                spinner.write(f"{status} vapp-chart not yet installed.")

            install_vehicleapp(app_name, log_output)
            spinner.write(f"> Installing vapp-chart for {app_name}... done!")
            spinner.ok("✅")
        except Exception as err:
            log_output.write(str(err))
            spinner.fail("💥")


if __name__ == "__main__":
    deploy_vehicleapp()
