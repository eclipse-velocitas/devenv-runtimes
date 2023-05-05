# Copyright (c) 2023 Robert Bosch GmbH and Microsoft Corporation
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

"""Provides methods and functions to download and install dependencies."""

import os
import subprocess
import sys


def get_script_path() -> str:
    """Return the absolute path to the directory the invoked Python script
    is located in."""
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def pip(args: list[str]) -> None:
    """Invoke the pip process with the given arguments."""
    subprocess.check_call([sys.executable, "-m", "pip", *args])


def install_packages():
    """Install all required Python packages."""
    script_path = get_script_path()
    pip(["install", "-r", f"{script_path}/requirements.txt"])


def install_velocitas_lib():
    """Install the velocitas lib."""
    script_path = get_script_path()
    pip(["install", "-e", f"{script_path}/../../velocitas_lib"])


if __name__ == "__main__":
    install_velocitas_lib()
    install_packages()
