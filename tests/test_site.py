# pylint: disable=redefined-outer-name,unused-argument,unused-variable,expression-not-assigned

from urllib.parse import unquote

import pytest


def get_html(response):
    return unquote(response.response.data.decode())


def describe_index():
    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_redirects_to_active_election(app, expect):
        client = app.test_client()
        response = await client.get("/")
        html = get_html(response)
        expect(html).contains('redirected to <a href="/elections/38/">')


def describe_election_list():
    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_links_to_elections(app, expect):
        client = app.test_client()
        response = await client.get("/elections/")
        html = get_html(response)
        expect(html).contains("Presidential Primary")


def describe_election_detail():
    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_includes_election_name(app, expect):
        client = app.test_client()
        response = await client.get("/elections/3/")
        html = get_html(response)
        expect(html).contains("State General")

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_redirects_to_ballot_with_valid_voter_information(app, expect):
        client = app.test_client()
        response = await client.post(
            "/elections/3/",
            form={
                "first_name": "Rosalynn",
                "last_name": "Bliss",
                "birth_date": "1975-08-03",
                "zip_code": 49503,
            },
        )
        html = get_html(response)
        expect(html).contains(
            'redirected to <a href="/elections/3/precincts/1173/?name=Rosalynn">'
        )

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_converts_polyfill_dates_to_RFC_3339(app, expect):
        client = app.test_client()
        response = await client.post(
            "/elections/3/",
            form={
                "first_name": "Rosalynn",
                "last_name": "Bliss",
                "birth_date": "8/3/1975",
                "zip_code": 49503,
            },
        )
        html = get_html(response)
        expect(html).contains(
            'redirected to <a href="/elections/3/precincts/1173/?name=Rosalynn">'
        )

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_displays_error_with_invalid_voter_information(app, expect):
        client = app.test_client()
        response = await client.post(
            "/elections/3/",
            form={
                "first_name": "Jane",
                "last_name": "Doe",
                "birth_date": "1970-01-01",
                "zip_code": 9999,
            },
        )
        html = get_html(response)
        expect(html).contains(
            'redirected to <a href="/elections/3/?first_name=Jane&last_name=Doe&birth_date=1970-01-01&zip_code=9999"'
        )


def describe_election_image():
    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def with_target(app, expect):
        client = app.test_client()
        response = await client.get("/elections/3/banner.png?target=facebook")
        expect(response.status_code) == 200

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def without_target(app, expect):
        client = app.test_client()
        response = await client.get("/elections/3/banner.png")
        expect(response.status_code) == 200


