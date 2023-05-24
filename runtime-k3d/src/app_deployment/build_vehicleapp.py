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

from yaspin import yaspin

from velocitas_lib import (
    create_log_file,
    get_app_manifest,
    get_workspace_dir,
    require_env,
)


def build_vehicleapp():
    """Build VehicleApp docker image and display the progress using a spinner."""

    print("Hint: Log files can be found in your workspace's logs directory")
    log_output = create_log_file("build-vapp", "runtime-k3d")
    with yaspin(text="Building VehicleApp...", color="cyan") as spinner:
        try:
            status = "> Building VehicleApp image"
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

            spinner.write(status)

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
            spinner.ok("✅")
        except Exception as err:
            log_output.write(str(err))
            spinner.fail("💥")


if __name__ == "__main__":
    build_vehicleapp()
