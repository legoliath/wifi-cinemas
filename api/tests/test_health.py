import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "wifi-cinemas-api"


@pytest.mark.asyncio
async def test_docs_available(client: AsyncClient):
    r = await client.get("/docs")
    assert r.status_code == 200
