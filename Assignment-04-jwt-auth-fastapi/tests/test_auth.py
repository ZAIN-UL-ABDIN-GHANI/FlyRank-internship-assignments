"""
Automated tests for the authentication system.

Run with:  pytest -v

Each test gets a fresh, isolated in-memory SQLite database via a
dependency override, so tests never interfere with each other or with
the real app.db file used at runtime.
"""
import datetime

import jwt as pyjwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    """
    Fresh TestClient per test, backed by a brand-new in-memory SQLite DB.
    Overrides the get_db dependency so no test touches the real database.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def registered_user(client):
    """Registers a user and returns (email, password)."""
    email = "ada@example.com"
    password = "Sup3rSecret"
    response = client.post(
        "/register",
        json={"full_name": "Ada Lovelace", "email": email, "password": password},
    )
    assert response.status_code == 201
    return email, password


@pytest.fixture()
def auth_token(client, registered_user):
    """Registers + logs in a user, returns a valid access token."""
    email, password = registered_user
    response = client.post("/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def test_register_success(client):
    response = client.post(
        "/register",
        json={"full_name": "Ada Lovelace", "email": "ada@example.com", "password": "Sup3rSecret"},
    )
    body = response.json()
    assert response.status_code == 201
    assert body["email"] == "ada@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email_returns_409(client, registered_user):
    email, password = registered_user
    response = client.post(
        "/register",
        json={"full_name": "Someone Else", "email": email, "password": password},
    )
    assert response.status_code == 409
    assert response.json()["success"] is False


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "noname@example.com", "password": "Sup3rSecret"},  # missing full_name
        {"full_name": "No Email", "password": "Sup3rSecret"},  # missing email
        {"full_name": "No Password", "email": "nopass@example.com"},  # missing password
        {"full_name": "Bad Email", "email": "not-an-email", "password": "Sup3rSecret"},
        {"full_name": "Weak", "email": "weak@example.com", "password": "weakpass"},  # no upper/digit
        {"full_name": "Short", "email": "short@example.com", "password": "Ab1"},  # too short
    ],
)
def test_register_validation_errors_return_400(client, payload):
    response = client.post("/register", json=payload)
    assert response.status_code == 400
    assert response.json()["success"] is False


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login_success(client, registered_user):
    email, password = registered_user
    response = client.post("/login", json={"email": email, "password": password})
    body = response.json()
    assert response.status_code == 200
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 0


def test_login_wrong_password_returns_401(client, registered_user):
    email, _ = registered_user
    response = client.post("/login", json={"email": email, "password": "WrongPassword1"})
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_login_nonexistent_user_returns_401(client):
    response = client.post("/login", json={"email": "nobody@example.com", "password": "Whatever1"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Protected route (/me)
# ---------------------------------------------------------------------------

def test_me_with_valid_token_returns_user(client, auth_token, registered_user):
    email, _ = registered_user
    response = client.get("/me", headers={"Authorization": f"Bearer {auth_token}"})
    body = response.json()
    assert response.status_code == 200
    assert body["email"] == email
    assert "hashed_password" not in body


def test_me_without_token_returns_401(client):
    response = client.get("/me")
    assert response.status_code == 401


def test_me_with_malformed_header_returns_401(client, auth_token):
    # Missing "Bearer " scheme prefix
    response = client.get("/me", headers={"Authorization": auth_token})
    assert response.status_code == 401


def test_me_with_garbage_token_returns_401(client):
    response = client.get("/me", headers={"Authorization": "Bearer not.a.valid.jwt"})
    assert response.status_code == 401


def test_me_with_expired_token_returns_401(client):
    now = datetime.datetime.now(datetime.timezone.utc)
    expired_payload = {
        "sub": "some-user-id",
        "iat": now - datetime.timedelta(hours=2),
        "exp": now - datetime.timedelta(hours=1),
    }
    expired_token = pyjwt.encode(expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    response = client.get("/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401


def test_me_with_token_signed_by_wrong_secret_returns_401(client, auth_token):
    tampered_token = pyjwt.encode({"sub": "some-user-id"}, "wrong-secret", algorithm="HS256")
    response = client.get("/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert response.status_code == 401
