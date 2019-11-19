from typing import Dict, Tuple

import log


def validate_seats(positions: Dict, original_votes: Dict) -> Tuple[Dict, int]:
    votes: Dict = {}
    votes_changed = False

    for key, value in original_votes.items():
        if key.startswith("position-"):
            if key in votes:
                votes[key].append(value)
            else:
                votes[key] = [value]

        elif key.startswith("proposal-"):
            if value in {"yes", "no"}:
                votes[key] = value
            else:
                log.warning(f"Removed unexpected proposal choice: {value}")
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


def _get_seats(positions: Dict, position_id: int) -> int:
    for position in positions:
        if position["id"] == position_id:
            return position["seats"]

    log.error(f"Could not find position {position_id} on ballot: {positions}")
    return 0
