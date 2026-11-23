"""Parse the directions part of a prescription line into structured fields.

Prescriptions use a compact shorthand: Latin abbreviations ("BD", "TDS", "PC"),
the dose-slot notation common in Pakistan ("1+0+1" means morning and night),
and fraction-style durations ("x 5/7" means five days). This module turns that
shorthand into explicit fields and a plain-English sentence.

The parser is deliberately conservative: anything it cannot read stays None,
so the app can show "not specified" instead of guessing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

FORMS = {
    "tab": "tablet", "tabs": "tablet", "tablet": "tablet", "tablets": "tablet",
    "cap": "capsule", "caps": "capsule", "capsule": "capsule", "capsules": "capsule",
    "syp": "syrup", "syrup": "syrup", "susp": "suspension", "suspension": "suspension",
    "inj": "injection", "injection": "injection",
    "drop": "drops", "drops": "drops", "gtt": "drops",
    "sachet": "sachet", "sachets": "sachet",
    "cream": "cream", "oint": "ointment", "ointment": "ointment", "gel": "gel",
    "inh": "inhaler", "inhaler": "inhaler", "puff": "puff", "puffs": "puff",
}

# Abbreviation -> times per day.
FREQUENCY_CODES = {
    "od": 1, "qd": 1, "once": 1, "daily": 1,
    "bd": 2, "bid": 2, "twice": 2,
    "tds": 3, "tid": 3,
    "qid": 4, "qds": 4,
}
HOURLY = re.compile(r"\b(?:q|every\s*)(\d{1,2})\s*(?:h|hr|hrs|hours?)\b")

AS_NEEDED = re.compile(r"\b(?:sos|prn|as\s+needed|when\s+required|if\s+needed)\b")
STAT = re.compile(r"\bstat\b")
BEDTIME = re.compile(r"\b(?:hs|at\s+bedtime|at\s+night)\b")
BEFORE_MEALS = re.compile(r"\b(?:ac|before\s+(?:meals?|food|breakfast)|empty\s+stomach)\b")
AFTER_MEALS = re.compile(r"\b(?:pc|after\s+(?:meals?|food|breakfast)|with\s+(?:meals?|food))\b")

# "1+0+1", "1-0-1", "1+1+1", "½+0+½" (morning, afternoon, night)
SLOTS = re.compile(r"(?<![\d/.])([\d½¼.]+)\s*[+-]\s*([\d½¼.]+)\s*[+-]\s*([\d½¼.]+)(?![\d/])")
SLOT_NAMES = ("morning", "afternoon", "night")

STRENGTH = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|mcg|µg|g|ml|iu|%)\b")
DOSE_BEFORE_FORM = re.compile(r"\b([\d½¼]+(?:\.\d+)?)\s*(" + "|".join(sorted(FORMS, key=len, reverse=True)) + r")\b")
DOSE_ML = re.compile(r"\b(\d+(?:\.\d+)?)\s*(?:ml|mL)\b(?!\s*/)")

# "x 5/7" (days), "x 2/52" (weeks), "x 1/12" (months); "for 10 days", "x 2 weeks", "5d"
FRACTION_DURATION = re.compile(r"(?:x|for)\s*(\d+)\s*/\s*(7|52|12)\b")
WORD_DURATION = re.compile(
    r"(?:x|for)?\s*(\d+)\s*(d|days?|w|wks?|weeks?|m|months?)\b(?!\s*/)"
)
UNIT_DAYS = {"d": 1, "day": 1, "days": 1, "w": 7, "wk": 7, "wks": 7, "week": 7, "weeks": 7,
             "m": 30, "month": 30, "months": 30}


@dataclass
class Directions:
    raw: str
    form: str | None = None
    strength: str | None = None
    dose: float | None = None
    dose_unit: str | None = None
    times_per_day: float | None = None
    slots: list[str] = field(default_factory=list)
    every_hours: int | None = None
    as_needed: bool = False
    once_only: bool = False
    timing: str | None = None
    duration_days: int | None = None

    def describe(self) -> str:
        """A plain-English sentence, leaving out anything that wasn't parsed."""
        parts = []
        if self.dose is not None:
            unit = self.dose_unit or "dose"
            plural = "" if self.dose <= 1 or unit in {"ml", "drops"} else "s"
            parts.append(f"{_fmt(self.dose)} {unit}{plural}")

        if self.once_only:
            parts.append("once, immediately")
        elif self.every_hours:
            parts.append(f"every {self.every_hours} hours")
        elif self.times_per_day:
            how_often = {1: "once a day", 2: "twice a day", 3: "three times a day",
                         4: "four times a day"}.get(int(self.times_per_day),
                                                    f"{_fmt(self.times_per_day)} times a day")
            if self.slots:
                how_often += f" ({_join(self.slots)})"
            parts.append(how_often)
        if self.as_needed:
            parts.append("only when needed")
        if self.timing:
            parts.append(self.timing)
        if self.duration_days:
            parts.append(f"for {_fmt_duration(self.duration_days)}")

        if not parts:
            return "Directions not recognised. Check the prescription or ask your pharmacist."
        sentence = ", ".join(parts)
        return sentence[0].upper() + sentence[1:] + "."


