import sys
import traceback
import functools
import multiprocessing
from enum import Enum
from fastapi import FastAPI
from pydantic import BaseModel, Field
from pydantic.functional_validators import model_validator
from typing import Optional, Literal, Union, Annotated, Any

from .spec_check import check_specification, SpecificationError
from .linked_list import ListPtr


TIMEOUT_SECONDS = 4


class Test(BaseModel):
    input_args: list[Any]
    output_args: Optional[list[Any]] = None
    output: Optional[Any] = None

    @model_validator(mode="after")
    def check_input_output_same_length(self):
        if self.output_args is not None and len(self.input_args) != len(self.output_args):
            raise ValueError("The length of input_args and output_args are not equal")
        return self


class Request(BaseModel):
    source: str
    tests: list[Test]
    function_name: Optional[str] = None
    is_linked_list: Optional[bool] = False
    is_level5: Optional[bool] = False
    check_timeout: Optional[bool] = True


class ResultType(str, Enum):
    SYNTAX_ERROR = "syntax_error"
    SPECIFICATION_ERROR = "specification_error"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    FAIL = "fail"
    SUCCESS = "success"


class BaseErrorResult(BaseModel):
    arg_names: list[str]
    input_args: list[str]
    expected_output_args: Optional[list[str]] = None
    expected_output: str


class SyntaxErrorResult(BaseModel):
    type: Literal[ResultType.SYNTAX_ERROR] = ResultType.SYNTAX_ERROR
    error: str


class SpecificationErrorResult(BaseModel):
    type: Literal[ResultType.SPECIFICATION_ERROR] = ResultType.SPECIFICATION_ERROR
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
    Union[SuccessResult, SyntaxErrorResult, SpecificationErrorResult, RuntimeErrorResult, TimeoutResult, FailResult],
    Field(discriminator="type"),
]


def string_to_lambda(source, function_name):
    custom_namespace = {}
    exec(source, custom_namespace)
    return functools.partial(custom_namespace[function_name])


def worker(source, function_name, args):
    try:
        fun = string_to_lambda(source, function_name)
        fun(*args)
    except Exception:
        pass


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


def get_error_string(exc_info):
    exc_type, exc_value, exc_traceback = exc_info
    line_number = traceback.extract_tb(exc_traceback)[-1].lineno
    error_string = traceback.format_exception_only(exc_type, exc_value)[-1].strip()
    return f"Line {line_number}. {error_string}"


def run_one(source, test, function_name, is_linked_list, is_level5, check_timeout) -> Result:
    input_args = transform_args(test.input_args, is_linked_list)
    timeout_input_args = transform_args(test.input_args, is_linked_list)
    output_args = transform_args(test.output_args, is_linked_list)
    error_dict = {
        "input_args": [repr(arg) for arg in input_args],
        "expected_output": repr(test.output),
    }
    if output_args is not None:
        error_dict["expected_output_args"] = [repr(arg) for arg in output_args]
    try:
        compile(source, "<string>", "exec")
    except Exception:
        error_string = get_error_string(sys.exc_info())
        return SyntaxErrorResult(error=error_string)
    try:
        function_name, arg_names = check_specification(source, input_args, function_name, is_level5)
        error_dict["arg_names"] = arg_names
    except SpecificationError as e:
        return SpecificationErrorResult(error=f"Line {e.lineno}. {str(e)}")
    if check_timeout:
        process = multiprocessing.Process(target=worker, args=(source, function_name, timeout_input_args))
        process.start()
        process.join(TIMEOUT_SECONDS)
        if process.is_alive():
            process.terminate()
            return TimeoutResult(**error_dict)
    try:
        fun = string_to_lambda(source, function_name)
        result = fun(*input_args)
    except Exception:
        error_string = get_error_string(sys.exc_info())
        return RuntimeErrorResult(error=error_string, **error_dict)
    if result != test.output:
        return FailResult(
            output=repr(result),
            output_args=[repr(arg) for arg in input_args],
            **error_dict,
        )
    if output_args is not None:
        for i in range(len(output_args)):
            if (output_args[i] is not None) and (input_args[i] != output_args[i]):
                return FailResult(
                    output=repr(result),
                    output_args=[repr(arg) for arg in input_args],
                    **error_dict,
                )
    return SuccessResult()


app = FastAPI()


@app.post("/checkmate")
def run_tests(request: Request) -> list[Result]:
    results = []
    for test in request.tests:
        result = run_one(
            request.source.strip(),
            test,
            request.function_name,
            request.is_linked_list,
            request.is_level5,
            request.check_timeout,
        )
        results.append(result)
    return results
