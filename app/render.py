import hashlib
from contextlib import suppress
from pathlib import Path

import bugsnag
import log
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from . import settings


def banner_image(
    target: str,
    *,
    election: dict | None = None,
    district: dict | None = None,
    explore: bool = False,
) -> Path:
    if election and explore:
        year = election["date"].split("-")[0]
        lines = ["Explore Ballots", f'{year} {election["name"]}']
    elif district and explore:
        if district["category"] in {"County"}:
            lines = ["Explore Ballots", f'{district["name"]} {district["category"]}']
        elif (
            district["category"]
            in {
                "State",
                "City",
                "Township",
                "Jurisdiction",
                "Village",
                "Ward",
                "Precinct",
            }
            or "Library" in district["category"]
            or "School" in district["category"]
        ):
            lines = ["Explore Ballots", district["name"]]
        else:
            lines = ["Explore Ballots", f'{district["name"]}\n({district["category"]})']
    elif election:
        lines = [election["name"], election["date_humanized"]]
    else:
        lines = ["Michigan Election", "Ballot Preview"]
    return ballot_image(lines, target, positions=[], proposals=[], votes={})


def ballot_image(
    share: str | list,
    target: str,
    positions: list,
    proposals: list,
    votes: dict,
    path: Path | None = None,
) -> Path:
    width, height, crop = settings.TARGET_SIZES[target]
    unit = max(1, height // 50)

    mark = ""
    fill = settings.BLACK
    if isinstance(share, list):
        title, response = share
    elif "-" not in share:
        title = "Michigan Election"
        response = "Ballot Preview"
    else:
        title = _get_title(share, positions, proposals)
        mark, fill, response = _get_response(share, positions, proposals, votes)

    if path is None:
        variant = title + mark + response + target
        fingerprint = hashlib.sha1(variant.encode()).hexdigest()
        images = Path("images")
        images.mkdir(exist_ok=True)
        path = images / f"{fingerprint}.jpg"

        if path.exists() and not settings.DEBUG:
            log.info(f"Found image at {path}")
            return path

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
    font = _get_font(title, width - (2 * border), height, border)
    draw.text(
        (border, height // 2 - border - int(font.size * 1.1)),
        title,
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
    font = _get_font(mark + response, width - (2 * border), height, border)
    draw.text(
        (border, height // 2),
        mark + response,
        fill=settings.BLACK,
        font=font,
        spacing=0,
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

    img.save(path, quality=85)

    return path


def _get_title(share: str, positions: list, proposals: list):
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
    with suppress(KeyError):
        return settings.SHORTENED_NAMES[text]

    words = text.split(" ")

    if district and district != "Michigan":
        words.append(f"({district})")

    line = " ".join(words)

    if line.startswith("Proposal ") and " A Proposal " in line:
        line = line.split(" A Proposal ", maxsplit=1)[0]

    while len(line) > 35 or words[-1].startswith("."):
        words.pop()
        line = " ".join(words)

    return line.removesuffix(" and").removesuffix(" the").removesuffix(" Authorizing")


def _get_response(share: str, positions: list, proposals: list, votes: dict):
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
                        return (
                            "■ ",
                            candidate["party"]["color"],
                            candidate["name"].replace(" & ", "\n &  "),
                        )

    if category == "proposal":
        return (
            "☑ " if vote == "approve" else "☒ ",
            settings.GREEN if vote == "approve" else settings.RED,
            vote.title(),
        )

    raise LookupError(f"{vote} not found in {positions} or {proposals}")


def _get_font(text: str, image_width: int, image_height: int, border: int):
    maximum_size = image_height // 4
    minimum_size = max(10, image_height // 30)
    font = ImageFont.truetype(str(settings.FONT), size=minimum_size)
    cutoff = True

    for size in range(maximum_size, minimum_size, -1):
        font = ImageFont.truetype(str(settings.FONT), size=size)
        text_width, text_height = _get_text_size(text, font)
        if text_width < image_width and text_height < image_height / 2 - border:
            cutoff = False
            break

    if cutoff:
        message = f"{text!r} was cut off for {image_width}x{image_height}"
        log.warn(message)
        bugsnag.notify(ValueError(message), context="get_font")

    return font


def _get_text_size(text: str, font: ImageFont) -> tuple[int, int]:
    image = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(image)
    bbox = draw.textbbox((0, 0), text, font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]
