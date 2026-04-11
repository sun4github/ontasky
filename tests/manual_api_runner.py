#!/usr/bin/env python3
"""Manual API test runner for Ontasky FastAPI endpoints.

This script exercises core endpoints in a realistic flow so you can tweak
payloads quickly while the server is running.

Default flow:
1. Health check
2. Create a project
3. Create a task in that project
4. Update the task
5. Create subtasks
6. Complete one subtask
7. Complete task
8. List tasks/subtasks/projects
9. Optionally clean up created resources

Examples:
  python tests/manual_api_runner.py \
        --token "<bearer-token>"

  python tests/manual_api_runner.py \
    --scheme http --host 127.0.0.1 --port 8000 \
        --token "<bearer-token>" \
    --project-path "Work/API" --task-title "Prepare sprint board" \
    --subtask-titles "Draft stories" "Estimate points" "Set owners" \
    --cleanup

Notes:
- The API requires Authorization: Bearer <token> for user-scoped endpoints.
- Task ownership is derived from the bearer token subject (sub claim).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from typing import Any
from urllib import error, parse, request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run manual API endpoint tests")

    parser.add_argument("--scheme", default="http", choices=["http", "https"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--api-prefix", default="/api/v1")
    parser.add_argument("--timeout", type=float, default=15.0)

    parser.add_argument("--token", required=True, help="Bearer access token")

    parser.add_argument("--project-path", default="Personal/Manual Endpoint Test")
    parser.add_argument("--updated-project-path", default="Personal/Manual Endpoint Test/Renamed")

    parser.add_argument("--task-title", default="Manual API smoke task")
    parser.add_argument("--task-note", default="Created by tests/manual_api_runner.py")
    parser.add_argument(
        "--task-due-in-days",
        type=int,
        default=1,
        help="Due date offset from today for create task payload",
    )
    parser.add_argument("--repeat-every", type=int, default=2)
    parser.add_argument(
        "--repeat-unit",
        default="day",
        choices=["day", "week", "month", "year"],
    )
    parser.add_argument("--updated-task-title", default="Manual API smoke task (updated)")
    parser.add_argument("--updated-task-note", default="Updated by manual API runner")

    parser.add_argument(
        "--subtask-titles",
        nargs="+",
        default=["First checklist item", "Second checklist item"],
        help="One or more subtask titles to create",
    )
    parser.add_argument(
        "--complete-subtask-index",
        type=int,
        default=0,
        help="Zero-based index of created subtask to mark completed",
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete created task and project at the end",
    )
    parser.add_argument(
        "--keep-task-open",
        action="store_true",
        help="Reopen task after completion to test /reopen endpoint",
    )

    return parser.parse_args()


class ApiClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def call(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
        auth_required: bool = True,
    ) -> tuple[int, Any]:
        full_url = f"{self.base_url}{path}"
        if params:
            clean_params = {k: v for k, v in params.items() if v is not None}
            full_url = f"{full_url}?{parse.urlencode(clean_params)}"

        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if auth_required:
            headers.update(self.default_headers)
        if extra_headers:
            headers.update(extra_headers)

        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        req = request.Request(url=full_url, method=method, headers=headers, data=data)

        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                status_code = resp.getcode()
                body = resp.read().decode("utf-8")
                return status_code, self._parse_body(body)
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8") if exc.fp else ""
            return exc.code, self._parse_body(body)
        except error.URLError as exc:
            raise RuntimeError(f"Failed to connect to {full_url}: {exc}") from exc

    @staticmethod
    def _parse_body(body: str) -> Any:
        if not body:
            return None
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return body


def step(name: str, status: int, body: Any, expected: set[int]) -> Any:
    ok = status in expected
    marker = "OK" if ok else "FAIL"
    print(f"[{marker}] {name} -> HTTP {status}")
    print(json.dumps(body, indent=2, default=str))
    print("-" * 80)
    if not ok:
        expected_text = ", ".join(str(v) for v in sorted(expected))
        raise RuntimeError(f"{name} failed: expected HTTP {expected_text}, got {status}")
    return body


def main() -> int:
    args = parse_args()
    base_url = f"{args.scheme}://{args.host}:{args.port}"
    api = ApiClient(base_url=base_url, token=args.token, timeout=args.timeout)

    created_project_id: str | None = None
    created_task_id: str | None = None
    created_subtask_ids: list[str] = []

    print(f"Base URL: {base_url}")
    print(f"API prefix: {args.api_prefix}")
    print("=" * 80)

    # 1) Health check
    status, body = api.call("GET", "/health", auth_required=False)
    step("Health check", status, body, {200})

    # 2) Create project
    create_project_payload = {"path": args.project_path}
    status, body = api.call("POST", f"{args.api_prefix}/projects", payload=create_project_payload)
    project_body = step("Create project", status, body, {201})
    created_project_id = project_body["id"]

    # 3) Update project
    status, body = api.call(
        "PATCH",
        f"{args.api_prefix}/projects/{created_project_id}",
        payload={"path": args.updated_project_path},
    )
    step("Update project", status, body, {200})

    # 4) Create task in project
    due_on = (date.today() + timedelta(days=args.task_due_in_days)).isoformat()
    create_task_payload = {
        "title": args.task_title,
        "project_id": created_project_id,
        "note": args.task_note,
        "due_on": due_on,
        "repeat_every": args.repeat_every,
        "repeat_unit": args.repeat_unit,
    }
    status, body = api.call(
        "POST",
        f"{args.api_prefix}/tasks",
        payload=create_task_payload,
    )
    task_body = step("Create task", status, body, {201})
    created_task_id = task_body["id"]

    # 5) Update task
    update_task_payload = {
        "title": args.updated_task_title,
        "note": args.updated_task_note,
        "project_id": created_project_id,
        "repeat_every": args.repeat_every,
        "repeat_unit": args.repeat_unit,
    }
    status, body = api.call(
        "PATCH",
        f"{args.api_prefix}/tasks/{created_task_id}",
        payload=update_task_payload,
    )
    step("Update task", status, body, {200})

    # 6) Create subtasks
    for idx, title in enumerate(args.subtask_titles):
        subtask_payload = {"title": title, "sort_order": idx}
        status, body = api.call(
            "POST",
            f"{args.api_prefix}/tasks/{created_task_id}/subtasks",
            payload=subtask_payload,
        )
        subtask_body = step(f"Create subtask #{idx + 1}", status, body, {201})
        created_subtask_ids.append(subtask_body["id"])

    # 7) Reorder subtasks
    status, body = api.call(
        "PUT",
        f"{args.api_prefix}/tasks/{created_task_id}/subtasks/reorder",
        payload={"subtask_ids": list(reversed(created_subtask_ids))},
    )
    step("Reorder subtasks", status, body, {200})

    # 8) Complete selected subtask
    if created_subtask_ids:
        if args.complete_subtask_index < 0 or args.complete_subtask_index >= len(created_subtask_ids):
            raise RuntimeError(
                f"--complete-subtask-index out of range. Must be 0..{len(created_subtask_ids) - 1}"
            )
        subtask_to_complete = created_subtask_ids[args.complete_subtask_index]
        status, body = api.call(
            "POST",
            f"{args.api_prefix}/subtasks/{subtask_to_complete}/complete",
        )
        step("Complete subtask", status, body, {200})

    # 9) Complete task
    status, body = api.call("POST", f"{args.api_prefix}/tasks/{created_task_id}/complete")
    step("Complete task", status, body, {200})

    # 10) Optionally reopen task
    if args.keep_task_open:
        status, body = api.call("POST", f"{args.api_prefix}/tasks/{created_task_id}/reopen")
        step("Reopen task", status, body, {200})

    # 11) List resources
    status, body = api.call("GET", f"{args.api_prefix}/projects")
    step("List projects", status, body, {200})

    status, body = api.call("GET", f"{args.api_prefix}/tasks", params={"project_id": created_project_id})
    step("List tasks by project", status, body, {200})

    status, body = api.call("GET", f"{args.api_prefix}/tasks/{created_task_id}")
    step("Get task", status, body, {200})

    status, body = api.call("GET", f"{args.api_prefix}/tasks/{created_task_id}/subtasks")
    step("List subtasks", status, body, {200})

    # 12) Optional cleanup
    if args.cleanup:
        if created_task_id:
            status, body = api.call("DELETE", f"{args.api_prefix}/tasks/{created_task_id}")
            step("Delete task", status, body, {200})
        if created_project_id:
            status, body = api.call("DELETE", f"{args.api_prefix}/projects/{created_project_id}")
            step("Delete project", status, body, {200})

    print("Run completed successfully.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted by user", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)