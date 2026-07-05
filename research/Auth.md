# OCR Research Notes

## Purpose

This document summarizes my research on Optical Character Recognition (OCR) and explains why it is important for MediLens AI.

---

# What is OCR?

Optical Character Recognition (OCR) is the process of converting text contained in an image into machine-readable text.

Computers cannot directly search or analyze text inside an image because images are stored as pixels rather than editable characters. OCR bridges this gap by extracting text that software can process.

---

# Classical OCR Pipeline

The traditional OCR pipeline consists of several stages.

## 1. Image Preprocessing

Before recognition, the image quality is improved through preprocessing techniques such as:

- Binarization
- Deskewing
- Noise removal (despeckling)
- Contrast enhancement

These steps improve recognition accuracy.

---

## 2. Text Recognition

Classical OCR systems recognize characters using techniques such as:

- Pattern matching
- Feature extraction

Feature extraction identifies characteristics such as loops, intersections, and line segments before matching them to known characters.

---

## 3. Post-processing

The extracted text is corrected using language models, dictionaries, or contextual information to reduce recognition errors.

---

# Modern OCR

Modern OCR systems such as Google Vision rely primarily on deep learning instead of handcrafted feature extraction.

Modern systems typically perform:

- Text detection
- Character recognition
- Document layout understanding
- Language correction

Rather than simply extracting text, they understand the structure of an entire document.

---

# OCR vs Multimodal AI

A multimodal LLM can often understand an image directly.

However, OCR remains valuable because it:

- Produces structured text
- Supports database storage
- Enables searching and analytics
- Is generally cheaper for large-scale document processing

---

# Why OCR for MediLens?

Version 1 of MediLens focuses on printed prescriptions and laboratory reports.

OCR extracts structured medical text, which is then passed to the Retrieval-Augmented Generation (RAG) pipeline for explanation.

Future versions may evaluate multimodal models for handwritten prescriptions.

---

# Key Learning

Although multimodal AI is becoming increasingly capable, OCR continues to play an important role in document processing pipelines due to its efficiency, cost-effectiveness, and ability to generate structured data.