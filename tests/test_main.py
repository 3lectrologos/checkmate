import pytest

from . import get_response
from checkmate import (
    SuccessResult,
    SyntaxErrorResult,
    SpecificationErrorResult,
    RuntimeErrorResult,
    FailResult,
)


def test_simple_success():
    source = """
def f(x):
    return x + 1
"""
    tests = [{"input_args": [1], "output": 2}]
    result_list = get_response(source, tests)
    assert len(result_list) == 1
    SuccessResult.model_validate(result_list[0])


def test_simple_success_with_output_args():
    source = """
def f(x):
    return x + 1
"""
    tests = [{"input_args": [1], "output_args": [1], "output": 2}]
    result_list = get_response(source, tests)
    assert len(result_list) == 1
    SuccessResult.model_validate(result_list[0])


def test_simple_fail_with_output_args():
    source = """
def f(x):
    return x + 1
"""
    tests = [{"input_args": [1], "output_args": [2], "output": 2}]
    result_list = get_response(source, tests)
    assert len(result_list) == 1
    FailResult.model_validate(result_list[0])


def test_simple_syntax_error():
    source = """
def f(x):
    return x +
"""
    tests = [{"input_args": [1], "output": 2}]
    result_list = get_response(source, tests)
    assert len(result_list) == 1
    SyntaxErrorResult.model_validate(result_list[0])


def test_simple_runtime_error():
    source = """
def f(x):
    return x + foo()
"""
    tests = [{"input_args": [1], "output": 2}]
    result_list = get_response(source, tests)
    assert len(result_list) == 1
    RuntimeErrorResult.model_validate(result_list[0])


def test_outside_runtime_error():
    source = """
def f(x):
    return x + 1

foo()
"""
    tests = [{"input_args": [1], "output": 2}]
    result_list = get_response(source, tests)
    assert len(result_list) == 1
    RuntimeErrorResult.model_validate(result_list[0])


def test_simple_fail():
    source = """
def f(x):
    return x + 2
"""
    tests = [{"input_args": [1], "output": 2}]
    result_list = get_response(source, tests)
    assert len(result_list) == 1
    FailResult.model_validate(result_list[0])


def test_fail_arg_names():
    source = """
def f(x, y):
    return x + 1 + y
"""
    tests = [{"input_args": [3, 1], "output": 6}]
    result_list = get_response(source, tests)
    assert len(result_list) == 1
    FailResult.model_validate(result_list[0])
    assert result_list[0].arg_names == ["x", "y"]


def test_fail_arg_names_two_funs():
    source = """
def bar(w, z):
    return w * z

def f(x, y):
    return x + 1 + y
"""
    tests = [{"input_args": [3, 1], "output": 6}]
    result_list = get_response(source, tests, function_name="f")
    assert len(result_list) == 1
    FailResult.model_validate(result_list[0])
    assert result_list[0].arg_names == ["x", "y"]


def test_runtime_arg_names_two_funs():
    source = """
def f(thisIsABigName, thisIsAnotherBigName):
    return x + 1 + y

baz()

def bar(w, z):
    return w * z
"""
    tests = [{"input_args": [3, 1], "output": 6}]
    result_list = get_response(source, tests, function_name="f")
    assert len(result_list) == 1
    RuntimeErrorResult.model_validate(result_list[0])
    assert result_list[0].arg_names == ["thisIsABigName", "thisIsAnotherBigName"]


def test_one_output_arg_success():
    source = """
def f(lst):
    lst.append(42)
"""
    tests = [{"input_args": [[]], "output_args": [[42]]}]
    result_list = get_response(source, tests)
    assert len(result_list) == 1
    SuccessResult.model_validate(result_list[0])


