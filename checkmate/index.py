import sys
import traceback
import functools
import multiprocessing
from fastapi import FastAPI
from .types import *

from .spec_check import check_specification, SpecificationError
from .linked_list import ListPtr


TIMEOUT_SECONDS = 4


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


def arg_list(args):
    result_list = []
    for arg in args:
        if isinstance(arg, ListPtr):
            result_list.append(arg._lst)
        else:
            result_list.append(arg)
    return result_list


def run_one(source, test, function_name, is_linked_list, is_level5, check_timeout) -> Result:
    input_args = transform_args(test.input_args, is_linked_list)
    timeout_input_args = transform_args(test.input_args, is_linked_list)
    output_args = transform_args(test.output_args, is_linked_list)
    error_dict = {
        "input_args": arg_list(input_args),
        "expected_output": test.output,
    }
    if output_args is not None:
        error_dict["expected_output_args"] = arg_list(output_args)
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
            output=result,
            output_args=arg_list(input_args),
            **error_dict,
        )
    if output_args is not None:
        for i in range(len(output_args)):
            if (output_args[i] is not None) and (input_args[i] != output_args[i]):
                return FailResult(
                    output=result,
                    output_args=arg_list(input_args),
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
