# Engineering Diary

This document records the day-to-day progress of MediLens AI.

The goal is to document not only what was built, but also the engineering decisions, lessons learned, mistakes, and open questions throughout development.

---

# Day 1

**Date:** July 5, 2026

## Working Hours

10:00 AM – 6:00 PM (planned)

---

## Objectives

- Define the project vision.
- Research OCR.
- Design a high-level architecture.
- Learn how authentication works.
- Set up project documentation.

---

## What I Learned

### Product Design

- A project should begin by identifying the target users and their pain points before writing code.
- A PRD helps define the project's goals, MVP, and future roadmap.

---

### OCR

Today I learned how classical OCR works.

Key stages include:

- Image preprocessing
- Character recognition
- Post-processing

I also learned that modern OCR systems such as Google Vision primarily rely on deep learning instead of handcrafted feature extraction.

An important realization was that OCR is still valuable even with multimodal LLMs because OCR produces structured text that can be searched, stored, and analyzed efficiently.

---

### Authentication

Today I finally understood the difference between:

- Authentication (Who are you?)
- Authorization (What are you allowed to do?)

I also learned why passwords should not be sent with every API request.

Using the carnival wristband analogy helped me understand why JWT tokens exist.

Firebase Authentication issues JWTs after successful login, and the backend verifies these tokens before processing requests.

---

### Software Architecture

I designed the first draft of MediLens' architecture.

Key decisions include:

- Flutter frontend
- FastAPI backend
- Firebase Authentication
- Separate OCR, RAG, and LLM services
- Service-oriented architecture

One important lesson was that the frontend should communicate only with the backend rather than calling AI services directly.

---

## Engineering Decisions

Current decisions:

- Flutter for mobile development.
- FastAPI for backend.
- Firebase Authentication for user authentication.
- OCR before RAG for Version 1.
- Printed prescriptions only for MVP.
- Handwritten prescriptions planned for future releases.

---

## Open Questions

Questions to research later:

- How Firebase verifies JWTs.
- Role-Based Access Control (RBAC).
- PostgreSQL vs MongoDB.
- Offline synchronization.
- Local vs encrypted cloud storage.
- Deployment strategy.
- Best OCR library for printed prescriptions.

---

## Challenges

One challenge today was understanding how the backend knows who is making each API request.

After reasoning through the problem instead of searching online immediately, I understood why JWTs exist.

---

## Reflection

Today's biggest takeaway was that software engineering is about understanding problems before choosing technologies.

Rather than memorizing concepts, I tried to reason through them first and then validated my understanding.

---

## Next Session Goals

- Create GitHub repository.
- Organize documentation.
- Initialize Flutter project.
- Initialize FastAPI backend.
- Build first API endpoint.
---

# Day 2

**Date:** November 23, 2026

## Rethinking the scope

Before writing more code I went back to the original problem. I stopped an SSRI because nobody explained what it was or that stopping suddenly causes withdrawal. That problem is about **medicines on a prescription**, not about accounts, roles or databases.

So for Version 1 I cut:

- Firebase Authentication, PostgreSQL and user roles
- Lab reports
- An LLM generating medical explanations

Version 1 only reads printed prescriptions, identifies each medicine, and explains it using official sources. Without accounts or a server-side database, no patient data has to be stored or protected on a server. Everything I cut is still a valid idea for later.

---

## Directions parser

The first real piece of the backend turns prescription shorthand into plain English:

`Tab Esita 10mg 1+0+1 x 5/7 PC` → "1 tablet, twice a day (morning and night), after meals, for 5 days."

### What it handles

- Latin frequency codes: OD, BD, TDS, QID, q8h, HS, SOS/PRN, stat
- The dose-slot notation used by doctors in Pakistan: `1+0+1`, `½-0-0`
- Fraction durations: `x 5/7` (days), `x 2/52` (weeks), `x 3/12` (months)
- Meal timing: AC / PC / empty stomach
- Telling the strength (`20mg`) apart from the dose (`1 cap`)

### Decisions

- **Conservative over clever.** If a field can't be read, it stays empty and the app says "not specified". A wrong frequency on a medicine is worse than no frequency.
- **Unequal slots don't get a single dose.** For `2+0+1` the parser records the times but not a dose, because "2 tablets" would be wrong at night.
- **Pure Python, no network.** The parser is the part I can test exhaustively, so it has no dependencies.

### Tests