def test_two_output_arg_success():
    source = """
def append_to(a, b):
    a += b
"""
    tests = [
        {"input_args": [[1], [2, 3]], "output_args": [[1, 2, 3], [2, 3]]},
        {"input_args": [[], []], "output_args": [[], []]},
        {"input_args": [[], [2, 3]], "output_args": [[2, 3], [2, 3]]},
    ]
    result_list = get_response(source, tests)
    assert len(result_list) == 3
    SuccessResult.model_validate(result_list[0])
    SuccessResult.model_validate(result_list[1])
    SuccessResult.model_validate(result_list[2])


def test_unequal_length_input_output_arg_lists():
    source = """
def append_to(a, b):
    a += b
"""
    tests = [{"input_args": [[1], [2, 3]], "output_args": [[1, 2, 3]]}]
    with pytest.raises(ValueError) as e:
        get_response(source, tests)
        assert str(e) == "The length of input_args and output_args are not equal"


def test_empty_list_of_tests():
    source = """
def f(lst):
    lst.append(42)
"""
    tests = []
    result_list = get_response(source, tests)
    assert len(result_list) == 0


def test_no_function_in_source():
    source = """
lst.append(42)
"""
    tests = [{"input_args": [1], "output": 2}]
    result_list = get_response(source, tests)
    assert len(result_list) == 1
    SpecificationErrorResult.model_validate(result_list[0])


def test_function_name_not_found():
    source = """
def foo(a):
    return a + 42
"""
    tests = [{"input_args": [1], "output": 43}]
    result_list = get_response(source, tests, function_name="bar")
    assert len(result_list) == 1
    SpecificationErrorResult.model_validate(result_list[0])


def test_wrong_number_of_args_less():
    source = """
def bar(a, b):
    return 10 * a + b

def foo(a, b, c):
    return 10 * a + b

def baz(a):
    return 10 * a + 2
"""
    tests = [{"input_args": [1, 2], "output": 12}]
    result_list = get_response(source, tests, function_name="foo")
    assert len(result_list) == 1
    SpecificationErrorResult.model_validate(result_list[0])


def test_wrong_number_of_args_more():
    source = """
def bar(a, b):
    return 10 * a + b

def foo(a, b, c):
    return 10 * a + b

def baz(a):
    return 10 * a + 2
"""
    tests = [{"input_args": [1, 2], "output": 12}]
    result_list = get_response(source, tests, function_name="baz")
    assert len(result_list) == 1
    SpecificationErrorResult.model_validate(result_list[0])


def test_empty_code():
    source = ""
    tests = [{"input_args": [1, 2], "output": 12}]
    result_list = get_response(source, tests)
    assert len(result_list) == 1
    SpecificationErrorResult.model_validate(result_list[0])


def test_nested_function():
    source = """
    def bar(a, b):
        def foo(a, b):
            return 10 * a + b

        return foo(a, b)
"""
    tests = [{"input_args": [1, 2], "output": 12}]
    result_list = get_response(source, tests)
    assert len(result_list) == 1
    SuccessResult.model_validate(result_list[0])


def test_nested_function_not_found():
    source = """
    def bar(a, b):
        def foo(a, b):
            return 10 * a + b

        return foo(a, b)
"""
    tests = [{"input_args": [1, 2], "output": 12}]
    result_list = get_response(source, tests, function_name="foo")
    assert len(result_list) == 1
    SpecificationErrorResult.model_validate(result_list[0])


def test_recursion_success():
    source = """
    def foo(a):
        if a == 0:
            return 0
        return foo(a - 1)
"""
    tests = [{"input_args": [5], "output": 0}]
    result_list = get_response(source, tests, function_name="foo")
    assert len(result_list) == 1
    SuccessResult.model_validate(result_list[0])


def test_recursion_infinite_error():
    source = """
    def foo(a):
        if a == 0:
            return 0
        return foo(a - 1)
"""
    tests = [{"input_args": [-1], "output": 0}]
    result_list = get_response(source, tests, function_name="foo")
    assert len(result_list) == 1
    RuntimeErrorResult.model_validate(result_list[0])
