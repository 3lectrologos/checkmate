# Checkmate

[![CI](https://github.com/3lectrologos/checkmate/actions/workflows/CI.yml/badge.svg)](https://github.com/3lectrologos/checkmate/actions/workflows/CI.yml)
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
from checkmate import Request, run_tests


source = """
def add(x, y):
    return x + y
"""

tests = [
    {"input_args": [1], "output": 2},
    {"input_args": [2], "output": 4},
]

request = Request(source=source, tests=tests)
result = run_tests(request)
for res in result:
    print(res.type)
#
#
```