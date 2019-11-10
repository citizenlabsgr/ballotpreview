from quart import Quart, url_for, render_template
from . import api

app = Quart(__name__)


@app.route("/")
async def hello():
    return await render_template("index.html")


@app.route("/elections/")
async def elections():
    elections = await api.get_elections()
    return await render_template("elections.html", elections=elections)


@app.route("/elections/<election_id>/")
async def elections_detail(election_id: int):
    election = await api.get_election(election_id)
    return await render_template("elections_detail.html", election=election)


@app.route("/elections/<election_id>/precincts/<precinct_id>/")
async def ballot(election_id: int, precinct_id: int):
    positions, proposals = await api.get_ballot(election_id, precinct_id)
    return await render_template(
        "ballot.html", positions=positions, proposals=proposals
    )
