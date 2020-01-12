import io
from typing import Dict, List, Tuple

import log
from PIL import Image, ImageDraw, ImageFont

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
    image_data = Image.new("RGB", (width, height), color=settings.BLACK)
    draw = ImageDraw.Draw(image_data)

    # Title text
    border = unit
    text = _get_title(share, positions, proposals)
    font, cutoff = _get_font(text, width - (2 * border), height)
    draw.text((border, 0), text, fill=settings.WHITE, font=font)
    if cutoff:
        log.warn(f"{text!r} was cut off for {target!r}")

    # Response box
    border = 2 * unit
    draw.rectangle(
        ((border, height // 2), (width - border, height - border)), fill=settings.WHITE,
    )

    # Response text
    mark, fill, text = _get_response(share, positions, proposals, votes)
    font, cutoff = _get_font(mark + " " + text, width - (4 * border), height)
    draw.text(
        ((2 * border), height // 2), mark + " " + text, fill=settings.BLACK, font=font,
    )
    if cutoff:
        log.warn(f"{text!r} was cut off for {target!r}")

    # Response mark
    draw.text((2 * border, height // 2), mark, fill=fill, font=font)

    stream = io.BytesIO()
    image_data.save(stream, format=extension)

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
        return "?", settings.GRAY, "Undecided"

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
    maximum_size = image_height // 5
    minimum_size = max(10, image_height // 30)
    font = ImageFont.truetype(str(settings.FONT), size=minimum_size)
    cutoff = True

    for size in range(maximum_size, minimum_size, -1):
        font = ImageFont.truetype(str(settings.FONT), size=size)
        text_width, _text_height = font.getsize(text)
        if text_width < image_width:
            cutoff = False
            break

    return font, cutoff
