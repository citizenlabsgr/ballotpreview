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
    image_data = Image.new("RGB", (width, height), color=settings.DEFAULT_COLOR)
    draw = ImageDraw.Draw(image_data)

    title = _get_title(share, positions, proposals)
    font, cutoff = _get_font(title, width, height)
    draw.text((0, 0), title, font=font)
    if cutoff:
        log.warn(f"{title!r} was cut off for {target!r}")

    response = _get_response(share, positions, proposals, votes)
    font, cutoff = _get_font(response, width, height)
    draw.text((0, height // 2), response, font=font)
    if cutoff:
        log.warn(f"{response!r} was cut off for {target!r}")

    stream = io.BytesIO()
    image_data.save(stream, format=extension)

    return stream, Image.MIME[extension]


def _get_title(share: str, positions: List, proposals: List):
    category, _key = share.split("-")
    key = int(_key)

    if category == "position":
        for position in positions:
            if position["id"] == key:
                return position["name"]

    if category == "proposal":
        for proposal in proposals:
            if proposal["id"] == key:
                return proposal["name"]

    raise LookupError(f"{share} not found in {positions} or {proposals}")


def _get_response(share: str, positions: List, proposals: List, votes: Dict):
    category, _key = share.split("-")
    key = int(_key)

    vote = votes.get(share)
    if not vote:
        return "???"

    if category == "position":
        for position in positions:
            if position["id"] == key:

                key2 = int(vote.split("-")[1])
                for candidate in position["candidates"]:
                    if candidate["id"] == key2:
                        return candidate["name"]

    if category == "proposal":
        return vote.title()

    raise LookupError(f"{vote} not found in {positions} or {proposals}")


def _get_font(text: str, image_width: int, image_height: int, minimum_size=8):
    font = ImageFont.truetype(settings.DEFAULT_FONT, size=minimum_size)
    cutoff = True

    for size in range(image_height // 4, minimum_size, -1):
        font = ImageFont.truetype(settings.DEFAULT_FONT, size=size)
        text_width, _text_height = font.getsize(text)
        if text_width < image_width:
            cutoff = False
            break

    return font, cutoff
