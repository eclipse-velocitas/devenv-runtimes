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

# flake8: noqa: E402 module level import
import subprocess
import sys
from pathlib import Path

from gen_helm import gen_helm
from lib import parse_service_config
from yaspin.core import Yaspin

sys.path.append(os.path.join(Path(__file__).parents[2], "velocitas_lib"))
from velocitas_lib import get_cache_data, get_services


def is_runtime_installed() -> bool:
    return (
        subprocess.call(
            ["helm", "status", "vehicleappruntime"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        == 0
    )


def retag_docker_image(image_name: str):
    subprocess.check_call(["docker", "pull", image_name], stdout=subprocess.DEVNULL)
    subprocess.check_call(
        ["docker", "tag", image_name, f"localhost:12345/{image_name}"],
        stdout=subprocess.DEVNULL,
    )
    subprocess.check_call(
        ["docker", "push", f"localhost:12345/{image_name}"], stdout=subprocess.DEVNULL
    )


def retag_docker_images():
    services = get_services()
    for service in services:
        service_config = parse_service_config(service["config"])
        retag_docker_image(service_config.image)


def create_vspec_config():
    get_cache_data()["vspec_file_path"]
    subprocess.check_call(
        [
            "kubectl",
            "create",
            "configmap",
            "vspec-config",
            "--from-file=$VSPEC_FILE_PATH",
        ]
    )


def install_runtime(helm_output_path: str):
    subprocess.check_call(
        [
            "helm",
            "install",
            "vehicleappruntime",
            f"{helm_output_path}",
            "--values",
            f"{helm_output_path}/values.yaml",
            "--set",
            "vspecFilePath=$VSPEC_FILE_PATH" "--wait",
            "--timeout",
            "60s",
            "--debug",
        ],
        stdout=subprocess.DEVNULL,
    )


def uninstall_runtime():
    subprocess.check_call(
        ["helm", "uninstall", "vehicleappruntime", "--wait"], stdout=subprocess.DEVNULL
    )


def deploy_runtime(spinner: Yaspin):
    status = "> Deploying runtime... "
    if not is_runtime_installed():
        gen_helm("./helm")
        retag_docker_images()
        install_runtime("./helm")
        status = status + "installed."
    else:
        status = status + "already installed."
    spinner.write(status)


def undeploy_runtime(spinner: Yaspin):
    status = "> Undeploying runtime... "
    if is_runtime_installed():
        uninstall_runtime()
        status = status + "uninstalled!"
    else:
        status = status + "runtime is not installed."
    spinner.write(status)
