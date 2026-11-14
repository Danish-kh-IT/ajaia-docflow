# AI-Native Workflow Note

## 1. AI Tools Used

- **Primary AI Engineering Partner:** Gemini (used for architectural decomposition, scope prioritization, FastAPI/SQLite schema scaffolding, frontend UI generation, and edge-case test design).
- **Local IDE Environment:** VS Code with integrated Git Bash terminal for rapid execution, iterative verification, and `pytest` runs.

## 2. Where AI Materially Sped Up Execution

- **Problem Decomposition & Timeboxing:** Converted an open-ended prompt into a strict 4-hour milestone plan with clear deliverable boundaries before writing code.
- **Boilerplate & Multi-Format File Parsing:** Accelerated writing the `.docx` run-level parser (`python-docx`), Markdown converter, and responsive Tailwind CSS editor layout—saving ~90 minutes of manual UI and parser scaffolding.
- **Test Case Generation:** Quickly scaffolded isolated `TestClient` tests using temporary SQLite databases so test runs never pollute local or seeded state.

## 3. What AI-Generated Output I Changed or Rejected

- **Rejected Separate React/Vite Build Pipeline:** Initial full-stack scaffolding suggested separate Node/Vite frontend and Python backend deployments. I rejected that to eliminate CORS configuration, dual-hosting overhead, and build-step latency—consolidating into a single FastAPI-served HTML client.
- **Added Server-Side HTML Sanitization (`bleach`):** Raw `contenteditable` HTML payloads can carry unsafe tags or attributes when pasted from external sources or imported from `.md` files. I enforced a strict tag/attribute allowlist (`bleach.clean`) on every create, update, and import endpoint.
- **Tightened Permission Enforcement:** Ensured `view`-only shared users are blocked not only in the frontend UI (`contentEditable="false"`), but strictly on the backend (`PATCH /api/documents/{id}` returning `403 Forbidden`).

## 4. Verification & Reliability Checks

- **Automated Integration Tests (`pytest`):** Verified document creation, inline rename persistence, cross-user access denial (`403`), `view` vs `edit` permission boundaries, and `.md` file ingestion.
- **Manual End-to-End Walkthrough:** Tested live browser workflows across all three seeded users (`Muhammad Danish`, `Alex Rivera`, `Sara Khan`), verified `.txt`/`.md`/`.docx` imports, confirmed refresh persistence, and validated `.md` export.
