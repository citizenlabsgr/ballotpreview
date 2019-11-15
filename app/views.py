from quart import Quart, redirect, render_template, request, url_for

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
    precincts = await api.get_precincts()
    return await render_template(
        "elections_detail.html", election=election, precincts=precincts
    )


@app.route("/elections/<election_id>/precincts/<precinct_id>/", methods=["GET", "POST"])
async def ballot(election_id: int, precinct_id: int):
    positions, proposals = await api.get_ballot(election_id, precinct_id)
    votes = request.args

    if request.method == "POST":
        form = await request.form

        for key, value in form.items():
            votes[key] = value

        return redirect(
            url_for("ballot", election_id=election_id, precinct_id=precinct_id, **votes)
        )

    return await render_template(
        "ballot.html", positions=positions, proposals=proposals, votes=votes
    )
