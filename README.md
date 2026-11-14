# Ajaia DocFlow — Lightweight Collaborative Document Editor

A focused, full-stack collaborative document workspace inspired by Google Docs, built for the **Ajaia LLC AI-Native Full Stack Developer Assignment**.

## Live Demo & Seeded Accounts

- **Live URL:** [INSERT_DEPLOYED_URL_HERE]
- **Pre-seeded Workspace Accounts (1-click switcher in top-right header):**
  1. `danish@ajaia.demo` — **Muhammad Danish** (Default active user; owns _Q4 AI Product Architecture Spec_)
  2. `alex@ajaia.demo` — **Alex Rivera** (Owns _Internal Productivity Tool — Review Notes_, shared with Danish)
  3. `sara@ajaia.demo` — **Sara Khan** (Available for testing sharing & View/Edit access enforcement)

## Core Capabilities Implemented

1. **Document Creation & Rich-Text Editing**
   - Create new documents, inline rename titles, edit rich-text content, and persist across page refreshes.
   - Formatting toolbar supporting **H1**, **H2**, **Normal**, **Bold**, **Italic**, **Underline**, **Bulleted Lists**, and **Numbered Lists**.
   - Debounced auto-save (1.8s) plus explicit manual **Save** action and **Export `.md`** stretch feature.
2. **Product-Relevant File Import**
   - Upload `.txt`, `.md`, or `.docx` files (up to 5 MB) from the sidebar to convert them directly into new editable rich-text documents.
   - Unsupported file types and oversized files are validated on both client and server with clear error messages.
3. **Sharing & Access Control**
   - Explicit document ownership (`Owner` badge) and collaborator sharing (`Can Edit` vs `Can View`).
   - Clear sidebar separation between **Owned by Me** and **Shared with Me**.
   - Server-side authorization enforces read/write boundaries (`403 Forbidden` on unauthorized reads or view-only mutation attempts).
4. **Persistence & Security**
   - Relational SQLite schema (`users`, `documents`, `document_shares`) with foreign keys and automatic demo seeding.
   - Server-side HTML sanitization via `bleach` to prevent XSS payloads while preserving safe rich-text formatting.

## Local Setup & Run Instructions

### Prerequisites

- Python 3.10+

### 1. Clone & Create Virtual Environment

```bash
git clone [https://github.com/Danish-kh-IT/ajaia-docflow.git](https://github.com/Danish-kh-IT/ajaia-docflow.git)
cd ajaia-docflow
python -m venv venv
# Windows (Git Bash):
source venv/Scripts/activate
# macOS / Linux:
# source venv/bin/activate
```
