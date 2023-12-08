import re
import json
import sys
import traceback
import inspect
from enum import Enum
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional, Literal, Union, List, Annotated
from pathos.multiprocessing import ProcessingPool
from multiprocess.context import TimeoutError


TIMEOUT_SECONDS = 3


class LinkedListError(Exception):
    pass


class ListPtr:
    def __init__(self, lst, start_idx=0):
        self._lst = list(lst)
        self._idx = start_idx
        self._MAX_VAL = 99
        self._MIN_VAL = -99

    def __repr__(self):
        return repr(self._lst)

    def go_next(self):
        if self._idx < len(self._lst) - 1:
            self._idx += 1
        else:
            caller_lineno = inspect.getframeinfo(inspect.stack()[1][0]).lineno
            raise LinkedListError(f'Line {caller_lineno}: Cannot \'go_next\' at the end of linked list')

    def go_prev(self):
        if self._idx > 0:
            self._idx -= 1
        else:
            caller_lineno = inspect.getframeinfo(inspect.stack()[1][0]).lineno
            raise LinkedListError(f'Line {caller_lineno}: Cannot \'go_prev\' at the start of linked list')

    def has_next(self):
        return self._idx < len(self._lst) - 1

    def has_prev(self):
        return self._idx > 0

    def get_value(self):
        return self._lst[self._idx]

    def set_value(self, value):
        if isinstance(value, int) and self._MIN_VAL <= value <= self._MAX_VAL:
            self._lst[self._idx] = value
        else:
            caller_lineno = inspect.getframeinfo(inspect.stack()[1][0]).lineno
            raise LinkedListError(f'Line {caller_lineno}: List values must be integers between -99 and 99')


class RequestData(BaseModel):
    source: str
    testJSON: str
    functionName: Optional[str] = None
    isLinkedList: Optional[bool] = False
    isLevel5: Optional[bool] = False


class ResultType(str, Enum):
    SYNTAX_ERROR = 'syntax_error'
    RUNTIME_ERROR = 'runtime_error'
    TIMEOUT = 'timeout'
    FAIL = 'fail'
    SUCCESS = 'success'


class BaseErrorResult(BaseModel):
    argNames: list[str]
    args: list[str]
    expected: str


class SyntaxErrorResult(BaseErrorResult):
    type: Literal[ResultType.SYNTAX_ERROR] = ResultType.SYNTAX_ERROR
    error: str


class RuntimeErrorResult(BaseErrorResult):
    type: Literal[ResultType.RUNTIME_ERROR] = ResultType.RUNTIME_ERROR
    error: str


class TimeoutResult(BaseErrorResult):
    type: Literal[ResultType.TIMEOUT] = ResultType.TIMEOUT


class FailResult(BaseErrorResult):
    type: Literal[ResultType.FAIL] = ResultType.FAIL
    result: str


class SuccessResult(BaseModel):
    type: Literal[ResultType.SUCCESS] = ResultType.SUCCESS


Result = Annotated[
    Union[SuccessResult, SyntaxErrorResult, RuntimeErrorResult, TimeoutResult, FailResult],
    Field(discriminator='type')
]


def first_function_name(source):
    match = re.match(r'\s*def \s*(\w+)\s*\(([^)]*)\)', source)
    return match.group(1)


def get_arg_names(source, function_name):
    match = re.findall(fr'def\s+{function_name}\s*\(([^)]*)\)', source)
    return [arg.strip() for arg in match[0].split(',')]


def string_to_lambda(source, function_name):
    custom_namespace = {}
    exec(source, custom_namespace)
    return lambda *args: custom_namespace[function_name](*args)


def transform_args(input_args, is_linked_list):
    result = []
    for arg in input_args:
        if is_linked_list and isinstance(arg, list):
            result.append(ListPtr(arg))
        else:
            result.append(arg)
    return result


app = FastAPI()


def get_error_string(exc_info):
    exc_type, exc_value, exc_traceback = exc_info
    line_number = traceback.extract_tb(exc_traceback)[-1].lineno
    error_string = traceback.format_exception_only(exc_type, exc_value)[-1].strip()
    return f'Line {line_number}. {error_string}'


def run_with_timeout(fun, timeout_seconds, *args):
    with ProcessingPool() as pool:
        result = pool.apipe(fun, *args)
        return result.get(timeout=timeout_seconds)


def run_one(source, test, function_name, is_linked_list=False, is_level_5=False) -> Result:
    input_args, output_args, expected = test['inputArgs'], test['outputArgs'], test['output']
    input_args = transform_args(input_args, is_linked_list)
    fresh_input_args = transform_args(input_args, is_linked_list)
    error_dict = {
        'argNames': get_arg_names(source, function_name),
        'args': [repr(arg) for arg in fresh_input_args],
        'expected': repr(expected),
    }
    try:
        compile(source, '<string>', 'exec')
    except Exception:
        error_string = get_error_string(sys.exc_info())
        return SyntaxErrorResult(error=error_string, **error_dict)
    try:
        fun = string_to_lambda(source, function_name)
        result = run_with_timeout(fun, TIMEOUT_SECONDS, *input_args)
    except TimeoutError:
        error_dict['type'] = 'timeout'
        return TimeoutResult(**error_dict)
    except Exception:
        error_string = get_error_string(sys.exc_info())
        return RuntimeErrorResult(error=error_string, **error_dict)
    if result != expected:
        return FailResult(result=repr(result), **error_dict)
    return SuccessResult()


@app.post('/api/python')
def run_tests(request: RequestData) -> List[Result]:
    function_name = first_function_name(request.source) if (request.functionName is None) else request.functionName
    test_list = json.loads(request.testJSON)
    results = []
    for test in test_list:
        result = run_one(request.source, test, function_name, request.isLinkedList, request.isLevel5)
        results.append(result)
    return results
