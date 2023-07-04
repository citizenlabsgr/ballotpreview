import asyncio
from collections import defaultdict

import bugsnag
import log
from quart import (
    Quart,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.datastructures import MultiDict

from . import api, bugsnag_quart, render, settings, utils

if settings.BUGSNAG_API_KEY:
    bugsnag.configure(api_key=settings.BUGSNAG_API_KEY)


app = Quart(__name__)
bugsnag_quart.handle_exceptions(app)


@app.route("/")
async def index():
    elections = await api.get_elections(active=True)

    for election in elections:
        if election["active"]:
            return redirect(url_for("election_detail", election_id=election["id"]))

    return redirect(url_for("election_list"))


@app.route("/banner.png")
async def banner():
    elections = await api.get_elections(active=True)
    target = request.args.get("target", "default")
    image = await asyncio.get_running_loop().run_in_executor(
        None, render.election_image, target, elections[0]
    )
    return await send_file(image, cache_timeout=settings.IMAGE_CACHE_TIMEOUT)


@app.route("/about/")
async def about():
    return await render_template("about.html")


@app.route("/elections/")
async def election_list():
    elections = await api.get_elections()

    years = defaultdict(list)
    for election in elections:
        year = election["date"].split("-")[0]
        years[year].append(election)

    return await render_template(
        "election_list.html", years=dict(sorted(years.items(), reverse=True))
    )


@app.route("/elections/<election_id>/", methods=["GET", "POST"])
async def election_detail(election_id: int):
    election = await api.get_election(election_id)

    if request.method == "POST":
        form = await request.form
        status = await api.get_status(**form)
        if status["registered"]:

            kwargs = {"name": form["first_name"]}
            if status["recently_moved"]:
                kwargs["recently_moved"] = "true"

            if ballots := status.get("ballots"):
                ballot_id = ballots[0]["id"]
                return redirect(
                    url_for(
                        "ballot_detail",
                        ballot_id=ballot_id,
                        **kwargs,
                    )
                )

            precinct_id = status["precinct"]["id"]
            return redirect(
                url_for(
                    "precinct_detail",
                    election_id=election_id,
                    precinct_id=precinct_id,
                    **kwargs,
                )
            )

        log.warning(f"Not registered: {form}")
        return redirect(url_for("election_detail", election_id=election_id, **form))

    if settings.TEST_VOTER["first_name"]:
        voter = settings.TEST_VOTER
    else:
        voter = request.args

    return await render_template("election_detail.html", election=election, voter=voter)


@app.route("/elections/<election_id>/banner.png")
async def election_image(election_id: int):
    election = await api.get_election(election_id)
    target = request.args.get("target", "default")
    image = await asyncio.get_event_loop().run_in_executor(
        None, render.election_image, target, election
    )
    return await send_file(image, cache_timeout=settings.IMAGE_CACHE_TIMEOUT)


@app.route(
    "/elections/<election_id>/precincts/<precinct_id>/",
    methods=["GET", "POST", "PUT"],
)
async def precinct_detail(election_id: int, precinct_id: int):
    params = request.args
    name = params.get("name", None)
    party = params.get("party", None)
    share = params.get("share", None)
    target = params.get("target", None)
    slug = params.get("slug", "")
    viewed = params.get("viewed", "")

    if share == "":
        return await precinct_share(election_id, precinct_id)

    if target:
        if share == "first":
            share, vote = list(params.items())[0]
            if "," in vote:
                vote = vote.split(",")[0]
        elif share and "~" in share:
            share, vote = share.split("~")
        else:
            vote = params.get(share)  # type: ignore
        return await precinct_image(election_id, precinct_id, share or "", vote)

    ballot, positions, proposals = await api.get_ballot(
        election_id=election_id, precinct_id=precinct_id, party=party or ""
    )

    if ballot is None:
        this_election = None
        other_elections = []
        for election in reversed(await api.get_elections()):
            if election["id"] == int(election_id):
                this_election = election
            else:
                other_elections.append(election)
                if this_election and not election["active"]:
                    break
        html = await render_template(
            "ballot_404.html",
            election=this_election,
            elections=other_elections,
            precinct_id=precinct_id,
            name=name,
        )
        return html, 404

    form = await request.form
    if request.method == "PUT":
        original_votes = params
        actions = form
    else:
        original_votes = form or params
        actions = MultiDict()

    votes, votes_changed = utils.validate_ballot(
        positions,
        proposals,
        original_votes=original_votes,
        actions=actions,
        allowed_parameters=(
            "name",
            "party",
            "share",
            "target",
            "recently_moved",
            "slug",
        ),
        keep_extra_parameters=bool(share),
        merge_votes=True,
    )

    if request.method == "PUT":
        url = url_for(
            "precinct_detail", election_id=election_id, precinct_id=precinct_id, **votes
        )
        await api.update_ballot(slug, url)
        response = await make_response("", 200)
        response.headers["HX-Location"] = url
        return response

    if request.method == "POST" or votes_changed:
        if party:
            votes["party"] = party
        if viewed:
            votes["viewed"] = viewed

        url = url_for(
            "precinct_detail",
            election_id=election_id,
            precinct_id=precinct_id,
            **votes,
            _external=True,
        ).replace("%2C", ",")
        await api.update_ballot(slug, url)

        if name:
            votes["name"] = name
        if slug:
            votes["slug"] = slug

        url = url_for(
            "precinct_detail",
            election_id=election_id,
            precinct_id=precinct_id,
            **votes,
        ).replace("%2C", ",")
        return redirect(url)

    if share and share != "all":
        for position in positions.copy():
            if f"position-{position['id']}" not in votes:
                positions.remove(position)

        for proposal in proposals.copy():
            if f"proposal-{proposal['id']}" not in votes:
                proposals.remove(proposal)

    return await render_template(
        "ballot_detail.html",
        name=name,
        ballot=ballot,
        positions=positions,
        proposals=proposals,
        votes=votes,
        election_url=f"{settings.BUDDIES_HOST}?referrer={slug}"
        if slug
        else url_for("election_detail", election_id=election_id),
        buddies_url=f"{settings.BUDDIES_HOST}/friends/{slug}" if slug else "",
    )


async def precinct_share(election_id: int, precinct_id: int):
    ballot, positions, proposals = await api.get_ballot(
        election_id=election_id, precinct_id=precinct_id
    )

    votes, _votes_changed = utils.validate_ballot(
        positions, proposals, original_votes=request.args, actions=MultiDict()
    )

    ballot_url = url_for(
        "precinct_detail", election_id=election_id, precinct_id=precinct_id
    )

    return await render_template(
        "ballot_share.html",
        name=request.args.get("name"),
        ballot=ballot,
        votes=votes,
        ballot_url=ballot_url,
    )


@app.route(
    "/elections/<election_id>/precincts/<precinct_id>/<item>/<vote>.<ext>",
    methods=["GET"],
)
async def precinct_image(
    election_id: int, precinct_id: int, item: str, vote: str, ext: str = "png"
):
    share = item
    votes = {item: vote}
    target = request.args.get("target", "default")

    positions = await api.get_positions(
        election_id=election_id, precinct_id=precinct_id
    )
    proposals = await api.get_proposals(
        election_id=election_id, precinct_id=precinct_id
    )

    image = await asyncio.get_event_loop().run_in_executor(
        None, render.ballot_image, share, target, positions, proposals, votes, ext
    )

    return await send_file(image, cache_timeout=settings.IMAGE_CACHE_TIMEOUT)


@app.route("/ballots/<ballot_id>/", methods=["GET", "POST", "PUT"])
async def ballot_detail(ballot_id: int):
    params = request.args
    name = params.get("name", None)
    party = params.get("party", None)
    share = params.get("share", None)
    target = params.get("target", None)
    slug = params.get("slug", "")
    viewed = params.get("viewed", "")

    if share == "":
        return await ballot_share(ballot_id)

    if target:
        if share == "first":
            share, vote = list(params.items())[0]
            if "," in vote:
                vote = vote.split(",")[0]
        elif share and "~" in share:
            share, vote = share.split("~")
        else:
            vote = params.get(share)  # type: ignore
        return await ballot_image(ballot_id, share or "", vote)

    ballot, positions, proposals = await api.get_ballot(
        ballot_id=ballot_id, party=party or ""
    )

    if ballot is None:
        elections = reversed(await api.get_elections())
        html = await render_template(
            "ballot_404.html",
            election=None,
            elections=elections,
            name=name,
        )
        return html, 404

    form = await request.form
    if request.method == "PUT":
        original_votes = params
        actions = form
    else:
        original_votes = form or params
        actions = MultiDict()

    votes, votes_changed = utils.validate_ballot(
        positions,
        proposals,
        original_votes=original_votes,
        actions=actions,
        allowed_parameters=(
            "name",
            "party",
            "share",
            "target",
            "recently_moved",
            "slug",
        ),
        keep_extra_parameters=bool(share),
        merge_votes=True,
    )

    if request.method == "PUT":
        url = url_for("ballot_detail", ballot_id=ballot_id, **votes)
        await api.update_ballot(slug, url)
        response = await make_response("", 200)
        response.headers["HX-Location"] = url
        return response

    if request.method == "POST" or votes_changed:
        if party:
            votes["party"] = party
        if viewed:
            votes["viewed"] = viewed

        url = url_for(
            "ballot_detail",
            ballot_id=ballot_id,
            **votes,
            _external=True,
        ).replace("%2C", ",")
        await api.update_ballot(slug, url)

        if name:
            votes["name"] = name
        if slug:
            votes["slug"] = slug

        url = url_for(
            "ballot_detail",
            ballot_id=ballot_id,
            **votes,
        ).replace("%2C", ",")
        return redirect(url)

    if share and share != "all":
        for position in positions.copy():
            if f"position-{position['id']}" not in votes:
                positions.remove(position)

        for proposal in proposals.copy():
            if f"proposal-{proposal['id']}" not in votes:
                proposals.remove(proposal)

    return await render_template(
        "ballot_detail.html",
        name=name,
        ballot=ballot,
        positions=positions,
        proposals=proposals,
        votes=votes,
        election_url=f"{settings.BUDDIES_HOST}?referrer={slug}"
        if slug
        else url_for("election_detail", election_id=ballot["election"]["id"]),
        buddies_url=f"{settings.BUDDIES_HOST}/friends/{slug}" if slug else "",
    )


async def ballot_share(ballot_id: int):
    ballot, positions, proposals = await api.get_ballot(ballot_id=ballot_id)

    votes, _votes_changed = utils.validate_ballot(
        positions, proposals, original_votes=request.args, actions=MultiDict()
    )

    ballot_url = url_for("ballot_detail", ballot_id=ballot_id)

    return await render_template(
        "ballot_share.html",
        name=request.args.get("name"),
        ballot=ballot,
        votes=votes,
        ballot_url=ballot_url,
    )


@app.route("/ballots/<ballot_id>/<item>/<vote>.<ext>", methods=["GET"])
async def ballot_image(ballot_id: int, item: str, vote: str, ext: str = "png"):
    share = item
    votes = {item: vote}
    target = request.args.get("target", "default")

    positions = await api.get_positions(ballot_id=ballot_id)
    proposals = await api.get_proposals(ballot_id=ballot_id)

    image = await asyncio.get_event_loop().run_in_executor(
        None, render.ballot_image, share, target, positions, proposals, votes, ext
    )

    return await send_file(image, cache_timeout=settings.IMAGE_CACHE_TIMEOUT)
