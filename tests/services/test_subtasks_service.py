import asyncio
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.subtasks import (
    SubtaskCreateRequest,
    SubtaskReorderRequest,
    SubtaskUpdateRequest,
)
from app.services import subtasks_service


def test_create_subtask_verifies_task_and_passes_user_id(monkeypatch):
    task_id = uuid4()
    user_id = uuid4()
    captured = {}

    async def fake_get_task(task_id, user_id):
        return {"id": task_id, "user_id": user_id}

    async def fake_create_subtask(**kwargs):
        captured.update(kwargs)
        return {"id": uuid4(), **kwargs}

    monkeypatch.setattr(subtasks_service.tasks_db, "get_task", fake_get_task)
    monkeypatch.setattr(subtasks_service.subtasks_db, "create_subtask", fake_create_subtask)

    async def run_case():
        req = SubtaskCreateRequest(title="child", sort_order=2)
        await subtasks_service.create_subtask(task_id=task_id, req=req, user_id=user_id)

    asyncio.run(run_case())

    assert captured["task_id"] == task_id
    assert captured["user_id"] == user_id
    assert captured["title"] == "child"
    assert captured["sort_order"] == 2


def test_create_subtask_raises_404_when_task_missing(monkeypatch):
    task_id = uuid4()
    user_id = uuid4()

    async def fake_get_task(task_id, user_id):
        return None

    monkeypatch.setattr(subtasks_service.tasks_db, "get_task", fake_get_task)

    async def run_case():
        req = SubtaskCreateRequest(title="child", sort_order=0)
        await subtasks_service.create_subtask(task_id=task_id, req=req, user_id=user_id)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run_case())

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Task not found"


def test_update_subtask_raises_404_when_not_found(monkeypatch):
    subtask_id = uuid4()
    user_id = uuid4()

    async def fake_update_subtask(**kwargs):
        return None

    monkeypatch.setattr(subtasks_service.subtasks_db, "update_subtask", fake_update_subtask)

    async def run_case():
        req = SubtaskUpdateRequest(title="renamed")
        await subtasks_service.update_subtask(subtask_id=subtask_id, req=req, user_id=user_id)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run_case())

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Subtask not found"


def test_complete_subtask_raises_404_when_not_found(monkeypatch):
    subtask_id = uuid4()
    user_id = uuid4()

    async def fake_complete_subtask(**kwargs):
        return None

    monkeypatch.setattr(subtasks_service.subtasks_db, "complete_subtask", fake_complete_subtask)

    async def run_case():
        await subtasks_service.complete_subtask(subtask_id=subtask_id, user_id=user_id)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run_case())

    assert exc_info.value.status_code == 404


def test_delete_subtask_raises_404_when_not_found(monkeypatch):
    subtask_id = uuid4()
    user_id = uuid4()

    async def fake_delete_subtask(**kwargs):
        return False

    monkeypatch.setattr(subtasks_service.subtasks_db, "delete_subtask", fake_delete_subtask)

    async def run_case():
        await subtasks_service.delete_subtask(subtask_id=subtask_id, user_id=user_id)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run_case())

    assert exc_info.value.status_code == 404


def test_reorder_subtasks_validates_membership(monkeypatch):
    task_id = uuid4()
    user_id = uuid4()
    s1 = uuid4()
    s2 = uuid4()

    async def fake_get_task(task_id, user_id):
        return {"id": task_id}

    async def fake_list_subtasks(task_id, user_id):
        return {"items": [{"id": s1}, {"id": s2}], "total": 2}

    monkeypatch.setattr(subtasks_service.tasks_db, "get_task", fake_get_task)
    monkeypatch.setattr(subtasks_service.subtasks_db, "list_subtasks", fake_list_subtasks)

    async def run_case():
        req = SubtaskReorderRequest(subtask_ids=[s1, uuid4()])
        await subtasks_service.reorder_subtasks(task_id=task_id, req=req, user_id=user_id)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run_case())

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Subtask not found"


def test_reorder_subtasks_calls_db_with_user_scope(monkeypatch):
    task_id = uuid4()
    user_id = uuid4()
    s1 = uuid4()
    s2 = uuid4()
    captured = {}

    async def fake_get_task(task_id, user_id):
        return {"id": task_id}

    async def fake_list_subtasks(task_id, user_id):
        return {"items": [{"id": s1}, {"id": s2}], "total": 2}

    async def fake_reorder_subtasks(**kwargs):
        captured.update(kwargs)
        return {"items": [], "total": 0}

    monkeypatch.setattr(subtasks_service.tasks_db, "get_task", fake_get_task)
    monkeypatch.setattr(subtasks_service.subtasks_db, "list_subtasks", fake_list_subtasks)
    monkeypatch.setattr(subtasks_service.subtasks_db, "reorder_subtasks", fake_reorder_subtasks)

    async def run_case():
        req = SubtaskReorderRequest(subtask_ids=[s2, s1])
        await subtasks_service.reorder_subtasks(task_id=task_id, req=req, user_id=user_id)

    asyncio.run(run_case())

    assert captured["task_id"] == task_id
    assert captured["user_id"] == user_id
    assert captured["subtask_ids"] == [s2, s1]
