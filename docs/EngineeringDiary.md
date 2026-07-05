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