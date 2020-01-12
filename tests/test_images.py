import shutil
from pathlib import Path

import pytest

from app import settings, utils


@pytest.fixture(scope="session")
def positions():
    return [
        {
            "id": 5141,
            "name": "President of The United States",
            "candidates": [
                {
                    "id": 21685,
                    "name": "Elizabeth Warren",
                    "party": {"name": "Democratic", "color": "#3333FF",},
                },
                {
                    "id": 21691,
                    "name": "Bill Weld",
                    "party": {"name": "Republican", "color": "#E81B23",},
                },
            ],
        }
    ]


@pytest.fixture(scope="session")
def proposals():
    return [
        {"id": 123, "name": "Proposal 123",},
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
    path = IMAGES_DIRECTORY = Path.cwd() / "tests" / "images"
    shutil.rmtree(path)
    path.mkdir()
    return path


def describe_images():
    def with_position_vote(positions, votes, images_directory):
        for target in settings.TARGET_SIZES:
            image, _ = utils.render_image(
                "PNG",
                share="position-5141",
                target=target,
                positions=positions,
                proposals=[],
                votes=votes,
            )
            path = images_directory / f"position-vote-{target}.png"
            with path.open("wb") as f:
                f.write(image.getvalue())

    def with_position_nonvote(positions, votes, images_directory):
        for target in settings.TARGET_SIZES:
            image, _ = utils.render_image(
                "PNG",
                share="position-5141",
                target=target,
                positions=positions,
                proposals=[],
                votes={},
            )
            path = images_directory / f"position-nonvote-{target}.png"
            with path.open("wb") as f:
                f.write(image.getvalue())

    def with_proposal_approve(proposals, votes, images_directory):
        for target in settings.TARGET_SIZES:
            image, _ = utils.render_image(
                "PNG",
                share="proposal-1882",
                target=target,
                positions=[],
                proposals=proposals,
                votes=votes,
            )
            path = images_directory / f"proposal-approve-{target}.png"
            with path.open("wb") as f:
                f.write(image.getvalue())

    def with_proposal_reject(proposals, votes, images_directory):
        for target in settings.TARGET_SIZES:
            image, _ = utils.render_image(
                "PNG",
                share="proposal-123",
                target=target,
                positions=[],
                proposals=proposals,
                votes=votes,
            )
            path = images_directory / f"proposal-reject-{target}.png"
            with path.open("wb") as f:
                f.write(image.getvalue())

    def with_proposal_nonvote(proposals, votes, images_directory):
        for target in settings.TARGET_SIZES:
            image, _ = utils.render_image(
                "PNG",
                share="proposal-1882",
                target=target,
                positions=[],
                proposals=proposals,
                votes={},
            )
            path = images_directory / f"proposal-nonvote-{target}.png"
            with path.open("wb") as f:
                f.write(image.getvalue())

    def with_unknown_share_position(expect, positions, proposals):
        with expect.raises(LookupError):
            utils.render_image(
                "PNG",
                share="position-99999",
                target="default",
                positions=positions,
                proposals=proposals,
                votes={},
            )

    def with_unknown_share_proposal(expect, positions, proposals):
        with expect.raises(LookupError):
            utils.render_image(
                "PNG",
                share="proposal-99999",
                target="default",
                positions=positions,
                proposals=proposals,
                votes={},
            )

    def with_unknown_vote_position(expect, positions, proposals):
        with expect.raises(LookupError):
            utils.render_image(
                "PNG",
                share="position-5141",
                target="default",
                positions=positions,
                proposals=proposals,
                votes={"position-5141": "candidate-99999"},
            )
