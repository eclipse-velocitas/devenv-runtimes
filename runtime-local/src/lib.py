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

# flake8: noqa: E402 module level import
from enum import Enum
from typing import Optional, Tuple
from velocitas_lib import get_script_path


class MiddlewareType(Enum):
    """Enumeration containing all possible middleware types."""
    NATIVE = (0,)
    DAPR = 1


def get_middleware_type() -> MiddlewareType:
    """Return the current middleware type."""
    return MiddlewareType.DAPR


def get_dapr_sidecar_args(
    app_id: str, app_port: Optional[str] = None, grpc_port: Optional[str] = None, http_port: Optional[str] = None
) -> Tuple[list[str], dict[str, Optional[str]]]:
    """Return all arguments to spawn a dapr sidecar for the given app."""
    env = dict()

    args = [
        "dapr",
        "run",
        "--app-id",
        app_id,
        "--app-protocol",
        "grpc",
        "--resources-path",
        f"{get_script_path()}/.dapr/components",
        "--config",
        f"{get_script_path()}/.dapr/config.yaml",
    ] + (
        ["--app-port", str(app_port)] if app_port else []
    ) + (
        ["--dapr-grpc-port", str(grpc_port)] if grpc_port else []
    ) + (
        ["--dapr-http-port", str(http_port)] if http_port else []
    )

    return (args, env)


def get_container_runtime_executable() -> str:
    """Return the current container runtime executable. E.g. docker."""
    return "docker"
