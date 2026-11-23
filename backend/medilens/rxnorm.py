"""Identify a medicine name from a prescription using RxNorm.

RxNorm (US National Library of Medicine) gives every drug concept a stable ID
(RxCUI) and links brands to their ingredients. Its approximate search always
returns *something*, even for names it doesn't know: "Concor" (a bisoprolol
brand) comes back as "Concord grape juice". So a candidate is only accepted
when its name is genuinely close to what was written.

Lookup order:
1. local brand list (brands sold in Pakistan that RxNorm doesn't cover)
2. international -> US name mapping (paracetamol -> acetaminophen)
3. RxNorm approximate search, accepted only above a similarity threshold
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

import httpx

RXNAV = "https://rxnav.nlm.nih.gov/REST"
DATA_DIR = Path(__file__).resolve().parent / "data"
MIN_SIMILARITY = 0.8
INGREDIENT_TYPES = {"IN", "MIN", "PIN"}


@dataclass
class Ingredient:
    rxcui: str
    name: str


@dataclass
class DrugMatch:
    written: str            # what was on the prescription
    name: str               # the concept it was matched to
    rxcui: str
    concept_type: str       # RxNorm term type: IN ingredient, BN brand, ...
    ingredients: list[Ingredient] = field(default_factory=list)
    source: str = "rxnorm"  # rxnorm | local-brand | synonym
    similarity: float = 1.0

    @property
    def generic_name(self) -> str:
        return " / ".join(i.name for i in self.ingredients) or self.name


def _load(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


class RxNormClient:
    def __init__(self, client: httpx.Client | None = None, timeout: float = 10.0):
        self._http = client or httpx.Client(base_url=RXNAV, timeout=timeout)
        self._cache: dict[str, dict] = {}
        self._brands = {k.lower(): v for k, v in _load("brands_pk.json")["brands"].items()}
        self._synonyms = {k.lower(): v for k, v in _load("synonyms.json")["synonyms"].items()}

    def identify(self, written: str) -> DrugMatch | None:
        """Match a written medicine name to an RxNorm concept, or return None."""
        term = _clean(written)
        if not term:
            return None

        source = "rxnorm"
        if term in self._brands:
            term, source = self._brands[term]["generic"].lower(), "local-brand"
        if term in self._synonyms:
            term = self._synonyms[term]
            source = "synonym" if source == "rxnorm" else source

        candidate = self._best_candidate(term)
        if candidate is None:
            return None
        rxcui, name, similarity = candidate

        concept_type = self._get(f"/rxcui/{rxcui}/properties.json")["properties"]["tty"]
        match = DrugMatch(
            written=written, name=name, rxcui=rxcui, concept_type=concept_type,
            source=source, similarity=round(similarity, 2),
        )
        match.ingredients = self._ingredients(rxcui, name, concept_type)
        return match

    def _best_candidate(self, term: str) -> tuple[str, str, float] | None:
        data = self._get("/approximateTerm.json", term=term, maxEntries=5)
        candidates = data.get("approximateGroup", {}).get("candidate", [])
        best = None
        for c in candidates:
            if c.get("source") != "RXNORM" or not c.get("name"):
                continue
            similarity = SequenceMatcher(None, term, c["name"].lower()).ratio()
            if similarity >= MIN_SIMILARITY and (best is None or similarity > best[2]):
                best = (c["rxcui"], c["name"], similarity)
        return best

    def _ingredients(self, rxcui: str, name: str, concept_type: str) -> list[Ingredient]:
        if concept_type in INGREDIENT_TYPES:
            return [Ingredient(rxcui, name)]
        data = self._get(f"/rxcui/{rxcui}/related.json", tty="IN")
        groups = data.get("relatedGroup", {}).get("conceptGroup", [])
        return [Ingredient(c["rxcui"], c["name"])
                for g in groups for c in g.get("conceptProperties", [])]

    def _get(self, path: str, **params) -> dict:
        key = path + "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        if key not in self._cache:
            response = self._http.get(path, params=params)
            response.raise_for_status()
            self._cache[key] = response.json()
        return self._cache[key]


def _clean(written: str) -> str:
    """Lower-case and drop strengths and punctuation: 'Risek 20mg' -> 'risek'."""
    text = written.lower()
    text = re.sub(r"\d+(\.\d+)?\s*(mg|mcg|µg|g|ml|iu|%)\b", " ", text)
    text = re.sub(r"[^a-z\s/-]", " ", text)
    return " ".join(text.split())
