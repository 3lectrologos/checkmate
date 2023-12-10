# Checkmate

[![CI](https://github.com/machine-teaching-group/checkmate/actions/workflows/CI.yml/badge.svg)](https://github.com/machine-teaching-group/checkmate/actions/workflows/CI.yml)
![Codecov](https://img.shields.io/codecov/c/gh/machine-teaching-group/checkmate)
![version](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fmachine-teaching-group%2Fcheckmate%2Fmain%2Fpyproject.toml)
[![license](https://img.shields.io/github/license/machine-teaching-group/checkmate.svg)](https://github.com/machine-teaching-group/checkmate/blob/main/LICENSE)

An API for testing a Python function on an input / output suite.


## Use locally without a server
Go for this option if you want to call checkmate on your machine from your own Python code.

### Install
```bash
python -m pip install 'checkmate@git+https://github.com/machine-teaching-group/checkmate.git'
```

### Usage example
```python
import pprint
from checkmate import Request, run_tests


source = """
def add(x, y):
    return x / y
"""


tests = [
    {"input_args": [2, 2], "output": 1},
    {"input_args": [3, 1], "output": 2},
    {"input_args": [1], "output": 1},
    {"input_args": [1, 0], "output": 1},
]


if __name__ == '__main__':
    request = Request(source=source, tests=tests)
    results = run_tests(request)
    for result in results:
        pprint.pprint(result.model_dump())
        print()

#> {'type': <ResultType.SUCCESS: 'success'>}
#> 
#> {'arg_names': ['x', 'y'],
#>  'expected_output': '2',
#>  'expected_output_args': None,
#>  'input_args': ['3', '1'],
#>  'output': '3.0',
#>  'output_args': ['3', '1'],
#>  'type': <ResultType.FAIL: 'fail'>}
#> 
#> {'error': "Line 1. Function 'add' accepts 1 argument, but was given 2",
#>  'type': <ResultType.SPECIFICATION_ERROR: 'specification_error'>}
#> 
#> {'arg_names': ['x', 'y'],
#>  'error': 'Line 2. ZeroDivisionError: division by zero',
#>  'expected_output': '1',
#>  'expected_output_args': None,
#>  'input_args': ['1', '0'],
#>  'type': <ResultType.RUNTIME_ERROR: 'runtime_error'>}
```

### Output value
If skipped, field `output` defaults to `None`.
This is useful for functions that are not expected to return anything (see next point).

### Input arguments mutated by the function
Use field `output_args` in the test to check for argument values after the function has run.
Use `None` for any output argument that should not be checked.
Omitting `output_args` is equivalent to `None` for all arguments.
```python
source = """
def append_to(a, b):
    a += b
"""


tests = [
    {"input_args": [[1], [2, 3]], "output_args": [[1, 2, 3], None]},
]
```

## `Request` parameters

### Specifying which function to run
Use `Request.function_name` to specify the name of the function on which to run the tests.
By default, if `is_level5` is `True` (see L5 explanation below), then `function_name` is fixed to be `"when_run"`,
otherwise the first top-level function in the source is run.

```python
from checkmate import Request, run_tests, ResultType


source = """
def foo(a):
    return a + 1

def bar(a):
    return a - 1
"""


tests = [
    {"input_args": [42], "output_args": [41]},
]


if __name__ == '__main__':
    request = Request(source=source, tests=tests, function_name="bar")
    results = run_tests(request)
    assert results[0].type == ResultType.SUCCESS
```


### L5 checks
Set `Request.is_level5` to `True` to enable additional L5-specific checks (default is `False`).
This fixes the function name to `"when_run"` and disallows any user import statements.


### L5 linked lists
Set `Request.is_linked_list` to `True` to enable custom L5 linked lists (default is `False`).
Any list in `input_args` or `output_args` will then be converted to a L5 linked list,
and all L5 linked list operations are available to use.
```python
from checkmate import Request, run_tests, ResultType


source = """
def when_run(a):
    list_sum = 0
    while a.has_next():
        list_sum += a.get_value()
        a.set_value(0)
        a.go_next()
    list_sum += a.get_value()
    a.set_value(0)
    return list_sum
"""


tests = [
    {"input_args": [[1, 2, 3]], "output_args": [[0, 0, 0]], "output": 6},
]


if __name__ == '__main__':
    request = Request(source=source, tests=tests, is_level5=True, is_linked_list=True)
    results = run_tests(request)
    assert results[0].type == ResultType.SUCCESS
```


### Timeout checks
Set `Request.check_timeout` to `False` to disable timeout checks (default is `True`).
This may result in faster test runs, because it avoids spawning a separate process for each test.
But it will also not interrupt infinite loops, so use with caution.


## Run local server
Go for this option if you want to call checkmate using HTTP requests, e.g., from non-Python code.

### Install
```bash
python -m pip install 'checkmate[api]@git+https://github.com/machine-teaching-group/checkmate.git'
```

### Run server
```bash
uvicorn checkmate:app
```

### Example
```python
import httpx
import json


url = 'http://127.0.0.1:8000/checkmate'


source = """
def foo(x):
    return x + 1
"""


tests = [
    {"input_args": [41], "output": 42},
]


request_data = {
    'source': source,
    'tests': tests,
}


post_result = httpx.post(url, data=json.dumps(request_data))
results = json.loads(post_result.content)
assert results[0]['type'] == 'success'
```

### FastAPI docs
Go to `http://127.0.0.1:8000/docs/` to see the FastAPI docs and try out example requests.