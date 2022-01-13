# pylint: disable=redefined-outer-name,unused-argument,unused-variable,expression-not-assigned

import shutil
from pathlib import Path

import pytest

from app import render, settings

RESET_IMAGES = False
REFRESH_RATE = 60
IMAGE_KEYS = [
    "overall",
    "position-vote",
    "position-nonvote",
    "proposal-approve",
    "proposal-reject",
    "proposal-nonvote",
]
IMAGE_TARGETS = ["default", "reddit", "twitter"]
SCRIPT = r"""<script>
setInterval(function() {
    var images = document.images;
    for (var i=0; i<images.length; i++) {
        images[i].src = images[i].src.replace(/\btime=[^&]*/, 'time=' + new Date().getTime());
    }
}, 2000);
</script>
"""


@pytest.fixture(scope="session")
def positions():
    return [
        {
            "id": 5141,
            "name": "President of The United States",
            "district": {"name": "Michigan"},
            "candidates": [
                {
                    "id": 21685,
                    "name": "Elizabeth Warren",
                    "party": {"name": "Democratic", "color": "#3333FF"},
                },
                {
                    "id": 21691,
                    "name": "Bill Weld",
                    "party": {"name": "Republican", "color": "#E81B23"},
                },
            ],
        },
        {
            "id": 48794,
            "name": "Electors of President and Vice-President of the United States",
            "district": {"name": "Michigan"},
            "candidates": [
                {
                    "id": 88287,
                    "name": "Rocky De La Fuente & Darcy Richardson",
                    "party": {"name": "Natural Law", "color": "#CA0F67"},
                },
            ],
        },
    ]


@pytest.fixture(scope="session")
def proposals():
    return [
        {
            "id": 123,
            "name": "Proposal 123",
        },
        {
            "id": 1882,
            "name": "Millage Renewal Proposition .9672 Mill For Operation of County-wide E-911 Emergency Answering and Dispatch System",
        },
    ]


@pytest.fixture(scope="session")
def votes():
    return {
        "position-5141": "candidate-21685",
        "proposal-1882": "approve",
        "proposal-123": "reject",
    }


@pytest.fixture(scope="session")
def images_directory():
    path = Path.cwd() / "tests" / "images"
    if RESET_IMAGES:
        shutil.rmtree(path)
        path.mkdir()
    return path


@pytest.fixture(scope="session", autouse=True)
def index(images_directory):
    path = images_directory / "index.html"
    with path.open("w") as f:
        f.write(f'<meta http-equiv="refresh" content="{REFRESH_RATE}">\n')
        for target in IMAGE_TARGETS:
            for key in IMAGE_KEYS:
                path = images_directory / f"{key}-{target}.png?time=0"
                f.write(f'<img src="{path}" style="padding: 10px;">\n')
        f.write(SCRIPT)
    path = images_directory / ".gitignore"
    with path.open("w") as f:
        f.write("index.html\n")
    return path


def describe_images():
    @pytest.mark.parametrize("target", settings.TARGET_SIZES)
    def with_position_vote(positions, votes, images_directory, target):
        render.ballot_image(
            share="position-5141",
            target=target,
            positions=positions,
            proposals=[],
            votes=votes,
            path=images_directory / f"position-vote-{target}.png",
        )

    def with_position_vote_multiline(positions, images_directory):
        render.ballot_image(
            share="position-48794",
            target="default",
            positions=positions,
            proposals=[],
            votes={"position-48794": "candidate-88287"},
            path=images_directory / "position-vote-multiline.png",
        )

    @pytest.mark.parametrize("target", settings.TARGET_SIZES)
    def with_position_nonvote(positions, votes, images_directory, target):
        render.ballot_image(
            share="position-5141",
            target=target,
            positions=positions,
            proposals=[],
            votes={},
            path=images_directory / f"position-nonvote-{target}.png",
        )

    @pytest.mark.parametrize("target", settings.TARGET_SIZES)
    def with_proposal_approve(proposals, votes, images_directory, target):
        render.ballot_image(
            share="proposal-1882",
            target=target,
            positions=[],
            proposals=proposals,
            votes=votes,
            path=images_directory / f"proposal-approve-{target}.png",
        )

    @pytest.mark.parametrize("target", settings.TARGET_SIZES)
    def with_proposal_reject(proposals, votes, images_directory, target):
        render.ballot_image(
            share="proposal-123",
            target=target,
            positions=[],
            proposals=proposals,
            votes=votes,
            path=images_directory / f"proposal-reject-{target}.png",
        )

    @pytest.mark.parametrize("target", settings.TARGET_SIZES)
    def with_proposal_nonvote(proposals, votes, images_directory, target):
        render.ballot_image(
            share="proposal-1882",
            target=target,
            positions=[],
            proposals=proposals,
            votes={},
            path=images_directory / f"proposal-nonvote-{target}.png",
        )

    @pytest.mark.parametrize("target", settings.TARGET_SIZES)
    def with_no_highlighted_item(images_directory, target):
        render.ballot_image(
            share=None,  # type: ignore
            target=target,
            positions=[],
            proposals=[],
            votes={},
            path=images_directory / f"overall-{target}.png",
        )

    def with_unknown_share_position(expect, positions, proposals):
        with expect.raises(LookupError):
            render.ballot_image(
                share="position-99999",
                target="default",
                positions=positions,
                proposals=proposals,
                votes={},
            )

    def with_unknown_share_proposal(expect, positions, proposals):
        with expect.raises(LookupError):
            render.ballot_image(
                share="proposal-99999",
                target="default",
                positions=positions,
                proposals=proposals,
                votes={},
            )

    def with_unknown_vote_position(expect, positions, proposals):
        with expect.raises(LookupError):
            render.ballot_image(
                share="position-5141",
                target="default",
                positions=positions,
                proposals=proposals,
                votes={"position-5141": "candidate-99999"},
            )
