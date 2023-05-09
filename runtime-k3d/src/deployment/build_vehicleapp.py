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

from velocitas_lib import get_app_manifest, get_workspace_dir


def build_vehicleapp():
    """Build VehicleApp docker image and display the progress using a spinner."""
    with yaspin(text="Building VehicleApp...") as spinner:
        try:
            status = "> Building VehicleApp image"
            app_name = get_app_manifest()["name"].lower()
            image_tag = f"localhost:12345/{app_name}:local"
            dockerfile_path = "./app/Dockerfile"
            os.environ["DOCKER_BUILDKIT"] = "1"
            has_proxy: bool = os.getenv("HTTP_PROXY") is not None

            extra_proxy_args: List[str] = list()

            if has_proxy:
                status = f"{status} with proxy configuration."
                http_proxy = os.getenv("HTTP_PROXY", default="")
                https_proxy = os.getenv("HTTPS_PROXY", default="")
                ftp_proxy = os.getenv("FTP_PROXY", default="")
                all_proxy = os.getenv("ALL_PROXY", default="")
                no_proxy = os.getenv("NO_PROXY", default="")
                extra_proxy_args = [
                    "--build-arg",
                    f"HTTP_PROXY={http_proxy}",
                    "--build-arg",
                    f"HTTPS_PROXY={https_proxy}",
                    "--build-arg",
                    f"FTP_PROXY={ftp_proxy}",
                    "--build-arg",
                    f"ALL_PROXY={all_proxy}",
                    "--build-arg",
                    f"NO_PROXY={no_proxy}",
                ]
            else:
                status = f"{status} without proxy configuration."

            spinner.write(status)

            subprocess.call(
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
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=get_workspace_dir(),
            )
            spinner.ok("✔")
        except Exception as err:
            spinner.fail(err)


if __name__ == "__main__":
    build_vehicleapp()
