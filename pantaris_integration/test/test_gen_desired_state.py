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

from pathlib import Path

from pantaris_integration.src.gen_desired_state import (
    get_md5_for_file,
    get_md5_from_uri,
    is_uri,
)


def test_get_md5_for_file():
    hash = get_md5_for_file(f"{Path.cwd()}/pantaris_integration/test/__init__.py")
    assert hash == "a6527c69275a58815400058232b53e2e"


def test_get_md5_for_uri():
    hash = get_md5_from_uri(
        "https://raw.githubusercontent.com/eclipse-velocitas/devenv-runtimes/main/pantaris_integration/test/__init__.py"
    )
    assert hash == "a6527c69275a58815400058232b53e2e"


def test_is_uri__true():
    assert is_uri("https://github.com/eclipse-velocitas")


def test_is_uri__false():
    assert not is_uri(f"{Path.cwd()}/pantaris_integration/test/__init__.py")
