import os

import pytest

from velocitas_lib import get_package_path
from velocitas_lib.variables import ProjectVariables


@pytest.fixture()
def set_test_env_var():
    os.environ["VELOCITAS_CACHE_DATA"] = '{"cache_key":"cache_value"}'


def test_replace_occurrences__returns_correct_resolved_string(set_test_env_var):
    input_str_a = "${{ test.string.a }}"
    input_str_b = "/test/${{ test.string.b }}/test"

    variables_to_replace = {
        "test.string.a": "testA",
        "test.string.b": "testB",
    }

    variables = ProjectVariables(variables_to_replace)
    assert (
        variables.replace_occurrences(input_str_a)
        == variables_to_replace["test.string.a"]
    )
    assert (
        variables.replace_occurrences(input_str_b)
        == f'/test/{variables_to_replace["test.string.b"]}/test'
    )


def test_replace_occurrences__variable_not_defined__raises_KeyError(set_test_env_var):
    with pytest.raises(KeyError):
        input_str_a = "${{ test.string.a }}"
        variables_to_replace = {
            "test.string.b": "testB",
        }
        ProjectVariables(variables_to_replace).replace_occurrences(input_str_a)


def test_replace_occurrences__no_replacement_in_input_str__returns_input_str(
    set_test_env_var,
):
    input_str_a = "test.string.a"
    input_str_b = "/test/test.string.b/test"
    input_str_c = "testImage:testVersion"
    input_str_d = "url.com/owner/repo/service:version"
    variables_to_replace = {
        "test.string.a": "testA",
        "test.string.b": "testB",
    }

    variables = ProjectVariables(variables_to_replace)
    assert variables.replace_occurrences(input_str_a) == input_str_a
    assert variables.replace_occurrences(input_str_b) == input_str_b
    assert variables.replace_occurrences(input_str_c) == input_str_c
    assert variables.replace_occurrences(input_str_d) == input_str_d


def test_replace_occurrences__builtins_provided(set_test_env_var):
    variables = ProjectVariables({})

    assert (
        variables.replace_occurrences(
            "This is the package path: '${{ builtin.package_dir }}'"
        )
        == f"This is the package path: {get_package_path().__str__()!r}"
    )
