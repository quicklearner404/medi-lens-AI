"""Generate the synthetic prescription evaluation set.

    python evaluation/generate_cases.py      # writes evaluation/cases.jsonl

Each case is the text of a printed prescription plus the correct answer for
every medicine on it. The answers come from the catalogue below, written by
hand, never from MediLens itself, so the evaluation measures the system
against independent ground truth.

The generator is seeded, so the same 50 cases are produced every time.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

SEED = 2026
N_CASES = 50
OUT = Path(__file__).resolve().parent / "cases.jsonl"

# name as written -> true active ingredients (RxNorm naming).
# None means no real medicine has this name: the right answer is "not recognised".
CATALOGUE = {
    # brands commonly prescribed in Pakistan
    "Panadol": ["acetaminophen"], "Calpol": ["acetaminophen"], "Brufen": ["ibuprofen"],
    "Ponstan": ["mefenamic acid"], "Augmentin": ["amoxicillin", "clavulanate"],
    "Amoxil": ["amoxicillin"], "Flagyl": ["metronidazole"], "Glucophage": ["metformin"],
    "Xanax": ["alprazolam"], "Lexapro": ["escitalopram"], "Zoloft": ["sertraline"],
    "Risek": ["omeprazole"], "Nexium": ["esomeprazole"], "Concor": ["bisoprolol"],
    "Norvasc": ["amlodipine"], "Lipitor": ["atorvastatin"], "Singulair": ["montelukast"],
    "Ventolin": ["albuterol"], "Zithromax": ["azithromycin"], "Synthroid": ["levothyroxine"],
    "Valium": ["diazepam"], "Disprin": ["aspirin"],
    # real brands MediLens has no way of knowing yet
    "Esita": ["escitalopram"], "Arinac": ["ibuprofen", "pseudoephedrine"],
    # generic names, including international spellings
    "paracetamol": ["acetaminophen"], "metformin": ["metformin"], "escitalopram": ["escitalopram"],
    "sertraline": ["sertraline"], "omeprazole": ["omeprazole"], "amlodipine": ["amlodipine"],
    "atorvastatin": ["atorvastatin"], "cetirizine": ["cetirizine"], "ciprofloxacin": ["ciprofloxacin"],
    "montelukast": ["montelukast"], "prednisolone": ["prednisolone"], "salbutamol": ["albuterol"],
    "levothyroxine": ["levothyroxine"], "co-amoxiclav": ["amoxicillin", "clavulanate"],
    # invented names: must never be matched to a real medicine
    "Zorbex": None, "Nuvamax": None, "Klortiva": None,
}
SYRUP_OK = {"Calpol", "Brufen", "paracetamol", "cetirizine", "salbutamol", "Augmentin", "Zithromax"}

# (written directions, expected fields). Fields not listed are not scored.
DIRECTIONS = [
    ("1+0+1", {"times_per_day": 2, "slots": ["morning", "night"], "dose": 1}),
    ("1+1+1", {"times_per_day": 3, "slots": ["morning", "afternoon", "night"], "dose": 1}),
    ("0+0+1", {"times_per_day": 1, "slots": ["night"], "dose": 1}),
    ("1+0+0", {"times_per_day": 1, "slots": ["morning"], "dose": 1}),
    ("½+0+½", {"times_per_day": 2, "slots": ["morning", "night"], "dose": 0.5}),
    ("OD", {"times_per_day": 1}),
    ("BD", {"times_per_day": 2}),
    ("TDS", {"times_per_day": 3}),
    ("QID", {"times_per_day": 4}),
    ("1 tab BD", {"times_per_day": 2, "dose": 1}),
    ("2 tabs TDS", {"times_per_day": 3, "dose": 2}),
    ("q8h", {"times_per_day": 3}),
    ("HS", {"times_per_day": 1, "timing": "at bedtime"}),
    ("SOS", {"as_needed": True}),
    ("1 tab SOS", {"as_needed": True, "dose": 1}),
    # plain-English phrasings that doctors also write
    ("twice daily", {"times_per_day": 2}),
    ("once a day", {"times_per_day": 1}),
    ("three times a day", {"times_per_day": 3}),
    ("1 tab morning and night", {"times_per_day": 2, "slots": ["morning", "night"], "dose": 1}),
    ("one tablet at night", {"times_per_day": 1, "dose": 1}),
]
SYRUP_DIRECTIONS = [
    ("5 ml TDS", {"times_per_day": 3, "dose": 5, "dose_unit": "ml"}),
    ("10 ml BD", {"times_per_day": 2, "dose": 10, "dose_unit": "ml"}),
    ("5ml SOS", {"as_needed": True, "dose": 5, "dose_unit": "ml"}),
]
TIMINGS = [("", None), ("", None), ("AC", "before meals"), ("PC", "after meals"),
           ("after meals", "after meals"), ("on empty stomach", "before meals")]
DURATIONS = [("", None), ("x 5/7", 5), ("x 2/52", 14), ("x 1/12", 30), ("for 10 days", 10),
             ("x 3 weeks", 21), ("for 1 month", 30), ("x 7 days", 7)]
FORMS = [("Tab", "tablet"), ("Tab.", "tablet"), ("TAB", "tablet"), ("Tablet", "tablet"),
         ("Cap", "capsule"), ("Cap.", "capsule")]
NUMBERING = ["{n}. ", "{n}) ", "- ", "", "{n}. "]
STRENGTHS = ["10mg", "20 mg", "500mg", "250mg", "5mg", "0.25mg", "40mg", ""]

DOCTORS = ["Dr. Ayesha Khan", "Dr. Bilal Ahmed", "Dr. Sana Malik", "Dr. Usman Tariq", "Dr. Hira Siddiqui"]
QUALIFICATIONS = ["MBBS, FCPS (Medicine)", "MBBS, MRCP", "MBBS, FCPS (Psychiatry)", "MBBS", "MBBS, MCPS"]
CLINICS = ["City Clinic, Lahore", "Shifa Medical Centre, Islamabad", "Al-Noor Hospital, Karachi",
           "Family Health Clinic, Rawalpindi", "Care Point Clinic, Multan"]
PATIENTS = ["Ali Raza", "Fatima Noor", "Hamza Iqbal", "Mariam Javed", "Zain Abbas", "Ayesha Tariq"]
DIAGNOSES = ["Generalised anxiety disorder", "URTI", "Type 2 diabetes", "Hypertension",
             "Acid peptic disease", "Asthma", "Migraine", "Depression", "UTI", ""]
FOOTERS = ["Follow up after 2 weeks", "Review in 1 month", "Avoid oily food", "Signature", ""]


def _typo(name: str, rng: random.Random) -> str:
    """One realistic slip: a dropped or doubled letter in the middle of the name."""
    i = rng.randrange(2, len(name) - 1)
    return name[:i] + name[i + 1:] if rng.random() < 0.5 else name[:i] + name[i] + name[i:]


def _medicine(rng: random.Random, n: int) -> tuple[list[str], dict]:
    name = rng.choice(list(CATALOGUE))
    written = name
    typo = name != name.lower() and len(name) > 5 and CATALOGUE[name] and rng.random() < 0.15
    if typo:
        written = _typo(name, rng)

    syrup = name in SYRUP_OK and rng.random() < 0.3
    if syrup:
        form_text = rng.choice(["Syp", "Syp."])
        directions, expected = rng.choice(SYRUP_DIRECTIONS)
        strength = rng.choice(["120mg/5ml", "250mg/5ml", ""])
    else:
        form_text, form = rng.choice(FORMS)
        directions, expected = rng.choice(DIRECTIONS)
        if expected.get("dose") is not None and "dose_unit" not in expected:
            expected = {**expected, "dose_unit": form}
        strength = rng.choice(STRENGTHS)

    timing_text, timing = rng.choice(TIMINGS)
    if "timing" in expected:
        timing_text, timing = "", expected["timing"]
    duration_text, duration = rng.choice(DURATIONS)
    expected = {**expected, "timing": timing, "duration_days": duration}

    head = rng.choice(NUMBERING).format(n=n) + " ".join(x for x in (form_text, written, strength) if x)
    tail = " ".join(x for x in (directions, timing_text, duration_text) if x)
    lines = [f"{head}\n   {tail}"] if rng.random() < 0.2 else [f"{head} {tail}"]

    truth = {
        "written_name": written,
        "true_name": name,
        "ingredients": CATALOGUE[name],
        "typo": bool(typo),
        "directions": expected,
    }
    return lines, truth


def make_case(rng: random.Random, case_id: int) -> dict:
    lines = [rng.choice(DOCTORS), rng.choice(QUALIFICATIONS), rng.choice(CLINICS),
             f"Patient: {rng.choice(PATIENTS)}   Age: {rng.randint(18, 75)}   "
             f"Date: {rng.randint(1, 28)}/{rng.randint(1, 12)}/2026"]
    diagnosis = rng.choice(DIAGNOSES)
    if diagnosis:
        lines.append(f"Diagnosis: {diagnosis}")
    if rng.random() < 0.6:
        lines.append("Rx")

    medicines = []
    for n in range(1, rng.randint(2, 5) + 1):
        med_lines, truth = _medicine(rng, n)
        lines.extend(med_lines)
        medicines.append(truth)

    footer = rng.choice(FOOTERS)
    if footer:
        lines.append(footer)
    return {"id": f"rx{case_id:02d}", "text": "\n".join(lines), "medicines": medicines}


def main() -> None:
    rng = random.Random(SEED)
    cases = [make_case(rng, i) for i in range(1, N_CASES + 1)]
    with OUT.open("w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")
    n_meds = sum(len(c["medicines"]) for c in cases)
    print(f"Wrote {len(cases)} prescriptions with {n_meds} medicines to {OUT.name}")


if __name__ == "__main__":
    main()
