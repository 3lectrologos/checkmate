import json
from fastapi.testclient import TestClient
from index import app
from index import SuccessResult, SyntaxErrorResult, RuntimeErrorResult, TimeoutResult, FailResult


client = TestClient(app)


def get_response(source, tests):
    response = client.post(
        '/api/python',
        json={
            'source': source.strip(),
            'tests': tests
        }
    )
    return response, response.json(), [json.dumps(result) for result in response.json()]


def get_response_with_function_name(source, tests, function_name):
    response = client.post(
        '/api/python',
        json={
            'source': source.strip(),
            'tests': tests,
            'functionName': function_name
        }
    )
    return response, response.json(), [json.dumps(result) for result in response.json()]


def test_simple_success():
    source = '''
def f(x):
    return x + 1
'''
    tests = [{"inputArgs": [1], "outputArgs": [1], "output": 2}]
    response, _json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    SuccessResult.model_validate_json(result_list[0])


def test_simple_syntax_error():
    source = '''
def f(x):
    return x +
'''
    tests = [{"inputArgs": [1], "outputArgs": [1], "output": 2}]
    response, _json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    SyntaxErrorResult.model_validate_json(result_list[0])


def test_simple_runtime_error():
    source = '''
def f(x):
    return x + foo()
'''
    tests = [{"inputArgs": [1], "outputArgs": [1], "output": 2}]
    response, _json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    RuntimeErrorResult.model_validate_json(result_list[0])


def test_simple_timeout():
    source = '''
def f(x):
    while True:
        pass
    return x + foo()
'''
    tests = [{"inputArgs": [1], "outputArgs": [1], "output": 2}]
    response, _json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    TimeoutResult.model_validate_json(result_list[0])


def test_outside_runtime_error():
    source = '''
def f(x):
    return x + 1

foo()
'''
    tests = [{"inputArgs": [1], "outputArgs": [1], "output": 2}]
    response, _json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    RuntimeErrorResult.model_validate_json(result_list[0])


def test_simple_fail():
    source = '''
def f(x):
    return x + 2
'''
    tests = [{"inputArgs": [1], "outputArgs": [1], "output": 2}]
    response, _json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    FailResult.model_validate_json(result_list[0])


def test_fail_arg_names():
    source = '''
def f(x, y):
    return x + 1 + y
'''
    tests = [{"inputArgs": [3, 1], "outputArgs": [3, 1], "output": 6}]
    response, json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    FailResult.model_validate_json(result_list[0])
    assert json_list[0]['argNames'] == ['x', 'y']


def test_fail_arg_names_two_funs():
    source = '''
def bar(w, z):
    return w * z

def f(x, y):
    return x + 1 + y
'''
    tests = [{"inputArgs": [3, 1], "outputArgs": [3, 1], "output": 6}]
    response, json_list, result_list = get_response_with_function_name(source, tests, 'f')
    assert response.status_code == 200
    assert len(result_list) == 1
    FailResult.model_validate_json(result_list[0])
    assert json_list[0]['argNames'] == ['x', 'y']


def test_runtime_arg_names_two_funs():
    source = '''
def f(thisIsABigName, thisIsAnotherBigName):
    return x + 1 + y

baz()

def bar(w, z):
    return w * z
'''
    tests = [{"inputArgs": [3, 1], "outputArgs": [3, 1], "output": 6}]
    response, json_list, result_list = get_response_with_function_name(source, tests, 'f')
    assert response.status_code == 200
    assert len(result_list) == 1
    RuntimeErrorResult.model_validate_json(result_list[0])
    assert json_list[0]['argNames'] == ['thisIsABigName', 'thisIsAnotherBigName']


def test_one_output_arg_success():
    source = '''
def f(lst):
    lst.append(42)
'''
    tests = [{"inputArgs": [[]], "outputArgs": [[42]]}]
    response, json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    SuccessResult.model_validate_json(result_list[0])


def test_two_output_arg_success():
    source = '''
def append_to(a, b):
    a += b
'''
    tests = [
        {"inputArgs": [[1], [2, 3]], "outputArgs": [[1, 2, 3], [2, 3]]},
        {"inputArgs": [[], []], "outputArgs": [[], []]},
        {"inputArgs": [[], [2, 3]], "outputArgs": [[2, 3], [2, 3]]},
    ]
    response, json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 3
    SuccessResult.model_validate_json(result_list[0])
    SuccessResult.model_validate_json(result_list[1])
    SuccessResult.model_validate_json(result_list[2])


def test_unequal_length_input_output_arg_lists():
    source = '''
def append_to(a, b):
    a += b
'''
    tests = [
        {"inputArgs": [[1], [2, 3]], "outputArgs": [[1, 2, 3]]},
    ]
    response, json_list, result_list = get_response(source, tests)
    print(response.content)
    assert response.status_code == 422
