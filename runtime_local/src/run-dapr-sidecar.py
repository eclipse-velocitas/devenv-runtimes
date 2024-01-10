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

from local_lib import get_dapr_sidecar_args


def start_sidecar(
    app_id: str,
    app_port: Optional[str] = None,
    grpc_port: Optional[str] = None,
    http_port: Optional[str] = None,
):
    args, _ = get_dapr_sidecar_args(
        app_id, app_port=app_port, grpc_port=grpc_port, http_port=http_port
    )

    subprocess.check_call(args)


if __name__ == "__main__":
    # The arguments we accept
    parser = argparse.ArgumentParser(
        description="Starts the Dapr sidecar for the app to debug."
    )
    # Add para to name package
    parser.add_argument(
        "app_id",
        type=str,
        help="The Dapr app-id of the app being debugged.",
    )
    parser.add_argument(
        "--app-port",
        type=str,
        help="The port where the app is listening on.",
    )
    parser.add_argument(
        "--dapr-grpc-port",
        type=str,
        help="The port number where the sidecar listens for grpc messages.",
    )
    parser.add_argument(
        "--dapr-http-port",
        type=str,
        help="The port number where the sidecar listens for grpc messages.",
    )

    args = parser.parse_args()

    start_sidecar(
        args.app_id,
        app_port=args.app_port,
        grpc_port=args.dapr_grpc_port,
        http_port=args.dapr_http_port,
    )
