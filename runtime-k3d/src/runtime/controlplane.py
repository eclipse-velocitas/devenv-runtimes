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
import os
from typing import List
from lib import require_env, get_script_path


def registry_exists() -> bool:
    return subprocess.call([
        "k3d",
        "registry",
        "get",
        "k3d-registry.localhost"
    ]) == 0


def create_registry():
    subprocess.check_call([
          "k3d",
          "registry",
          "create",
          "registry.localhost",
          "--port",
          "12345"
    ])


def delete_registry():
    subprocess.check_call([
        "k3d",
        "registry",
        "delete",
        "k3d-registry.localhost"
    ])


def cluster_exists() -> bool:
    return subprocess.call([
        "k3d",
        "cluster",
        "get",
        "cluster"
    ]) == 0


def create_cluster(dapr_config_dir: str):
    has_proxy: bool = os.getenv("HTTP_PROXY") is not None

    extra_proxy_args: List[str] = list()
    if has_proxy:
        print("Creating cluster with proxy configuration")
        http_proxy = os.getenv("HTTP_PROXY")
        https_proxy = os.getenv("HTTPS_PROXY")
        no_proxy = os.getenv("NO_PROXY")
        extra_proxy_args = [
                            "-e", f"HTTP_PROXY={http_proxy}@server:0",
                            "-e", f"HTTPS_PROXY={https_proxy}@server:0",
                            "-e", f"NO_PROXY={no_proxy}@server:0"
        ]
    else:
        print("Creating cluster without proxy configuration")

    subprocess.call([
       "k3d",
       "cluster",
       "create",
       "cluster",
       "-p", "30555:30555",
       "-p", "31883:31883",
       "-p", "30051:30051",
       "--volume", f"{dapr_config_dir}/volume:/mnt/data@server:0",
       "--registry-use", "k3d-registry.localhost:12345"
    ] + extra_proxy_args)


def delete_cluster():
    subprocess.call([
        "k3d",
        "cluster",
        "delete",
        "cluster"
    ])


def deployment_exists(deployment_name: str) -> bool:
    return subprocess.call([
        "kubectl",
        "get",
        "deployment",
        deployment_name
    ]) == 0


def deploy_zipkin():
    subprocess.check_call([
        "kubectl",
        "create",
        "deployment",
        "zipkin",
        "--image",
        "openzipkin/zipkin"
    ])
    subprocess.check_call([
        "kubectl",
        "expose",
        "deployment",
        "zipkin",
        "--type",
        "ClusterIP",
        "--port",
        "9411"
    ])


def dapr_is_initialized_with_k3d() -> bool:
    return subprocess.call([
        "dapr",
        "status",
        "-k"
    ])


def initialize_dapr_with_k3d(dapr_runtime_version: str, dapr_config_dir: str):
    subprocess.check_call([
        "dapr",
        "init",
        "-k",
        "--wait",
        "--timeout 600",
        "--runtime-version",
        dapr_runtime_version
    ])

    subprocess.check_call([
        "kubectl",
        "apply",
        "-f",
        f"{dapr_config_dir}/config.yaml"
    ])

    subprocess.check_call([
        "kubectl",
        "apply",
        "-f",
        f"{dapr_config_dir}/components/pubsub.yaml"
    ])


def configure_controlplane():
    dapr_config_dir = os.path.join(
        get_script_path(),
        "runtime",
        "config",
        ".dapr"
    )

    if not registry_exists():
        create_registry()
    else:
        print("Registry already exists.")

    if not cluster_exists():
        create_cluster(dapr_config_dir)
    else:
        print("Cluster already exists.")

    if not deployment_exists("zipkin"):
        deploy_zipkin()
    else:
        print("Zipkin is already deployed.")

    if not dapr_is_initialized_with_k3d():
        dapr_runtime_version = require_env("daprRuntimeVersion")
        initialize_dapr_with_k3d(dapr_runtime_version, dapr_config_dir)
    else:
        print("Dapr is already initialized with K3D.")


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
