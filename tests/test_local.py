from checkmate import Request, ResultType, run_tests
from pydantic import ValidationError
import pytest


def test_multi():
    source = """
def f(x):
    return x + 1
"""
    tests = [{"input_args": ["1"], "output": "2"}, {"input_args": ["2"], "output": "4"}]
    request = Request(source=source.strip(), tests=tests)
    result = run_tests(request)
    assert len(result) == 2
    assert result[0].type == ResultType.SUCCESS
    assert result[1].type == ResultType.FAIL


def test_unequal_input_output_args():
    source = """
def concat(a, b):
    a += b
"""
    tests = [
        {"input_args": ["[1, 2]", "[3]"], "output_args": ["[1, 2, 3]"]},
    ]
    with pytest.raises(ValidationError):
        Request(source=source.strip(), tests=tests)
