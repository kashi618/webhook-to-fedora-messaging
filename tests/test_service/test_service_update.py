import pytest

from webhook_to_fedora_messaging.database import get_or_create
from webhook_to_fedora_messaging.models import User


@pytest.mark.parametrize(
    "db_service",
    [
        pytest.param(
            "github",
            id="GitHub",
        ),
        pytest.param(
            "forgejo",
            id="Forgejo",
        ),
    ],
    indirect=["db_service"],
)
async def test_service_update(client, authenticated, db_service, db_session):
    """
    Updating an existing service
    """
    data = {"name": "new name"}
    response = await client.put(f"/api/v1/services/{db_service.uuid}", json={"data": data})
    assert response.status_code == 202, response.text
    assert response.json()["data"]["name"] == "new name"
    await db_session.refresh(db_service)
    assert db_service.name == "new name"


@pytest.mark.parametrize(
    "db_service",
    [
        pytest.param(
            "github",
            id="GitHub",
        ),
        pytest.param(
            "forgejo",
            id="Forgejo",
        ),
    ],
    indirect=["db_service"],
)
async def test_service_update_user(client, authenticated, db_service, db_user, db_session):
    """
    Updating an existing user
    """
    username = "new-user"
    _, _ = await get_or_create(db_session, User, name=username)
    await db_session.commit()
    response = await client.put(
        f"/api/v1/services/{db_service.uuid}", json={"data": {"username": username}}
    )
    assert response.status_code == 202, response.text
    await db_session.refresh(db_service)
    users = await db_service.awaitable_attrs.users
    assert len(users) == 2
    assert {u.name for u in users} == {db_user.name, username}


@pytest.mark.parametrize(
    "db_service",
    [
        pytest.param(
            "github",
            id="GitHub",
        ),
        pytest.param(
            "forgejo",
            id="Forgejo",
        ),
    ],
    indirect=["db_service"],
)
async def test_service_update_user_duplicate(client, authenticated, db_service, db_session):
    """
    Verifying an existing user uniqueness during update
    """
    username = "mehmet"
    response = await client.put(
        f"/api/v1/services/{db_service.uuid}", json={"data": {"username": username}}
    )
    assert response.status_code == 202, response.text
    await db_session.refresh(db_service)
    users = await db_service.awaitable_attrs.users
    assert len(users) == 1
    assert users[0].name == "mehmet"


@pytest.mark.parametrize(
    "db_service",
    [
        pytest.param(
            "github",
            id="GitHub",
        ),
        pytest.param(
            "forgejo",
            id="Forgejo",
        ),
    ],
    indirect=["db_service"],
)
async def test_service_update_user_non_existent(client, authenticated, db_service, db_session):
    """
    Transferring an existing service to a non-existent user
    """
    data = {"username": "new-user"}
    response = await client.put(f"/api/v1/services/{db_service.uuid}", json={"data": data})
    assert response.status_code == 422, response.text
    assert response.json() == {
        "detail": "Service was attempted to be transferred to a non-existent user"
    }


async def test_service_update_404(client, authenticated):
    """
    Updating a non-existent service
    """
    data = {"name": "new name"}
    response = await client.put("/api/v1/services/non-existent-uuid", json={"data": data})
    assert response.status_code == 404


@pytest.mark.parametrize(
    "db_service",
    [
        pytest.param(
            "github",
            id="GitHub",
        ),
        pytest.param(
            "forgejo",
            id="Forgejo",
        ),
    ],
    indirect=["db_service"],
)
async def test_service_update_bad_request(client, authenticated, db_service):
    """
    Updating an existing service with invalid data
    """
    data = {"something-else": "extra attr"}
    response = await client.put(f"/api/v1/services/{db_service.uuid}", json={"data": data})
    assert response.status_code == 422
