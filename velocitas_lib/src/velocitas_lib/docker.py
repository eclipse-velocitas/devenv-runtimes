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
from io import TextIOWrapper
from typing import List

from velocitas_lib import get_app_manifest, get_workspace_dir, require_env


def build_vehicleapp_image(log_output: TextIOWrapper | int = subprocess.DEVNULL):
    """Build VehicleApp docker image and display the progress using a spinner."""
    app_name = get_app_manifest()["name"].lower()
    image_tag = f"localhost:12345/{app_name}:local"
    dockerfile_path = require_env("dockerfilePath")
    os.environ["DOCKER_BUILDKIT"] = "1"

    extra_proxy_args: List[str] = [
        "--build-arg",
        "HTTP_PROXY",
        "--build-arg",
        "HTTPS_PROXY",
        "--build-arg",
        "FTP_PROXY",
        "--build-arg",
        "ALL_PROXY",
        "--build-arg",
        "NO_PROXY",
    ]

    subprocess.check_call(
        [
            "docker",
            "build",
            "-f",
            dockerfile_path,
            "--progress=plain",
            "-t",
            image_tag,
        ]
        + extra_proxy_args
        + [
            ".",
            "--no-cache",
        ],
        stdout=log_output,
        stderr=log_output,
        cwd=get_workspace_dir(),
    )


def is_docker_image_build_locally(app_name: str) -> bool:
    """Check if vehicle app docker image is locally available

    Args:
        app_name (str): App name to check for
    """
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


def push_docker_image_to_registry(
    app_name: str, log_output: TextIOWrapper | int = subprocess.DEVNULL
):
    """Push docker image to local image registry

    Args:
        app_name (str): App name to push to registry
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    subprocess.check_call(
        ["docker", "push", f"localhost:12345/{app_name}:local"],
        stdout=log_output,
        stderr=log_output,
    )