27 test cases, including the exact sentence shown to the user for common prescriptions. Writing the expected sentences first made me decide how the app should actually speak to patients.

---

## Continuous integration

I added a GitHub Actions workflow that installs the backend and runs the tests on every push and pull request that touches `backend/`.

The parser will keep growing as I meet new prescription styles, and each new rule can quietly break an old one. With CI, every change is checked against all the earlier cases automatically, so I find out from a red check rather than from a wrong instruction on someone's screen.

---

## Identifying medicines with RxNorm

To explain a medicine I first need to know exactly which one it is. I'm using **RxNorm** from the US National Library of Medicine: every drug has a stable ID (RxCUI), and brands are linked to their ingredients, so "Augmentin" becomes amoxicillin + clavulanate.

### The surprise

RxNorm's approximate search always returns *something*, even for names it doesn't know. Testing it with medicines prescribed in Pakistan:

| Written | RxNorm's top match |
|---|---|
| Concor (bisoprolol, a heart medicine) | **Concord grape juice** |
| Esita (an escitalopram brand) | **a cosmetic SPF kit** |
| Risek (omeprazole) | an unrelated product |

If I had simply taken the top result, the app would have confidently explained the wrong thing. For a medical app that is the worst possible failure.

### What I did

- **Similarity check.** A candidate is accepted only if its name is at least 80% similar to what was written. Typos still work ("omeprazol" → omeprazole at 0.95, "Augmentn" → Augmentin at 0.94), while the bad matches above score far lower and are rejected.
- **International names.** RxNorm uses US names, so "paracetamol" returns nothing; it is "acetaminophen" there. I added a small mapping of international to US names (paracetamol, salbutamol, co-amoxiclav and others).
- **Local brand list.** Many Pakistani brands simply aren't in RxNorm, so there is a small brand → generic list. It is deliberately short, and every entry has to be checked against the pack or the DRAP drug registry. When a brand isn't known, the app says so and asks the user. It never guesses.

### Testing without the internet

The tests replay **real recorded RxNorm responses** (`scripts/record_rxnorm_fixtures.py`), so they run offline in CI and don't depend on an external service being up. If a test ever makes a request that wasn't recorded, it fails loudly instead of quietly going to the network.

### Open question

Escitalopram, the medicine that started this project, is sold here under brand names RxNorm doesn't know. Growing the local brand list reliably, from a trustworthy source, is the part I still need to solve.

---

## Explaining each medicine from official sources

Once a medicine is identified, the app needs to explain it. I decided early that **nothing medical will be generated**. Every sentence the user sees comes from an official source, with a link to it.

### Sources

- **MedlinePlus** (US National Library of Medicine): a short summary written for patients, e.g. "Escitalopram is used to treat depression… It is in a class of antidepressants called SSRIs." That is exactly the sentence I never got.
- **FDA drug labels** (openFDA / DailyMed): what the medicine is approved for, the boxed warning, and the label's key warnings.

### The "don't stop suddenly" flag

This is the feature the whole project is really about. For escitalopram, the FDA label says:

> Discontinuation syndrome: When discontinuing escitalopram, reduce dosage gradually whenever possible…

The app pulls that sentence out and shows it separately and prominently.

Getting this right took several rounds of testing against real labels:

- **First attempt:** any mention of "withdrawal" counted. For alprazolam it picked a sentence about *newborns* of mothers taking the drug, instead of the boxed warning that stopping suddenly "can be life-threatening". Sentences about neonates are now excluded, and explicit instructions (taper, gradually, abrupt) win over passing mentions.
- **False positive:** metformin's label says "gradual dose escalation", which is about *starting* the medicine. A sentence now has to mention stopping (discontinue, cessation, dose reduction) **and** how (gradually, taper, abrupt).
- **Older label format:** bisoprolol's label doesn't use the newer summary layout, so its "Abrupt Cessation of Therapy" warning was missed at first. Stopping a beta-blocker suddenly can cause a heart attack, so this one really mattered. The search now falls back to the full warnings text.
- **Wrong product:** prednisolone matched an *eye-drop* label at first. Oral labels are now preferred, because prescriptions are mostly tablets and syrups.

After these changes the flag appears for escitalopram, sertraline, alprazolam, clonazepam, bisoprolol, propranolol and prednisolone, and not for paracetamol, omeprazole, metformin or co-amoxiclav.

### Choosing the right label

