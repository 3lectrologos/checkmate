from . import get_response
from checkmate import (
    SuccessResult,
    SpecificationErrorResult,
    RuntimeErrorResult,
)


def test_linked_list_operations_not_available():
    source = """
def f(a):
    while a.has_next():
        a.go_next()
    return a.get_value()
"""
    tests = [{"input_args": [[1, 2, 3]], "output": 3}]
    response, _json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    RuntimeErrorResult.model_validate_json(result_list[0])


def test_linked_list_operations_available():
    source = """
def f(a):
    while a.has_next():
        a.go_next()
    return a.get_value()
"""
    tests = [{"input_args": [[1, 2, 3]], "output": 3}]
    response, _json_list, result_list = get_response(source, tests, is_linked_list=True)
    assert response.status_code == 200
    assert len(result_list) == 1
    SuccessResult.model_validate_json(result_list[0])


def test_when_run_not_found():
    source = """
def f(a):
    while a.has_next():
        a.go_next()
    return a.get_value()
"""
    tests = [{"input_args": [[1, 2, 3]], "output": 3}]
    response, _json_list, result_list = get_response(source, tests, is_level5=True)
    assert response.status_code == 200
    assert len(result_list) == 1
    SpecificationErrorResult.model_validate_json(result_list[0])


def test_when_run_found_list_operations_not_available():
    source = """
def when_run(a):
    while a.has_next():
        a.go_next()
    return a.get_value()
"""
    tests = [{"input_args": [[1, 2, 3]], "output": 3}]
    response, _json_list, result_list = get_response(source, tests, is_level5=True)
    assert response.status_code == 200
    assert len(result_list) == 1
    RuntimeErrorResult.model_validate_json(result_list[0])


def test_when_run_found_list_operations_available():
    source = """
def when_run(a):
    while a.has_next():
        a.go_next()
    return a.get_value()
"""
    tests = [{"input_args": [[1, 2, 3]], "output": 3}]
    response, _json_list, result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert response.status_code == 200
    assert len(result_list) == 1
    SuccessResult.model_validate_json(result_list[0])


def test_linked_list_modification():
    source = """
def when_run(a):
    while a.has_next():
        a.set_value(0)
        a.go_next()
    a.set_value(0)
"""
    tests = [{"input_args": [[1, 2, 3]], "output_args": [[0, 0, 0]]}]
    response, _json_list, result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert response.status_code == 200
    assert len(result_list) == 1
    SuccessResult.model_validate_json(result_list[0])


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
    tests = [{"input_args": [[1, 2, 3], [0, 0, 0]], "output_args": [[3, 2, 1], None]}]
    response, _json_list, result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert response.status_code == 200
    assert len(result_list) == 1
    SuccessResult.model_validate_json(result_list[0])


def test_outer_import_before():
    source = """
import os
def when_run(a):
    while a.has_next():
        a.go_next()
    return a.get_value()
"""
    tests = [{"input_args": [[1, 2, 3]], "output": 3}]
    response, _json_list, result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert response.status_code == 200
    assert len(result_list) == 1
    SpecificationErrorResult.model_validate_json(result_list[0])


def test_outer_import_after():
    source = """
def when_run(a):
    while a.has_next():
        a.go_next()
    return a.get_value()

import numpy
"""
    tests = [{"input_args": [[1, 2, 3]], "output": 3}]
    response, _json_list, result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert response.status_code == 200
    assert len(result_list) == 1
    SpecificationErrorResult.model_validate_json(result_list[0])


def test_inner_import():
    source = """
def when_run(a):
    import os
    while a.has_next():
        import numpy
        a.go_next()
    return a.get_value()
"""
    tests = [{"input_args": [[1, 2, 3]], "output": 3}]
    response, _json_list, result_list = get_response(source, tests, is_linked_list=True, is_level5=True)
    assert response.status_code == 200
    assert len(result_list) == 1
    SpecificationErrorResult.model_validate_json(result_list[0])
