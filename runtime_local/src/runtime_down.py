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

from runtime_up import terminate_spawned_processes
from yaspin import yaspin


def runtime_down():
    """Stop the local runtime."""

    print("Hint: Log files can be found in your workspace's logs directory")
    with yaspin(text="Stopping local runtime...", color="cyan") as spinner:
        try:
            terminate_spawned_processes()
        except Exception:
            spinner.fail("💥")


if __name__ == "__main__":
    runtime_down()
