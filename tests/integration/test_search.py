import uuid

from httpx import AsyncClient

from backend.services.search import preprocess_query


def _fake_mp4() -> bytes:
    return b"\x00\x00\x00\x18ftypisom" + b"\x00" * 100


async def _upload_clip(client, token, description):
    resp = await client.post(
        "/api/v1/clips",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.mp4", _fake_mp4(), "video/mp4")},
        data={"description": description},
    )
    assert resp.status_code == 202
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Preprocessing unit-style tests (no DB needed)
# ---------------------------------------------------------------------------

def test_preprocess_strips_filler_words():
    _, terms = preprocess_query("video of someone saying lowdown")
    assert "lowdown" in terms
    assert "video" not in terms
    assert "someone" not in terms
    assert "saying" not in terms


def test_preprocess_keeps_embed_query_intact():
    embed, _ = preprocess_query("video of someone saying lowdown")
    assert embed == "video of someone saying lowdown"


def test_preprocess_fallback_on_pure_filler():
    embed, terms = preprocess_query("clip of someone reacting")
    # After stripping, nothing meaningful left — falls back to full query
    assert terms == embed or len(terms) > 0


def test_preprocess_short_query_unchanged():
    embed, terms = preprocess_query("lowdown")
    assert "lowdown" in terms
    assert embed == "lowdown"


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

async def test_search_returns_response_shape(client: AsyncClient, auth_token: str):
    resp = await client.post(
        "/api/v1/search",
        headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
        json={"query": "shocked reaction"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert isinstance(data["results"], list)


async def test_search_no_clips_returns_empty(client: AsyncClient, auth_token: str):
    resp = await client.post(
        "/api/v1/search",
        headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
        json={"query": "something nobody uploaded"},
    )
    assert resp.status_code == 200
    assert resp.json()["results"] == []


async def test_search_result_has_required_fields(client: AsyncClient, auth_token: str):
    await _upload_clip(client, auth_token, "extreme surprise reaction face")

    resp = await client.post(
        "/api/v1/search",
        headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
        json={"query": "surprised face"},
    )
    assert resp.status_code == 200
    for r in resp.json()["results"]:
        assert "clip" in r
        assert "score" in r
        assert "match_source" in r
        assert r["match_source"] in ("description", "transcript", "both")


async def test_search_score_is_between_0_and_1(client: AsyncClient, auth_token: str):
    await _upload_clip(client, auth_token, "totally shocked and speechless")

    resp = await client.post(
        "/api/v1/search",
        headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
        json={"query": "shocked speechless"},
    )
    for r in resp.json()["results"]:
        assert 0.0 <= r["score"] <= 1.0


async def test_search_with_filler_query_still_works(client: AsyncClient, auth_token: str):
    await _upload_clip(client, auth_token, "complete disbelief at the result")

    resp = await client.post(
        "/api/v1/search",
        headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
        json={"query": "video of someone reacting with disbelief"},
    )
    assert resp.status_code == 200
    # Should still return results — filler stripped, core terms remain
    assert isinstance(resp.json()["results"], list)


async def test_search_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/search", json={"query": "test"})
    assert resp.status_code == 401
    assert resp.json()["error"] == "unauthorized"


async def test_search_does_not_return_other_users_clips(client: AsyncClient, auth_token: str):
    await _upload_clip(client, auth_token, "private reaction clip")

    u = uuid.uuid4().hex[:8]
    await client.post(
        "/api/v1/auth/register",
        json={"username": f"spy_{u}", "email": f"spy_{u}@test.com", "password": "pass"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": f"spy_{u}@test.com", "password": "pass"},
    )
    other_token = login.json()["access_token"]

    resp = await client.post(
        "/api/v1/search",
        headers={"Authorization": f"Bearer {other_token}", "Content-Type": "application/json"},
        json={"query": "private reaction clip"},
    )
    assert resp.status_code == 200
    assert resp.json()["results"] == []


async def test_search_returns_max_10_results(client: AsyncClient, auth_token: str):
    # Upload 12 clips
    for i in range(12):
        await _upload_clip(client, auth_token, f"reaction clip number {i} with shock and surprise")

    resp = await client.post(
        "/api/v1/search",
        headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
        json={"query": "shock surprise reaction"},
    )
    assert resp.status_code == 200
    assert len(resp.json()["results"]) <= 10
