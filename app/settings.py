from pathlib import Path


IMAGES_DIRECTORY = Path.cwd() / "app" / "images"
FONTS_DIRECTORY = Path.cwd() / "app" / "fonts"

FONT = FONTS_DIRECTORY / "OpenSans-Regular.ttf"

BLACK = "#000000"
WHITE = "#FFFFFF"

TARGET_SIZES = {
    "default": (400, 200),
    "facebook": (1200, 628),
    "reddit": (70, 70),
    "twitter": (506, 253),
    "instagram": (510, 510),
    "linkedin": (1104, 736),
}
