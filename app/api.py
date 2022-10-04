from datetime import datetime
from typing import Dict, List, Tuple

import aiohttp
import bugsnag
import log

from . import settings


async def get_status(
    first_name: str, last_name: str, birth_date: str, zip_code: int
) -> Dict:
    if "-" not in birth_date:
        dt = datetime.strptime(birth_date, "%m/%d/%Y")
        birth_date = dt.date().isoformat()

    async with aiohttp.ClientSession() as session:
        url = f"{settings.ELECTIONS_HOST}/api/registrations/?first_name={first_name}&last_name={last_name}&birth_date={birth_date}&zip_code={zip_code}"
        async with session.get(url) as response:
            try:
                data = await response.json()
            except aiohttp.ContentTypeError:
                data = {}

    if "registered" not in data:
        bugsnag.notify(
            ValueError(f"No registration status: {url}"),
            context="get_status",
            metadata={
                "registration": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "birth_date": birth_date,
                    "zip_code": zip_code,
                }
            },
        )
        data = {"registered": False}

    return data


async def get_elections(*, active=None) -> List:
    url = f"{settings.ELECTIONS_HOST}/api/elections/"
    if active:
        url += "?active=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()

    return list(reversed(data["results"]))


async def get_election(election_id: int) -> Dict:
    async with aiohttp.ClientSession() as session:
        url = f"{settings.ELECTIONS_HOST}/api/elections/{election_id}/"
        async with session.get(url) as response:
            data = await response.json()

    return data


async def get_ballot(
    election_id: int, precinct_id: int, party: str = ""
) -> Tuple[Dict, List, List]:
    async with aiohttp.ClientSession() as session:
        url = f"{settings.ELECTIONS_HOST}/api/ballots/?election_id={election_id}&precinct_id={precinct_id}&active_election=null"
        async with session.get(url) as response:
            data = await response.json()
            try:
                ballot = data["results"][0]
            except LookupError:
                ballot = None

        if ballot is None and settings.BUGSNAG_VERBOSE:
            bugsnag.notify(
                LookupError(f"No ballot: {url}"),
                context="get_ballot",
                metadata={
                    "ballot": {"election_id": election_id, "precinct_id": precinct_id}
                },
            )

    positions = await get_positions(election_id, precinct_id, party)
    proposals = await get_proposals(election_id, precinct_id)

    return ballot, positions, proposals


async def get_positions(election_id: int, precinct_id: int, party: str = "") -> List:
    async with aiohttp.ClientSession() as session:
        url = f"{settings.ELECTIONS_HOST}/api/positions/?election_id={election_id}&precinct_id={precinct_id}&active_election=null&limit=1000"
        if party:
            url += f"&section={party}"
        async with session.get(url) as response:
            positions = await response.json()

    return positions["results"]


async def get_proposals(election_id: int, precinct_id: int) -> List:
    async with aiohttp.ClientSession() as session:
        url = f"{settings.ELECTIONS_HOST}/api/proposals/?election_id={election_id}&precinct_id={precinct_id}&active_election=null&limit=1000"
        async with session.get(url) as response:
            proposals = await response.json()

    return sorted(proposals["results"], key=lambda d: d["name"])


async def update_ballot(slug: str, url: str):
    if slug and url:
        data = {"voter": slug, "url": url}
    else:
        return

    if "localhost" in url and "localhost" not in settings.BUDDIES_HOST:
        log.warn(f"Refusing to update {settings.BUDDIES_HOST} with {url}")
        return

    log.info("Updating voter's ballot on Ballot Buddies")
    async with aiohttp.ClientSession() as session:
        url = f"{settings.BUDDIES_HOST}/api/update-ballot/"
        async with session.post(url, data=data) as response:
            try:
                data = await response.json()
            except Exception as e:
                log.error(f"Exception while calling API: {e}")
                data = {}

            if response.status == 200:
                message = data["message"].strip(".")
                log.info(f"{response.status} response from API: {message}")
            else:
                log.error(f"{response.status} response from API: {data}")
