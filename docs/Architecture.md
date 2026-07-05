# Architecture Document

## MediLens AI

## Purpose

This document describes the high-level software architecture of MediLens AI and explains the reasoning behind major design decisions.

The architecture is expected to evolve as the project grows.

---

# High-Level Architecture

```text
Patient
    │
    ▼
Flutter Mobile App
    │
    ▼
FastAPI Backend
    │
    ├──────────────┐
    │              │
    ▼              ▼
OCR Service     Authentication
    │              │
    ▼              ▼
RAG Pipeline   PostgreSQL
    │
    ▼
LLM
    │
    ▼
Response returned to Flutter
```

The Flutter application communicates only with the FastAPI backend. The backend is responsible for coordinating authentication, OCR, retrieval, AI inference, and database operations.

---

# Authentication

The application will use **Firebase Authentication** for user login.

Planned features include:

- Email/password authentication
- Email verification
- Secure authentication using Firebase-issued JWT tokens

The backend will verify Firebase tokens before allowing access to protected API endpoints.

One area I plan to research further is how Firebase tokens are verified by FastAPI and how role-based access control is implemented.

---

# User Roles

The application will support multiple user roles.

### Planned Roles

- Patient
- Doctor (future release)
- Administrator (future release)

Initially, the MVP will focus only on patient functionality.

Role-Based Access Control (RBAC) will determine which API endpoints each user can access.

---

# Privacy and Security

Medical information is highly sensitive.

Some design principles I want to follow include:

- Minimize storage of sensitive information whenever possible.
- Encrypt confidential medical information before storing it.
- Never expose database credentials or API keys to the Flutter application.
- Authenticate every protected request using Firebase-issued tokens.

I am also interested in researching offline-first architectures where patients can access some of their medical information locally while securely synchronizing data across devices.

---

# Service-Oriented Design

Instead of placing all application logic inside the Flutter application, MediLens separates responsibilities into independent services.

Planned services include:

- Authentication Service
- OCR Service
- Retrieval-Augmented Generation (RAG) Service
- LLM Service
- Storage Service

Separating these responsibilities improves maintainability and allows individual services to evolve independently.

---

# OCR Pipeline

Current planned flow:

Patient uploads report

↓

OCR extracts machine-readable text

↓

Text is cleaned and validated

↓

Structured text is forwarded to the RAG pipeline

---

# RAG Pipeline

The Retrieval-Augmented Generation pipeline is responsible for:

- Retrieving trusted medical references
- Providing relevant context to the language model
- Reducing hallucinations
- Improving explanation quality

The RAG pipeline remains independent from the OCR service.

---

# AI Processing

The language model receives:

- OCR output
- Retrieved medical context
- User query

The model generates a simplified explanation suitable for non-medical users.

---

# Storage Strategy

This area is still under investigation.

Current considerations include balancing:

- Patient privacy
- Cross-device synchronization
- Offline availability
- Security
- Performance

Possible approaches include encrypted cloud storage, local device storage, or a hybrid architecture.

Further research is required before making a final decision.

---

# Planned Request Flow

```text
Patient

↓

Flutter App

↓

FastAPI Backend

↓

Verify Firebase Authentication

↓

OCR Service

↓

RAG Service

↓

LLM

↓

Store Consultation

↓

Return Explanation

↓

Flutter displays result
```

---

# Current Open Questions

The following architectural decisions are intentionally left open while I continue researching.

- Should reports be stored locally, in the cloud, or both?
- What is the best synchronization strategy?
- Should OCR and RAG be separate microservices or internal backend modules?
- Which database is most appropriate (PostgreSQL, MongoDB, Firebase Firestore)?
- How should doctor and patient roles be implemented?

These questions will be revisited as the project evolves.