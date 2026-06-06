import pytest
from httpx import AsyncClient


async def test_list_tags_returns_all_tags(client: AsyncClient):
    resp = await client.get("/api/v1/tags")
    assert resp.status_code == 200
    tags = resp.json()
    assert isinstance(tags, list)
    assert len(tags) == 9


async def test_tags_have_id_and_label(client: AsyncClient):
    resp = await client.get("/api/v1/tags")
    for tag in resp.json():
        assert "id" in tag
        assert "label" in tag
        assert isinstance(tag["label"], str)


async def test_tags_sorted_alphabetically(client: AsyncClient):
    resp = await client.get("/api/v1/tags")
    labels = [t["label"] for t in resp.json()]
    assert labels == sorted(labels)


async def test_tags_no_auth_required(client: AsyncClient):
    # Must not require Authorization header
    resp = await client.get("/api/v1/tags")
    assert resp.status_code == 200
