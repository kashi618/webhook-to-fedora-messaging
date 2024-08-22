import hashlib
import hmac
import json
import pathlib
from unittest import mock

import pytest
from twisted.internet import defer
from webhook_to_fedora_messaging_messages.github import GithubMessageV1


@pytest.fixture
def request_data():
    fixtures_dir = pathlib.Path(__file__).parent.joinpath("fixtures")
    with open(fixtures_dir.joinpath("payload.json")) as fh:
        return fh.read().strip()


@pytest.fixture
def request_headers(db_service, request_data):
    sig_hash = hmac.new(
        db_service.token.encode("utf-8"),
        msg=request_data.encode("utf-8"),
        digestmod=hashlib.sha256,
    )
    signature = sig_hash.hexdigest()
    return {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": f"sha256={signature}",
        "X-Github-Event": "push",
        "X-Github-Delivery": "f1064eb2-4995-11ef-82e4-18ae0022c13c",
        "X-Github-Hook-Id": "491622597",
        "X-Github-Hook-Installation-Target-Id": "807808293",
        "X-Github-Hook-Installation-Target-Type": "repository",
        "X-Hub-Signature": "sha1=0e44dae9a9c979dc05d1f5846b06fe578e581533",
    }


@pytest.fixture()
def fasjson_client():
    client = mock.Mock(name="fasjson")
    with mock.patch(
        "webhook_to_fedora_messaging.endpoints.parser.github.get_fasjson",
        return_value=client,
    ):
        yield client


@pytest.fixture
def sent_messages():
    sent = []

    def _add_and_return(message, exchange=None):
        sent.append(message)
        return defer.succeed(None)

    with mock.patch(
        "webhook_to_fedora_messaging.publishing.api.twisted_publish", side_effect=_add_and_return
    ):
        yield sent


async def test_message_create(
    client, db_service, request_data, request_headers, fasjson_client, sent_messages
):
    fasjson_client.get_username_from_github = mock.AsyncMock(return_value="dummy-fas-username")
    response = await client.post(
        f"/api/v1/messages/{db_service.uuid}", content=request_data, headers=request_headers
    )
    assert response.status_code == 202, response.text
    assert len(sent_messages) == 1
    sent_msg = sent_messages[0]
    assert isinstance(sent_msg, GithubMessageV1)
    assert sent_msg.topic == "github.push"
    assert sent_msg.agent_name == "dummy-fas-username"
    assert sent_msg.body["body"] == json.loads(request_data)

    assert response.json() == {
        "data": {
            "message_id": sent_msg.id,
            "url": f"http://datagrepper.example.com/v2/id?id={sent_msg.id}&is_raw=true&size=extra-large",
        }
    }


async def test_message_create_400(client, db_service, request_data, request_headers):
    request_headers["X-Hub-Signature-256"] = ""
    response = await client.post(
        f"/api/v1/messages/{db_service.uuid}", content=request_data, headers=request_headers
    )
    assert response.status_code == 400


async def test_message_create_404(client):
    response = await client.post("/api/v1/messages/non-exsitent", json={})
    assert response.status_code == 404


async def test_message_create_bad_request(client, db_service):
    response = await client.post(f"/api/v1/messages/{db_service.uuid}", content="not json")
    assert response.status_code == 422
