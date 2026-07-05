# Product Requirements Document (PRD)

# MediLens AI

## Problem Statement

Many patients leave medical appointments confused about their diagnosis, prescriptions, and treatment plans. Medical terminology is often difficult for non-medical users to understand, and patients may not know:

- Why a medicine was prescribed
- How to take it correctly
- Possible side effects
- What their lab reports actually mean

This confusion can lead to medication errors and poor treatment adherence.

---

## Target Users

### Primary Users

Regular patients who want a simple explanation of:

- Prescriptions
- Lab reports
- Medical terminology
- Medications

### Secondary Users

Family members or caregivers who help manage a patient's healthcare, especially elderly patients or people with chronic illnesses.

---

## User Pain Points

Patients often experience:

- Confusing handwritten or printed prescriptions
- Medical jargon that is difficult to understand
- Multiple medications with unclear purposes
- Difficulty tracking chronic diseases over time

### Real-world Motivation

While taking medication myself, I did not realize I had been prescribed an SSRI. I stopped taking it abruptly without understanding the consequences.

Similarly, my aunt manages diabetes and frequently has multiple appointments and lab reports. Organizing and understanding all this information is difficult.

These real-life experiences inspired MediLens AI.

---

## Product Vision

MediLens AI should allow patients to simply upload a prescription or medical report and receive a clear, human-readable explanation.

Instead of searching every medical term manually, patients should understand their healthcare in seconds.

---

## Minimum Viable Product (MVP)

Version 1 will support:

- Uploading printed prescriptions
- Uploading printed laboratory reports
- OCR-based text extraction
- AI-generated explanations in simple language
- Medicine explanations
- Report history

---

## Success Metrics

Technical Metrics

- High OCR accuracy for printed prescriptions
- High medicine recognition accuracy
- Fast response time

User Experience Metrics

- Patients can understand their reports without searching the internet
- Simple upload process
- Easy-to-read explanations
- Minimal user interaction required

---

## Future Features

Planned after MVP:

- Doctor dashboard
- Handwritten prescription support
- Disease tracking
- Health trend visualization
- Pharmacy integration
- Medication reminders
- Online medicine ordering

---

## User Flow

Patient

↓

Login

↓

Upload Prescription or Lab Report

↓

OCR extracts text

↓

Backend processes request

↓

Medical knowledge retrieval (RAG)

↓

LLM generates explanation

↓

Patient receives structured explanation

↓

Report saved to history

---

## Non-Goals

Version 1 will **not**:

- Diagnose diseases
- Replace doctors
- Recommend stopping medication
- Prescribe medicines
- Provide emergency medical advice
