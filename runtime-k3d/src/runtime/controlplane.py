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

from yaspin.core import Yaspin

from velocitas_lib import get_package_path, get_script_path, require_env


def registry_exists() -> bool:
    """Check if the K3D registry exists.

    Returns:
        bool: True if the registry exists, False if not.
    """
    return (
        subprocess.call(
            ["k3d", "registry", "get", "k3d-registry.localhost"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        == 0
    )


def create_registry():
    """Create the K3D registry."""
    subprocess.check_call(
        ["k3d", "registry", "create", "registry.localhost", "--port", "12345"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def delete_registry():
    """Delete the K3D registry."""
    subprocess.check_call(
        ["k3d", "registry", "delete", "k3d-registry.localhost"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def cluster_exists() -> bool:
    """Check if the K3D cluster exists.

    Returns:
        bool: True if the cluster exists, False if not.
    """
    return (
        subprocess.call(
            ["k3d", "cluster", "get", "cluster"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        == 0
    )


def create_cluster(config_dir_path: str):
    """Create the cluster with the given config dir.

    Args:
        config_dir_path (str): The path to the config directory.
    """
    has_proxy: bool = os.getenv("HTTP_PROXY") is not None

    extra_proxy_args: List[str] = list()
    if has_proxy:
        print("Creating cluster with proxy configuration.")
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
        print("Creating cluster without proxy configuration.")

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
            f"{config_dir_path}/feedercan:/mnt/data@server:0",
            "--registry-use",
            "k3d-registry.localhost:12345",
        ]
        + extra_proxy_args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def delete_cluster():
    """Delete the K3D cluster."""
    subprocess.call(
        ["k3d", "cluster", "delete", "cluster"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def deployment_exists(deployment_name: str) -> bool:
    """Check if the deployment of a given name exists.

    Args:
        deployment_name (str): The name of the deployment.

    Returns:
        bool: True if the deployment exists, False if not.
    """
    return (
        subprocess.call(
            ["kubectl", "get", "deployment", deployment_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        == 0
    )


def deploy_zipkin():
    """Deploy zipkin to the cluster."""
    subprocess.check_call(
        ["kubectl", "create", "deployment", "zipkin", "--image", "openzipkin/zipkin"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
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
        stderr=subprocess.DEVNULL,
    )


def dapr_is_initialized_with_k3d() -> bool:
    """Check if dapr is initialized with k3d."""
    return (
        subprocess.call(
            ["dapr", "status", "-k"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        == 0
    )


def initialize_dapr_with_k3d(dapr_runtime_version: str, dapr_config_dir_path: str):
    """Initialize dapr with K3D.

    Args:
        dapr_runtime_version (str): The runtime version of dapr.
        dapr_config_dir_path (str): The path to the dapr config directory.
    """
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
        stderr=subprocess.DEVNULL,
    )

    subprocess.check_call(
        ["kubectl", "apply", "-f", f"{dapr_config_dir_path}/config.yaml"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def configure_controlplane(spinner: Yaspin):
    """Configure the K3D control plane and display the progress
    using the given spinner.

    Args:
        spinner (Yaspin): The progress spinner to update.
    """
    config_dir = os.path.join(get_package_path(), "config")
    dapr_config_dir = os.path.join(
        get_package_path(),
        "runtime-k3d",
        "src",
        "runtime",
        "deployment",
        "config",
        ".dapr",
    )

    status = "> Checking K3D registry... "
    if not registry_exists():
        create_registry()
        status = status + "created."
    else:
        status = status + "registry already exists."
    spinner.write(status)

    status = "> Checking K3D cluster... "
    if not cluster_exists():
        create_cluster(config_dir)
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


def reset_controlplane(spinner: Yaspin):
    """Reset the K3D control plane and display the progress
    using the given spinner.

    Args:
        spinner (Yaspin): The progress spinner to update.
    """
    status = "> Checking K3D cluster... "
    if cluster_exists():
        delete_cluster()
        status = status + "deleted."
    else:
        status = status + "does not exist."
    spinner.write(status)

    status = "> Checking K3D registry... "
    if registry_exists():
        delete_registry()
        status = status + "uninstalled."
    else:
        status = status + "does not exist."
    spinner.write(status)
