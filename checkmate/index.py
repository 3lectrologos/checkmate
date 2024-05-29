import sys
import traceback
import functools
import multiprocessing
from .types import *

from .spec_check import check_specification, SpecificationError


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


def parse_args(args, linked_list):
    if args is None:
        return None
    return [parse_arg(arg, linked_list) for arg in args]


def parse_arg(arg, linked_list):
    if linked_list:
        from .linked_list import ListPtr
    if arg is None:
        return None
    return eval(arg)


def get_syntax_error_string(e):
    return f"Line {e.lineno}. {e.msg}"


def get_runtime_error_string(exc_info):
    exc_type, exc_value, exc_traceback = exc_info
    line_number = traceback.extract_tb(exc_traceback)[-1].lineno
    error_string = traceback.format_exception_only(exc_type, exc_value)[-1].strip()
    return f"Line {line_number}. {error_string}"


def run_one(source, test, function_name, is_linked_list, is_level5, check_timeout) -> Result:
    try:
        input_args = parse_args(test.input_args, linked_list=is_linked_list)
        timeout_input_args = parse_args(test.input_args, linked_list=is_linked_list)
        output_args = parse_args(test.output_args, linked_list=is_linked_list)
        parsed_output = parse_arg(test.output, linked_list=is_linked_list)
    except Exception as e:
        return SpecificationErrorResult(error="Invalid test specification.")

    error_dict = {
        "input_args": [repr(arg) for arg in input_args],
        "expected_output": repr(parsed_output),
    }
    if output_args is not None:
        error_dict["expected_output_args"] = [repr(arg) for arg in output_args]
    try:
        compile(source, "<string>", "exec")
    except Exception as e:
        error_string = get_syntax_error_string(e)
        return SyntaxErrorResult(error=error_string)
    try:
        function_name, arg_names = check_specification(source, input_args, function_name, is_level5)
        error_dict["arg_names"] = arg_names
        error_dict["function_name"] = function_name
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
    except KeyboardInterrupt:
        return TimeoutResult(**error_dict)
    except Exception:
        error_string = get_runtime_error_string(sys.exc_info())
        return RuntimeErrorResult(error=error_string, **error_dict)
    if parsed_output is not None and result != parsed_output:
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


def run_tests(request: Request) -> list[Result]:
    results = []
    for test in request.tests:
        function_name = test.function_name if test.function_name is not None else request.function_name
        result = run_one(
            request.source.strip(),
            test,
            function_name,
            request.is_linked_list,
            request.is_level5,
            request.check_timeout,
        )
        results.append(result)
    return results
