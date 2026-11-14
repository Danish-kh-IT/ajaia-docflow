---

#### File 2: `ARCHITECTURE.md`

```markdown
# Architecture & Product Prioritization Note

## 1. System Architecture Overview

Ajaia DocFlow uses a streamlined, single-service full-stack architecture designed for rapid local execution, zero-CORS friction, and reliable cloud deployment:

- **Backend & API Layer (`backend/main.py`):** FastAPI + Pydantic v2 exposing RESTful endpoints (`/api/users`, `/api/documents`, `/api/documents/{id}`, `/api/documents/{id}/share`, `/api/documents/import`) and serving the frontend directly from `/`.
- **Persistence Layer (`SQLite`):** Three normalized relational tables (`users`, `documents`, `document_shares`) with `UNIQUE(document_id, user_id)` constraints and cascading deletes.
- **File Ingestion Pipeline:** Server-side parsers convert `.txt` (line-to-paragraph escaping), `.md` (`python-markdown` with `extra` extension), and `.docx` (`python-docx` preserving Heading 1–3, lists, bold, italic, and underline runs) into sanitized HTML.
- **Frontend Workspace (`frontend/index.html`):** Zero-build reactive UI built with Tailwind CSS and vanilla ES6+ JavaScript, maintaining active session headers (`X-User-Id`), debounced auto-save, and role-aware UI state (disabling toolbar/title inputs for `view`-only collaborators).

## 2. Prioritization & Scope Tradeoffs

Within a 4-hour delivery constraint, I prioritized **end-to-end product coherence, server-enforced permissions, and frictionless reviewer testing** over complex distributed infrastructure:

| Area                    | Chosen Approach                                                                      | What Was Deprioritized & Why                                                                                                                                                        |
| :---------------------- | :----------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Collaboration Model** | Turn-based persistence with debounced auto-save (1.8s) + explicit View/Edit ACLs     | **CRDT / Operational Transformation (Yjs/WebSockets):** Real-time multi-cursor sync adds significant edge-case complexity without strengthening core document lifecycle evaluation. |
| **Authentication**      | Pre-seeded workspace accounts with an instant top-bar session switcher (`X-User-Id`) | **OAuth / Password Signup Flows:** Password registration slows down reviewers testing cross-user sharing (`Owner` vs `Edit` vs `View`).                                             |
| **Rich-Text Storage**   | Sanitized HTML (`bleach` allowlist) stored in SQLite                                 | **Custom JSON AST / Slate Schema:** Sanitized HTML renders natively in `contenteditable`, maps cleanly from Markdown/DOCX imports, and eliminates client-side serialization drift.  |
| **Deployment Topology** | Single FastAPI process serving API + static HTML                                     | **Split Vercel + Separate API + Managed Postgres:** Single-container deployment avoids cross-origin cookie/CORS issues and cold-start split failures.                               |

## 3. What I Would Build Next (With Another 2–4 Hours)

1. **Document Version History:** Snapshot `content` on save into a `document_revisions` table with one-click diff preview and restore.
2. **Real-Time Presence & Live Sync:** WebSocket room subscriptions per `doc_id` showing active viewers/editors and broadcasting incremental updates.
3. **Inline Comments & Suggestions:** Anchored text annotations stored in a `document_comments` table with resolved/open status.
```
