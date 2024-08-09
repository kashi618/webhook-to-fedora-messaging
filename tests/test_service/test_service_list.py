async def test_service_list(client, authenticated, db_service):
    response = await client.get("/api/v1/services")
    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {
                "creation_date": db_service.creation_date.isoformat(),
                "desc": db_service.desc,
                "name": db_service.name,
                "token": db_service.token,
                "type": db_service.type,
                "user_id": db_service.user_id,
                "uuid": db_service.uuid,
            },
        ],
    }
