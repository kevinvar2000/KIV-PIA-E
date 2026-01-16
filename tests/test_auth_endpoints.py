import os
import pytest

import sys
from pathlib import Path


os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import create_app


@pytest.fixture()
def client():
    app = create_app({"TESTING": True, "SECRET_KEY": "test-secret"})
    return app.test_client()


def test_api_login_success_sets_session_and_returns_role(client, monkeypatch):
    from services.AuthService import AuthService

    def fake_authenticate_user(name, password):
        assert name == "kevin"
        assert password == "pass123"
        return {"id": "u-1", "name": "kevin", "email": "k@e.com", "role": "CUSTOMER"}

    monkeypatch.setattr(AuthService, "authenticate_user", staticmethod(fake_authenticate_user))

    resp = client.post("/auth/api/login", json={"name": "kevin", "password": "pass123"})
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {"status": "success", "role": "CUSTOMER"}

    with client.session_transaction() as sess:
        assert "user" in sess
        assert sess["user"]["user_id"] == "u-1"
        assert sess["user"]["name"] == "kevin"
        assert sess["user"]["email"] == "k@e.com"
        assert sess["user"]["role"] == "CUSTOMER"


def test_api_login_failure_returns_401_and_does_not_set_session(client, monkeypatch):
    from services.AuthService import AuthService

    def fake_authenticate_user(name, password):
        return None

    monkeypatch.setattr(AuthService, "authenticate_user", staticmethod(fake_authenticate_user))

    resp = client.post("/auth/api/login", json={"name": "kevin", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.is_json
    assert resp.get_json() == {"status": "failure"}

    with client.session_transaction() as sess:
        assert sess.get("user") is None


def test_api_login_missing_json_returns_400(client):
    resp = client.post("/auth/api/login", data="not-json", content_type="text/plain")
    assert resp.status_code in (400, 415, 500)


def test_api_register_success_calls_hash_and_register_and_returns_201(client, monkeypatch):
    from services.AuthService import AuthService
    from services.UserService import UserService

    calls = {"hash": 0, "register": 0}

    def fake_hash_password(pw):
        calls["hash"] += 1
        assert pw == "pass123"
        return "HASHED_PASS"

    def fake_register_user(name, email, hashed_password, role, languages):
        calls["register"] += 1
        assert name == "Kevin"
        assert email == "kevin@example.com"
        assert hashed_password == "HASHED_PASS"
        assert role == "CUSTOMER"
        assert languages == ["en", "cs"]

    monkeypatch.setattr(AuthService, "hash_password", staticmethod(fake_hash_password))
    monkeypatch.setattr(UserService, "create_user", staticmethod(fake_register_user))

    resp = client.post(
        "/auth/api/register",
        json={
            "name": "Kevin",
            "email": "kevin@example.com",
            "password": "pass123",
            "role": "CUSTOMER",
            "languages": ["en", "cs"],
        },
    )
    assert resp.status_code == 201
    assert resp.is_json
    assert resp.get_json() == {"status": "success"}
    assert calls["hash"] == 1
    assert calls["register"] == 1


def test_api_register_defaults_languages_to_empty_list(client, monkeypatch):
    from services.AuthService import AuthService
    from services.UserService import UserService

    def fake_hash_password(pw):
        return "HASHED_PASS"

    def fake_register_user(name, email, hashed_password, role, languages):
        assert languages == []

    monkeypatch.setattr(AuthService, "hash_password", staticmethod(fake_hash_password))
    monkeypatch.setattr(UserService, "create_user", staticmethod(fake_register_user))

    resp = client.post(
        "/auth/api/register",
        json={
            "name": "Kevin",
            "email": "kevin@example.com",
            "password": "pass123",
            "role": "CUSTOMER",
        },
    )
    assert resp.status_code == 201
    assert resp.is_json
    assert resp.get_json() == {"status": "success"}


def test_api_logout_clears_session_and_returns_200(client):
    with client.session_transaction() as sess:
        sess["user"] = {"user_id": "u-1", "name": "kevin", "email": "k@e.com", "role": "CUSTOMER"}

    resp = client.post("/auth/api/logout")
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {"status": "success"}

    with client.session_transaction() as sess:
        assert sess.get("user") is None
