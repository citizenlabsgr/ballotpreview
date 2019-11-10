import pytest

from app import views


@pytest.fixture
def app():
    return views.app


@pytest.mark.asyncio
async def test_index(app, expect):
    client = app.test_client()
    response = await client.get("/")
    html = response.response.data.decode()
    expect(html).contains("View Elections")


@pytest.mark.asyncio
async def test_elections(app, expect):
    client = app.test_client()
    response = await client.get("/elections/")
    html = response.response.data.decode()
    expect(html).contains("State General")


@pytest.mark.asyncio
async def test_elections_detail(app, expect):
    client = app.test_client()
    response = await client.get("/elections/3/")
    html = response.response.data.decode()
    expect(html).contains("State General")


@pytest.mark.asyncio
async def test_ballot(app, expect):
    client = app.test_client()
    response = await client.get("/elections/3/precincts/1172/")
    html = response.response.data.decode()
    expect(html).contains("Attorney General")
    expect(html).contains("18-1")
