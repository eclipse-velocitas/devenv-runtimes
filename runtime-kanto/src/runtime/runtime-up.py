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

from controlplane import configure_controlplane
from yaspin import yaspin

from velocitas_lib import create_log_file


def runtime_up():
    """Start up the K3D runtime."""

    print("Hint: Log files can be found in your workspace's logs directory")
    log_output = create_log_file("runtime-up", "runtime-kanto")
    with yaspin(text="Configuring controlplane for Kanto...", color="cyan") as spinner:
        try:
            configure_controlplane(spinner, log_output)
            spinner.ok("✅")
        except Exception as err:
            log_output.write(str(err))
            spinner.fail("💥")


def main():
    runtime_up()


if __name__ == "__main__":
    main()
