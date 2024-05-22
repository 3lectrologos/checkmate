from checkmate import Request, run_tests


def get_response(source, tests, check_timeout=False, **kwargs):
    request = Request(source=source.strip(), tests=tests, check_timeout=check_timeout, **kwargs)
    return run_tests(request)
