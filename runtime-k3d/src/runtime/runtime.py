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

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "runtime"))
from deployment.gen_helm import gen_helm
from deployment.lib import parse_service_config
from yaspin.core import Yaspin

from velocitas_lib import get_services


def is_runtime_installed() -> bool:
    """Return whether the runtime is installed or not."""
    return (
        subprocess.call(
            ["helm", "status", "vehicleappruntime"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        == 0
    )


def retag_docker_image(image_name: str):
    """Retag the given docker image to be available in K8S."""
    subprocess.check_call(
        ["docker", "pull", image_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.check_call(
        ["docker", "tag", image_name, f"localhost:12345/{image_name}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.check_call(
        ["docker", "push", f"localhost:12345/{image_name}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def retag_docker_images():
    """Retag docker images of all defined services from runtime.json"""
    services = get_services()
    for service in services:
        service_config = parse_service_config(service["config"])
        retag_docker_image(service_config.image)


def create_config_maps():
    """Create config maps for all services."""
    services = get_services()
    for service in services:
        service_config = parse_service_config(service["config"])
        for mount in service_config.mounts:
            local_path = mount.split(":")[0]
            # if folder, don't create configmap
            if "." not in local_path.split(os.sep)[-1]:
                return

            file = os.path.splitext(os.path.basename(local_path))[0]
            subprocess.check_call(
                [
                    "kubectl",
                    "create",
                    "configmap",
                    f"{file}-config",
                    f"--from-file={local_path}",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


def install_runtime(helm_chart_path: str):
    """Install the runtime from the given helm chart.

    Args:
        helm_chart_path (str): Path to the helm chart directory to install.
    """
    subprocess.check_call(
        [
            "helm",
            "install",
            "vehicleappruntime",
            f"{helm_chart_path}",
            "--values",
            f"{helm_chart_path}/values.yaml",
            "--wait",
            "--timeout",
            "60s",
            "--debug",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def uninstall_runtime():
    """Uninstall the runtime."""
    subprocess.check_call(
        ["helm", "uninstall", "vehicleappruntime", "--wait"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def deploy_runtime(spinner: Yaspin):
    """Deploy the runtime and display the progress using the given spinner.

    Args:
        spinner (Yaspin): The progress spinner to update.
    """
    status = "> Deploying runtime... "
    if not is_runtime_installed():
        gen_helm("./helm")
        retag_docker_images()
        create_config_maps()
        install_runtime("./helm")
        status = status + "installed."
    else:
        status = status + "already installed."
    spinner.write(status)


def undeploy_runtime(spinner: Yaspin):
    """Undeploy/remove the runtime and display the progress
    using the given spinner.

    Args:
        spinner (Yaspin): The progress spinner to update.
    """
    status = "> Undeploying runtime... "
    if is_runtime_installed():
        uninstall_runtime()
        status = status + "uninstalled!"
    else:
        status = status + "runtime is not installed."
    spinner.write(status)
