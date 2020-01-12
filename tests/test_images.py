import shutil
from pathlib import Path

import pytest

from app import settings, utils


@pytest.fixture(scope="session")
def ballot():
    return {
        "election": {"name": "Presidential Primary", "date": "2020-03-10"},
        "precinct": {"jurisdiction": "City of Hastings", "ward": 12, "number": 34},
    }


@pytest.fixture(scope="session")
def positions():
    return {"position-42": {"name": "President of the United State"}}


@pytest.fixture(scope="session")
def proposals():
    return {
        "proposal-42": {
            "name": "Millage Renewal Proposition .9672 Mill For Operation of County-wide E-911 Emergency Answering and Dispatch System"
        }
    }


@pytest.fixture(scope="session")
def images_directory():
    path = IMAGES_DIRECTORY = Path.cwd() / "tests" / "images"
    shutil.rmtree(path)
    path.mkdir()
    return path


def describe_images():
    def with_position(ballot, positions, images_directory):
        for target in settings.TARGET_SIZES:
            image, _ = utils.render_image(
                "PNG",
                name="Jane",
                share="position-42",
                target=target,
                ballot=ballot,
                positions=positions,
                proposals={},
                votes={},
            )
            path = images_directory / f"position-{target}.png"
            with path.open("wb") as f:
                f.write(image.getvalue())

    def with_proposal(ballot, proposals, images_directory):
        for target in settings.TARGET_SIZES:
            image, _ = utils.render_image(
                "PNG",
                name="Jane",
                share="proposal-42",
                target=target,
                ballot=ballot,
                positions={},
                proposals=proposals,
                votes={},
            )
            path = images_directory / f"proposal-{target}.png"
            with path.open("wb") as f:
                f.write(image.getvalue())
