# Checkmate

[![CI](https://github.com/3lectrologos/checkmate/actions/workflows/CI.yml/badge.svg)](https://github.com/3lectrologos/checkmate/actions/workflows/CI.yml)
![Codecov](https://img.shields.io/codecov/c/gh/3lectrologos/checkmate)
![version](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2F3lectrologos%2Fcheckmate%2Fmain%2Fpyproject.toml)
[![license](https://img.shields.io/github/license/3lectrologos/checkmate.svg)](https://github.com/3lectrologos/checkmate/blob/main/LICENSE)

An API for testing a Python function on an input / output suite.


## Local use (no server)
Install from GitHub:
```bash
python -m pip install 'checkmate@git+https://github.com/3lectrologos/checkmate.git'
```

Example:
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
    {"input_args": [1, 0], "output": 1}
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