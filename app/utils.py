from typing import Dict, List, Optional, Tuple

import log
from werkzeug.datastructures import MultiDict


def validate_ballot(
    positions: List,
    proposals: List,
    *,
    original_votes: MultiDict,
    allowed_parameters: Tuple = (),
    keep_extra_parameters: bool = False,
    merge_votes: bool = False,
) -> Tuple[Dict, int]:
    votes: Dict = {}
    votes_changed = False

    for key, value in original_votes.items(multi=True):
        if key.startswith("position-"):
            if key in votes:
                votes[key].extend(value.split(","))
            else:
                votes[key] = value.split(",")

        elif key.startswith("proposal-"):
            proposal_id = int(key.split("-")[-1])
            if _get_proposal(proposals, proposal_id):
                if value in {"approve", "reject"}:
                    votes[key] = value
                else:
                    log.warning(f"Removed unexpected proposal choice: {value}")
                    votes_changed = True
            else:
                log.warning(f"Removed unexpected proposal: {key}")
                votes_changed = True

        elif key == "viewed":
            if key in votes:
                votes[key].extend(value.split(","))
            else:
                votes[key] = value.split(",")

        elif key == "hide":
            try:
                votes["viewed"].append(value)
            except KeyError:
                votes["viewed"] = [value]

        elif key == "show":
            try:
                votes["viewed"].remove(value)
            except KeyError:
                votes["viewed"] = []

        elif key in allowed_parameters or keep_extra_parameters:
            log.debug(f"Keeping extra parameter: {key}")
            votes[key] = value

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

    if merge_votes:
        for key, value in votes.items():
            if value and isinstance(value, list):
                votes[key] = ",".join(value)

    return votes, votes_changed


def _get_proposal(proposals: List, proposal_id: int) -> Optional[Dict]:
    for proposal in proposals:
        if proposal["id"] == proposal_id:
            return proposal

    log.error(f"Could not find proposal {proposal_id} on ballot: {proposals}")
    return None


def _get_seats(positions: List, position_id: int) -> int:
    for position in positions:
        if position["id"] == position_id:
            return position["seats"]

    log.error(f"Could not find position {position_id} on ballot: {positions}")
    return 0
