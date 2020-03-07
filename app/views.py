from typing import Dict, List

import bugsnag
import log
from quart import Quart, redirect, render_template, request, send_file, url_for

from . import api, bugsnag_quart, render, settings, utils


if settings.BUGSNAG_API_KEY:
    bugsnag.configure(api_key=settings.BUGSNAG_API_KEY)


app = Quart(__name__)
bugsnag_quart.handle_exceptions(app)


@app.route("/")
async def index():
    elections = await api.get_elections()

    for election in elections:
        if election["active"]:
            return redirect(url_for("election_detail", election_id=election["id"]))

    return redirect(url_for("election_list"))


@app.route("/banner.png")
async def banner():
    elections = await api.get_elections()
    target = request.args.pop("target", None)
    image, mimetype = render.election_image("PNG", target=target, election=elections[0])
    return await send_file(image, mimetype)


@app.route("/about/")
async def about():
    return await render_template("about.html")


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
            extra = {"recently_moved": "true"} if status["recently_moved"] else {}
            return redirect(
                url_for(
                    "ballot_detail",
                    election_id=election_id,
                    precinct_id=precinct_id,
                    name=form["first_name"],
                    **extra,  # type: ignore
                )
            )

        log.warning(f"Not registered: {form}")
        return redirect(url_for("election_detail", election_id=election_id, **form))

    return await render_template(
        "election_detail.html", election=election, voter=request.args
    )


@app.route("/elections/<election_id>/banner.png")
async def election_image(election_id: int):
    election = await api.get_election(election_id)
    target = request.args.pop("target", None)
    image, mimetype = render.election_image("PNG", target=target, election=election)
    return await send_file(image, mimetype)


@app.route("/elections/<election_id>/precincts/<precinct_id>/", methods=["GET", "POST"])
async def ballot_detail(election_id: int, precinct_id: int):
    params = request.args
    name = params.get("name", None)
    share = params.get("share", None)
    target = params.get("target", None)

    if params.get("recently_moved", False):
        return (
            await render_template("ballot_404.html", name=name, recently_moved=True),
            404,
        )

    ballot, positions, proposals = await api.get_ballot(election_id, precinct_id)

    if target:
        return await ballot_image(
            share=share,
            target=target,
            positions=positions,
            proposals=proposals,
            votes=params,
        )

    if ballot is None:
        return (
            await render_template("ballot_404.html", name=name),
            404,
        )

    form = await request.form
    votes, votes_changed = utils.validate_ballot(
        positions,
        proposals,
        original_votes=form or params,
        allowed_parameters=("name", "share", "target", "recently_moved"),
        keep_extra_parameters=share,
    )

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
    share: str, target: str, positions: List, proposals: List, votes: Dict,
):
    image, mimetype = render.ballot_image(
        "PNG",
        share=share,
        target=target,
        positions=positions,
        proposals=proposals,
        votes=votes,
    )
    return await send_file(image, mimetype)
