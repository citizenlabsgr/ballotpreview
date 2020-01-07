from typing import Dict

import log
from quart import (
    Quart,
    abort,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)

from . import api, settings, utils


app = Quart(__name__)


@app.route("/")
async def index():
    elections = await api.get_elections()
    return await render_template("index.html", elections=elections)


@app.route("/elections/")
async def elections():
    return redirect(url_for("index"))


@app.route("/elections/<election_id>/", methods=["GET", "POST"])
async def election(election_id: int):
    election = await api.get_election(election_id)

    if request.method == "POST":
        form = await request.form
        status = await api.get_status(**form)
        if status["registered"]:
            precinct_id = status["precinct"]["id"]
            return redirect(
                url_for(
                    "ballot",
                    election_id=election_id,
                    precinct_id=precinct_id,
                    name=form["first_name"],
                )
            )

        log.warning(f"Not registered: {form}")
        return redirect(url_for("election", election_id=election_id, **form))

    return await render_template("election.html", election=election, voter=request.args)


@app.route("/elections/<election_id>/precincts/<precinct_id>/", methods=["GET", "POST"])
async def ballot(election_id: int, precinct_id: int):
    params = request.args
    name = params.pop("name", None)
    share = params.pop("share", None)

    ballot, positions, proposals = await api.get_ballot(election_id, precinct_id)

    if share:
        return await ballot_image(name, ballot, share)

    if ballot is None:
        return await render_template("ballot_404.html", name=name), 404

    form = await request.form
    votes, votes_changed = utils.validate_ballot(positions, proposals, form or params)

    if request.method == "POST" or votes_changed:
        if name:
            votes["name"] = name
        return redirect(
            url_for("ballot", election_id=election_id, precinct_id=precinct_id, **votes)
        )

    return await render_template(
        "ballot.html",
        name=name,
        ballot=ballot,
        positions=positions,
        proposals=proposals,
        votes=votes,
    )


async def ballot_image(name: str, ballot: Dict, share: str):
    if ballot is None:
        return await send_from_directory(settings.IMAGES_DIRECTORY, "logo.png")

    image, mimetype = utils.render_image(name, ballot, share, "PNG")
    return await send_file(image, mimetype)
