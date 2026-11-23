"""Turn prescription text into one explained card per medicine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import httpx

from medilens.directions import Directions
from medilens.druginfo import DrugInfo, DrugInfoClient
from medilens.prescription import read_prescription
from medilens.rxnorm import DrugMatch, RxNormClient

DISCLAIMER = (
    "MediLens explains what is written on your prescription using official drug information. "
    "It is not medical advice. Do not start, stop or change a medicine without asking your "
    "doctor or pharmacist."
)

@dataclass
class MedicineCard:
    line: str
    written_name: str
    directions: dict
    recognised: bool
    matched_name: str | None = None
    generic_name: str | None = None
    match_source: str | None = None
    info: dict | None = None
    needs_review: list[str] = field(default_factory=list)


class PrescriptionAnalyzer:
    def __init__(self, rxnorm: RxNormClient | None = None, druginfo: DrugInfoClient | None = None):
        self.rxnorm = rxnorm or RxNormClient()
        self.druginfo = druginfo or DrugInfoClient()
        self._info_cache: dict[tuple[str, ...], DrugInfo] = {}

    def analyze(self, text: str) -> list[MedicineCard]:
        return [self._card(item.line, item.written_name, item.directions)
                for item in read_prescription(text)]

    def _card(self, line: str, written: str, directions: Directions) -> MedicineCard:
        card = MedicineCard(
            line=line,
            written_name=written,
            directions={**asdict(directions), "summary": directions.describe()},
            recognised=False,
        )
        if directions.times_per_day is None and not (directions.once_only or directions.as_needed):
            card.needs_review.append("How often to take it could not be read.")

        try:
            match = self.rxnorm.identify(written)
        except httpx.HTTPError:
            card.needs_review.append("The drug database could not be reached. Please try again.")
            return card
        if match is None:
            card.needs_review.append(
                f'"{written}" was not recognised. Check the spelling, or ask your pharmacist '
                "for the generic name."
            )
            return card

        card.recognised = True
        card.matched_name = match.name
        card.generic_name = match.generic_name
        card.match_source = match.source
        if not match.exact:
            card.needs_review.append(f'Read as "{match.name}". Please confirm this is correct.')

        try:
            info = self._info(match)
        except httpx.HTTPError:
            card.needs_review.append("Drug information could not be loaded. Please try again.")
            return card
        card.info = asdict(info) if info.found else None
        if not info.found:
            card.needs_review.append("No official information was found for this medicine.")
        return card

    def _info(self, match: DrugMatch) -> DrugInfo:
        key = tuple(sorted(i.name for i in match.ingredients))
        if key not in self._info_cache:
            rxcui = match.ingredients[0].rxcui if len(match.ingredients) == 1 else match.rxcui
            self._info_cache[key] = self.druginfo.lookup([i.name for i in match.ingredients], rxcui)
        return self._info_cache[key]