def describe_ballot_detail():
    def describe_get():
        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_includes_ballot_items(app, expect):
            client = app.test_client()
            response = await client.get("/elections/3/precincts/1172/")
            html = get_html(response)
            expect(html).contains("Attorney General")
            expect(html).contains("18-1")
            expect(html).excludes("recently moved")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_handles_missing_ballots(app, expect):
            client = app.test_client()
            response = await client.get("/elections/43/precincts/9774/")
            html = get_html(response)
            expect(html).contains("Michigan Special Election")
            expect(html).contains("We can't find a sample ballot for this election")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_warns_when_voter_has_moved(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/3/precincts/1172/?recently_moved=true"
            )
            html = get_html(response)
            expect(html).contains("Attorney General")
            expect(html).contains("18-1")
            expect(html).includes("recently moved")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_prompts_for_party_when_primary_ballot(app, expect):
            client = app.test_client()
            response = await client.get("/elections/40/precincts/1209/")
            html = get_html(response)
            expect(html).contains("Democratic Primary Ballot")  # party selection
            expect(html).excludes("Candidates")  # positions listing

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_filters_primary_ballot_based_on_party(app, expect):
            client = app.test_client()
            response = await client.get("/elections/40/precincts/591/?party=Democratic")
            html = get_html(response)
            expect(html).excludes("Democratic Primary Ballot")  # party selection
            expect(html).contains("Gary Peters")  # Democratic primary candidate
            expect(html).excludes("John James")  # Republican primary candidate
            expect(html).contains("Donna Adams")  # nonpartisan candidate

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_hides_positions_with_zero_candidates(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/40/precincts/1209/?party=Democratic&position-17099=candidate-43453"
            )
            html = get_html(response)
            expect(html).includes("County Commissioner")
            expect(html).excludes("Delegate to County Convention")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_accepts_commas_to_separate_candidates(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/3/precincts/1172/?position-710=candidate-10590,candidate-10589"
            )
            expect(response.status_code) == 200
            html = get_html(response)
            expect(html.count("checked")) == 2

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_redirects_to_remove_extra_votes(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?position-5068=candidate-21490&position-5068=candidate-21489"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?position-5068=candidate-21490</a>")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_redirects_to_remove_extra_votes_based_on_seats(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/3/precincts/1172/?position-710=candidate-10590&position-710=candidate-10589&position-710=candidate-10591"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?position-710=candidate-10590,candidate-10589</a>")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_redirects_to_remove_invalid_votes(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?proposal-1009=foobar&position-5068=candidate-21490"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?position-5068=candidate-21490</a>")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_redirects_to_remove_unknown_positions(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?position-999=candidate-42&position-5068=candidate-21490"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?position-5068=candidate-21490</a>")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_redirects_to_remove_unknown_proposals(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?proposal-999=approve&position-5068=candidate-21490"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?position-5068=candidate-21490</a>")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_redirects_to_remove_unknown_keys(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?foo=bar&position-5068=candidate-21490"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?position-5068=candidate-21490</a>")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_keeps_name_through_redirect(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?foo=bar&name=Jane"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?name=Jane</a>")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_keeps_party_through_redirect(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?foo=bar&party=Democratic"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?party=Democratic</a>")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_handles_unknown_ballots(app, expect):
            client = app.test_client()
            response = await client.get("/elections/42/precincts/99999/")
            expect(response.status_code) == 404
            html = get_html(response)
            expect(html.count("May Consolidated")) == 1
            expect(html).contains("can't find a sample ballot")
            expect(html).contains("Special Election")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_hides_share_button_when_no_votes(app, expect):
            client = app.test_client()
            response = await client.get("/elections/3/precincts/1172/?name=Jane")
            html = get_html(response)
            expect(html).excludes("Share on Facebook")
            expect(html).excludes("Find Your Ballot")
            expect(html).contains("official ballot")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_shows_share_button_after_voting(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/3/precincts/1172/?position-710=candidate-10590"
            )
            html = get_html(response)
            expect(html).contains("Share Your Plan")

    def describe_post():
        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_adds_votes_to_url(app, expect):
            client = app.test_client()
            response = await client.post(
                "/elections/5/precincts/1172/", form={"proposal-1009": "approve"}
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?proposal-1009=approve</a>")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_keeps_name_through_submit(app, expect):
            client = app.test_client()
            response = await client.post(
                "/elections/5/precincts/1172/?name=Jane&slug=test",
                form={"proposal-1009": "approve"},
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("&name=Jane&slug=test</a>")

        @pytest.mark.vcr
        @pytest.mark.asyncio
        async def it_keeps_party_through_submit(app, expect):
            client = app.test_client()
            response = await client.post(
                "/elections/5/precincts/1172/?party=Democratic",
                form={"proposal-1009": "approve"},
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("&party=Democratic</a>")


def describe_ballot_share_preview():
    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_shows_images(app, expect):
        client = app.test_client()
        response = await client.get(
            "/elections/40/precincts/591/"
            "?position-17099=candidate-43453&position-17100=candidate-43454&position-17084=candidate-43433&position-17084=candidate-43430&proposal-3190=approve"
            "&share="
        )
        html = get_html(response)
        expect(html.count("<img ")) == 5


def describe_ballot_share():
    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_shows_find_button_after_sharing(app, expect):
        client = app.test_client()
        response = await client.get(
            "/elections/3/precincts/1172/"
            "?position-3137=candidate-10258"
            "&share=position-3137"
        )
        html = get_html(response)
        expect(html).contains("Find Your Ballot")
        expect(html).excludes("Share on Facebook")
        expect(html).contains("pointer-events:none")
        expect(html).excludes("official ballot")

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_hides_items_without_votes(app, expect):
        client = app.test_client()
        response = await client.get(
            "/elections/41/precincts/1209/"
            "?position-46073=candidate-75684&position-46195=candidate-76005"
            "&share=first"
        )
        html = get_html(response)
        expect(html).contains("Positions")
        expect(html).contains("Representative in Congress")
        expect(html).excludes("United States Senator")
        expect(html).excludes("Proposals")

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_hides_edit_links(app, expect):
        client = app.test_client()
        response = await client.get("/elections/3/precincts/1172/?share=position-710")
        html = get_html(response)
        expect(html).excludes("edit")

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_allows_sites_to_add_tracking_parameters(app, expect):
        client = app.test_client()
        response = await client.get(
            "/elections/3/precincts/1172/"
            "?position-3137=candidate-10258"
            "&share=position-3137"
            "&fbclid=abc123"
        )
        html = get_html(response)
        expect(html).contains("Find Your Ballot")
        expect(html).excludes("Share on Facebook")
        expect(html).contains("pointer-events:none")
        expect(html).excludes("official ballot")


def describe_ballot_image():
    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_can_highlight_the_first_item(app, expect):
        client = app.test_client()
        response = await client.get(
            "/elections/41/precincts/1209/?"
            "position-46053=candidate-75615&position-46073=candidate-75684"
            "&share=first"
            "&target=default"
        )
        expect(response.status_code) == 200
        expect(response.content_type) == "image/png"

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_can_highlight_a_specific_item(app, expect):
        client = app.test_client()
        response = await client.get(
            "/elections/41/precincts/1209/?"
            "position-46053=candidate-75615&position-46073=candidate-75684"
            "&share=position-46073~candidate-75684"
            "&target=default"
        )
        expect(response.status_code) == 200
        expect(response.content_type) == "image/png"

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_support_multiple_position_votes(app, expect):
        client = app.test_client()
        response = await client.get(
            "/elections/41/precincts/1209/?"
            "position-46053=candidate-75615,candidate-75684"
            "&share=first"
            "&target=default"
        )
        expect(response.status_code) == 200
        expect(response.content_type) == "image/png"

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_handles_lack_of_highlighted_item(app, expect):
        client = app.test_client()
        response = await client.get("/elections/3/precincts/1172/?target=facebook")
        expect(response.status_code) == 200
        expect(response.content_type) == "image/png"

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def it_handles_lack_of_votes(app, expect):
        client = app.test_client()
        response = await client.get(
            "/elections/41/precincts/1209/?share=first&target=default"
        )
        expect(response.status_code) == 200
        expect(response.content_type) == "image/png"
