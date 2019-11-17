from typing import Dict, Tuple

import log


def validate_seats(positions: Dict, original_votes: Dict) -> Tuple[Dict, int]:
    votes: Dict = {}
    votes_changed = False

    for key, value in original_votes.items():
        if key.startswith("position-"):
            position_id = int(key.split("-")[-1])
            seats = _get_seats(positions, position_id)
            if not seats:
                votes_changed = True
                continue

            votes[key] = []
            for candidate in value.split(","):
                if len(votes[key]) >= seats:
                    log.warning(f"Removed extra candidate vote: {value}")
                    votes_changed = True
                    break
                votes[key].append(candidate)

        elif key.startswith("proposal-"):
            if value in {"yes", "no"}:
                votes[key] = value
            else:
                log.warning(f"Removed unexpected proposal choice: {value}")
                votes_changed = True
        else:
            log.warning(f"Removed unexpected ballot item: {key}")
            votes_changed = True

    return votes, votes_changed


def _get_seats(positions: Dict, position_id: int) -> int:
    for position in positions:
        if position["id"] == position_id:
            return position["seats"]

    log.error(f"Could not find position {position_id} on ballot: {positions}")
    return 0
