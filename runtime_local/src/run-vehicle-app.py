# Copyright (c) 2023-2024 Contributors to the Eclipse Foundation
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
import subprocess
from typing import Optional

from local_lib import MiddlewareType, get_dapr_sidecar_args, get_middleware_type
from velocitas_lib.services import get_services


def get_dapr_app_id(service_id: str) -> str:
    return f"{service_id.upper()}_DAPR_APP_ID"


def run_app(
    executable_path: str,
    args: list[str],
    app_id: Optional[str] = None,
    app_port: Optional[str] = None,
):
    program_args = [executable_path, *args]
    envs = dict()
    for service in get_services():
        service_id = service.id
        envs[get_dapr_app_id(service_id)] = service_id

    if get_middleware_type() == MiddlewareType.DAPR:
        if not app_id:
            app_id = "vehicleapp"
        dapr_args, dapr_env = get_dapr_sidecar_args(app_id, app_port=app_port)
        dapr_args = dapr_args + ["--"]
        envs.update(dapr_env)
        program_args = dapr_args + program_args

    subprocess.check_call(program_args)


if __name__ == "__main__":
    # The arguments we accept
    parser = argparse.ArgumentParser(
        description="Starts the Dapr sidecar for the app to debug."
    )
    # Add para to name package
    parser.add_argument(
        "--dapr-app-id",
        type=str,
        help="The Dapr app-id of the app being debugged.",
    )
    parser.add_argument(
        "--dapr-app-port",
        type=str,
        help="The port where the app is listening on.",
    )
    parser.add_argument(
        "executable_path", type=str, help="Path to the executable to be invoked."
    )
    parser.add_argument("app_args", nargs="*")

    args = parser.parse_args()
    run_app(
        args.executable_path,
        args.app_args,
        app_id=args.dapr_app_id,
        app_port=args.dapr_app_port,
    )