openFDA returns many labels per medicine, including combination products ("acetaminophen, dextromethorphan, phenylephrine"). I pick the label whose active ingredients match exactly, preferring oral prescription labels and the most recent version. If only combination products exist, the app shows nothing from the label rather than describing a different product.

### Tests

Seven cases replayed from recorded real responses, including the alprazolam and metformin traps above and a made-up medicine name that must return nothing.

---

## Reading the whole prescription

Text recognition gives back every printed line: the doctor's letterhead, qualifications, clinic phone number, patient name and age, date, diagnosis, the medicines, and "Follow up after 4 weeks". Only the medicine lines matter here.

### How it works

- A **medicine line** starts with a dosage form (Tab, Cap, Syp, Inj, Drops…), optionally after numbering like `1.`, `3)` or `Rx`.
- The **written name** is everything between the form and the first word that starts the directions: a number (`20mg`, `120mg/5ml`, `1+0+0`), a frequency code (`OD`, `TDS`) or words like "after"/"for". Names that contain digits but start with a letter, like "Vitamin D3", survive.
- **Directions on the next line.** Doctors often write the name on one line and the dosing underneath:

  ```
  2. Tab Xanax 0.25mg
     0+0+1 x 2/52 at night
  ```

  A line that contains only directions is attached to the medicine above it.

### A bug the tests caught

My first rule for "this word starts the directions" only recognised plain strengths like `20mg`, so a syrup written as `Calpol 120mg/5ml` came out with the name "Calpol 120mg/5ml". The simpler rule (any word starting with a digit begins the directions) handles every strength format I've seen.

### Tests

A realistic test prescription with a letterhead, patient details (including numbers like age, date and blood pressure, which must not be mistaken for medicines), four medicines in different numbering styles, and a follow-up note.

---

## A crash I only found by running the real server

All the tests passed, but the first time I ran the actual API on a sample prescription it crashed. The cause was **Calpol**, the paracetamol syrup almost every child here has had. RxNorm still offers "Calpol" as a search result, but that entry was **retired in 2013**, and retired entries come back with empty details. My code assumed the details were always there.

### Fixes

- Retired entries are now skipped, and the lookup moves on to the next good candidate (or reports the medicine as unrecognised).
- Calpol is on the local brand list (→ paracetamol).
- A test reproduces RxNorm's exact behaviour for a retired entry.

The lesson for me: tests built only from recorded "good" responses can't catch the bad responses I haven't seen yet. Running the real thing with realistic input is part of testing, not an optional extra.

---

## The API

Everything now comes together behind one endpoint:

`POST /analyze` with the text of a prescription returns one card per medicine:

- what was written, and which medicine it was matched to
- the directions as a plain-English sentence
- the MedlinePlus summary, approved uses and warnings, with sources
- the "don't stop suddenly" warning when the label has one
- a `needs_review` list for anything the user should double-check

Every response also carries a disclaimer that this is not medical advice.

### Decisions

- **Text only, never the photo.** The app reads the prescription on the phone and sends only the text. Nothing is stored on the server.
- **Unrecognised doesn't mean useless.** If a brand isn't recognised (like Esita), the card still explains the directions, because those don't depend on knowing the medicine, and asks the user to check the generic name with a pharmacist.
- **Ask, don't assume.** A match below 90% name similarity is shown with "Read as X. Please confirm."
- **Failures belong on the card, not as an error page.** If RxNorm or openFDA is down, the card says so and the request still succeeds, so one slow service doesn't hide the rest of the prescription.

### Tests

API tests run a five-medicine prescription through the full pipeline using recorded responses, plus empty, oversized and "database offline" cases. All 65 backend tests pass.

---

# Day 3

**Date:** November 23, 2026

## An evaluation set

The unit tests show that individual rules work. They don't tell me how well MediLens reads a whole prescription it hasn't seen. For that I need an evaluation set: prescriptions with known correct answers, and a score.

### Where the correct answers come from

The most important rule: **the answers must not come from MediLens itself.** If I ran the system and saved its output as "expected", the evaluation would only check the code against itself.

