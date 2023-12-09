import json
from fastapi.testclient import TestClient
from index import app


client = TestClient(app)


def get_response(source, tests, **kwargs):
    request_args = {'source': source.strip(), 'tests': tests}
    response = client.post('/api/python', json=dict(**request_args, **kwargs))
    return response, response.json(), [json.dumps(result) for result in response.json()]
