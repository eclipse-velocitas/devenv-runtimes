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
import time
from enum import Enum
from io import TextIOWrapper
from itertools import filterfalse
from re import Pattern, compile
from threading import Timer
from typing import Optional, Tuple

from velocitas_lib import (
    get_cache_data,
    get_package_path,
    get_script_path,
    get_services,
    get_workspace_dir,
    json_obj_to_flat_map,
    replace_variables,
)


class MiddlewareType(Enum):
    """Enumeration containing all possible middleware types."""

    NATIVE = (0,)
    DAPR = 1


def get_middleware_type() -> MiddlewareType:
    """Return the current middleware type."""
    return MiddlewareType.DAPR


def get_specific_service(service_id: str):
    """Return the specified service as Python object."""
    services = get_services()
    services = list(filter(lambda service: service["id"] == service_id, services))
    if len(services) == 0:
        raise RuntimeError(f"Service with id '{service_id}' not defined")
    if len(services) > 1:
        raise RuntimeError(
            f"Multiple service definitions of id '{service_id}' found, which to take?"
        )
    return services[0]


def get_dapr_sidecar_args(
    app_id: str,
    app_port: Optional[str] = None,
    grpc_port: Optional[str] = None,
    http_port: Optional[str] = None,
) -> Tuple[list[str], dict[str, Optional[str]]]:
    """Return all arguments to spawn a dapr sidecar for the given app."""
    env = dict()
    env["DAPR_GRPC_PORT"] = None
    env["DAPR_HTTP_PORT"] = None

    args = (
        [
            "dapr",
            "run",
            "--app-id",
            app_id,
            "--app-protocol",
            "grpc",
            "--resources-path",
            f"{get_script_path()}/runtime/config/.dapr/components",
            "--config",
            f"{get_script_path()}/runtime/config/.dapr/config.yaml",
        ]
        + (["--app-port", str(app_port)] if app_port else [])
        + (["--dapr-grpc-port", str(grpc_port)] if grpc_port else [])
        + (["--dapr-http-port", str(http_port)] if http_port else [])
    )

    return (args, env)


def get_container_runtime_executable() -> str:
    """Return the current container runtime executable. E.g. docker."""
    return "docker"


def get_log_file_name(service_id: str) -> str:
    """Build the log file name for the given service.

    Args:
        service_id (str): The ID of the service to log.

    Returns:
        str: The log file name.
    """
    return os.path.join(get_workspace_dir(), "logs", f"{service_id}.txt")


def create_log_file(service_id: str) -> TextIOWrapper:
    """Create a log file for the given service.

    Args:
        service_id (str): The ID of the service to log.

    Returns:
        TextIOWrapper: The log file.
    """
    log_file_name = get_log_file_name(service_id)
    os.makedirs(os.path.dirname(log_file_name), exist_ok=True)
    return open(log_file_name, "w", encoding="utf-8")


dapr_pattern: Pattern[str] = compile(
    r".*You\'re up and running! Both Dapr and your app logs will appear here\.\n"
)


def run_service(service_spec) -> subprocess.Popen:
    """Run a single service.

    Args:
        service_spec: The specification of the service.

    Returns:
       The Popen object representing the root process running the required service
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
    patterns = []

    variables = json_obj_to_flat_map(get_cache_data(), "builtin.cache")
    variables["builtin.package_dir"] = get_package_path()

    for config_entry in service_spec["config"]:
        if config_entry["key"] == "image":
            container_image = replace_variables(config_entry["value"], variables)
        elif config_entry["key"] == "env":
            pair = config_entry["value"].split("=", 1)
            env_vars[pair[0].strip()] = None
            if len(pair) > 1:
                env_vars[pair[0].strip()] = replace_variables(
                    pair[1].strip(), variables
                )
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
        elif config_entry["key"] == "start-pattern":
            patterns.append(compile(config_entry["value"]))

    dapr_args = []
    if not no_dapr and get_middleware_type() == MiddlewareType.DAPR:
        dapr_args, dapr_env = get_dapr_sidecar_args(service_id, service_port)
        dapr_args = dapr_args + ["--"]
        env_vars.update(dapr_env)
        patterns.append(dapr_pattern)

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
        "--init",
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

    return spawn_process(docker_args, log, patterns, startup_timeout_sec=60)


def spawn_process(
    args: list[str],
    log: TextIOWrapper,
    patterns: list[Pattern[str]],
    startup_timeout_sec: int,
) -> subprocess.Popen:
    """Spawn the process defined by the passed args.

    Args:
        args:
            The executable name to be spawned and its arguments
        log:
            Log file to receive the outputs (stdout + stderr) of the spawned process
        patterns:
            List of patterns, which match the lines in the log file to rate the
            process being started up successfully.
            All of the patterns need to match in any order.
            If the list is empty, startup will be rated successfully without
            doing any pattern matching.
        startup_timeout_sec:
            Timeout [in seconds] after which the spawned process gets killed,
            if not all patterns did match so far

    Returns:
       The created Popen object
    """
    with open(log.name, "r", encoding="utf-8") as monitor:
        log.write(" ".join(args) + "\n\n")
        log.flush()
        process = subprocess.Popen(
            args,
            start_new_session=True,
            stderr=subprocess.STDOUT,
            stdout=log,
        )

        timer: Timer = Timer(startup_timeout_sec, process.kill)
        timer.start()
        for line in iter(monitor.readline, b""):
            if not timer.is_alive():
                raise RuntimeError(
                    """Timeout reached after {startup_timeout_sec}
                    seconds, service killed!"""
                )
            if process.poll() is not None:
                raise RuntimeError("Service unexpectedly terminated")
            if line == "":
                time.sleep(0.1)
                continue
            patterns[:] = filterfalse(
                lambda pattern: pattern.search(line), patterns  # noqa: B023
            )
            if len(patterns) == 0:
                timer.cancel()
                break

    return process


def stop_container(service_id, log=None):
    """Stop the container representing the specified service.

    Args:
        service_id: The service_id of the container to stop.
        log: Log stream to forward the outputs to.
    """
    subprocess.call(
        [get_container_runtime_executable(), "stop", service_id],
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

    stop_container(service_id, log)
