import pytest


@pytest.mark.parametrize(
    "data, code",
    [
        pytest.param(
            {"username": "mehmet"},
            201,
            id="USER Endpoint - 201 Created",
        ),
        pytest.param({"password": ""}, 400, id="USER Endpoint - 400 Bad Request"),
        pytest.param(None, 415, id="USER Endpoint - 415 Unsupported Media Type"),
    ],
)
def test_user_create(client, data, code):
    response = client.post("/user/", json=data)
    assert response.status_code == code


def test_user_create_conflict(client):
    data = {"username": "mehmet"}
    response = client.post("/user/", json=data)
    assert response.status_code == 201
    response = client.post("/user/", json=data)
    assert response.status_code == 409
