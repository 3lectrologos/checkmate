from . import get_response
from checkmate import ResultType


def test_linked_list_operations_not_available():
    source = """
def f(a):
    while a.has_next():
        a.go_next()
    return a.get_value()
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output": "3"}]
    result_list = get_response(source, tests)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.SPECIFICATION_ERROR


def test_linked_list_operations_available():
    source = """
def f(a):
    while a.has_next():
        a.go_next()
    return a.get_value()
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output": "3"}]
    result_list = get_response(source, tests, is_linked_list=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.SUCCESS


def test_when_run_not_found():
    source = """
def f(a):
    while a.has_next():
        a.go_next()
    return a.get_value()
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output": "3"}]
    result_list = get_response(source, tests, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.SPECIFICATION_ERROR


def test_when_run_found_list_operations_not_available():
    source = """
def when_run(a):
    while a.has_next():
        a.go_next()
    return a.get_value()
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output": "3"}]
    result_list = get_response(source, tests, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.SPECIFICATION_ERROR


def test_when_run_found_list_operations_available():
    source = """
def when_run(a):
    while a.has_next():
        a.go_next()
    return a.get_value()
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output": "3"}]
    result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.SUCCESS


def test_linked_list_modification():
    source = """
def when_run(a):
    while a.has_next():
        a.set_value(0)
        a.go_next()
    a.set_value(0)
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output_args": ["ListPtr([0, 0, 0], None)"]}]
    result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.SUCCESS


def test_linked_list_pointer_location_matters_fail():
    source = """
def when_run(a):
    while a.has_next():
        a.set_value(0)
        a.go_next()
    a.set_value(0)
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output_args": ["ListPtr([0, 0, 0], 0)"]}]
    result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.FAIL


def test_linked_list_pointer_location_matters_success():
    source = """
def when_run(a):
    while a.has_next():
        a.set_value(0)
        a.go_next()
    a.set_value(0)
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output_args": ["ListPtr([0, 0, 0], 2)"]}]
    result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.SUCCESS


def test_only_some_output_args_of_interest():
    source = """
def when_run(a, b):
    while a.has_next():
        b.set_value(a.get_value())
        a.go_next()
        b.go_next()
    b.set_value(a.get_value())
    while b.has_prev():
        b.go_prev()
    while a.has_prev():
        a.set_value(b.get_value())
        a.go_prev()
        b.go_next()
    a.set_value(b.get_value())
"""
    tests = [
        {
            "input_args": ["ListPtr([1, 2, 3], 0)", "ListPtr([0, 0, 0], 0)"],
            "output_args": ["ListPtr([3, 2, 1], None)", None],
        }
    ]
    result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.SUCCESS


def test_outer_import_before():
    source = """
import os
def when_run(a):
    while a.has_next():
        a.go_next()
    return a.get_value()
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output": "3"}]
    result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.SPECIFICATION_ERROR


def test_outer_import_after():
    source = """
def when_run(a):
    while a.has_next():
        a.go_next()
    return a.get_value()

import numpy
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output": "3"}]
    result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.SPECIFICATION_ERROR


def test_inner_import():
    source = """
def when_run(a):
    import os
    while a.has_next():
        import numpy
        a.go_next()
    return a.get_value()
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output": "3"}]
    result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.SPECIFICATION_ERROR


def test_nested_function_import():
    source = """
def when_run(a):
    def foo():
        import os

    while a.has_next():
        import numpy
        a.go_next()
    return a.get_value()
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output": "3"}]
    result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.SPECIFICATION_ERROR


def test_linked_list_out_of_bounds_right():
    source = """
def when_run(a):
    while a.has_next():
        a.set_value(0)
        a.go_next()
    a.set_value(0)
    a.go_next()
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output_args": ["ListPtr([0, 0, 0], None)"]}]
    result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.RUNTIME_ERROR


def test_linked_list_out_of_bounds_left():
    source = """
def when_run(a):
    a.go_prev()
    while a.has_next():
        a.set_value(0)
        a.go_next()
    a.set_value(0)
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output_args": ["ListPtr([0, 0, 0], None)"]}]
    result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.RUNTIME_ERROR


def test_linked_list_invalid_value():
    source = """
def when_run(a):
    a.set_value('foo')
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output_args": ["ListPtr([0, 0, 0], None)"]}]
    result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.RUNTIME_ERROR


def test_linked_list_output_args():
    source = """
def when_run(a):
    return a
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output_args": ["ListPtr([0, 0, 0], 0)"]}]
    result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.FAIL


def test_linked_list_output():
    source = """
def when_run(a):
    while a.has_next():
        a.set_value(0)
        a.go_next()
    a.set_value(0)
    return a
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output": "ListPtr([0, 0, 0], 2)"}]
    result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.SUCCESS


def test_linked_list_output_compared_to_other_type():
    source = """
def when_run(a):
    return [(0, 0, 0), 0]
"""
    tests = [{"input_args": ["ListPtr([1, 2, 3], 0)"], "output": "ListPtr([0, 0, 0], 0)"}]
    result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert len(result_list) == 1
    assert result_list[0].type == ResultType.FAIL
