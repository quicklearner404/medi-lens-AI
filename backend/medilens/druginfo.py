"""Official information about a medicine, with sources.

Two public sources, both from US government agencies:

- **MedlinePlus** (National Library of Medicine): a plain-language summary
  written for patients ("Escitalopram is used to treat depression...").
- **FDA drug labels** via openFDA: what the medicine is approved for, the boxed
  warning, and the label's key warnings.

Nothing here is generated: every sentence is taken from one of these sources
and comes with a link to it. When a label says the medicine must not be
stopped suddenly (SSRIs, benzodiazepines, beta-blockers, steroids...), that is
surfaced as a separate flag so the app can show it prominently.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

import httpx

OPENFDA = "https://api.fda.gov/drug/label.json"
MEDLINEPLUS = "https://connect.medlineplus.gov/service"
RXNORM_CODE_SYSTEM = "2.16.840.1.113883.6.88"
DAILYMED_LABEL = "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={}"

# Salt and form words that don't change which medicine a label is for.
SALT_WORDS = {
    "and", "hcl", "hydrochloride", "sodium", "potassium", "calcium", "magnesium",
    "oxalate", "maleate", "fumarate", "succinate", "tartrate", "besylate", "mesylate",
    "citrate", "sulfate", "phosphate", "acetate", "hydrobromide", "hbr", "monohydrate",
    "dihydrate", "trihydrate", "extended", "release", "delayed", "oral", "tablets",
    "capsules", "solution", "suspension", "usp", "er", "xr", "dr", "sr", "odt",
}

# How a label says the medicine must not be stopped suddenly. A sentence must
# talk about stopping AND say how (gradually, taper, abrupt...), so "gradual dose
# escalation" when starting a medicine doesn't count.
STOPPING = re.compile(r"discontinu|\bstop|cessation|withdraw|dosage reduction|reduc\w* (the )?dos", re.I)
HOW = re.compile(r"\btaper|gradual|abrupt|rapid", re.I)
DO_NOT_STOP = re.compile(r"do not stop", re.I)
STOP_MENTION = re.compile(
    r"discontinuation (syndrome|symptoms|reactions)|withdrawal (reactions|symptoms|syndrome)",
    re.IGNORECASE,
)
NOT_ABOUT_PATIENT = re.compile(r"neonat|newborn|infant", re.IGNORECASE)

SECTION_TITLE = re.compile(
    r"^\s*(\d+(\.\d+)?\s+)?(INDICATIONS\s*(AND|&)\s*USAGE|WARNINGS\s*AND\s*PRECAUTIONS|WARNINGS"
    r"|DOSAGE\s*AND\s*ADMINISTRATION|BOXED WARNING|WARNING|Uses|Warnings|Stop use and ask a doctor if)"
    r"\s*:?\s*"
)


@dataclass
class Source:
    name: str
    url: str


@dataclass
class DrugInfo:
    generic_name: str
    summary: str | None = None
    used_for: str | None = None
    boxed_warning: str | None = None
    key_warnings: list[str] = field(default_factory=list)
    stop_gradually: str | None = None      # the label's own words, when present
    label_date: str | None = None
    sources: list[Source] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return bool(self.summary or self.used_for)


class DrugInfoClient:
    def __init__(self, client: httpx.Client | None = None, timeout: float = 15.0):
        self._http = client or httpx.Client(timeout=timeout)

    def lookup(self, ingredients: list[str], rxcui: str | None = None) -> DrugInfo:
        """Information for a medicine given its ingredient names (and RxCUI if known)."""
        info = DrugInfo(generic_name=" / ".join(ingredients))
        if rxcui:
            self._add_medlineplus(info, rxcui)
        label = self._find_label(ingredients)
        if label:
            self._add_label(info, label)
        return info

    # ----------------------------------------------------------- MedlinePlus
    def _add_medlineplus(self, info: DrugInfo, rxcui: str) -> None:
        params = {
            "mainSearchCriteria.v.cs": RXNORM_CODE_SYSTEM,
            "mainSearchCriteria.v.c": rxcui,
            "knowledgeResponseType": "application/json",
            "informationRecipient.languageCode.c": "en",
        }
        response = self._http.get(MEDLINEPLUS, params=params)
        if response.status_code != 200:
            return
        for entry in response.json().get("feed", {}).get("entry", []):
            url = next((link["href"] for link in entry.get("link", [])), "")
            if "/druginfo/meds/" not in url:  # drug page, not a general health topic
                continue
            info.summary = _plain(entry.get("summary", {}).get("_value", ""))
            info.sources.append(Source("MedlinePlus", url.split("?")[0]))
            return

    # ------------------------------------------------------------ FDA label
    def _find_label(self, ingredients: list[str]) -> dict | None:
        query = " AND ".join(f'openfda.generic_name:"{name}"' for name in ingredients)
        response = self._http.get(OPENFDA, params={"search": query, "limit": 20})
        if response.status_code != 200:  # openFDA answers 404 when nothing matches
            return None

        wanted = {w for name in ingredients for w in _words(name)}
        best, best_key = None, None
        for label in response.json().get("results", []):
            if not label.get("indications_and_usage"):
                continue
            for generic in label.get("openfda", {}).get("generic_name", []):
                extra = len(_words(generic) - wanted)   # other active ingredients
                if not wanted <= _words(generic):
                    continue
                openfda = label.get("openfda", {})
                key = (extra,
                       "ORAL" not in openfda.get("route", []),       # prescriptions are mostly oral
                       openfda.get("product_type") != ["HUMAN PRESCRIPTION DRUG"],
                       -int(label.get("effective_time", "0")))
                if best_key is None or key < best_key:
                    best, best_key = label, key
        if best_key is not None and best_key[0] > 0:
            return None  # only combination products found; don't describe the wrong product
        return best

    def _add_label(self, info: DrugInfo, label: dict) -> None:
        info.used_for = _first_sentences(_section(label, "indications_and_usage"), 2)
        boxed = _section(label, "boxed_warning")
        if boxed:
            info.boxed_warning = _first_sentences(boxed, 2)

        warnings = _section(label, "warnings_and_cautions") or _section(label, "warnings")
        info.key_warnings = _highlights(warnings) or [_first_sentences(warnings, 2)] if warnings else []
        if label.get("stop_use"):                        # over-the-counter labels
            info.key_warnings.append(_first_sentences(_section(label, "stop_use"), 2))

        # One-line warning summaries first (cleanest wording), then full text.
        texts = [boxed or "", *_highlights(warnings, limit=None), warnings,
                 _section(label, "dosage_and_administration")]
        info.stop_gradually = (_sentence_matching(texts, _explicit_stop)
                               or _sentence_matching(texts, STOP_MENTION.search))

        info.label_date = _date(label.get("effective_time"))
        info.sources.append(Source("FDA drug label (DailyMed)", DAILYMED_LABEL.format(label["set_id"])))


# ---------------------------------------------------------------- helpers
def _section(label: dict, key: str) -> str:
    text = " ".join(label.get(key, []))
    text = SECTION_TITLE.sub("", text)                   # "1 INDICATIONS AND USAGE"
    text = re.sub(r"\[\s*see[^\]]*\]", "", text, flags=re.I)  # cross references
    text = re.sub(r"^[\s•·-]+", "", text)
    return " ".join(text.split())


def _highlights(text: str, limit: int | None = 6) -> list[str]:
    """Prescription labels open with one-line summaries ending in '( 5.3 )'."""
    head = re.split(r"\s5\.1\s+[A-Z]", text, maxsplit=1)[0]
    items = re.split(r"\(\s*[\d.,\s]+\)", head)
    if len(items) < 2:
        return []                                         # older label format without summaries
    warnings = [" ".join(i.split()).lstrip(".•·- ") for i in items]
    return [w for w in warnings if ":" in w and len(w.split()) > 3][:limit]


def _first_sentences(text: str, n: int) -> str:
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text.strip())
    return " ".join(sentences[:n]).strip()


def _explicit_stop(sentence: str) -> bool:
    return bool(DO_NOT_STOP.search(sentence) or (STOPPING.search(sentence) and HOW.search(sentence)))


def _sentence_matching(texts: list[str], matches) -> str | None:
    for text in texts:
        text = re.sub(r"\(\s*[\d.,\s]+\)", ".", text)                 # "( 4 , 5.2 )" references
        for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z])|\s\d+\.\d+\s+(?=[A-Z])", text):
            sentence = sentence.strip().lstrip(".•·- ").rstrip(" .") + "."
            if matches(sentence) and not NOT_ABOUT_PATIENT.search(sentence) and len(sentence) < 400:
                return sentence
    return None


def _words(name: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", name.lower()) if w not in SALT_WORDS}


def _plain(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    return " ".join(html.unescape(text).split())


def _date(yyyymmdd: str | None) -> str | None:
    if not yyyymmdd or len(yyyymmdd) != 8:
        return None
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"
