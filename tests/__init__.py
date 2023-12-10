import json
from fastapi.testclient import TestClient
from checkmate import app


client = TestClient(app)


def get_response(source, tests, check_timeout=False, **kwargs):
    request_args = {"source": source.strip(), "tests": tests, "check_timeout": check_timeout}
    response = client.post("/checkmate", json=dict(**request_args, **kwargs))
    return response, response.json(), [json.dumps(result) for result in response.json()]
