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

from velocitas_lib.services import get_services
from yaspin.core import Yaspin

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "runtime"))
from deployment.gen_helm import gen_helm  # noqa: E402


def is_runtime_installed(log_output: TextIOWrapper | int = subprocess.DEVNULL) -> bool:
    """Return whether the runtime is installed or not.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    process = subprocess.run(
        ["helm", "status", "vehicleappruntime"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    for line in process.stdout.splitlines():
        key_value = line.split(":", 1)
        key = key_value[0].strip()
        value = key_value[1].strip()
        if key == "STATUS" and value == "deployed":
            return True

    log_output.write(process.stdout)

    return False


def retag_docker_image(
    image_name: str, log_output: TextIOWrapper | int = subprocess.DEVNULL
):
    """Retag the given docker image to be available in K8S.

    Args:
        image_name (str): Image name to retag.
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    subprocess.check_call(
        ["docker", "pull", image_name],
        stdout=log_output,
        stderr=log_output,
    )
    subprocess.check_call(
        ["docker", "tag", image_name, f"localhost:12345/{image_name}"],
        stdout=log_output,
        stderr=log_output,
    )
    subprocess.check_call(
        ["docker", "push", f"localhost:12345/{image_name}"],
        stdout=log_output,
        stderr=log_output,
    )


def retag_docker_images(log_output: TextIOWrapper | int = subprocess.DEVNULL):
    """Retag docker images of all defined services from runtime.json

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    services = get_services()
    for service in services:
        retag_docker_image(service.config.image, log_output)


def create_config_maps(log_output: TextIOWrapper | int = subprocess.DEVNULL):
    """Create config maps for all services.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    services = get_services()
    for service in services:
        for mount in service.config.mounts:
            local_path = mount.split(":")[0]
            # if folder, don't create configmap
            if "." not in local_path.split(os.sep)[-1]:
                return

            file = os.path.splitext(os.path.basename(local_path))[0]
            if (
                not subprocess.call(
                    ["kubectl", "describe", "configmaps", f"{file}-config"],
                    stdout=log_output,
                    stderr=log_output,
                )
                == 0
            ):
                subprocess.check_call(
                    [
                        "kubectl",
                        "create",
                        "configmap",
                        f"{file}-config",
                        f"--from-file={local_path}",
                    ],
                    stdout=log_output,
                    stderr=log_output,
                )


def install_runtime(
    helm_chart_path: str, log_output: TextIOWrapper | int = subprocess.DEVNULL
):
    """Install the runtime from the given helm chart.

    Args:
        helm_chart_path (str): Path to the helm chart directory to install.
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    subprocess.check_call(
        [
            "helm",
            "install",
            "--replace",
            "vehicleappruntime",
            f"{helm_chart_path}",
            "--values",
            f"{helm_chart_path}/values.yaml",
            "--wait",
            "--timeout",
            "60s",
            "--debug",
        ],
        stdout=log_output,
        stderr=log_output,
    )


def uninstall_runtime(log_output: TextIOWrapper | int = subprocess.DEVNULL):
    """Uninstall the runtime.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    subprocess.check_call(
        ["helm", "uninstall", "vehicleappruntime", "--wait"],
        stdout=log_output,
        stderr=log_output,
    )


def deploy_runtime(
    spinner: Yaspin, log_output: TextIOWrapper | int = subprocess.DEVNULL
):
    """Deploy the runtime and display the progress using the given spinner.

    Args:
        spinner (Yaspin): The progress spinner to update.
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    status = "> Deploying runtime... "
    if not is_runtime_installed(log_output):
        gen_helm("./helm")
        retag_docker_images(log_output)
        create_config_maps(log_output)
        install_runtime("./helm", log_output)
        status = status + "installed."
    else:
        status = status + "already installed."
    spinner.write(status)


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
    if is_runtime_installed(log_output):
        uninstall_runtime(log_output)
        status = status + "uninstalled!"
    else:
        status = status + "runtime is not installed."
    spinner.write(status)
