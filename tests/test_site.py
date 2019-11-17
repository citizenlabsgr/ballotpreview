from urllib.parse import unquote

import pytest


def get_html(response):
    return unquote(response.response.data.decode())


def describe_index():
    @pytest.mark.asyncio
    async def it_links_to_elections(app, expect):
        client = app.test_client()
        response = await client.get("/")
        html = get_html(response)
        expect(html).contains("View Elections")


def describe_elections():
    @pytest.mark.asyncio
    async def it_includes_election_names(app, expect):
        client = app.test_client()
        response = await client.get("/elections/")
        html = get_html(response)
        expect(html).contains("State General")


def describe_elections_detail():
    @pytest.mark.asyncio
    async def it_includes_election_name(app, expect):
        client = app.test_client()
        response = await client.get("/elections/3/")
        html = get_html(response)
        expect(html).contains("State General")


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
                "/elections/5/precincts/1172/?position-3626=candidate-17345,candidate-17344"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?position-3626=candidate-17345</a>")

        @pytest.mark.asyncio
        async def it_redirects_to_remove_invalid_votes(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?proposal-1009=foobar&position-3626=candidate-17345"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?position-3626=candidate-17345</a>")

        @pytest.mark.asyncio
        async def it_redirects_to_remove_unknown_positions(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?position-999=candidate-42&position-3626=candidate-17345"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?position-3626=candidate-17345</a>")

        @pytest.mark.asyncio
        async def it_redirects_to_remove_unknown_keys(app, expect):
            client = app.test_client()
            response = await client.get(
                "/elections/5/precincts/1172/?foo=bar&position-3626=candidate-17345"
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?position-3626=candidate-17345</a>")

    def describe_post():
        @pytest.mark.asyncio
        async def it_adds_votes_to_url(app, expect):
            client = app.test_client()
            response = await client.post(
                "/elections/5/precincts/1172/", form={"proposal-194": "yes"}
            )
            expect(response.status_code) == 302
            html = get_html(response)
            expect(html).contains("?proposal-194=yes</a>")
