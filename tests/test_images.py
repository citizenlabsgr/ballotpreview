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
def images_directory():
    path = IMAGES_DIRECTORY = Path.cwd() / "tests" / "images"
    shutil.rmtree(path)
    path.mkdir()
    return path


def describe_images():
    def with_name(ballot, images_directory):
        for target in settings.TARGET_SIZES:
            image, _ = utils.render_image("Jane", ballot, target, "PNG")
            path = images_directory / f"ballot-name-{target}.png"
            with path.open("wb") as f:
                f.write(image.getvalue())

    def without_name(ballot, images_directory):
        for target in settings.TARGET_SIZES:
            image, _ = utils.render_image("", ballot, target, "PNG")
            path = images_directory / f"ballot-nameless-{target}.png"
            with path.open("wb") as f:
                f.write(image.getvalue())
