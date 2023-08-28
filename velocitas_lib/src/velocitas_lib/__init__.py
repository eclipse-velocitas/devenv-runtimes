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

import inspect
import json
import os
import sys
from io import TextIOWrapper
from pathlib import Path
from typing import Any, Dict


def require_env(name: str) -> str:
    """Require and return an environment variable.

    Args:
        name (str): The name of the variable.

    Raises:
        ValueError: In case the environment variable is not set.

    Returns:
        str: The value of the variable.
    """
    var = os.getenv(name)
    if not var:
        raise ValueError(f"Environment variable {name!r} not set!")
    return var


def get_workspace_dir() -> str:
    """Return the workspace directory."""
    return require_env("VELOCITAS_WORKSPACE_DIR")


def get_app_manifest() -> dict:
    return json.loads(require_env("VELOCITAS_APP_MANIFEST"))


def get_script_path() -> str:
    """Return the absolute path to the directory the invoked Python script
    is located in."""
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def get_package_path() -> Path:
    """Return the absolute path to the package directory the invoked Python
    script belongs to."""
    invoking_file_path = inspect.stack()[1].filename
    parents = Path(invoking_file_path).resolve().parents
    for parent in parents:
        if parent.is_dir() and "manifest.json" in os.listdir(parent):
            return parent

    raise FileNotFoundError(
        f"Unable to find the package path of '{invoking_file_path}'!"
    )


def get_cache_data() -> Dict[str, Any]:
    """Return the data of the cache as Python object."""
    return json.loads(require_env("VELOCITAS_CACHE_DATA"))


def get_log_file_name(service_id: str, runtime_id: str) -> str:
    """Build the log file name for the given service and runtime.

    Args:
        service_id (str): The ID of the service to log.
        runtime_id (str): The ID of the runtime to log.

    Returns:
        str: The log file name.
    """
    return os.path.join(get_workspace_dir(), "logs", runtime_id, f"{service_id}.log")


def create_log_file(service_id: str, runtime_id: str) -> TextIOWrapper:
    """Create a log file for the given service and runtime.

    Args:
        service_id (str): The ID of the service to log.
        runtime_id (str): The ID of the runtime to log.

    Returns:
        TextIOWrapper: The log file.
    """
    log_file_name = get_log_file_name(service_id, runtime_id)
    os.makedirs(os.path.dirname(log_file_name), exist_ok=True)
    return open(log_file_name, "w", encoding="utf-8")
