import asyncio
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.projects import ProjectCreateRequest, ProjectUpdateRequest
from app.services import projects_service


def test_create_project_passes_user_id_and_path(monkeypatch):
    user_id = uuid4()
    captured = {}

    async def fake_create_project(**kwargs):
        captured.update(kwargs)
        return {"id": uuid4(), **kwargs}

    monkeypatch.setattr(projects_service.projects_db, "create_project", fake_create_project)

    async def run_case():
        req = ProjectCreateRequest(path="work/client-a")
        await projects_service.create_project(req=req, user_id=user_id)

    asyncio.run(run_case())

    assert captured["user_id"] == user_id
    assert captured["path"] == "work/client-a"


def test_list_projects_delegates_and_returns_payload(monkeypatch):
    user_id = uuid4()
    payload = {"items": [{"id": uuid4(), "path": "work/client-a"}], "total": 1}

    async def fake_list_projects(*, user_id):
        return payload

    monkeypatch.setattr(projects_service.projects_db, "list_projects", fake_list_projects)

    async def run_case():
        return await projects_service.list_projects(user_id=user_id)

    result = asyncio.run(run_case())

    assert result == payload


def test_get_project_raises_404_when_missing(monkeypatch):
    project_id = uuid4()
    user_id = uuid4()

    async def fake_get_project(**kwargs):
        return None

    monkeypatch.setattr(projects_service.projects_db, "get_project", fake_get_project)

    async def run_case():
        await projects_service.get_project(project_id=project_id, user_id=user_id)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run_case())

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Project not found"


def test_get_project_returns_row_when_present(monkeypatch):
    project_id = uuid4()
    user_id = uuid4()
    row = {"id": project_id, "user_id": user_id, "path": "work/client-a"}

    async def fake_get_project(**kwargs):
        return row

    monkeypatch.setattr(projects_service.projects_db, "get_project", fake_get_project)

    async def run_case():
        return await projects_service.get_project(project_id=project_id, user_id=user_id)

    result = asyncio.run(run_case())

    assert result == row


def test_update_project_raises_404_when_missing(monkeypatch):
    project_id = uuid4()
    user_id = uuid4()

    async def fake_update_project(**kwargs):
        return None

    monkeypatch.setattr(projects_service.projects_db, "update_project", fake_update_project)

    async def run_case():
        req = ProjectUpdateRequest(path="work/client-b")
        await projects_service.update_project(project_id=project_id, req=req, user_id=user_id)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run_case())

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Project not found"


def test_update_project_passes_args_and_returns_row(monkeypatch):
    project_id = uuid4()
    user_id = uuid4()
    captured = {}
    row = {"id": project_id, "user_id": user_id, "path": "work/client-b"}

    async def fake_update_project(**kwargs):
        captured.update(kwargs)
        return row

    monkeypatch.setattr(projects_service.projects_db, "update_project", fake_update_project)

    async def run_case():
        req = ProjectUpdateRequest(path="work/client-b")
        return await projects_service.update_project(project_id=project_id, req=req, user_id=user_id)

    result = asyncio.run(run_case())

    assert captured["project_id"] == project_id
    assert captured["user_id"] == user_id
    assert captured["path"] == "work/client-b"
    assert result == row


def test_delete_project_raises_404_when_missing(monkeypatch):
    project_id = uuid4()
    user_id = uuid4()

    async def fake_delete_project(**kwargs):
        return False

    monkeypatch.setattr(projects_service.projects_db, "delete_project", fake_delete_project)

    async def run_case():
        await projects_service.delete_project(project_id=project_id, user_id=user_id)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run_case())

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Project not found"


def test_delete_project_succeeds_when_present(monkeypatch):
    project_id = uuid4()
    user_id = uuid4()

    async def fake_delete_project(**kwargs):
        return True

    monkeypatch.setattr(projects_service.projects_db, "delete_project", fake_delete_project)

    async def run_case():
        await projects_service.delete_project(project_id=project_id, user_id=user_id)

    asyncio.run(run_case())


def test_search_projects_trims_query_and_delegates(monkeypatch):
    user_id = uuid4()
    captured = {}
    payload = {"items": [{"id": uuid4(), "path": "work/client-a"}], "total": 1}

    async def fake_search_projects(**kwargs):
        captured.update(kwargs)
        return payload

    monkeypatch.setattr(projects_service.projects_db, "search_projects", fake_search_projects)

    async def run_case():
        return await projects_service.search_projects(user_id=user_id, q="  client  ", limit=15)

    result = asyncio.run(run_case())

    assert captured["user_id"] == user_id
    assert captured["q"] == "client"
    assert captured["limit"] == 15
    assert result == payload


def test_search_projects_rejects_empty_query():
    user_id = uuid4()

    async def run_case():
        await projects_service.search_projects(user_id=user_id, q="   ")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(run_case())

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Search query cannot be empty"
