# Submission Checklist & Reviewer Guide — Ajaia DocFlow

**Candidate:** Muhammad Danish (`danishkhalid7799@gmail.com`)  
**Role:** AI-Native Full Stack Developer — Ajaia LLC

## Included Deliverables

1. **Source Code (`backend/`, `frontend/`):** Complete FastAPI + SQLite + Tailwind/ES6 collaborative document editor.
2. **Live Deployed Application:** [INSERT_DEPLOYED_URL_HERE]
3. **Walkthrough Video URL (`walkthrough_url.txt`):** [INSERT_VIDEO_URL_HERE]
4. **`README.md`:** Local setup, test execution, and run instructions.
5. **`ARCHITECTURE.md`:** System design, prioritization tradeoffs, and next-step roadmap.
6. **`AI_WORKFLOW.md`:** Practical AI usage, rejected suggestions, and verification discipline.
7. **`SUBMISSION.md`:** This reviewer guide and deliverable inventory.
8. **`screenshots/`:** Visual verification of editor, file import, and cross-user sharing states.

## Quick Reviewer Test Flow (2 Minutes)

1. Open the live URL (defaults to **Muhammad Danish — `danish@ajaia.demo`**).
2. Click **+ New Document**, edit the title inline, format text using **H1/H2/Bold/Italic/Underline/Lists**, and refresh the browser to confirm SQLite persistence.
3. Click **Upload File to New Doc** and upload any `.txt`, `.md`, or `.docx` file to convert it into an editable document.
4. Click **Share** on an owned document, share with `sara@ajaia.demo` as **Can View**, then switch the top-right **Active Session** dropdown to **Sara Khan (`sara@ajaia.demo`)** to verify **Shared with Me** visibility and read-only enforcement.

## Status & Known Limitations

- **Working End-to-End:** Document CRUD, inline rename, rich-text formatting, auto-save + manual save, `.txt`/`.md`/`.docx` import, `.md` export, owner vs shared categorization, `view`/`edit` ACL enforcement, and `pytest` suite.
- **Intentional Scope Cuts:** Single-instance SQLite storage (ephemeral disk on free cloud tiers resets on container restart) and turn-based editing rather than CRDT real-time multi-cursor sync.
