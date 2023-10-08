import typing

import pytest
from _pytest.fixtures import SubRequest

if typing.TYPE_CHECKING:
    from httpx import Request


@pytest.fixture(scope="module")
def vcr_config():
    def before_record_request(request: "Request") -> "Request":
        for header in ("accept", "accept-encoding", "connection", "user-agent"):
            request.headers.pop(header, None)
        return request

    def before_record_response(response: dict) -> dict:
        response.update({"headers": {}})
        return response

    return {
        "record_mode": "once",
        "before_record_request": [before_record_request],
        "before_record_response": [before_record_response],
    }


@pytest.fixture(scope="module")
def vcr_cassette_dir(request: SubRequest) -> str:
    return str(request.node.path.parent) + "/cassettes"
