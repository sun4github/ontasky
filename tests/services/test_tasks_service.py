import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.tasks import TaskCreateRequest
from app.services import tasks_service


def _make_create_request(user_id=None, created_by_user_id=None):
    return TaskCreateRequest(
        user_id=user_id,
        title="Write tests",
        created_by_user_id=created_by_user_id,
    )


def test_create_task_self_defaults_created_by(monkeypatch):
    requester = uuid4()
    captured = {}

    async def fake_create_task(**kwargs):
        captured.update(kwargs)
        return {"id": uuid4(), **kwargs}

    monkeypatch.setattr(tasks_service.tasks_db, "create_task", fake_create_task)

    async def run_case():
        req = _make_create_request()
        await tasks_service.create_task(req, requester_user_id=requester, assigner_key=None)

    asyncio.run(run_case())

    assert captured["user_id"] == requester
    assert captured["created_by_user_id"] == requester


def test_create_task_self_preserves_created_by_when_provided(monkeypatch):
    requester = uuid4()
    explicit_creator = uuid4()
    captured = {}

    async def fake_create_task(**kwargs):
        captured.update(kwargs)
        return {"id": uuid4(), **kwargs}

    monkeypatch.setattr(tasks_service.tasks_db, "create_task", fake_create_task)

    async def run_case():
        req = _make_create_request(user_id=requester, created_by_user_id=explicit_creator)
        await tasks_service.create_task(req, requester_user_id=requester, assigner_key=None)

    asyncio.run(run_case())

    assert captured["created_by_user_id"] == explicit_creator


def test_create_task_for_another_user_requires_assigner_key(monkeypatch):
    requester = uuid4()
    owner = uuid4()

    async def run_case():
        req = _make_create_request(user_id=owner)
        await tasks_service.create_task(req, requester_user_id=requester, assigner_key=None)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run_case())

    assert exc_info.value.status_code == 400


def test_create_task_for_another_user_rejects_invalid_key(monkeypatch):
    requester = uuid4()
    owner = uuid4()

    async def fake_list_active_assigner_credentials(assigner_user_id):
        assert assigner_user_id == requester
        return {"items": [{"key_hash": "deadbeef"}], "total": 1}

    monkeypatch.setattr(
        tasks_service.assigners_db,
        "list_active_assigner_credentials",
        fake_list_active_assigner_credentials,
    )

    async def run_case():
        req = _make_create_request(user_id=owner)
        await tasks_service.create_task(req, requester_user_id=requester, assigner_key="wrong")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run_case())

    assert exc_info.value.status_code == 403


def test_create_task_for_another_user_requires_active_grant(monkeypatch):
    requester = uuid4()
    owner = uuid4()

    async def fake_list_active_assigner_credentials(assigner_user_id):
        return {
            "items": [
                {
                    "key_hash": "8810ad581e59f2bc3928b261707a71308f7e139eb04820366dc4d5c18d980225"
                }
            ],
            "total": 1,
        }

    async def fake_get_task_assigner_grant(user_id, assigner_user_id):
        assert user_id == owner
        assert assigner_user_id == requester
        return {
            "revoked_at": None,
            "expires_at": datetime.now(timezone.utc) - timedelta(minutes=1),
            "permissions": {"create_task": True},
        }

    monkeypatch.setattr(
        tasks_service.assigners_db,
        "list_active_assigner_credentials",
        fake_list_active_assigner_credentials,
    )
    monkeypatch.setattr(
        tasks_service.assigners_db,
        "get_task_assigner_grant",
        fake_get_task_assigner_grant,
    )

    async def run_case():
        req = _make_create_request(user_id=owner)
        await tasks_service.create_task(req, requester_user_id=requester, assigner_key="secret")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run_case())

    assert exc_info.value.status_code == 403


def test_create_task_for_another_user_allows_valid_key_and_grant(monkeypatch):
    requester = uuid4()
    owner = uuid4()
    captured = {}

    async def fake_list_active_assigner_credentials(assigner_user_id):
        return {
            "items": [
                {
                    "key_hash": "2bb80d537b1da3e38bd30361aa855686bde0eacd7162fef6a25fe97bf527a25b"
                }
            ],
            "total": 1,
        }

    async def fake_get_task_assigner_grant(user_id, assigner_user_id):
        return {
            "revoked_at": None,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
            "permissions": {"create_task": True},
        }

    async def fake_create_task(**kwargs):
        captured.update(kwargs)
        return {"id": uuid4(), **kwargs}

    monkeypatch.setattr(
        tasks_service.assigners_db,
        "list_active_assigner_credentials",
        fake_list_active_assigner_credentials,
    )
    monkeypatch.setattr(
        tasks_service.assigners_db,
        "get_task_assigner_grant",
        fake_get_task_assigner_grant,
    )
    monkeypatch.setattr(tasks_service.tasks_db, "create_task", fake_create_task)

    async def run_case():
        req = _make_create_request(user_id=owner)
        await tasks_service.create_task(req, requester_user_id=requester, assigner_key="secret")

    asyncio.run(run_case())

    assert captured["user_id"] == owner
    assert captured["created_by_user_id"] == requester


def test_search_tasks_trims_query_and_delegates(monkeypatch):
    user_id = uuid4()
    captured = {}
    payload = {"items": [{"id": uuid4(), "title": "Write tests"}], "total": 1}

    async def fake_search_tasks(**kwargs):
        captured.update(kwargs)
        return payload

    monkeypatch.setattr(tasks_service.tasks_db, "search_tasks", fake_search_tasks)

    async def run_case():
        return await tasks_service.search_tasks(user_id=user_id, q="  tests  ", limit=10)

    result = asyncio.run(run_case())

    assert captured["user_id"] == user_id
    assert captured["q"] == "tests"
    assert captured["limit"] == 10
    assert result == payload


def test_search_tasks_rejects_empty_query():
    user_id = uuid4()

    async def run_case():
        await tasks_service.search_tasks(user_id=user_id, q="   ")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run_case())

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Search query cannot be empty"
