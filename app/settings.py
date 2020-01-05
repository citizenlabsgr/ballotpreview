from pathlib import Path


IMAGES_DIRECTORY = Path.cwd() / "app" / "images"

DEFAULT_COLOR = (0xF6, 0x52, 0x21)

TARGET_SIZES = {
    "default": (400, 200),
    "facebook": (1200, 628),
    "reddit": (70, 70),
    "twitter": (506, 253),
    "instagram": (510, 510),
    "linkedin": (1104, 736),
}
