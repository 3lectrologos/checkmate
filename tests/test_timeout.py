from . import get_response
from checkmate import TimeoutResult, RuntimeErrorResult


def test_inner_timeout():
    source = """
def f(x):
    while True:
        pass
    return x + foo()
"""
    tests = [{"input_args": [1], "output": 2}]
    response, _json_list, result_list = get_response(source, tests, check_timeout=True)
    assert response.status_code == 200
    assert len(result_list) == 1
    TimeoutResult.model_validate_json(result_list[0])


def test_outer_timeout():
    source = """
def f(x):
    return x + 1

while True:
    pass
"""
    tests = [{"input_args": [1], "output": 2}]
    response, _json_list, result_list = get_response(source, tests, check_timeout=True)
    assert response.status_code == 200
    assert len(result_list) == 1
    TimeoutResult.model_validate_json(result_list[0])


def test_timeout_with_exception():
    source = """
def f(x):
    i = 0
    while True:
        i += 1
        if i > 10**6:
            foo()
    return x + foo()
"""
    tests = [{"input_args": [1], "output": 2}]
    response, _json_list, result_list = get_response(source, tests, check_timeout=True)
    assert response.status_code == 200
    assert len(result_list) == 1
    RuntimeErrorResult.model_validate_json(result_list[0])
