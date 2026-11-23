"""Record real RxNorm responses used by the tests, so they run offline.

    python scripts/record_rxnorm_fixtures.py

Re-run when adding test cases; the output is tests/fixtures/rxnorm.json.
"""

import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from medilens.rxnorm import RXNAV, RxNormClient  # noqa: E402

TERMS = [
    "Risek 20mg", "Concor", "Esita", "Panadol", "paracetamol", "Augmentn", "Calpol",
    "omeprazol", "Glucophage 500mg", "co-amoxiclav", "Xanax", "Disprin", "salbutamol", "Brufen", "Ponstan", "omeprazole 20mg", "Disprn", "Calpl",
]
OUT = ROOT / "tests" / "fixtures" / "rxnorm.json"


def main() -> None:
    recorded: dict[str, dict] = {}

    def save(response: httpx.Response) -> None:
        response.read()
        request = response.request
        recorded[request.url.path + "?" + request.url.query.decode()] = response.json()

    with httpx.Client(base_url=RXNAV, timeout=20, event_hooks={"response": [save]}) as http:
        client = RxNormClient(client=http)
        for term in TERMS:
            client.identify(term)

    OUT.write_text(json.dumps(recorded, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Recorded {len(recorded)} responses to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
