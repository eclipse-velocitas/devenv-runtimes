# Copyright (c) 2023 Robert Bosch GmbH and Microsoft Corporation
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

import argparse
import signal
import subprocess
import time
from typing import Dict

from lib import get_specific_service, run_service, stop_container, stop_service
from yaspin import yaspin

from velocitas_lib import get_log_file_name

spawned_processes: Dict[str, subprocess.Popen] = {}


def run_specific_service(service_id: str) -> None:
    """Run specified service."""

    with yaspin(text=f"Starting service {service_id}") as spinner:
        try:
            service = get_specific_service(service_id)
            stop_service(service)
            spawned_processes[service_id] = run_service(service)
            spinner.ok("✔")
        except RuntimeError as error:
            spinner.write(error.args)
            spinner.fail("💥")
            terminate_spawned_processes()
            print(f"Starting {service_id=} failed")
            with open(
                get_log_file_name(service_id, "runtime-local"),
                mode="r",
                encoding="utf-8",
            ) as log:
                print(f">>>> Start log of {service_id} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print(log.read(), end="")
                print(f"<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< End log of {service_id} <<<<")


def wait_while_processes_are_running():
    while len(spawned_processes) > 0:
        time.sleep(1)
        for process in spawned_processes.values():
            process.poll()


def terminate_spawned_processes():
    with yaspin(text="Stopping service") as spinner:
        while len(spawned_processes) > 0:
            (service_id, process) = spawned_processes.popitem()
            process.terminate()
            stop_container(service_id, subprocess.DEVNULL)
            spinner.write(f"> {process.args[0]} (service-id='{service_id}') terminated")
        spinner.ok("✔")


def handler(_signum, _frame):  # noqa: U101 unused arguments
    terminate_spawned_processes()


if __name__ == "__main__":
    # The arguments we accept
    parser = argparse.ArgumentParser(
        description="Start the specified service as defined in runtime.json."
    )
    parser.add_argument(
        "service_id",
        type=str,
        help="Id of the service to start - refers to 'id' key in runtime.json",
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    run_specific_service(args.service_id)
    wait_while_processes_are_running()
