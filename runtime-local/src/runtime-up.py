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

from io import TextIOWrapper
import os
import subprocess
import time
import signal
import sys
from typing import Optional

from yaspin import yaspin

from lib import (
    MiddlewareType,
    get_cache_data,
    get_container_runtime_executable,
    get_middleware_type,
    get_services,
    get_workspace_dir,
    json_obj_to_flat_map,
    replace_variables,
    get_dapr_sidecar_args,
    get_script_path
)


def create_log_file(service_id: str) -> TextIOWrapper:
    """Create a log file for the given service.

    Args:
        service_id (str): The ID of the service to log.

    Returns:
        TextIOWrapper: The log file.
    """
    log_path = os.path.join(get_workspace_dir(), "logs")
    os.makedirs(log_path, exist_ok=True)
    return open(os.path.join(log_path, f"{service_id}.txt"), "w", encoding="utf-8")


def run_service(service_spec) -> subprocess.Popen:
    """Run a single service.

    Args:
        service_spec: The specification of the service.
    """
    service_id = service_spec["id"]

    log = create_log_file(service_id)
    log.write(f"Starting {service_id!r}\n")

    no_dapr = False

    container_image = None
    service_port = None
    env_vars = dict[str, Optional[str]]()
    port_forwards = []
    mounts = []
    args = []

    variables = json_obj_to_flat_map(get_cache_data(), "builtin.cache")
    variables["builtin.script_dir"] = get_script_path()

    for config_entry in service_spec["config"]:
        if config_entry["key"] == "image":
            container_image = replace_variables(config_entry["value"], variables)
        elif config_entry["key"] == "env":
            pair = config_entry["value"].split("=", 1)
            env_vars[pair[0].strip()] = None
            if len(pair) > 1:
                env_vars[pair[0].strip()] = replace_variables(pair[1].strip(), variables)
        elif config_entry["key"] == "port":
            service_port = replace_variables(config_entry["value"], variables)
        elif config_entry["key"] == "no-dapr":
            no_dapr = config_entry["value"]
        elif config_entry["key"] == "arg":
            args.append(replace_variables(config_entry["value"], variables))
        elif config_entry["key"] == "port-forward":
            port_forwards.append(replace_variables(config_entry["value"], variables))
        elif config_entry["key"] == "mount":
            mounts.append(replace_variables(config_entry["value"], variables))

    dapr_args = []
    if not no_dapr and get_middleware_type() == MiddlewareType.DAPR:
        dapr_args, dapr_env = get_dapr_sidecar_args(service_id, service_port)
        dapr_args = dapr_args + ["--"]
        env_vars.update(dapr_env)

    port_forward_args = []
    for port_forward in port_forwards:
        port_forward_args.append("-p")
        port_forward_args.append(port_forward)

    mount_args = []
    for mount in mounts:
        mount_args.append("-v")
        mount_args.append(mount)

    env_forward_args = []
    for key, value in env_vars.items():
        env_forward_args.append("-e")
        if value:
            env_forward_args.append(f"{key}={value}")
        else:
            env_forward_args.append(f"{key}")

    docker_args = [
        *dapr_args,
        get_container_runtime_executable(),
        "run",
        "--rm",
        "--name",
        service_id,
        *env_forward_args,
        *port_forward_args,
        *mount_args,
        "--network",
        "host",
        container_image,
        *args,
    ]

    log.write(" ".join(docker_args) + "\n")
    return subprocess.Popen(
        docker_args,
        start_new_session=True,
        stderr=subprocess.STDOUT,
        stdout=log,
    )


def stop_service(service_spec):
    """Stop the given service.

    Args:
        service_spec (_type_): The service to stop.
    """
    service_id = service_spec["id"]
    no_dapr = False

    log = create_log_file(service_id)
    log.write(f"Stopping {service_id!r}\n")

    for config_entry in service_spec["config"]:
        if config_entry["key"] == "no-dapr":
            no_dapr = config_entry["value"]

    if not no_dapr and get_middleware_type() == MiddlewareType.DAPR:
        subprocess.call(
            ["dapr", "stop", "--app-id", service_id],
            stderr=subprocess.STDOUT,
            stdout=log,
        )

    subprocess.call(
        [get_container_runtime_executable(), "stop", service_id],
        stderr=subprocess.STDOUT,
        stdout=log,
    )


spawned_processes = list[subprocess.Popen]()


def run_services() -> None:
    """Run all required services."""

    with yaspin(text="Starting runtime") as spinner:
        try:
            for service in get_services():
                stop_service(service)
                spawned_processes.append(run_service(service))
                time.sleep(3)
                spinner.write(f"> {service['id']} running")
            spinner.ok("✔ ")
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
    signal.signal(signal.SIGINT, handler)
    run_services()
    wait_while_processes_are_running()
