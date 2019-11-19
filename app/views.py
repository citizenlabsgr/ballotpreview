import log
from quart import Quart, redirect, render_template, request, url_for

from . import api, utils

app = Quart(__name__)


@app.route("/")
async def index():
    elections = await api.get_elections()
    return await render_template("index.html", elections=elections)


@app.route("/elections/")
async def elections():
    return redirect(url_for("index"))


@app.route("/elections/<election_id>/", methods=["GET", "POST"])
async def elections_detail(election_id: int):
    election = await api.get_election(election_id)

    if request.method == "POST":
        form = await request.form
        status = await api.get_status(
            first_name=form["first_name"],
            last_name=form["last_name"],
            birth_date=form["birth_date"],
            zip_code=form["zip_code"],
        )
        if status["registered"]:
            precinct_id = status["precinct"]["id"]
            return redirect(
                url_for("ballot", election_id=election_id, precinct_id=precinct_id)
            )
        log.warning(f"Not registered: {form}")

    return await render_template("election.html", election=election)


@app.route("/elections/<election_id>/precincts/<precinct_id>/", methods=["GET", "POST"])
async def ballot(election_id: int, precinct_id: int):
    election = await api.get_election(election_id)
    precinct = await api.get_precinct(precinct_id)
    positions, proposals = await api.get_ballot(election_id, precinct_id)

    form = await request.form
    votes, votes_changed = utils.validate_seats(positions, form or request.args)

    if request.method == "POST" or votes_changed:
        return redirect(
            url_for("ballot", election_id=election_id, precinct_id=precinct_id, **votes)
        )

    return await render_template(
        "ballot.html",
        election=election,
        precinct=precinct,
        positions=positions,
        proposals=proposals,
        votes=votes,
    )
