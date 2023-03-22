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
import sys

from lib import MiddlewareType, get_middleware_type, get_services, get_dapr_sidecar_args


def get_dapr_app_id(service_id: str) -> str:
    return f"{service_id.upper()}_DAPR_APP_ID"


def deploy_app(executable_path: str, args: list[str]):
    program_args = [executable_path, *args]
    envs = dict()
    for service in get_services():
        service_id = service["id"]
        envs[get_dapr_app_id(service_id)] = service_id

    if get_middleware_type() == MiddlewareType.DAPR:
        dapr_args, dapr_env = get_dapr_sidecar_args("vehicleapp", 50008)
        dapr_args = dapr_args + ["--"]
        envs.update(dapr_env)

    print(program_args)
    subprocess.check_call(program_args)


if __name__ == "__main__":
    print(sys.argv)
    deploy_app(sys.argv[1], sys.argv[2:])
