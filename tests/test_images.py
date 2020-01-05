import shutil
from pathlib import Path

import pytest

from app import settings, utils


@pytest.fixture(scope="session")
def ballot():
    return {}


@pytest.fixture(scope="session")
def images_directory():
    path = IMAGES_DIRECTORY = Path.cwd() / "tests" / "images"
    shutil.rmtree(path)
    path.mkdir()
    return path


def describe_images():
    def with_name(ballot, images_directory):
        for target in settings.TARGET_SIZES:
            image, _ = utils.render_image("Jane", ballot, target, "JPEG")
            path = images_directory / f"ballot-name-{target}.jpg"
            with path.open("wb") as f:
                f.write(image.getvalue())

    def without_name(ballot, images_directory):
        for target in settings.TARGET_SIZES:
            image, _ = utils.render_image("", ballot, target, "JPEG")
            path = images_directory / f"ballot-nameless-{target}.jpg"
            with path.open("wb") as f:
                f.write(image.getvalue())
