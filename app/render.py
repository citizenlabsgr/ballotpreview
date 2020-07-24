import io
from typing import Dict, List, Tuple

import bugsnag
import log
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from . import settings


def election_image(
    extension: str, target: str, election: Dict
) -> Tuple[io.BytesIO, str]:
    log.debug(election)  # Include election date in image
    return ballot_image(
        extension, share="", target=target, positions=[], proposals=[], votes={}
    )


def ballot_image(
    extension: str,
    share: str,
    target: str,
    positions: List,
    proposals: List,
    votes: Dict,
) -> Tuple[io.BytesIO, str]:
    width, height, crop = settings.TARGET_SIZES[target]
    unit = max(1, height // 50)

    # Background image
    img = Image.open(settings.IMAGES_DIRECTORY / "michigan.jpg")
    img = img.resize((width, height))
    converter = ImageEnhance.Color(img)
    img = converter.enhance(0.25)
    converter = ImageEnhance.Brightness(img)
    img = converter.enhance(0.75)
    draw = ImageDraw.Draw(img, "RGBA")

    # Title text
    border = (4 * unit) + crop
    text = _get_title(share or "", positions, proposals)
    font = _get_font(text, width - (2 * border), height)
    draw.text(
        (border, height // 2 - border - int(font.size * 1.1)),
        text,
        fill=settings.WHITE,
        font=font,
    )

    # Response box
    border = (2 * unit) + crop
    draw.rectangle(
        ((border - 1, height // 2), (width - border, height - border)),
        fill=(255, 255, 255, 110),
    )

    # Response text
    border = (4 * unit) + crop
    mark, fill, text = _get_response(share or "", positions, proposals, votes)
    font = _get_font(mark + text, width - (2 * border), height)
    draw.text(
        (border, height // 2), mark + text, fill=settings.BLACK, font=font,
    )

    # Response mark
    border = (4 * unit) + crop
    x = border
    y = height // 2
    draw.text((x - 1, y), mark, fill=settings.BLACK, font=font)
    draw.text((x + 1, y), mark, fill=settings.BLACK, font=font)
    draw.text((x, y - 1), mark, fill=settings.BLACK, font=font)
    draw.text((x, y + 1), mark, fill=settings.BLACK, font=font)
    draw.text((x - 1, y - 1), mark, fill=settings.BLACK, font=font)
    draw.text((x + 1, y - 1), mark, fill=settings.BLACK, font=font)
    draw.text((x - 1, y + 1), mark, fill=settings.BLACK, font=font)
    draw.text((x + 1, y + 1), mark, fill=settings.BLACK, font=font)
    draw.text((x, y), mark, fill=fill, font=font)

    stream = io.BytesIO()
    img.save(stream, format=extension)

    return stream, Image.MIME[extension]


def _get_title(share: str, positions: List, proposals: List):
    if "-" not in share:
        return "Michigan Election"

    category, _key = share.split("-")
    key = int(_key)

    if category == "position":
        for position in positions:
            if position["id"] == key:
                return _shorten(position["name"], position["district"]["name"])

    if category == "proposal":
        for proposal in proposals:
            if proposal["id"] == key:
                return _shorten(proposal["name"])

    raise LookupError(f"{share} not found in {positions} or {proposals}")


def _shorten(text: str, district: str = "") -> str:
    words = text.split(" ")

    if district and district != "Michigan":
        words.append(f"({district})")

    line = " ".join(words)
    while len(line) > 35 or words[-1].startswith("."):
        words.pop()
        line = " ".join(words)

    return line


def _get_response(share: str, positions: List, proposals: List, votes: Dict):
    if "-" not in share:
        return "", settings.BLACK, "Ballot Preview"

    category, _key = share.split("-")
    key = int(_key)

    vote = votes.get(share)
    if not vote:
        return "? ", settings.PURPLE, "Undecided"

    if category == "position":
        for position in positions:
            if position["id"] == key:

                key2 = int(vote.split("-")[1])
                for candidate in position["candidates"]:
                    if candidate["id"] == key2:
                        return "■ ", candidate["party"]["color"], candidate["name"]

    if category == "proposal":
        return (
            "☑ " if vote == "approve" else "☒ ",
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
