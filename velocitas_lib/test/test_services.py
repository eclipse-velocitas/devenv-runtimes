import os

import pytest

from velocitas_lib import get_package_path, get_workspace_dir
from velocitas_lib.services import resolve_functions


def test_resolve_functions__unknown_function__raises_exception():
    with pytest.raises(RuntimeError, match="Unsupported function: 'foo'!"):
        resolve_functions("$foo( asd )")


def test_resolve_functions__pathInWorkspaceOrPackage__file_missing__raises_exception():
    with pytest.raises(
        RuntimeError, match="Path 'asd' not found in workspace or package!"
    ):
        resolve_functions("$pathInWorkspaceOrPackage( asd )")


def test_resolve_functions__pathInWorkspaceOrPackage__file_exists_in_workspace():
    assert resolve_functions(
        "$pathInWorkspaceOrPackage( manifest.json )"
    ) == os.path.join(get_workspace_dir(), "manifest.json")


def test_resolve_functions__pathInWorkspaceOrPackage__file_exists_in_package():
    os.environ["VELOCITAS_WORKSPACE_DIR"] = ".."
    assert resolve_functions(
        "$pathInWorkspaceOrPackage( manifest.json )"
    ) == os.path.join(get_package_path(), "manifest.json")
