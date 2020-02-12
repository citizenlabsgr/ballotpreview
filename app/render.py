import io
from typing import Dict, List, Tuple

import bugsnag
import log
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from . import settings


def image(
    extension: str,
    *,
    share: str,
    target: str,
    positions: List,
    proposals: List,
    votes: Dict,
) -> Tuple[io.BytesIO, str]:
    width, height = settings.TARGET_SIZES[target]
    unit = max(1, height // 50)

    # Background image
    img = Image.open(settings.IMAGES_DIRECTORY / "michigan.jpg")
    img = img.resize(settings.TARGET_SIZES[target])
    converter = ImageEnhance.Color(img)
    img = converter.enhance(0.25)
    converter = ImageEnhance.Brightness(img)
    img = converter.enhance(0.75)
    draw = ImageDraw.Draw(img, "RGBA")

    # Title text
    border = 4 * unit
    text = _get_title(share, positions, proposals)
    font = _get_font(text, width - (2 * border), height)
    draw.text(
        (border, height // 2 - border - int(font.size * 1.1)),
        text,
        fill=settings.WHITE,
        font=font,
    )

    # Response box
    border = 2 * unit
    draw.rectangle(
        ((border, height // 2), (width - border, height - border)),
        fill=(255, 255, 255, 110),
    )

    # Response text
    border = 4 * unit
    mark, fill, text = _get_response(share, positions, proposals, votes)
    font = _get_font(mark + " " + text, width - (2 * border), height)
    draw.text(
        (border, height // 2), mark + " " + text, fill=settings.BLACK, font=font,
    )

    # Response mark
    border = 4 * unit
    draw.text((border, height // 2), mark, fill=fill, font=font)

    stream = io.BytesIO()
    img.save(stream, format=extension)

    return stream, Image.MIME[extension]


def _get_title(share: str, positions: List, proposals: List):
    category, _key = share.split("-")
    key = int(_key)

    if category == "position":
        for position in positions:
            if position["id"] == key:
                return _shorten(position["name"])

    if category == "proposal":
        for proposal in proposals:
            if proposal["id"] == key:
                return _shorten(proposal["name"])

    raise LookupError(f"{share} not found in {positions} or {proposals}")


def _shorten(text: str) -> str:
    words = text.split(" ")

    line = " ".join(words)
    while len(line) > 30:
        words.pop()
        line = " ".join(words)

    return line


def _get_response(share: str, positions: List, proposals: List, votes: Dict):
    category, _key = share.split("-")
    key = int(_key)

    vote = votes.get(share)
    if not vote:
        return "?", settings.PURPLE, "Undecided"

    if category == "position":
        for position in positions:
            if position["id"] == key:

                key2 = int(vote.split("-")[1])
                for candidate in position["candidates"]:
                    if candidate["id"] == key2:
                        return "■", candidate["party"]["color"], candidate["name"]

    if category == "proposal":
        return (
            "☑" if vote == "approve" else "☒",
            settings.GREEN if vote == "approve" else settings.RED,
            vote.title(),
        )

    raise LookupError(f"{vote} not found in {positions} or {proposals}")


def _get_font(text: str, image_width: int, image_height: int):
    maximum_size = image_height // 4
    minimum_size = max(10, image_height // 30)
    font = ImageFont.truetype(str(settings.FONT), size=minimum_size)
    cutoff = True

    for size in range(maximum_size, minimum_size, -1):
        font = ImageFont.truetype(str(settings.FONT), size=size)
        text_width, _text_height = font.getsize(text)
        if text_width < image_width:
            cutoff = False
            break

    if cutoff:
        message = f"{text!r} was cut off for {image_width}x{image_height}"
        log.warn(message)
        bugsnag.notify(ValueError(message), context="get_font")

    return font
