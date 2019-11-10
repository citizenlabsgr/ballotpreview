import pytest

from app import main


@pytest.fixture
def app():
    return main.app


@pytest.mark.asyncio
async def test_app(app):
    client = app.test_client()
    response = await client.get("/")
    assert response.status_code == 200
