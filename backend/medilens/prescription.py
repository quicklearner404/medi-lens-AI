"""Find the medicine lines in the text of a prescription.

The input is the text a phone's text recognition produces from a photo: the
doctor's letterhead, patient details, diagnosis, the medicines, and a
signature, one line per printed line. This module keeps only the medicine
lines, separates the written medicine name from its directions, and attaches
directions that were printed on the following line.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from medilens.directions import FORMS, FREQUENCY_CODES, Directions, parse_directions

NUMBERING = re.compile(r"^\s*(?:\(?\d{1,2}[.)]|rx[.:]?|[-•*])\s*", re.I)
FORM_PREFIX = re.compile(r"^(" + "|".join(sorted(FORMS, key=len, reverse=True)) + r")\b\.?\s*", re.I)

# A token that starts the directions rather than continuing the name.
DIRECTION_START = re.compile(
    r"^([\d½¼].*|"
    + "|".join(sorted(FREQUENCY_CODES, key=len, reverse=True))
    + r"|sos|prn|hs|stat|ac|pc|x|q\d+h?|every|for|after|before|at|with)$",
    re.I,
)
UNIT_TOKEN = re.compile(r"^(mg|mcg|µg|g|ml|iu|%)$", re.I)


@dataclass
class PrescriptionItem:
    line: str
    written_name: str
    directions: Directions


def read_prescription(text: str) -> list[PrescriptionItem]:
    items: list[PrescriptionItem] = []
    for raw in text.splitlines():
        line = " ".join(raw.split())
        if not line:
            continue

        body = NUMBERING.sub("", line)
        form = FORM_PREFIX.match(body)
        if form:
            name = _written_name(body[form.end():])
            if name:
                items.append(PrescriptionItem(line, name, parse_directions(line)))
                continue

        if items and _is_continuation(body):
            previous = items[-1]
            previous.line = f"{previous.line} {line}"
            previous.directions = parse_directions(previous.line)
    return items


def _written_name(rest: str) -> str:
    words = []
    for token in rest.split():
        clean = token.strip(".,;:()")
        if not clean or DIRECTION_START.match(clean) or UNIT_TOKEN.match(clean):
            break
        words.append(clean)
    return " ".join(words[:4])


def _is_continuation(body: str) -> bool:
    """A line holding only directions, e.g. '1+0+1 x 5 days after meals'."""
    first = body.split()[0].strip(".,;:()") if body.split() else ""
    if not DIRECTION_START.match(first):
        return False
    d = parse_directions(body)
    return bool(d.times_per_day or d.duration_days or d.as_needed or d.timing)
