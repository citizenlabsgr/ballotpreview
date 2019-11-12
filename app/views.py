from quart import Quart, render_template, request, url_for

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
    selected = _parse_ids(request, "selected")
    approved = _parse_ids(request, "approved")
    rejected = _parse_ids(request, "rejected")
    return await render_template(
        "ballot.html",
        positions=positions,
        proposals=proposals,
        selected=selected,
        approved=approved,
        rejected=rejected,
    )


def _parse_ids(request, key):
    ids = request.args.get(key, "").split(",")
    return [int(x) for x in ids if x]