So `evaluation/generate_cases.py` builds prescriptions from a hand-written catalogue. For every name I wrote down the true active ingredients (Augmentin → amoxicillin + clavulanate, salbutamol → albuterol in RxNorm's naming). The generator then assembles prescriptions and records the answer for each medicine.

### What's in it

50 prescriptions, 174 medicines:

- letterheads, qualifications, patient details, dates, diagnoses and footers, all of which must be ignored
- numbering styles (`1.`, `2)`, `-`, none) and form spellings (Tab, Tab., TAB, Tablet, Cap, Syp)
- directions on the same line or on the line below (30 prescriptions)
- shorthand (`1+0+1`, `BD`, `q8h`, `x 2/52`) **and plain English** that doctors also write ("twice daily", "three times a day", "1 tab morning and night"), some of which I know the parser doesn't handle yet
- **15 typos** (a dropped or doubled letter)
- **real brands MediLens can't know** (Esita, Arinac): the right behaviour is to say "not recognised"
- **invented names** (Zorbex, Nuvamax, Klortiva): matching these to any real medicine would be the worst possible error

The generator is seeded, so the same 50 cases come out every time.

### Limits

These cases test *reading*, not medicine. The combinations aren't clinically realistic (azithromycin as a capsule twice daily), and every case is clean printed text. Text recognition errors from photos come later. I also wrote both the generator and the parser, so some of my own blind spots will be in both. Real prescriptions will eventually be the real test.

---

## The first score

`evaluation/run.py` runs every prescription through MediLens and compares the result with the answers. Medicine identification has three outcomes, because they are not equally bad:

- **correct**: matched to the true ingredients
- **abstained**: "not recognised". Safe, but the user gets no help.
- **wrong**: matched to a different medicine. This is the dangerous one.

For invented names, the only correct outcome is "not recognised". Directions are scored field by field (times per day, dose, slots, timing, duration, as needed).

RxNorm responses are recorded (`--record`), so the evaluation replays offline and gives the same numbers every time.

### Baseline

| Metric | Value |
|---|---|
| Medicine lines detected | 99.4% |
| Known names identified correctly | 86.0% |
| **Wrong matches** | **2** |
| Invented names matched to a real medicine | 0 of 11 |
| Medicines fully correct | 68.4% |

### What failed, by cause

1. **The 2 "wrong matches" are co-amoxiclav.** The medicine was right, but the combination came back as a single ingredient called "amoxicillin / clavulanate" instead of two. That also means the FDA label search would fail for it.
2. **Very common brands are unrecognised:** Brufen (7 times), Amoxil (5), Ponstan (2). RxNorm still lists them, but as retired entries, the same problem as Calpol. Typos of brands on my local list (Disprn, Cocor, Calpl) also fail, because that list only matches exact names.
3. **Parser gaps:** "three times a day", "1 tab morning and night" and "one tablet" aren't understood. A syrup dose like "5 ml" printed without a strength is mistaken *for* the strength. Directions on the next line that start with a word ("three times a day…") aren't attached to their medicine.
4. **Some failures are bugs in my answer key.** The generator writes lines like "Cap Concor 1 tab BD" and then expects the unit "capsule". It also says "one tablet at night" has no timing, while the parser reads "at night" as bedtime, which is reasonable.

Esita and Arinac being "not recognised" is the **correct** behaviour. I have no data on them, and saying so is better than guessing.

Next: fix the answer key first, so the score measures MediLens and not my generator, then fix the system problems one at a time, measuring each.

---

## Fixing my answer key first

Before changing MediLens, I fixed the two bugs in the evaluation itself, so that every remaining failure is a real problem with the system:

- Directions now use the word for the form that was actually prescribed ("1 cap BD" under a capsule, "1 tab BD" under a tablet).
- "one tablet at night" is now expected to be read as bedtime.

The random sequence is unchanged, so these are the same 50 prescriptions with corrected answers. Fully correct medicines went from 68.4% to 71.8%, and timing from 96% to 100%, without touching MediLens. That is a good reminder that an evaluation can be wrong too, and that a score is only as trustworthy as its answer key.

---

## Fix 1: combination medicines

Co-amoxiclav is one name for two medicines, amoxicillin and clavulanate. RxNorm stores names like this as a "multiple-ingredient" concept, and my code treated that concept as a single ingredient called "amoxicillin / clavulanate". The identity was right, but the ingredient list was wrong, and searching FDA labels for "amoxicillin / clavulanate" finds nothing.

Combination concepts are now split into their real ingredients, the same way brands like Augmentin already were.

| | Before | After |
|---|---|---|
| Wrong matches | 2 | **0** |
| Known names identified | 86.0% | 87.3% |
| Fully correct | 71.8% | 72.4% |
