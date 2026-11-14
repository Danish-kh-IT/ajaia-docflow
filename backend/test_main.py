import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

# Use isolated temp DB for tests
tmp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
tmp_db.close()
os.environ["DB_PATH"] = tmp_db.name

from backend.main import app, init_db  # noqa: E402

init_db()
client = TestClient(app)


def test_create_rename_and_persist_document():
    res = client.post(
        "/api/documents",
        headers={"X-User-Id": "usr_danish"},
        json={"title": "Sprint Plan", "content": "<h2>Goals</h2><p><strong>Ship MVP</strong></p>"},
    )
    assert res.status_code == 201
    doc = res.json()
    doc_id = doc["id"]
    assert doc["title"] == "Sprint Plan"

    # Rename & update content
    patch = client.patch(
        f"/api/documents/{doc_id}",
        headers={"X-User-Id": "usr_danish"},
        json={"title": "Sprint Plan v2", "content": "<p>Updated <em>content</em></p>"},
    )
    assert patch.status_code == 200
    assert patch.json()["title"] == "Sprint Plan v2"

    # Re-fetch to verify persistence
    fetched = client.get(f"/api/documents/{doc_id}", headers={"X-User-Id": "usr_danish"})
    assert fetched.status_code == 200
    assert "<em>content</em>" in fetched.json()["content"]


def test_sharing_and_access_enforcement():
    create = client.post(
        "/api/documents",
        headers={"X-User-Id": "usr_danish"},
        json={"title": "Private Spec", "content": "<p>Confidential</p>"},
    )
    doc_id = create.json()["id"]

    # Sara cannot access before sharing
    forbidden = client.get(f"/api/documents/{doc_id}", headers={"X-User-Id": "usr_sara"})
    assert forbidden.status_code == 403

    # Share with Sara as view-only
    share = client.post(
        f"/api/documents/{doc_id}/share",
        headers={"X-User-Id": "usr_danish"},
        json={"email": "sara@ajaia.demo", "permission": "view"},
    )
    assert share.status_code == 200

    # Sara can read, but cannot edit
    read_ok = client.get(f"/api/documents/{doc_id}", headers={"X-User-Id": "usr_sara"})
    assert read_ok.status_code == 200
    assert read_ok.json()["access_level"] == "view"

    edit_blocked = client.patch(
        f"/api/documents/{doc_id}",
        headers={"X-User-Id": "usr_sara"},
        json={"title": "Hacked Title"},
    )
    assert edit_blocked.status_code == 403


def test_markdown_file_import():
    md_content = b"# Imported Notes\n\n- First item\n- **Second item**"
    res = client.post(
        "/api/documents/import",
        headers={"X-User-Id": "usr_alex"},
        files={"file": ("meeting-notes.md", md_content, "text/markdown")},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "meeting-notes"
    assert "<h1>Imported Notes</h1>" in body["content"]
    assert "<strong>Second item</strong>" in body["content"]