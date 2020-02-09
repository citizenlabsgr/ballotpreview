import os
from pathlib import Path


TARGET_SIZES = {
    "default": (400, 200),
    "facebook": (1200, 628),
    "reddit": (70, 70),
    "twitter": (506, 253),
    "instagram": (510, 510),
    "linkedin": (1104, 736),
}

IMAGES_DIRECTORY = Path.cwd() / "app" / "images"
FONTS_DIRECTORY = Path.cwd() / "app" / "fonts"

FONT = FONTS_DIRECTORY / "SourceSansPro-Regular.ttf"

BLACK = (0, 0, 0)
WHITE = (207, 207, 207)
GREEN = (21, 173, 21)
RED = (191, 33, 33)
PURPLE = (135, 10, 163)

BUGSNAG_API_KEY = os.getenv("BUGSNAG_API_KEY")
