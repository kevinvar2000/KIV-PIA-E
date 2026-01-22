import os
import uuid
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_HOST"] = "127.0.0.1"
os.environ["DATABASE_USER"] = "pia_user"
os.environ["DATABASE_PASSWORD"] = "pia_password"
os.environ["DATABASE_NAME"] = "pia_db"

from app import create_app
from models.db import db


def _client():
    os.environ["FLASK_ENV"] = "testing"
    os.environ["TESTING"] = "1"
    app = create_app({"TESTING": True, "SECRET_KEY": "test-secret"})
    return app.test_client(), app


def _set_session(client, user_id: str, name: str, email: str, role_session: str):
    with client.session_transaction() as sess:
        sess["user"] = {"user_id": user_id, "name": name, "email": email, "role": role_session}


def _make_unique_identity(prefix: str):
    suffix = uuid.uuid4().hex[:10]
    name = f"{prefix}_{suffix}"
    email = f"{name}@example.com"
    return name, email


def _insert_user(user_id: str, name: str, email: str, password_hash: str, role_db: str):
    """
    Insert a user row with a fixed UUID (so FK to Projects works).
    We intentionally use unique email per test, so INSERT never conflicts.
    """
    db.execute_query(
        """
        INSERT INTO Users (id, name, email, password, role)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, name, email, password_hash, role_db),
    )


def _create_project_expect_201(client, name="P1", description="D1", language="en"):
    with open("tests/test_files/sample.txt", "rb") as f:
        resp = client.post(
            "/api/projects",
            data={
                "project_name": name,
                "description": description,
                "language": language,
                "source_file": (f, "sample.txt", "text/plain"),
            },
            content_type="multipart/form-data",
        )
    assert resp.status_code == 201, resp.get_data(as_text=True)
    assert resp.is_json
    assert resp.get_json() == {"message": "Project created successfully."}
    return resp


# ------------------- TESTS -------------------

def test_projects_list_requires_login():
    client, _ = _client()
    resp = client.get("/api/projects")
    assert resp.status_code == 401


def test_project_create_requires_login():
    client, _ = _client()
    resp = client.post("/api/projects", data={"project_name": "P", "description": "D", "language": "en"})
    assert resp.status_code == 401


def test_translator_cannot_create_project():
    client, _ = _client()

    tid = str(uuid.uuid4())
    t_name, t_email = _make_unique_identity("translator")
    _insert_user(tid, t_name, t_email, password_hash="x", role_db="TRANSLATOR")

    _set_session(client, tid, t_name, t_email, role_session="TRANSLATOR")

    with open("tests/test_files/sample.txt", "rb") as f:
        resp = client.post(
            "/api/projects",
            data={
                "project_name": "P",
                "description": "D",
                "language": "en",
                "source_file": (f, "sample.txt", "text/plain"),
            },
            content_type="multipart/form-data",
        )
    assert resp.status_code == 403


def test_customer_can_create_project():
    client, _ = _client()

    cid = str(uuid.uuid4())
    c_name, c_email = _make_unique_identity("customer")
    _insert_user(cid, c_name, c_email, password_hash="x", role_db="CUSTOMER")

    _set_session(client, cid, c_name, c_email, role_session="CUSTOMER")

    _create_project_expect_201(client, name="CustProj")


def test_admin_sees_all_projects():
    """
    GET /api/projects is allowed only for ADMIN or TRANSLATOR.
    Your decorators check the SESSION ROLE, not the DB role.
    """
    client, _ = _client()

    aid = str(uuid.uuid4())
    a_name, a_email = _make_unique_identity("admin")
    _insert_user(aid, a_name, a_email, password_hash="x", role_db="ADMINISTRATOR")

    _set_session(client, aid, a_name, a_email, role_session="ADMINISTRATOR")

    resp = client.get("/api/projects")
    assert resp.status_code == 200, resp.get_data(as_text=True)
    assert resp.is_json
    data = resp.get_json()
    assert "projects" in data
