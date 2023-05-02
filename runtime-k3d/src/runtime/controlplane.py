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
from typing import List

from lib import get_script_path, require_env
from yaspin.core import Yaspin


def registry_exists() -> bool:
    return (
        subprocess.call(
            ["k3d", "registry", "get", "k3d-registry.localhost"],
            stdout=subprocess.DEVNULL,
        )
        == 0
    )


def create_registry():
    subprocess.check_call(
        ["k3d", "registry", "create", "registry.localhost", "--port", "12345"],
        stdout=subprocess.DEVNULL,
    )


def delete_registry():
    subprocess.check_call(
        ["k3d", "registry", "delete", "k3d-registry.localhost"],
        stdout=subprocess.DEVNULL,
    )


def cluster_exists() -> bool:
    return (
        subprocess.call(["k3d", "cluster", "get", "cluster"], stdout=subprocess.DEVNULL)
        == 0
    )


def create_cluster(dapr_config_dir: str):
    has_proxy: bool = os.getenv("HTTP_PROXY") is not None

    extra_proxy_args: List[str] = list()
    if has_proxy:
        print("Creating cluster with proxy configuration")
        http_proxy = os.getenv("HTTP_PROXY")
        https_proxy = os.getenv("HTTPS_PROXY")
        no_proxy = os.getenv("NO_PROXY")
        extra_proxy_args = [
            "-e",
            f"HTTP_PROXY={http_proxy}@server:0",
            "-e",
            f"HTTPS_PROXY={https_proxy}@server:0",
            "-e",
            f"NO_PROXY={no_proxy}@server:0",
        ]
    else:
        print("Creating cluster without proxy configuration")

    subprocess.call(
        [
            "k3d",
            "cluster",
            "create",
            "cluster",
            "-p",
            "30555:30555",
            "-p",
            "31883:31883",
            "-p",
            "30051:30051",
            "--volume",
            f"{dapr_config_dir}/volume:/mnt/data@server:0",
            "--registry-use",
            "k3d-registry.localhost:12345",
        ]
        + extra_proxy_args,
        stdout=subprocess.DEVNULL,
    )


def delete_cluster():
    subprocess.call(["k3d", "cluster", "delete", "cluster"], stdout=subprocess.DEVNULL)


def deployment_exists(deployment_name: str) -> bool:
    return (
        subprocess.call(
            ["kubectl", "get", "deployment", deployment_name], stdout=subprocess.DEVNULL
        )
        == 0
    )


def deploy_zipkin():
    subprocess.check_call(
        ["kubectl", "create", "deployment", "zipkin", "--image", "openzipkin/zipkin"],
        stdout=subprocess.DEVNULL,
    )

    subprocess.check_call(
        [
            "kubectl",
            "expose",
            "deployment",
            "zipkin",
            "--type",
            "ClusterIP",
            "--port",
            "9411",
        ],
        stdout=subprocess.DEVNULL,
    )


def dapr_is_initialized_with_k3d() -> bool:
    return subprocess.call(["dapr", "status", "-k"], stdout=subprocess.DEVNULL) == 0


def initialize_dapr_with_k3d(dapr_runtime_version: str, dapr_config_dir: str):
    subprocess.check_call(
        [
            "dapr",
            "init",
            "-k",
            "--wait",
            "--timeout",
            "600",
            "--runtime-version",
            dapr_runtime_version,
        ],
        stdout=subprocess.DEVNULL,
    )

    subprocess.check_call(
        ["kubectl", "apply", "-f", f"{dapr_config_dir}/config.yaml"],
        stdout=subprocess.DEVNULL,
    )

    subprocess.check_call(
        ["kubectl", "apply", "-f", f"{dapr_config_dir}/components/pubsub.yaml"],
        stdout=subprocess.DEVNULL,
    )


def configure_controlplane(spinner: Yaspin):
    dapr_config_dir = os.path.join(get_script_path(), "runtime", "config", ".dapr")

    status = "> Checking K3D registry... "
    if not registry_exists():
        create_registry()
        status = status + "created."
    else:
        status = status + "registry already exists."
    spinner.write(status)

    status = "> Checking K3D cluster... "
    if not cluster_exists():
        status = status + "created."
    else:
        status = status + "registry already exists."
    spinner.write(status)

    status = "> Checking zipkin deployment... "
    if not deployment_exists("zipkin"):
        deploy_zipkin()
        status = status + "deployed."
    else:
        status = status + "already deployed."
    spinner.write(status)

    status = "> Checking dapr... "
    if not dapr_is_initialized_with_k3d():
        dapr_runtime_version = require_env("daprRuntimeVersion")
        initialize_dapr_with_k3d(dapr_runtime_version, dapr_config_dir)
        status = status + "initialized."
    else:
        status = status + "already initialized."
    spinner.write(status)


def reset_controlplane():
    if cluster_exists():
        print("Uninstalling runtime...")
        delete_cluster()
    else:
        print("Control plane is not configured, skipping cluster deletion.")

    if registry_exists():
        print("Uninstalling runtime...")
        delete_registry()
    else:
        print("Registry does not exist, skipping deletion.")
