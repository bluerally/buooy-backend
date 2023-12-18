import pytest


@pytest.mark.asyncio
async def test_create_test_endpoint(client):
    response = await client.get("/test")
    assert response.status_code == 200
