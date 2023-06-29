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
from io import TextIOWrapper
from pathlib import Path
import time
import json
import os
import sys

from yaspin.core import Yaspin

from velocitas_lib import (
    get_workspace_dir,
    get_script_path,
    get_package_path,
    get_app_manifest
)

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app_deployment"))
from deploy_vehicleapp import remove_vehicleapp  # noqa: E402


def remove_container(log_output: TextIOWrapper | int = subprocess.DEVNULL):
    """Uninstall the runtime.

    Args:
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    subprocess.call(
        ["kanto-cm", "remove", "-f", "-n", "databroker"],
        stdout=log_output,
        stderr=log_output,
    )
    subprocess.call(
        ["kanto-cm", "remove", "-f", "-n", "mosquitto"],
        stdout=log_output,
        stderr=log_output,
    )
    subprocess.call(
        ["kanto-cm", "remove", "-f", "-n", "feedercan"],
        stdout=log_output,
        stderr=log_output,
    )
    subprocess.call(
        ["kanto-cm", "remove", "-f", "-n", "seatservice"],
        stdout=log_output,
        stderr=log_output,
    )

    app_name = get_app_manifest()["name"].lower()
    remove_vehicleapp(app_name, log_output)


def adapt_feedercan_deployment_file():
    with open(
        os.path.join(get_script_path(), "deployment", "feedercan.json"),
        "r+",
        encoding="utf-8",
    ) as f:
        data = json.load(f)
        data["mount_points"][0]["source"] = os.path.join(
            get_package_path(), "config", "feedercan"
        )
        f.seek(0)
        json.dump(data, f, indent=4)


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
    remove_container(log_output)
    status = status + "uninstalled!"
    spinner.write(status)


def is_kanto_running(log_output: TextIOWrapper | int = subprocess.DEVNULL) -> bool:
    try:
        subprocess.check_call(
            [
                "kanto-cm",
                "sysinfo",
                "--timeout",
                "1",
            ],
            stdout=log_output,
            stderr=log_output,
        )
    except Exception:
        return False
    return True


def start_kanto(spinner: Yaspin, log_output: TextIOWrapper | int = subprocess.DEVNULL):
    """Starting the Kanto process in background

    Args:
        spinner (Yaspin): The progress spinner to update.
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    adapt_feedercan_deployment_file()
    kanto = subprocess.Popen(
        [
            "sudo",
            "container-management",
            "--cfg-file",
            f"{get_script_path()}/config.json",
            "--deployment-ctr-dir",
            f"{get_script_path()}/deployment",
            "--log-file",
            f"{get_workspace_dir()}/logs/runtime-kanto/container-management.log"

        ],
        start_new_session=True,
        stderr=log_output,
        stdout=log_output,
    )
    socket = Path("/run/container-management/container-management.sock")
    while not socket.exists():
        print("waiting")
        time.sleep(1)

    subprocess.call(
        [
            "sudo",
            "chmod",
            "a+rw",
            "/run/container-management/container-management.sock",
        ],
        stdout=log_output,
        stderr=log_output,
    )

    # sleep a bit to properly get the errors
    time.sleep(0.1)
    if kanto.poll() == 1:
        spinner.text = "Starting Kanto failed!"
        spinner.fail("💥")
        stop_kanto(log_output)
        return

    spinner.text = "Kanto is ready to use!"
    spinner.ok("✅")
    kanto.wait()


def stop_kanto(log_output: TextIOWrapper | int = subprocess.DEVNULL):
    """Starting the Kanto process in background

    Args:
        spinner (Yaspin): The progress spinner to update.
        log_output (TextIOWrapper | int): Logfile to write or DEVNULL by default.
    """
    subprocess.check_call(
        [
            "sudo", "pkill", "-1", "-f", "container-management",
        ],
        stdout=log_output,
        stderr=log_output,
    )
