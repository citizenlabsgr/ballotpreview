import io
from typing import Dict, Optional, Tuple

import log
from PIL import Image, ImageDraw, ImageFont

from . import settings


def validate_ballot(
    positions: Dict, proposals: Dict, original_votes: Dict
) -> Tuple[Dict, int]:
    votes: Dict = {}
    votes_changed = False

    for key, value in original_votes.items():
        if key.startswith("position-"):
            if key in votes:
                votes[key].append(value)
            else:
                votes[key] = [value]

        elif key.startswith("proposal-"):
            proposal_id = int(key.split("-")[-1])
            if _get_proposal(proposals, proposal_id):
                if value in {"yes", "no"}:
                    votes[key] = value
                else:
                    log.warning(f"Removed unexpected proposal choice: {value}")
                    votes_changed = True
            else:
                log.warning(f"Removed unexpected proposal: {key}")
                votes_changed = True

        else:
            log.warning(f"Removed unexpected ballot item: {key}")
            votes_changed = True

    for key, value in votes.items():
        if key.startswith("position-"):
            position_id = int(key.split("-")[-1])
            seats = _get_seats(positions, position_id)
            while len(value) > seats:
                log.warning(f"Removed extra candidate vote: {value}")
                votes_changed = True
                value.pop()

    return votes, votes_changed


def _get_proposal(proposals: Dict, proposal_id: int) -> Optional[Dict]:
    for proposal in proposals:
        if proposal["id"] == proposal_id:
            return proposal

    log.error(f"Could not find proposal {proposal_id} on ballot: {proposals}")
    return None


def _get_seats(positions: Dict, position_id: int) -> int:
    for position in positions:
        if position["id"] == position_id:
            return position["seats"]

    log.error(f"Could not find position {position_id} on ballot: {positions}")
    return 0


def render_image(
    extension: str,
    *,
    name: str,
    share: str,
    target: str,
    ballot: Dict,
    positions: Dict,
    proposals: Dict,
    votes: Dict,
) -> Tuple[io.BytesIO, str]:
    width, height = settings.TARGET_SIZES[target]
    image = Image.new("RGB", (width, height), color=settings.DEFAULT_COLOR)

    unit = height // 20
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("app/fonts/OpenSans-Regular.ttf", size=unit * 4)

    item = positions.get(share) or proposals[share]
    draw.text((unit, unit), item["name"], font=font)

    stream = io.BytesIO()
    image.save(stream, format=extension)

    return stream, Image.MIME[extension]
