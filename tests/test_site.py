# pylint: disable=redefined-outer-name,unused-argument,unused-variable,expression-not-assigned

from urllib.parse import unquote

import pytest


def get_html(response):
    return unquote(response.response.data.decode())


def describe_index():
    @pytest.mark.asyncio
    async def it_redirects_to_active_election(app, expect):
        client = app.test_client()
        response = await client.get("/")
        html = get_html(response)
        expect(html).contains('redirected to <a href="/elections/38/">')


def describe_elections():
    @pytest.mark.asyncio
    async def it_links_to_elections(app, expect):
        client = app.test_client()
        response = await client.get("/elections/")
        html = get_html(response)
        expect(html).contains("State General")


def describe_election():
    @pytest.mark.asyncio
    async def it_includes_election_name(app, expect):
        client = app.test_client()
        response = await client.get("/elections/3/")
        html = get_html(response)
        expect(html).contains("State General")

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

    @pytest.mark.asyncio
    async def it_display_error_with_invalid_voter_information(app, expect):
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


def describe_ballot():
    def describe_get():
        @pytest.mark.asyncio
        async def it_includes_ballot_items(app, expect):
            client = app.test_client()
            response = await client.get("/elections/3/precincts/1172/")
            html = get_html(response)
            expect(html).contains("Attorney General")
            expect(html).contains("18-1")

        @pytest.mark.asyncio
        async def it_redirects_to_remove_extra_votes(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?position-5068=candidate-21490&position-5068=candidate-21489"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?position-5068=candidate-21490</a>")

        @pytest.mark.asyncio
        async def it_redirects_to_remove_extra_votes_based_on_seats(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/3/precincts/1172/?position-710=candidate-10590&position-710=candidate-10589&position-710=candidate-10591"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains(
                "?position-710=candidate-10590&position-710=candidate-10589</a>"
            )

        @pytest.mark.asyncio
        async def it_redirects_to_remove_invalid_votes(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?proposal-1009=foobar&position-5068=candidate-21490"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?position-5068=candidate-21490</a>")

        @pytest.mark.asyncio
        async def it_redirects_to_remove_unknown_positions(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?position-999=candidate-42&position-5068=candidate-21490"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?position-5068=candidate-21490</a>")

        @pytest.mark.asyncio
        async def it_redirects_to_remove_unknown_proposals(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?proposal-999=approve&position-5068=candidate-21490"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?position-5068=candidate-21490</a>")

        @pytest.mark.asyncio
        async def it_redirects_to_remove_unknown_keys(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?foo=bar&position-5068=candidate-21490"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?position-5068=candidate-21490</a>")

        @pytest.mark.asyncio
        async def it_keeps_name_through_redirect(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?foo=bar&name=Jane"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?name=Jane</a>")

        @pytest.mark.asyncio
        async def it_handles_unknown_ballots(app, expect):
            client = app.test_client()
            response = await client.get("/elections/5/precincts/99999/")
            expect(response.status_code) == 404
            html = get_html(response)
            expect(html).contains("can't find a sample ballot")

        @pytest.mark.asyncio
        async def it_hides_share_button_when_no_votes(app, expect):
            client = app.test_client()
            response = await client.get("/elections/3/precincts/1172/?name=Jane")
            html = get_html(response)
            expect(html).excludes("Share This Ballot")
            expect(html).excludes("Find Your Ballot")
            expect(html).contains("official ballot")

        @pytest.mark.asyncio
        async def it_shows_share_button_after_voting(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/3/precincts/1172/?position-710=candidate-10590"
            )
            html = get_html(response)
            expect(html).contains("Share This Ballot")
            expect(html).excludes("Find Your Ballot")
            expect(html).contains("official ballot")

        @pytest.mark.asyncio
        async def it_shows_find_button_after_sharing(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/3/precincts/1172/?share=position-710"
            )
            html = get_html(response)
            expect(html).contains("Find Your Ballot")
            expect(html).excludes("Share This Ballot")
            expect(html).contains(" disabled>")
            expect(html).excludes("official ballot")

    def describe_post():
        @pytest.mark.asyncio
        async def it_adds_votes_to_url(app, expect):
            client = app.test_client()
            response = await client.post(
                "/elections/5/precincts/1172/", form={"proposal-1009": "approve"}
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?proposal-1009=approve</a>")
