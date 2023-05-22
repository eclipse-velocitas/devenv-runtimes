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

from build_vehicleapp import build_vehicleapp
from runtime.deployment.lib import create_log_file
from yaspin import yaspin

from velocitas_lib import get_app_manifest, get_script_path, require_env


def is_docker_image_build_locally(app_name: str) -> bool:
    """Check if vehicle app docker image is locally available"""
    output = subprocess.check_output(
        [
            "docker",
            "images",
            "-a",
            f"localhost:12345/{app_name}:local",
            "--format",
            "{{.Repository}}:{{.Tag}}",
        ],
    )
    return output.decode("utf-8").strip() == f"localhost:12345/{app_name}:local"


def push_docker_image_to_registry(app_name: str, log_file=subprocess.DEVNULL):
    """Push docker image to local k3d image registry"""
    subprocess.check_call(
        ["docker", "push", f"localhost:12345/{app_name}:local"],
        stdout=log_file,
        stderr=log_file,
    )


def is_vehicleapp_installed(log_file=subprocess.DEVNULL) -> bool:
    """Return whether the runtime is installed or not."""
    return (
        subprocess.call(
            ["helm", "status", "vapp-chart"],
            stdout=log_file,
            stderr=log_file,
        )
        == 0
    )


def uninstall_vehicleapp(log_file=subprocess.DEVNULL):
    """Uninstall VehicleApp helm chart"""
    subprocess.check_call(
        ["helm", "uninstall", "vapp-chart", "--wait"],
        stdout=log_file,
        stderr=log_file,
    )


def install_vehicleapp(app_name: str, log_file=subprocess.DEVNULL):
    """Install VehicleApp helm chart"""
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
        stdout=log_file,
        stderr=log_file,
    )


def deploy_vehicleapp(log_file):
    """Deploy VehicleApp docker image via helm to k3d cluster
    and display the progress using a given spinner."""

    log_file = create_log_file("deploy-vapp")
    with yaspin(text="Deploying VehicleApp...") as spinner:
        try:
            app_name = get_app_manifest()["name"].lower()

            if not is_docker_image_build_locally(app_name):
                spinner.write("Cannot find vehicle app image...")
                spinner.stop()
                build_vehicleapp(log_file)

            spinner.start()
            push_docker_image_to_registry(app_name, log_file)
            status = f"> Pushing {app_name} docker image to k3d registry done!"
            spinner.write(status)

            status = "> Uninstalling vapp-chart..."
            if is_vehicleapp_installed(log_file):
                uninstall_vehicleapp(log_file)
                spinner.write(f"{status} done!")
            else:
                spinner.write(f"{status} vapp-chart not yet installed.")

            install_vehicleapp(app_name, log_file)
            spinner.write(f"> Installing vapp-chart for {app_name}... done!")
            spinner.ok("✔")
        except Exception as err:
            spinner.fail(err)


if __name__ == "__main__":
    deploy_vehicleapp()
