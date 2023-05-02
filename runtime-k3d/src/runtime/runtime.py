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

from lib import get_services, parse_service_config
from gen_helm import gen_helm


def is_runtime_installed() -> bool:
    return subprocess.call(["helm", "status", "vehicleappruntime"]) == 0


def retag_docker_image(image_name: str):
    subprocess.check_call(["docker", "pull", image_name])
    subprocess.check_call([
        "docker",
        "tag",
        image_name,
        f"localhost:12345/{image_name}"
        ])
    subprocess.check_call(["docker", "push", f"localhost:12345/{image_name}"])


def retag_docker_images():
    services = get_services()
    for service in services:
        service_config = parse_service_config(service["config"])
        retag_docker_image(service_config.image)


def install_runtime(helm_output_path: str):
    print(f"reading helm from {helm_output_path!r}")
    subprocess.check_call([
        "helm",
        "install",
        "vehicleappruntime",
        f"{helm_output_path}",
        "--values",
        f"{helm_output_path}/values.yaml",
        "--set",
        "vspecFilePath=$VSPEC_FILE_PATH"
        "--wait",
        "--timeout",
        "60s",
        "--debug"
    ])


def uninstall_runtime():
    subprocess.check_call([
        "helm",
        "uninstall",
        "vehicleappruntime",
        "--wait"
    ])


def deploy_runtime():
    if not is_runtime_installed():
        gen_helm("./helm")
        retag_docker_images()
        install_runtime("./helm")
    else:
        print("Runtime already installed!")


def undeploy_runtime():
    if is_runtime_installed():
        print("Uninstalling runtime...")
        uninstall_runtime()
    else:
        print("Runtime is not installed.")
