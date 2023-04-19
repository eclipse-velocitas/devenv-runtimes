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

from yaspin import yaspin

from lib import get_specific_services, run_service, stop_service


spawned_processes = list[subprocess.Popen]()


def run_specific_service(service_id: str) -> None:
    """Run specified service."""

    with yaspin(text=f"Starting service {service_id}") as spinner:
        try:
            services = get_specific_services(service_id)
            if len(services) == 1:
                service = services[0]
                stop_service(service)
                spawned_processes.append(run_service(service))
                time.sleep(3)
                spinner.ok("✔ ")
            elif len(services) == 0:
                spinner.write("Service not defined")
                spinner.fail("💥 ")
            else:
                spinner.write("Multiple service definitions found, which to take?")
                spinner.fail("💥 ")
        except RuntimeError as error:
            spinner.write(error.with_traceback())
            spinner.fail("💥 ")
            terminate_spawned_processes()


def wait_while_processes_are_running():
    while len(spawned_processes) > 0:
        time.sleep(1)
        for process in spawned_processes:
            process.poll()


def terminate_spawned_processes():
    with yaspin(text="Stopping runtime") as spinner:
        while len(spawned_processes) > 0:
            process = spawned_processes.pop()
            process.terminate()
            spinner.write(f"> {process.args[0]} terminated")
        spinner.ok("✔")


def handler(_signum, _frame):
    terminate_spawned_processes()


if __name__ == "__main__":
    # The arguments we accept
    parser = argparse.ArgumentParser(
        description="Start the specified service as defined in runtime.json."
    )
    parser.add_argument(
        "service_id",
        type=str,
        help="Id of the service to start - refers to 'id' key in runtime.json"
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, handler)
    run_specific_service(args.service_id)
    wait_while_processes_are_running()
