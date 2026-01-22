import os
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_HOST"] = "127.0.0.1"
os.environ["DATABASE_USER"] = "pia_user"
os.environ["DATABASE_PASSWORD"] = "pia_password"
os.environ["DATABASE_NAME"] = "pia_db"

from app import create_app

API_PREFIX = "/api"


@pytest.fixture()
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test-secret"})
    return app.test_client()


def _make_unique_identity(prefix: str):
    suf = uuid.uuid4().hex[:10]
    name = f"{prefix}_{suf}"
    email = f"{name}@example.com"
    return name, email


def _set_session_user(client, *, user_id=None, name="admin", email="a@a.com", role="ADMIN"):
    """
    Must match your auth controller:
    session['user'] = {'user_id': ..., 'name': ..., 'email': ..., 'role': ...}
    """
    if user_id is None:
        user_id = str(uuid.uuid4())
    with client.session_transaction() as sess:
        sess["user"] = {"user_id": user_id, "name": name, "email": email, "role": role}


# -------------------------
# POST /api/users
# -------------------------

def test_post_users_success_returns_201_and_calls_services(client, monkeypatch):
    from services.AuthService import AuthService
    from services.UserService import UserService

    calls = {"hash": 0, "create": 0}
    name, email = _make_unique_identity("Kevin")

    def fake_hash_password(password):
        calls["hash"] += 1
        assert password == "pass123"
        return "HASHED"

    def fake_create_user(n, e, hashed_password, role, languages):
        calls["create"] += 1
        assert n == name
        assert e == email
        assert hashed_password == "HASHED"
        assert role == "CUSTOMER"
        assert languages == ["en", "cs"]

    monkeypatch.setattr(AuthService, "hash_password", staticmethod(fake_hash_password))
    monkeypatch.setattr(UserService, "create_user", staticmethod(fake_create_user))

    resp = client.post(
        f"{API_PREFIX}/users",
        json={
            "name": name,
            "email": email,
            "password": "pass123",
            "role": "CUSTOMER",
            "languages": ["en", "cs"],
        },
    )

    assert resp.status_code == 201, resp.get_data(as_text=True)
    assert resp.is_json
    assert resp.get_json() == {"message": "User created successfully."}
    assert calls["hash"] == 1
    assert calls["create"] == 1


def test_post_users_value_error_returns_400(client, monkeypatch):
    from services.AuthService import AuthService
    from services.UserService import UserService

    monkeypatch.setattr(AuthService, "hash_password", staticmethod(lambda pw: "HASHED"))

    def fake_create_user(*args, **kwargs):
        raise ValueError("Email already exists")

    monkeypatch.setattr(UserService, "create_user", staticmethod(fake_create_user))

    name, email = _make_unique_identity("Kevin")

    resp = client.post(
        f"{API_PREFIX}/users",
        json={
            "name": name,
            "email": email,
            "password": "pass123",
            "role": "CUSTOMER",
            "languages": [],
        },
    )

    assert resp.status_code == 400
    assert resp.is_json
    assert resp.get_json() == {"error": "Email already exists"}


# -------------------------
# GET /api/users  (ADMIN only)
# -------------------------

def test_get_users_requires_login(client):
    resp = client.get(f"{API_PREFIX}/users")
    assert resp.status_code == 401


def test_get_users_forbidden_for_non_admin(client):
    _set_session_user(client, role="CUSTOMER")
    resp = client.get(f"{API_PREFIX}/users")
    assert resp.status_code == 403


def test_get_users_success_for_admin(client, monkeypatch):
    from services.UserService import UserService

    _set_session_user(client, role="ADMINISTRATOR")

    monkeypatch.setattr(
        UserService,
        "get_all_users",
        staticmethod(lambda: [{"id": "u1", "name": "a"}, {"id": "u2", "name": "b"}]),
    )

    resp = client.get(f"{API_PREFIX}/users")
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {"users": [{"id": "u1", "name": "a"}, {"id": "u2", "name": "b"}]}


# -------------------------
# GET /api/users/<name>  (ADMIN only)
# -------------------------

def test_get_user_by_name_requires_login(client):
    resp = client.get(f"{API_PREFIX}/users/someone")
    assert resp.status_code == 401


def test_get_user_by_name_forbidden_for_non_admin(client):
    _set_session_user(client, role="TRANSLATOR")
    resp = client.get(f"{API_PREFIX}/users/someone")
    assert resp.status_code == 403


def test_get_user_by_name_not_found_returns_404(client, monkeypatch):
    from services.UserService import UserService

    _set_session_user(client, role="ADMINISTRATOR")
    monkeypatch.setattr(UserService, "get_user_by_name", staticmethod(lambda name: None))

    resp = client.get(f"{API_PREFIX}/users/ghost")
    assert resp.status_code == 404
    assert resp.is_json
    assert resp.get_json() == {"error": "User not found."}


def test_get_user_by_name_success_returns_200(client, monkeypatch):
    from services.UserService import UserService

    _set_session_user(client, role="ADMINISTRATOR")
    monkeypatch.setattr(
        UserService,
        "get_user_by_name",
        staticmethod(lambda name: {"id": "u-1", "name": name, "role": "CUSTOMER"}),
    )

    resp = client.get(f"{API_PREFIX}/users/kevin")
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {"user": {"id": "u-1", "name": "kevin", "role": "CUSTOMER"}}