def parse_directions(line: str) -> Directions:
    """Parse one prescription line, e.g. "Tab Esita 10mg 1+0+0 x 1 month PC"."""
    text = " ".join(line.replace("×", "x").split())
    low = text.lower()
    d = Directions(raw=text)

    strength = STRENGTH.search(low)
    if strength:
        d.strength = f"{strength.group(1)} {strength.group(2)}"

    form_match = DOSE_BEFORE_FORM.search(low)
    for word in re.findall(r"[a-z]+", low):
        if word in FORMS:
            d.form = FORMS[word]
            break

    slots = SLOTS.search(low)
    if slots:
        amounts = [_num(x) for x in slots.groups()]
        taken = [(name, amt) for name, amt in zip(SLOT_NAMES, amounts) if amt]
        d.slots = [name for name, _ in taken]
        d.times_per_day = len(taken)
        if taken and len({amt for _, amt in taken}) == 1:
            d.dose = taken[0][1]
            d.dose_unit = d.form
    else:
        if form_match:
            d.dose, d.dose_unit = _num(form_match.group(1)), FORMS[form_match.group(2)]
        elif d.form in {"syrup", "suspension"}:
            ml = [m for m in DOSE_ML.finditer(low) if not strength or m.start() != strength.start()]
            if ml:
                d.dose, d.dose_unit = float(ml[-1].group(1)), "ml"

        hourly = HOURLY.search(low)
        if hourly:
            d.every_hours = int(hourly.group(1))
            d.times_per_day = 24 / d.every_hours
        else:
            for word in re.findall(r"[a-z]+", low):
                if word in FREQUENCY_CODES:
                    d.times_per_day = FREQUENCY_CODES[word]
                    break

    if d.dose is not None and d.dose_unit is None:
        d.dose_unit = d.form

    d.as_needed = bool(AS_NEEDED.search(low))
    d.once_only = bool(STAT.search(low))

    if BEDTIME.search(low):
        d.timing = "at bedtime"
        if d.times_per_day is None:
            d.times_per_day = 1
    elif BEFORE_MEALS.search(low):
        d.timing = "before meals"
    elif AFTER_MEALS.search(low):
        d.timing = "after meals"

    d.duration_days = _duration(low)
    return d


def _duration(low: str) -> int | None:
    fraction = FRACTION_DURATION.search(low)
    if fraction:
        count, base = int(fraction.group(1)), fraction.group(2)
        return count * {"7": 1, "52": 7, "12": 30}[base]
    for m in WORD_DURATION.finditer(low):
        unit = m.group(2)
        if unit in UNIT_DAYS:
            return int(m.group(1)) * UNIT_DAYS[unit]
    return None


def _num(token: str) -> float:
    return {"½": 0.5, "¼": 0.25}.get(token) or float(token)


def _fmt(value: float) -> str:
    if value == 0.5:
        return "half a"
    return str(int(value)) if float(value).is_integer() else str(value)


def _fmt_duration(days: int) -> str:
    if days % 30 == 0:
        n = days // 30
        return f"{n} month" + ("s" if n > 1 else "")
    if days % 7 == 0:
        n = days // 7
        return f"{n} week" + ("s" if n > 1 else "")
    return f"{days} day" + ("s" if days > 1 else "")


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]
