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
