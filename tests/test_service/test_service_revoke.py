async def test_service_revoke(client, authenticated, db_service):
    response = await client.put(f"/api/v1/services/{db_service.uuid}/revoke")
    assert response.status_code == 202


async def test_service_revoke_404(client, authenticated, db_service):
    response = await client.put("/api/v1/services/non-existent-uuid/revoke")
    assert response.status_code == 404
