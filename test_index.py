import json
from fastapi.testclient import TestClient
from index import app
from index import SuccessResult, SyntaxErrorResult, RuntimeErrorResult, TimeoutResult, FailResult


client = TestClient(app)


def get_response(source, tests, **kwargs):
    request_args = {'source': source.strip(), 'tests': tests}
    response = client.post('/api/python', json=dict(**request_args, **kwargs))
    return response, response.json(), [json.dumps(result) for result in response.json()]


def test_simple_success():
    source = '''
def f(x):
    return x + 1
'''
    tests = [{"input_args": [1], "output": 2}]
    response, _json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    SuccessResult.model_validate_json(result_list[0])


def test_simple_success_with_output_args():
    source = '''
def f(x):
    return x + 1
'''
    tests = [{"input_args": [1], "output_args": [1], "output": 2}]
    response, _json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    SuccessResult.model_validate_json(result_list[0])


def test_simple_fail_with_output_args():
    source = '''
def f(x):
    return x + 1
'''
    tests = [{"input_args": [1], "output_args": [2], "output": 2}]
    response, _json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    FailResult.model_validate_json(result_list[0])


def test_simple_syntax_error():
    source = '''
def f(x):
    return x +
'''
    tests = [{"input_args": [1], "output": 2}]
    response, _json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    SyntaxErrorResult.model_validate_json(result_list[0])


def test_simple_runtime_error():
    source = '''
def f(x):
    return x + foo()
'''
    tests = [{"input_args": [1], "output": 2}]
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
    tests = [{"input_args": [1], "output": 2}]
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
    tests = [{"input_args": [1], "output": 2}]
    response, _json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    RuntimeErrorResult.model_validate_json(result_list[0])


def test_simple_fail():
    source = '''
def f(x):
    return x + 2
'''
    tests = [{"input_args": [1], "output": 2}]
    response, _json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    FailResult.model_validate_json(result_list[0])


def test_fail_arg_names():
    source = '''
def f(x, y):
    return x + 1 + y
'''
    tests = [{"input_args": [3, 1], "output": 6}]
    response, json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    FailResult.model_validate_json(result_list[0])
    assert json_list[0]['arg_names'] == ['x', 'y']


def test_fail_arg_names_two_funs():
    source = '''
def bar(w, z):
    return w * z

def f(x, y):
    return x + 1 + y
'''
    tests = [{"input_args": [3, 1], "output": 6}]
    response, json_list, result_list = get_response(source, tests, function_name='f')
    assert response.status_code == 200
    assert len(result_list) == 1
    FailResult.model_validate_json(result_list[0])
    assert json_list[0]['arg_names'] == ['x', 'y']


def test_runtime_arg_names_two_funs():
    source = '''
def f(thisIsABigName, thisIsAnotherBigName):
    return x + 1 + y

baz()

def bar(w, z):
    return w * z
'''
    tests = [{"input_args": [3, 1], "output": 6}]
    response, json_list, result_list = get_response(source, tests, function_name='f')
    assert response.status_code == 200
    assert len(result_list) == 1
    RuntimeErrorResult.model_validate_json(result_list[0])
    assert json_list[0]['arg_names'] == ['thisIsABigName', 'thisIsAnotherBigName']


def test_one_output_arg_success():
    source = '''
def f(lst):
    lst.append(42)
'''
    tests = [{"input_args": [[]], "output_args": [[42]]}]
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
        {"input_args": [[1], [2, 3]], "output_args": [[1, 2, 3], [2, 3]]},
        {"input_args": [[], []], "output_args": [[], []]},
        {"input_args": [[], [2, 3]], "output_args": [[2, 3], [2, 3]]},
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
    tests = [{"input_args": [[1], [2, 3]], "output_args": [[1, 2, 3]]}]
    response, json_list, result_list = get_response(source, tests)
    assert response.status_code == 422


def test_empty_list_of_tests():
    source = '''
def f(lst):
    lst.append(42)
'''
    tests = []
    response, json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 0


def test_no_function_in_source():
    source = '''
lst.append(42)
'''
    tests = [{"input_args": [1], "output": 2}]
    response, json_list, result_list = get_response(source, tests)
    assert response.status_code == 200
    assert len(result_list) == 1
    SyntaxErrorResult.model_validate_json(result_list[0])


def test_function_name_not_found():
    source = '''
def foo(a):
    return a + 42
'''
    tests = [{"input_args": [1], "output": 43}]
    response, json_list, result_list = get_response(source, tests, function_name='bar')
    assert response.status_code == 200
    assert len(result_list) == 1
    print(result_list[0])
    SyntaxErrorResult.model_validate_json(result_list[0])


def test_wrong_number_of_args_less():
    source = '''
def bar(a, b):
    return 10 * a + b

def foo(a, b, c):
    return 10 * a + b

def baz(a):
    return 10 * a + 2
'''
    tests = [{"input_args": [1, 2], "output": 12}]
    response, json_list, result_list = get_response(source, tests, function_name='foo')
    assert response.status_code == 200
    assert len(result_list) == 1
    SyntaxErrorResult.model_validate_json(result_list[0])


def test_wrong_number_of_args_more():
    source = '''
def bar(a, b):
    return 10 * a + b

def foo(a, b, c):
    return 10 * a + b

def baz(a):
    return 10 * a + 2
'''
    tests = [{"input_args": [1, 2], "output": 12}]
    response, json_list, result_list = get_response(source, tests, function_name='baz')
    assert response.status_code == 200
    assert len(result_list) == 1
    SyntaxErrorResult.model_validate_json(result_list[0])