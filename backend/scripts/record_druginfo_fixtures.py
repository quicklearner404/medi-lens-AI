"""Record real openFDA and MedlinePlus responses used by the tests.

    python scripts/record_druginfo_fixtures.py

Label results are trimmed to the fields MediLens reads, to keep the file small.
The output is tests/fixtures/druginfo.json.
"""

import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from medilens.druginfo import DrugInfoClient  # noqa: E402

# (ingredients, RxCUI for MedlinePlus)
CASES = [
    (["escitalopram"], "321988"),
    (["alprazolam"], "596"),
    (["bisoprolol"], "19484"),
    (["metformin"], "6809"),
    (["acetaminophen"], "161"),
    (["amoxicillin", "clavulanate"], "19711"),
    (["notarealmedicine"], None),
]
LABEL_FIELDS = {
    "indications_and_usage", "boxed_warning", "warnings_and_cautions", "warnings", "stop_use",
    "dosage_and_administration", "effective_time", "set_id",
}
OPENFDA_FIELDS = {"generic_name", "route", "product_type"}
OUT = ROOT / "tests" / "fixtures" / "druginfo.json"


def _trim(body: dict) -> dict:
    for label in body.get("results", []):
        for key in list(label):
            if key not in LABEL_FIELDS | {"openfda"}:
                del label[key]
        label["openfda"] = {k: v for k, v in label.get("openfda", {}).items() if k in OPENFDA_FIELDS}
    return body


def main() -> None:
    recorded: dict[str, dict] = {}

    def save(response: httpx.Response) -> None:
        response.read()
        url = response.request.url
        body = response.json()
        if url.host == "api.fda.gov":
            body = _trim(body)
        recorded[f"{url.host}{url.path}?{url.query.decode()}"] = {"status": response.status_code, "body": body}

    with httpx.Client(timeout=30, event_hooks={"response": [save]}) as http:
        client = DrugInfoClient(client=http)
        for ingredients, rxcui in CASES:
            client.lookup(ingredients, rxcui)

    OUT.write_text(json.dumps(recorded, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Recorded {len(recorded)} responses to {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
