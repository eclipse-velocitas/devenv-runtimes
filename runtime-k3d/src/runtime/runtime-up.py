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

import argparse

from lib import create_log_file
from controlplane import configure_controlplane
from runtime import deploy_runtime
from yaspin import yaspin


def runtime_up(skip_services: bool):
    """Start up the K3D runtime."""
    print('Hint: Log files can be found in your workspace\'s logs directory')
    log_file = create_log_file('runtime')
    with yaspin(text="Configuring controlplane for k3d...") as spinner:
        try:
            configure_controlplane(spinner, log_file)
            if not skip_services:
                spinner.text = "Starting k3d runtime..."
                deploy_runtime(spinner, log_file)
            else:
                spinner.write("Skipping services")
            spinner.ok("✔")
        except Exception as err:
            spinner.fail(err)


def main():
    parser = argparse.ArgumentParser("runtime-up")
    parser.add_argument(
        "-s",
        "--skip-services",
        required=False,
        action="store_true",
        help="Configure only the cluster and don't deploy all services",
    )
    args = parser.parse_args()

    runtime_up(args.skip_services)


if __name__ == "__main__":
    main()
