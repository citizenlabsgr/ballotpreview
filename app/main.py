import aiohttp
from quart import Quart, url_for

app = Quart(__name__)


@app.route("/")
async def hello():
    return "hello"


@app.route("/elections/")
async def elections():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://michiganelections.io/api/elections/"
        ) as response:
            data = await response.json()

    html = ""
    for result in data["results"]:
        url = url_for("elections_detail", election_id=result["id"])
        name = f"{result['name']} ({result['date']})"
        html += f'<a href="{url}">{name}</a>' + "<br>"

    return html


@app.route("/elections/<election_id>/")
async def elections_detail(election_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://michiganelections.io/api/elections/{election_id}/"
        ) as response:
            data = await response.json()

    return f"{data['name']} ({data['date']})"


@app.route("/elections/<election_id>/precincts/<precinct_id>/")
async def ballot(election_id: int, precinct_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://michiganelections.io/api/positions/?election_id={election_id}&precinct_id={precinct_id}"
        ) as response:
            positions = await response.json()

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://michiganelections.io/api/positions/?election_id={election_id}&precinct_id={precinct_id}"
        ) as response:
            proposals = await response.json()

    return {"positions": positions["results"], "proposals": proposals["results"]}
