from typing import Dict, List

import bugsnag
import log
from bugsnag.flask import handle_exceptions
from quart import (
    Quart,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)

from . import api, render, settings, utils


if settings.BUGSNAG_API_KEY:
    bugsnag.configure(api_key=settings.BUGSNAG_API_KEY)


app = Quart(__name__)
handle_exceptions(app)


@app.route("/")
async def index():
    elections = await api.get_elections()

    for election in elections:
        if election["active"]:
            return redirect(url_for("election_detail", election_id=election["id"]))

    return redirect(url_for("election_list"))


@app.route("/elections/")
async def election_list():
    elections = await api.get_elections()
    return await render_template("election_list.html", elections=elections)


@app.route("/elections/<election_id>/", methods=["GET", "POST"])
async def election_detail(election_id: int):
    election = await api.get_election(election_id)

    if request.method == "POST":
        form = await request.form
        status = await api.get_status(**form)
        if status["registered"]:
            precinct_id = status["precinct"]["id"]
            return redirect(
                url_for(
                    "ballot_detail",
                    election_id=election_id,
                    precinct_id=precinct_id,
                    name=form["first_name"],
                )
            )

        log.warning(f"Not registered: {form}")
        return redirect(url_for("election_detail", election_id=election_id, **form))

    return await render_template(
        "election_detail.html", election=election, voter=request.args
    )


@app.route("/elections/<election_id>/precincts/<precinct_id>/", methods=["GET", "POST"])
async def ballot_detail(election_id: int, precinct_id: int):
    params = request.args
    name = params.pop("name", None)
    share = params.pop("share", None)
    target = params.pop("target", None)

    ballot, positions, proposals = await api.get_ballot(election_id, precinct_id)

    if target:
        return await ballot_image(
            share=share,
            target=target,
            ballot=ballot,
            positions=positions,
            proposals=proposals,
            votes=params,
        )

    if ballot is None:
        bugsnag.notify(LookupError(f"No ballot: {request.url}"))
        return await render_template("ballot_404.html", name=name), 404

    form = await request.form
    votes, votes_changed = utils.validate_ballot(positions, proposals, form or params)

    if request.method == "POST" or votes_changed:
        if name:
            votes["name"] = name
        return redirect(
            url_for(
                "ballot_detail",
                election_id=election_id,
                precinct_id=precinct_id,
                **votes,
            )
        )

    return await render_template(
        "ballot_detail.html",
        name=name,
        ballot=ballot,
        positions=positions,
        proposals=proposals,
        votes=votes,
    )


async def ballot_image(
    share: str,
    target: str,
    ballot: Dict,
    positions: List,
    proposals: List,
    votes: Dict,
):
    if ballot is None:
        return await send_from_directory(settings.IMAGES_DIRECTORY, "logo.png")

    image, mimetype = render.image(
        "PNG",
        share=share,
        target=target,
        positions=positions,
        proposals=proposals,
        votes=votes,
    )
    return await send_file(image, mimetype)
