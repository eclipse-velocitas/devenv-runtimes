# Copyright (c) 2024 Contributors to the Eclipse Foundation
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

# Workaround fix begin: Databroker CLI is not reactive if started via CLI in Python venv.
# With this fix in this file only standard libs are used avoiding the need for a venv.

# from local_lib import get_container_runtime_executable
# from velocitas_lib import require_env
import os
import subprocess


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


def get_container_runtime_executable() -> str:
    """Return the current container runtime executable. E.g. docker."""
    return "docker"


# Workaround fix end: Databroker CLI is not reactive if started via CLI in Python venv


def run_databroker_cli():
    databroker_cli_image = require_env("vehicleDatabrokerCliImage")
    program_args = [
        get_container_runtime_executable(),
        "run",
        "-it",
        "--rm",
        "--network",
        "host",
        databroker_cli_image,
    ]
    subprocess.check_call(program_args)


if __name__ == "__main__":
    run_databroker_cli()
