# Checkmate

[![CI](https://github.com/machine-teaching-group/checkmate/actions/workflows/CI.yml/badge.svg)](https://github.com/machine-teaching-group/checkmate/actions/workflows/CI.yml)
![Codecov](https://img.shields.io/codecov/c/gh/machine-teaching-group/checkmate)
![version](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fmachine-teaching-group%2Fcheckmate%2Fmain%2Fpyproject.toml)
[![license](https://img.shields.io/github/license/machine-teaching-group/checkmate.svg)](https://github.com/machine-teaching-group/checkmate/blob/main/LICENSE)

A library for executing a test suite on one or more Python functions.


## Install
```bash
python -m pip install 'checkmate@git+https://github.com/machine-teaching-group/checkmate.git'
```

## Getting started
```python
import pprint
from checkmate import Request, run_tests


source = """
def add(x, y):
    return x / y
"""


tests = [
    {"input_args": ["2", "2"], "output": "1"},
    {"input_args": ["3", "1"], "output": "2"},
    {"input_args": ["1"], "output": "1"},
    {"input_args": ["1", "0"], "output": "1"},
]


if __name__ == '__main__':
    request = Request(source=source, tests=tests)
    results = run_tests(request)
    for result in results:
        pprint.pprint(result.dict())
        print()

#> {'type': <ResultType.SUCCESS: 'success'>}

#> {'arg_names': ['x', 'y'],
#> 'expected_output': '2',
#> 'expected_output_args': None,
#> 'function_name': 'add',
#> 'input_args': ['3', '1'],
#> 'output': '3.0',
#> 'output_args': ['3', '1'],
#> 'type': <ResultType.FAIL: 'fail'>}

#> {'error': "Line 1. Function 'add' accepts 1 argument, but was given 2",
#> 'type': <ResultType.SPECIFICATION_ERROR: 'specification_error'>}

#> {'arg_names': ['x', 'y'],
#> 'error': 'Line 2. ZeroDivisionError: division by zero',
#> 'expected_output': '1',
#> 'expected_output_args': None,
#> 'function_name': 'add',
#> 'input_args': ['1', '0'],
#> 'type': <ResultType.RUNTIME_ERROR: 'runtime_error'>}
```

## Test fields
Each test is a dictionary with the following fields:
* `input_args`: a list of input arguments
* `output_args`: a list of expected values of the input arguments after the function has executed (optional)
* `output`: the expected return value of the function (optional)
* `function_name`: the name of the function to run the test on (optional)

All arguments and outputs are strings, which are converted to the appropriate types before running the test.
If `output_args` or `output` are not specified, they are not checked, that is, any value is considered correct.
Furthermore, any element of `output_args` can be `None`, in which case the value of that element is not checked.

```python
import pprint
from checkmate import Request, run_tests


source = """
def append_to(a, b):
    a += b
"""


tests = [
    {"input_args": ["[1]", "[2, 3]"], "output_args": ["[1, 2, 3]", None]},
]


if __name__ == '__main__':
    request = Request(source=source, tests=tests)
    results = run_tests(request)
    for result in results:
        pprint.pprint(result.dict())
        print()

#> {'type': <ResultType.SUCCESS: 'success'>}
```

### Function name precedence
If `function_name` is not specified on the test level, then the value from `Request.function_name` is used (see below).
If `Request.function_name` is not specified, the first top-level function in the source is run.
If `Request.is_level5` is `True`, all `function_name` values are ignored and the function name is fixed to `"when_run"`.

## Request parameters

### Specifying which function to run
Use `Request.function_name` to specify the name of the function on which to run all tests.
This is equivalent to specifying `function_name` in each test.
Setting `function_name` in a test will override this value.

```python
import pprint
from checkmate import Request, run_tests


source = """
def foo(a):
    return a + 1

def bar(a):
    return a - 1
"""


tests = [
    {"input_args": ["42"], "output": "43"},
    {"input_args": ["42"], "output": "41", "function_name": "bar"},
]


if __name__ == '__main__':
    request = Request(source=source, tests=tests, function_name="foo")
    results = run_tests(request)
    for result in results:
        pprint.pprint(result.dict())
        print()

#> {'type': <ResultType.SUCCESS: 'success'>}

#> {'type': <ResultType.SUCCESS: 'success'>}
```

### L5 checks
Set `Request.is_level5` to `True` to enable additional L5-specific checks (default is `False`).
This fixes the function name to `"when_run"`, and disallows any import statements in the user code.


### L5 linked lists
Set `Request.is_linked_list` to `True` to enable custom L5 linked lists (default is `False`).
You can then specify linked list arguments in the form `ListPtr([1, 2, 3], 0)`, where the first element contains the list values, and the second the location of the pointer.

The pointer location for `output_args` and `output` can be `None`, in which case any location is considered correct.
```python
import pprint
from checkmate import Request, run_tests


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


tests = [{
    "input_args": ["ListPtr([1, 2, 3], 0)"],
    "output_args": ["ListPtr([0, 0, 0], None)"],
    "output": 6
}]


if __name__ == '__main__':
    request = Request(source=source, tests=tests, is_level5=True, is_linked_list=True)
    results = run_tests(request)
    for result in results:
        pprint.pprint(result.dict())
        print()

#> {'type': <ResultType.SUCCESS: 'success'>}
```


### Timeout checks
Set `Request.check_timeout` to `False` to disable timeout checks (default is `True`).
This may result in faster test runs, because it avoids spawning a separate process for each test.
But it will also not interrupt infinite loops, so use with caution.

## Additional notes

### Running in the main module
When running on Windows, the code that calls `run_tests` should be in the main module, due to the use of Python multiprocessing.
For more details, see [https://docs.python.org/3/library/multiprocessing.html#programming-guidelines](https://docs.python.org/3/library/multiprocessing.html#programming-guidelines).