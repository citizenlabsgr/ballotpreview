import os
from pathlib import Path


TARGET_SIZES = {
    "default": (400, 200, 0),
    "facebook": (1200, 628, 0),
    "reddit": (280, 280, 0),
    "twitter": (506, 253, 10),
    "instagram": (510, 510, 0),
    "linkedin": (1104, 736, 0),
}

IMAGES_DIRECTORY = Path.cwd() / "app" / "images"
FONTS_DIRECTORY = Path.cwd() / "app" / "fonts"

FONT = FONTS_DIRECTORY / "SourceSansPro-Regular.ttf"

BLACK = (0, 0, 0)
WHITE = (230, 230, 230)
GREEN = (21, 173, 21)
RED = (191, 33, 33)
PURPLE = (135, 10, 163)

BUGSNAG_API_KEY = os.getenv("BUGSNAG_API_KEY")
