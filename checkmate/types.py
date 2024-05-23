from enum import Enum
from pydantic import BaseModel, Field, root_validator
from typing import Optional, Literal, Union, Annotated, Any


class Test(BaseModel):
    input_args: list[Any]
    output_args: Optional[list[Any]] = None
    output: Optional[Any] = None
    function_name: Optional[str] = None

    @root_validator(skip_on_failure=True)
    def check_input_output_same_length(cls, values):
        input_args = values.get("input_args")
        output_args = values.get("output_args")
        if output_args is not None and len(input_args) != len(output_args):
            raise ValueError("The length of input_args and output_args are not equal")
        return values


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
    input_args: list[Any]
    expected_output_args: Optional[list[Any]] = None
    expected_output: Any
    function_name: str


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
    output_args: list[Any]
    output: Any


class SuccessResult(BaseModel):
    type: Literal[ResultType.SUCCESS] = ResultType.SUCCESS


Result = Annotated[
    Union[SuccessResult, SyntaxErrorResult, SpecificationErrorResult, RuntimeErrorResult, TimeoutResult, FailResult],
    Field(discriminator="type"),
]
