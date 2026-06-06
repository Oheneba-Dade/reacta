import io
import uuid

import pytest
from httpx import AsyncClient


def _fake_mp4() -> bytes:
    """Minimal byte sequence recognised as a file upload (content doesn't matter for unit tests)."""
    return b"\x00\x00\x00\x18ftypisom" + b"\x00" * 100


async def _upload_clip(client: AsyncClient, token: str, description: str = "test clip") -> dict:
    resp = await client.post(
        "/api/v1/clips",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.mp4", _fake_mp4(), "video/mp4")},
        data={"description": description, "title": "Test clip"},
    )
    assert resp.status_code == 202, resp.text
    return resp.json()


async def test_upload_returns_202_with_clip_id(client: AsyncClient, auth_token: str):
    data = await _upload_clip(client, auth_token)
    assert "id" in data
    assert data["processing_status"] == "pending"


async def test_list_clips_returns_uploaded_clip(client: AsyncClient, auth_token: str):
    await _upload_clip(client, auth_token)
    resp = await client.get("/api/v1/clips", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    clips = resp.json()
    assert len(clips) >= 1


async def test_get_clip_returns_clip(client: AsyncClient, auth_token: str):
    uploaded = await _upload_clip(client, auth_token)
    clip_id = uploaded["id"]

    resp = await client.get(
        f"/api/v1/clips/{clip_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == clip_id


async def test_get_clip_not_found_returns_404(client: AsyncClient, auth_token: str):
    resp = await client.get(
        f"/api/v1/clips/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 404


async def test_get_clip_wrong_owner_returns_403(client: AsyncClient, auth_token: str):
    # Upload as user A
    uploaded = await _upload_clip(client, auth_token)
    clip_id = uploaded["id"]

    # Register and login as user B
    u = uuid.uuid4().hex[:8]
    await client.post(
        "/api/v1/auth/register",
        json={"username": f"other_{u}", "email": f"other_{u}@test.com", "password": "pass"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": f"other_{u}@test.com", "password": "pass"},
    )
    other_token = login.json()["access_token"]

    resp = await client.get(
        f"/api/v1/clips/{clip_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"] == "forbidden"


async def test_patch_title_does_not_reset_embedding(client: AsyncClient, auth_token: str):
    uploaded = await _upload_clip(client, auth_token)
    clip_id = uploaded["id"]

    resp = await client.patch(
        f"/api/v1/clips/{clip_id}",
        headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
        json={"title": "Updated title"},
    )
    assert resp.status_code == 200
    # Embedding status should still be pending (upload just happened, not reset by title change)
    assert resp.json()["desc_embedding_status"] == "pending"


async def test_patch_description_resets_embedding_status(client: AsyncClient, auth_token: str):
    uploaded = await _upload_clip(client, auth_token)
    clip_id = uploaded["id"]

    resp = await client.patch(
        f"/api/v1/clips/{clip_id}",
        headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
        json={"description": "A completely different description"},
    )
    assert resp.status_code == 200
    assert resp.json()["desc_embedding_status"] == "pending"


async def test_delete_clip_returns_204(client: AsyncClient, auth_token: str):
    uploaded = await _upload_clip(client, auth_token)
    clip_id = uploaded["id"]

    resp = await client.delete(
        f"/api/v1/clips/{clip_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 204

    # Confirm it's gone
    get_resp = await client.get(
        f"/api/v1/clips/{clip_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert get_resp.status_code == 404


async def test_status_endpoint_returns_three_status_fields(client: AsyncClient, auth_token: str):
    uploaded = await _upload_clip(client, auth_token)
    clip_id = uploaded["id"]

    resp = await client.get(
        f"/api/v1/clips/{clip_id}/status",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "processing_status" in data
    assert "desc_embedding_status" in data
    assert "transcript_status" in data


async def test_upload_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/clips",
        files={"file": ("test.mp4", _fake_mp4(), "video/mp4")},
        data={"description": "test"},
    )
    assert resp.status_code == 401


async def test_clip_response_includes_tags(client: AsyncClient, auth_token: str):
    uploaded = await _upload_clip(client, auth_token)
    clip_id = uploaded["id"]

    resp = await client.get(
        f"/api/v1/clips/{clip_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert "tags" in resp.json()
    assert isinstance(resp.json()["tags"], list)
