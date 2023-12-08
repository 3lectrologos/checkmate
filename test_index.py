import json
from fastapi.testclient import TestClient
from index import app
from index import SuccessResult, SyntaxErrorResult, RuntimeErrorResult, TimeoutResult, FailResult


client = TestClient(app)


def get_response(source, test_json):
    response = client.post(
        '/api/python',
        json={
            'source': source.strip(),
            'testJSON': test_json.strip()
        }
    )
    return response, response.json(), [json.dumps(result) for result in response.json()]


def get_response_with_function_name(source, test_json, function_name):
    response = client.post(
        '/api/python',
        json={
            'source': source.strip(),
            'testJSON': test_json.strip(),
            'functionName': function_name
        }
    )
    return response, response.json(), [json.dumps(result) for result in response.json()]


def test_simple_success():
    response, _json_list, result_list = get_response(
'''
def f(x):
    return x + 1
''',
'''
[{"inputArgs": [1], "outputArgs": [1], "output": 2}]
'''
    )
    assert response.status_code == 200
    assert len(result_list) == 1
    SuccessResult.model_validate_json(result_list[0])


def test_simple_syntax_error():
    response, _json_list, result_list = get_response(
'''
def f(x):
    return x +
''',
'''
[{"inputArgs": [1], "outputArgs": [1], "output": 2}]
'''
    )
    assert response.status_code == 200
    assert len(result_list) == 1
    SyntaxErrorResult.model_validate_json(result_list[0])


def test_simple_runtime_error():
    response, _json_list, result_list = get_response(
'''
def f(x):
    return x + foo()
''',
'''
[{"inputArgs": [1], "outputArgs": [1], "output": 2}]
'''
    )
    assert response.status_code == 200
    assert len(result_list) == 1
    RuntimeErrorResult.model_validate_json(result_list[0])


def test_simple_timeout():
    response, _json_list, result_list = get_response(
'''
def f(x):
    while True:
        pass
    return x + foo()
''',
'''
[{"inputArgs": [1], "outputArgs": [1], "output": 2}]
'''
    )
    assert response.status_code == 200
    assert len(result_list) == 1
    TimeoutResult.model_validate_json(result_list[0])


def test_outside_runtime_error():
    response, _json_list, result_list = get_response(
'''
def f(x):
    return x + 1\nfoo()
''',
'''
[{"inputArgs": [1], "outputArgs": [1], "output": 2}]
'''
    )
    assert response.status_code == 200
    assert len(result_list) == 1
    RuntimeErrorResult.model_validate_json(result_list[0])


def test_simple_fail():
    response, _json_list, result_list = get_response(
'''
def f(x):
    return x + 2
''',
'''
[{"inputArgs": [1], "outputArgs": [1], "output": 2}]
'''
    )
    assert response.status_code == 200
    assert len(result_list) == 1
    FailResult.model_validate_json(result_list[0])


def test_fail_arg_names():
    response, json_list, result_list = get_response(
'''
def f(x, y):
    return x + 1 + y
''',
'''
[{"inputArgs": [3, 1], "outputArgs": [3, 1], "output": 6}]
'''
    )
    assert response.status_code == 200
    assert len(result_list) == 1
    FailResult.model_validate_json(result_list[0])
    assert json_list[0]['argNames'] == ['x', 'y']


def test_fail_arg_names_two_funs():
    response, json_list, result_list = get_response_with_function_name(
'''
def bar(w, z):
    return w * z

def f(x, y):
    return x + 1 + y
''',
'''
[{"inputArgs": [3, 1], "outputArgs": [3, 1], "output": 6}]
''',
'f'
    )
    assert response.status_code == 200
    assert len(result_list) == 1
    FailResult.model_validate_json(result_list[0])
    assert json_list[0]['argNames'] == ['x', 'y']


def test_runtime_arg_names_two_funs():
    response, json_list, result_list = get_response_with_function_name(
'''
def f(thisIsABigName, thisIsAnotherBigName):
    return x + 1 + y

baz()

def bar(w, z):
    return w * z
''',
'''
[{"inputArgs": [3, 1], "outputArgs": [3, 1], "output": 6}]
''',
'f'
    )
    assert response.status_code == 200
    assert len(result_list) == 1
    RuntimeErrorResult.model_validate_json(result_list[0])
    assert json_list[0]['argNames'] == ['thisIsABigName', 'thisIsAnotherBigName']
