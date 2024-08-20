async def test_root_redirect(client):
    response = await client.get("/")
    assert response.status_code == 307
    assert response.headers.get("location") == "/docs"
