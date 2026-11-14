import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import bleach
import docx
import markdown as md_lib
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "docflow.db"))
FRONTEND_FILE = BASE_DIR / "frontend" / "index.html"

ALLOWED_TAGS = [
    "p", "br", "strong", "b", "em", "i", "u", "s",
    "h1", "h2", "h3", "ul", "ol", "li", "blockquote", "code", "pre", "div", "span"
]
ALLOWED_ATTRS = {"*": ["style"]}

SEED_USERS = [
    {"id": "usr_danish", "name": "Muhammad Danish", "email": "danish@ajaia.demo", "role": "AI/ML Engineer"},
    {"id": "usr_alex", "name": "Alex Rivera", "email": "alex@ajaia.demo", "role": "Product Lead"},
    {"id": "usr_sara", "name": "Sara Khan", "email": "sara@ajaia.demo", "role": "Design Lead"},
]

app = FastAPI(title="Ajaia DocFlow — Lightweight Collaborative Editor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sanitize_html(raw_html: str) -> str:
    return bleach.clean(raw_html or "", tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '<p></p>',
                owner_id TEXT NOT NULL,
                source_filename TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS document_shares (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                permission TEXT NOT NULL CHECK(permission IN ('view', 'edit')),
                shared_at TEXT NOT NULL,
                UNIQUE(document_id, user_id),
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )

        for u in SEED_USERS:
            conn.execute(
                "INSERT OR IGNORE INTO users (id, name, email, role) VALUES (?, ?, ?, ?)",
                (u["id"], u["name"], u["email"], u["role"]),
            )

        existing_docs = conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()["cnt"]
        if existing_docs == 0:
            ts = now_iso()
            doc1_id = "doc_welcome_01"
            doc2_id = "doc_roadmap_02"
            conn.execute(
                """
                INSERT INTO documents (id, title, content, owner_id, source_filename, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc1_id,
                    "Q4 AI Product Architecture Spec",
                    "<h1>Q4 AI Product Architecture Spec</h1><p>Welcome to <strong>Ajaia DocFlow</strong>. Use the toolbar above to format text with <strong>Bold</strong>, <em>Italic</em>, <u>Underline</u>, headings, and lists.</p><ul><li>Create, rename, and persist rich-text documents</li><li>Import <code>.txt</code>, <code>.md</code>, or <code>.docx</code> files directly into editable drafts</li><li>Share documents with teammates using View or Edit access</li></ul>",
                    "usr_danish",
                    None,
                    ts,
                    ts,
                ),
            )
            conn.execute(
                """
                INSERT INTO documents (id, title, content, owner_id, source_filename, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc2_id,
                    "Internal Productivity Tool — Review Notes",
                    "<h2>Reviewer Onboarding Notes</h2><p>This document is owned by <strong>Alex Rivera</strong> and shared with <strong>Muhammad Danish</strong> with <em>Edit</em> access so you can immediately test cross-user sharing.</p><ol><li>Switch active user in the top-right dropdown</li><li>Verify Owned vs Shared with Me badges</li><li>Test editing permissions across accounts</li></ol>",
                    "usr_alex",
                    None,
                    ts,
                    ts,
                ),
            )
            conn.execute(
                """
                INSERT INTO document_shares (id, document_id, user_id, permission, shared_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("shr_seed_01", doc2_id, "usr_danish", "edit", ts),
            )
        conn.commit()
    finally:
        conn.close()


@app.on_event("startup")
def on_startup():
    init_db()


class CreateDocRequest(BaseModel):
    title: str = Field(default="Untitled Document", min_length=1, max_length=200)
    content: str = Field(default="<p>Start writing here...</p>")


class UpdateDocRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = None


class ShareDocRequest(BaseModel):
    email: str
    permission: str = Field(default="edit", pattern="^(view|edit)$")


def resolve_user(conn: sqlite3.Connection, x_user_id: Optional[str]) -> sqlite3.Row:
    uid = x_user_id or "usr_danish"
    user = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid active user session.")
    return user


def get_doc_with_access(conn: sqlite3.Connection, doc_id: str, user_id: str) -> dict:
    doc = conn.execute(
        """
        SELECT d.*, u.name AS owner_name, u.email AS owner_email
        FROM documents d
        JOIN users u ON d.owner_id = u.id
        WHERE d.id = ?
        """,
        (doc_id,),
    ).fetchone()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc["owner_id"] == user_id:
        access = "owner"
    else:
        share = conn.execute(
            "SELECT permission FROM document_shares WHERE document_id = ? AND user_id = ?",
            (doc_id, user_id),
        ).fetchone()
        if not share:
            raise HTTPException(status_code=403, detail="You do not have access to this document.")
        access = share["permission"]

    shares = conn.execute(
        """
        SELECT ds.id, ds.permission, ds.shared_at, u.id AS user_id, u.name, u.email
        FROM document_shares ds
        JOIN users u ON ds.user_id = u.id
        WHERE ds.document_id = ?
        ORDER BY ds.shared_at ASC
        """,
        (doc_id,),
    ).fetchall()

    return {
        "id": doc["id"],
        "title": doc["title"],
        "content": doc["content"],
        "owner_id": doc["owner_id"],
        "owner_name": doc["owner_name"],
        "owner_email": doc["owner_email"],
        "source_filename": doc["source_filename"],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
        "access_level": access,
        "shared_with": [dict(s) for s in shares],
    }


@app.get("/")
def serve_frontend():
    if FRONTEND_FILE.exists():
        return FileResponse(FRONTEND_FILE)
    return {"status": "ok", "message": "Frontend index.html not found."}


@app.get("/api/health")
def health():
    return {"status": "healthy", "timestamp": now_iso()}


@app.get("/api/users")
def list_users():
    init_db()
    conn = get_conn()
    try:
        rows = conn.execute("SELECT id, name, email, role FROM users ORDER BY rowid ASC").fetchall()
        return {"users": [dict(r) for r in rows]}
    finally:
        conn.close()


@app.get("/api/documents")
def list_documents(x_user_id: Optional[str] = Header(default="usr_danish")):
    init_db()
    conn = get_conn()
    try:
        user = resolve_user(conn, x_user_id)
        owned_rows = conn.execute(
            """
            SELECT d.*, u.name AS owner_name, u.email AS owner_email,
                   (SELECT COUNT(*) FROM document_shares ds WHERE ds.document_id = d.id) AS share_count
            FROM documents d
            JOIN users u ON d.owner_id = u.id
            WHERE d.owner_id = ?
            ORDER BY d.updated_at DESC
            """,
            (user["id"],),
        ).fetchall()

        shared_rows = conn.execute(
            """
            SELECT d.*, u.name AS owner_name, u.email AS owner_email, ds.permission AS access_level
            FROM document_shares ds
            JOIN documents d ON ds.document_id = d.id
            JOIN users u ON d.owner_id = u.id
            WHERE ds.user_id = ?
            ORDER BY d.updated_at DESC
            """,
            (user["id"],),
        ).fetchall()

        owned = [{**dict(r), "access_level": "owner"} for r in owned_rows]
        shared = [dict(r) for r in shared_rows]
        return {"owned": owned, "shared": shared}
    finally:
        conn.close()


@app.post("/api/documents", status_code=201)
def create_document(
    payload: CreateDocRequest,
    x_user_id: Optional[str] = Header(default="usr_danish"),
):
    init_db()
    conn = get_conn()
    try:
        user = resolve_user(conn, x_user_id)
        doc_id = f"doc_{uuid.uuid4().hex[:10]}"
        ts = now_iso()
        clean_title = payload.title.strip() or "Untitled Document"
        clean_content = sanitize_html(payload.content)
        conn.execute(
            """
            INSERT INTO documents (id, title, content, owner_id, source_filename, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (doc_id, clean_title, clean_content, user["id"], None, ts, ts),
        )
        conn.commit()
        return get_doc_with_access(conn, doc_id, user["id"])
    finally:
        conn.close()


@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str, x_user_id: Optional[str] = Header(default="usr_danish")):
    init_db()
    conn = get_conn()
    try:
        user = resolve_user(conn, x_user_id)
        return get_doc_with_access(conn, doc_id, user["id"])
    finally:
        conn.close()


@app.patch("/api/documents/{doc_id}")
def update_document(
    doc_id: str,
    payload: UpdateDocRequest,
    x_user_id: Optional[str] = Header(default="usr_danish"),
):
    init_db()
    conn = get_conn()
    try:
        user = resolve_user(conn, x_user_id)
        doc = get_doc_with_access(conn, doc_id, user["id"])
        if doc["access_level"] not in ("owner", "edit"):
            raise HTTPException(status_code=403, detail="View-only access: cannot edit this document.")

        new_title = payload.title.strip() if payload.title is not None else doc["title"]
        if not new_title:
            raise HTTPException(status_code=400, detail="Document title cannot be empty.")

        new_content = sanitize_html(payload.content) if payload.content is not None else doc["content"]
        ts = now_iso()

        conn.execute(
            "UPDATE documents SET title = ?, content = ?, updated_at = ? WHERE id = ?",
            (new_title, new_content, ts, doc_id),
        )
        conn.commit()
        return get_doc_with_access(conn, doc_id, user["id"])
    finally:
        conn.close()


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str, x_user_id: Optional[str] = Header(default="usr_danish")):
    init_db()
    conn = get_conn()
    try:
        user = resolve_user(conn, x_user_id)
        doc = conn.execute("SELECT owner_id FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        if doc["owner_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Only the document owner can delete it.")
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        return {"deleted": True, "id": doc_id}
    finally:
        conn.close()


@app.post("/api/documents/{doc_id}/share")
def share_document(
    doc_id: str,
    payload: ShareDocRequest,
    x_user_id: Optional[str] = Header(default="usr_danish"),
):
    init_db()
    conn = get_conn()
    try:
        user = resolve_user(conn, x_user_id)
        doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        if doc["owner_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Only the document owner can manage sharing.")

        target_email = payload.email.strip().lower()
        target_user = conn.execute("SELECT * FROM users WHERE LOWER(email) = ?", (target_email,)).fetchone()
        if not target_user:
            raise HTTPException(
                status_code=404,
                detail="No workspace user found with that email. Try alex@ajaia.demo, sara@ajaia.demo, or danish@ajaia.demo.",
            )
        if target_user["id"] == user["id"]:
            raise HTTPException(status_code=400, detail="You already own this document.")

        ts = now_iso()
        conn.execute(
            """
            INSERT INTO document_shares (id, document_id, user_id, permission, shared_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(document_id, user_id) DO UPDATE SET permission = excluded.permission, shared_at = excluded.shared_at
            """,
            (f"shr_{uuid.uuid4().hex[:8]}", doc_id, target_user["id"], payload.permission, ts),
        )
        conn.commit()
        return get_doc_with_access(conn, doc_id, user["id"])
    finally:
        conn.close()


@app.delete("/api/documents/{doc_id}/share/{target_user_id}")
def revoke_share(
    doc_id: str,
    target_user_id: str,
    x_user_id: Optional[str] = Header(default="usr_danish"),
):
    init_db()
    conn = get_conn()
    try:
        user = resolve_user(conn, x_user_id)
        doc = conn.execute("SELECT owner_id FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        if doc["owner_id"] != user["id"]:
            raise HTTPException(status_code=403, detail="Only the document owner can revoke access.")
        conn.execute(
            "DELETE FROM document_shares WHERE document_id = ? AND user_id = ?",
            (doc_id, target_user_id),
        )
        conn.commit()
        return get_doc_with_access(conn, doc_id, user["id"])
    finally:
        conn.close()


def parse_uploaded_file(filename: str, raw_bytes: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".txt":
        text = raw_bytes.decode("utf-8", errors="replace")
        paragraphs = [f"<p>{bleach.clean(line)}</p>" if line.strip() else "<p><br></p>" for line in text.splitlines()]
        return "".join(paragraphs) or "<p></p>"

    if ext == ".md":
        text = raw_bytes.decode("utf-8", errors="replace")
        html = md_lib.markdown(text, extensions=["extra"])
        return sanitize_html(html) or "<p></p>"

    if ext == ".docx":
        from io import BytesIO
        document = docx.Document(BytesIO(raw_bytes))
        blocks = []
        for p in document.paragraphs:
            txt = p.text.strip()
            if not txt:
                continue
            style_name = (p.style.name or "").lower()
            if "heading 1" in style_name:
                blocks.append(f"<h1>{bleach.clean(txt)}</h1>")
            elif "heading 2" in style_name:
                blocks.append(f"<h2>{bleach.clean(txt)}</h2>")
            elif "heading 3" in style_name:
                blocks.append(f"<h3>{bleach.clean(txt)}</h3>")
            elif "list" in style_name:
                blocks.append(f"<ul><li>{bleach.clean(txt)}</li></ul>")
            else:
                runs_html = []
                for r in p.runs:
                    chunk = bleach.clean(r.text)
                    if r.bold:
                        chunk = f"<strong>{chunk}</strong>"
                    if r.italic:
                        chunk = f"<em>{chunk}</em>"
                    if r.underline:
                        chunk = f"<u>{chunk}</u>"
                    runs_html.append(chunk)
                blocks.append(f"<p>{''.join(runs_html) or bleach.clean(txt)}</p>")
        return "".join(blocks) or "<p></p>"

    raise HTTPException(
        status_code=400,
        detail="Unsupported file format. Please upload a .txt, .md, or .docx file.",
    )


@app.post("/api/documents/import", status_code=201)
async def import_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
    x_user_id: Optional[str] = Header(default="usr_danish"),
):
    init_db()
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".txt", ".md", ".docx"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Supported formats: .txt, .md, .docx",
        )

    raw_bytes = await file.read()
    if len(raw_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 5 MB limit.")

    html_content = parse_uploaded_file(file.filename, raw_bytes)
    doc_title = (title or Path(file.filename).stem).strip() or "Imported Document"

    conn = get_conn()
    try:
        user = resolve_user(conn, x_user_id)
        doc_id = f"doc_{uuid.uuid4().hex[:10]}"
        ts = now_iso()
        conn.execute(
            """
            INSERT INTO documents (id, title, content, owner_id, source_filename, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (doc_id, doc_title, html_content, user["id"], file.filename, ts, ts),
        )
        conn.commit()
        return get_doc_with_access(conn, doc_id, user["id"])
    finally:
        conn.close()