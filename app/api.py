import aiohttp

BASE_URL = "https://michiganelections.io/api"


async def get_elections():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/elections/?limit=1000") as response:
            data = await response.json()

    return data["results"]


async def get_election(election_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/elections/{election_id}/") as response:
            data = await response.json()

    return data


async def get_ballot(election_id: int, precinct_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/positions/?election_id={election_id}&precinct_id={precinct_id}&active_election=null&limit=1000"
        ) as response:
            positions = await response.json()

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/proposals/?election_id={election_id}&precinct_id={precinct_id}&active_election=null&limit=1000"
        ) as response:
            proposals = await response.json()

    return positions["results"], proposals["results"]
