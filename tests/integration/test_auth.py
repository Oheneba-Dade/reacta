import uuid

import pytest
from httpx import AsyncClient


def _unique_user():
    u = uuid.uuid4().hex[:8]
    return {"username": f"u_{u}", "email": f"{u}@test.com", "password": "password123"}


async def test_register_returns_201_with_user(client: AsyncClient):
    user = _unique_user()
    resp = await client.post("/api/v1/auth/register", json=user)
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == user["username"]
    assert data["email"] == user["email"]
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


async def test_register_duplicate_email_returns_409(client: AsyncClient):
    user = _unique_user()
    await client.post("/api/v1/auth/register", json=user)
    # Same email, different username
    resp = await client.post(
        "/api/v1/auth/register",
        json={**user, "username": "different_name"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "conflict"


async def test_register_duplicate_username_returns_409(client: AsyncClient):
    user = _unique_user()
    await client.post("/api/v1/auth/register", json=user)
    resp = await client.post(
        "/api/v1/auth/register",
        json={**user, "email": "different@test.com"},
    )
    assert resp.status_code == 409


async def test_login_returns_tokens(client: AsyncClient):
    user = _unique_user()
    await client.post("/api/v1/auth/register", json=user)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password_returns_401(client: AsyncClient):
    user = _unique_user()
    await client.post("/api/v1/auth/register", json=user)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user["email"], "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"] == "unauthorized"


async def test_login_unknown_email_returns_401(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@nowhere.com", "password": "anything"},
    )
    assert resp.status_code == 401


async def test_refresh_returns_new_access_token(client: AsyncClient):
    user = _unique_user()
    await client.post("/api/v1/auth/register", json=user)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    refresh_token = login.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_with_access_token_returns_401(client: AsyncClient):
    user = _unique_user()
    await client.post("/api/v1/auth/register", json=user)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    access_token = login.json()["access_token"]

    # Passing an access token where a refresh token is expected
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401
