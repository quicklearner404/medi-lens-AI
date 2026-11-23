"""Score MediLens on the synthetic prescription set.

    python evaluation/run.py              # replay recorded RxNorm responses (offline)
    python evaluation/run.py --record     # query RxNorm live and refresh the recording
    python evaluation/run.py --check      # fail if results fall below evaluation/baseline.json

Writes evaluation/results/metrics.json and evaluation/results/report.md.

For every medicine on every prescription:

- detection     was the medicine line found, with the right written name?
- identification
    correct     matched to the true ingredients
    abstained   reported as "not recognised" (safe, but unhelpful)
    wrong       matched to a different medicine (the dangerous outcome)
  For invented names the only correct outcome is "not recognised".
- directions    each expected field (times per day, dose, slots, timing,
                duration, as needed) compared with what was parsed
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from medilens.prescription import read_prescription  # noqa: E402
from medilens.rxnorm import RXNAV, RxNormClient  # noqa: E402

CASES = HERE / "cases.jsonl"
RECORDING = HERE / "rxnorm_recording.json"
RESULTS = HERE / "results"
BASELINE = HERE / "baseline.json"
FIELDS = ["times_per_day", "slots", "dose", "dose_unit", "timing", "duration_days", "as_needed"]


def rxnorm_client(record: bool) -> tuple[RxNormClient, dict]:
    recorded: dict = {} if record else json.loads(RECORDING.read_text())

    def replay(request: httpx.Request) -> httpx.Response:
        key = f"{request.url.path}?{request.url.query.decode()}"
        if key not in recorded:
            raise SystemExit(f"No recorded response for {key}. Run with --record.")
        return httpx.Response(200, json=recorded[key])

    def save(response: httpx.Response) -> None:
        response.read()
        recorded[f"{response.request.url.path}?{response.request.url.query.decode()}"] = response.json()

    if record:
        http = httpx.Client(base_url=RXNAV, timeout=20, event_hooks={"response": [save]})
    else:
        http = httpx.Client(base_url=RXNAV, transport=httpx.MockTransport(replay))
    return RxNormClient(client=http), recorded


def identification(expected: list[str] | None, match) -> str:
    if match is None:
        return "correct" if expected is None else "abstained"
    if expected is None:
        return "wrong"
    found = {i.name.lower() for i in match.ingredients}
    return "correct" if found == {e.lower() for e in expected} else "wrong"


def same(field: str, expected, got) -> bool:
    if isinstance(expected, float) or isinstance(got, float):
        return got is not None and expected is not None and abs(float(expected) - float(got)) < 1e-6
    if field == "slots":
        return list(expected or []) == list(got or [])
    return expected == got


def evaluate(cases: list[dict], rxnorm: RxNormClient) -> dict:
    detection = Counter()
    outcomes = defaultdict(Counter)          # group -> outcome -> count
    field_scores = defaultdict(Counter)      # field -> correct/total
    failures = []
    fully_correct = 0

    for case in cases:
        predicted = read_prescription(case["text"])
        unused = list(predicted)
        for truth in case["medicines"]:
            item = next((p for p in unused if p.written_name.lower() == truth["written_name"].lower()), None)
            if item is None:
                detection["missed"] += 1
                failures.append((case["id"], truth["written_name"], "not detected", ""))
                continue
            unused.remove(item)
            detection["found"] += 1

            group = ("invented name" if truth["ingredients"] is None
                     else "unknown real brand" if truth["true_name"] in {"Esita", "Arinac"}
                     else "typo" if truth["typo"] else "known name")
            outcome = identification(truth["ingredients"], rxnorm.identify(item.written_name))
            outcomes[group][outcome] += 1
            if outcome != "correct":
                failures.append((case["id"], truth["written_name"], f"identification: {outcome}",
                                 f"expected {truth['ingredients']}"))

            all_fields = True
            for field, expected in truth["directions"].items():
                got = getattr(item.directions, field)
                ok = same(field, expected, got)
                field_scores[field]["correct"] += ok
                field_scores[field]["total"] += 1
                if not ok:
                    all_fields = False
                    failures.append((case["id"], truth["written_name"], f"directions.{field}",
                                     f"expected {expected!r}, got {got!r} | {item.line!r}"))
            fully_correct += outcome == "correct" and all_fields
        detection["extra"] += len(unused)
        for extra in unused:
            failures.append((case["id"], extra.written_name, "extra item", extra.line))

    total = detection["found"] + detection["missed"]
    known = sum(outcomes[g][o] for g in ("known name", "typo") for o in outcomes[g])
    return {
        "medicines": total,
        "detection_recall": detection["found"] / total,
        "detection_extra": detection["extra"],
        "identification": {g: dict(c) for g, c in sorted(outcomes.items())},
        "known_name_accuracy": sum(outcomes[g]["correct"] for g in ("known name", "typo")) / known,
        "wrong_matches": sum(c["wrong"] for c in outcomes.values()),
        "directions": {f: round(field_scores[f]["correct"] / field_scores[f]["total"], 3)
                       for f in FIELDS if field_scores[f]["total"]},
        "fully_correct": fully_correct / total,
        "failures": failures,
    }


def report(m: dict) -> str:
    lines = [
        "# MediLens evaluation",
        "",
        f"Synthetic set: {m['medicines']} medicines on 50 printed prescriptions "
        "(`evaluation/cases.jsonl`, ground truth written by hand).",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Medicine lines detected | {m['detection_recall']:.1%} |",
        f"| Extra (non-medicine) lines taken as medicines | {m['detection_extra']} |",
        f"| Known names identified correctly (incl. typos) | {m['known_name_accuracy']:.1%} |",
        f"| **Wrong matches (dangerous)** | **{m['wrong_matches']}** |",
        f"| Medicines fully correct (identity + every direction field) | {m['fully_correct']:.1%} |",
        "",
        "## Identification by group",
        "",
        "| Group | Correct | Abstained (\"not recognised\") | Wrong |",
        "|---|---|---|---|",
    ]
    for group, c in m["identification"].items():
        lines.append(f"| {group} | {c.get('correct', 0)} | {c.get('abstained', 0)} | {c.get('wrong', 0)} |")
    lines += ["", "For invented names, \"correct\" means they were reported as not recognised.", "",
              "## Directions, per field", "", "| Field | Accuracy |", "|---|---|"]
    lines += [f"| {f} | {v:.1%} |" for f, v in m["directions"].items()]
    lines += ["", f"## Failures ({len(m['failures'])})", "", "| Case | Medicine | Problem | Detail |",
              "|---|---|---|---|"]
    lines += [f"| {c} | {n} | {p} | {d.replace('|', '/')} |" for c, n, p, d in m["failures"]]
    return "\n".join(lines) + "\n"


def regressions(metrics: dict, baseline: dict) -> list[str]:
    """Safety limits are absolute; scores may not drop below the recorded baseline."""
    problems = []
    if metrics["wrong_matches"] > baseline["max_wrong_matches"]:
        problems.append(f"wrong matches: {metrics['wrong_matches']} (allowed {baseline['max_wrong_matches']})")
    invented = metrics["identification"].get("invented name", {})
    if invented.get("wrong", 0):
        problems.append(f"invented names matched to a real medicine: {invented['wrong']}")
    for key in ("detection_recall", "known_name_accuracy", "fully_correct"):
        if metrics[key] < baseline[key] - 1e-9:
            problems.append(f"{key}: {metrics[key]:.3f} < baseline {baseline[key]:.3f}")
    for field, floor in baseline["directions"].items():
        if metrics["directions"].get(field, 0) < floor - 1e-9:
            problems.append(f"directions.{field}: {metrics['directions'].get(field, 0):.3f} < baseline {floor:.3f}")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--record", action="store_true", help="query RxNorm live and save the responses")
    parser.add_argument("--check", action="store_true", help="fail if results fall below the baseline")
    args = parser.parse_args()

    cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line]
    rxnorm, recorded = rxnorm_client(args.record)
    metrics = evaluate(cases, rxnorm)
    if args.record:
        RECORDING.write_text(json.dumps(recorded, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    RESULTS.mkdir(exist_ok=True)
    summary = {k: v for k, v in metrics.items() if k != "failures"}
    (RESULTS / "metrics.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (RESULTS / "report.md").write_text(report(metrics), encoding="utf-8")
    print(json.dumps(summary, indent=2))

    if args.check:
        problems = regressions(metrics, json.loads(BASELINE.read_text()))
        for problem in problems:
            print(f"REGRESSION {problem}", file=sys.stderr)
        if problems:
            sys.exit(1)
        print("Evaluation at or above baseline.")


if __name__ == "__main__":
    main()
