import re
import sys
import traceback
import inspect
from enum import Enum
from fastapi import FastAPI
from pydantic import BaseModel, Field
from pydantic.functional_validators import model_validator
from typing import Optional, Literal, Union, List, Annotated, Any
from pathos.multiprocessing import ProcessingPool
from multiprocess.context import TimeoutError
import syntax_check


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


class Test(BaseModel):
    input_args: list[Any]
    output_args: Optional[list[Any]] = None
    output: Optional[Any] = None

    @model_validator(mode='after')
    def check_input_output_same_length(self):
        if self.output_args is not None and len(self.input_args) != len(self.output_args):
            raise ValueError('The length of input_args and output_args are not equal')
        return self


class RequestData(BaseModel):
    source: str
    tests: list[Test]
    function_name: Optional[str] = None
    is_linked_list: Optional[bool] = False
    is_level5: Optional[bool] = False


class ResultType(str, Enum):
    SYNTAX_ERROR = 'syntax_error'
    RUNTIME_ERROR = 'runtime_error'
    TIMEOUT = 'timeout'
    FAIL = 'fail'
    SUCCESS = 'success'


class BaseErrorResult(BaseModel):
    arg_names: list[str]
    input_args: list[str]
    expected_output_args: Optional[list[str]] = None
    expected_output: str


class SyntaxErrorResult(BaseModel):
    type: Literal[ResultType.SYNTAX_ERROR] = ResultType.SYNTAX_ERROR
    error: str


class RuntimeErrorResult(BaseErrorResult):
    type: Literal[ResultType.RUNTIME_ERROR] = ResultType.RUNTIME_ERROR
    error: str


class TimeoutResult(BaseErrorResult):
    type: Literal[ResultType.TIMEOUT] = ResultType.TIMEOUT


class FailResult(BaseErrorResult):
    type: Literal[ResultType.FAIL] = ResultType.FAIL
    output_args: list[str]
    output: str


class SuccessResult(BaseModel):
    type: Literal[ResultType.SUCCESS] = ResultType.SUCCESS


Result = Annotated[
    Union[SuccessResult, SyntaxErrorResult, RuntimeErrorResult, TimeoutResult, FailResult],
    Field(discriminator='type')
]


def string_to_lambda(source, function_name):
    custom_namespace = {}
    exec(source, custom_namespace)
    return lambda *args: custom_namespace[function_name](*args)


def transform_args(input_args, is_linked_list):
    if input_args is None:
        return None
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


def run_one(source, test, function_name, is_linked_list=False, is_level5=False) -> Result:
    input_args = transform_args(test.input_args, is_linked_list)
    timeout_input_args = transform_args(test.input_args, is_linked_list)
    output_args = transform_args(test.output_args, is_linked_list)
    error_dict = {
        'input_args': [repr(arg) for arg in input_args],
        'expected_output': repr(test.output),
    }
    if output_args is not None:
        error_dict['expected_output_args'] = [repr(arg) for arg in output_args]
    try:
        compile(source, '<string>', 'exec')
        function_name, arg_names = syntax_check.check_specification(source, input_args, function_name, is_level5)
        error_dict['arg_names'] = arg_names
    except Exception:
        error_string = get_error_string(sys.exc_info())
        return SyntaxErrorResult(error=error_string)
    try:
        fun = string_to_lambda(source, function_name)
        run_with_timeout(fun, TIMEOUT_SECONDS, *timeout_input_args)
    except TimeoutError:
        return TimeoutResult(**error_dict)
    except Exception:
        pass
    try:
        fun = string_to_lambda(source, function_name)
        result = fun(*input_args)
    except Exception:
        error_string = get_error_string(sys.exc_info())
        return RuntimeErrorResult(error=error_string, **error_dict)
    if result != test.output:
        return FailResult(output=repr(result), output_args=[repr(arg) for arg in input_args], **error_dict)
    if output_args is not None:
        for i in range(len(output_args)):
            if input_args[i] != output_args[i]:
                return FailResult(output=repr(result), output_args=[repr(arg) for arg in input_args], **error_dict)
    return SuccessResult()


@app.post('/api/python')
def run_tests(request: RequestData) -> List[Result]:
    results = []
    for test in request.tests:
        result = run_one(request.source, test, request.function_name, request.is_linked_list, request.is_level5)
        results.append(result)
    return results
