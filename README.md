# OnTasky

A lightweight task manager with an integrated server-driven Pomodoro timer, built with FastAPI. Designed to be used directly by humans via a browser UI and by AI agents via the REST API.

---

## Features

- **Projects** — organise tasks into named projects (hierarchical names supported via `/` path convention).
- **Tasks** — create, list, update, and delete tasks with:
  - Due-bucket scheduling (`today`, `tomorrow`, `this_week`, `someday`).
  - Optional calendar date pinning (`due_date_epoch` – UTC midnight epoch seconds).
  - Recurring schedules (`repeat_every_number` + `repeat_every_unit`).
  - Free-form JSONB `attributes` bag for agent-readable metadata.
  - Status lifecycle: `pending → in_progress → completed`.
  - Pomodoro work-session counter per task.
- **Subtasks** — ordered checklist items attached to a task.
- **Pomodoro timer** — server-side, stateless-client design:
  - Start, pause, stop a work/break cycle for any pending task.
  - Remaining time is computed from timestamps on every `GET /api/pomodoro/status` call — no background workers.
  - Configurable work and break durations per user.
  - Automatically advances work → break → work phases.
  - Increments the task's `pomodoro_counter` on each completed work phase.
- **Browser UI** — single-page interface served from the same FastAPI app at `/`.

---

## Architecture

```
Browser / Agent
      │
      ▼
FastAPI app  (main.py)
  ├── /           → Jinja2 HTML UI         (app/ui/routes.py)
  ├── /static     → CSS + JS               (app/static/)
  └── /api        → JSON REST API          (app/api/routes.py)
        │
        ├── app/services/pomodoro.py  – timer business logic
        ├── app/repositories.py       – async SQLAlchemy queries
        ├── app/schemas.py            – Pydantic I/O models
        ├── app/models.py             – SQLAlchemy ORM models
        └── app/db.py                 – lazy async engine / session factory
```

There is no separate frontend build step. All JavaScript is plain ES modules served as static files.

---

## Data model summary

| Table | Key columns | Notes |
|---|---|---|
| `users` | `id` (UUID PK), `email`, `display_name` | Auto-created from `X-User-Id` header on first request. |
| `projects` | `id`, `user_id` FK, `name` | `name` supports `a/b/c` hierarchy by convention. |
| `tasks` | `id`, `user_id`, `project_id`, `title`, `due_bucket`, `due_date_epoch`, `repeat_every_number`, `repeat_every_unit`, `status`, `pomodoro_counter`, `note`, `attributes` JSONB | `attributes` is a free-form JSONB bag for extra metadata; `due_date_epoch` is UTC midnight epoch seconds. |
| `subtasks` | `id`, `task_id` FK, `title`, `completed` | Ordered checklist under a task. |
| `pomodoro_sessions` | `id`, `user_id`, `task_id`, `phase`, `phase_started_at`, `status`, `work_minutes`, `break_minutes`, `accumulated_pause_seconds`, `paused_at` | All timing state is stored here; remaining seconds are derived at request time. |
| `app_settings` | `key` (PK), `value` JSONB | Key-value bag; used to store per-app Pomodoro defaults (`pomodoro_defaults`). |

Indexes are placed on `tasks(user_id)`, `tasks(due_bucket)`, `tasks(status)`, and `pomodoro_sessions(user_id, status)`.

---

## Setup

### Prerequisites

- Python 3.11+
- A running PostgreSQL server

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/your-org/ontasky.git
cd ontasky
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example below to a `.env` file in the project root and fill in your values:

```dotenv
DB_SERVER=localhost
DB_NAME=ontasky
DB_SCHEMA=public
DB_USER=postgres
DB_PWD=yourpassword
DB_PORT=5432
```

All `DB_*` variables are read by `app/config.py` via `pydantic-settings`. The `.env` file is loaded automatically on startup.

### 4. Initialise the database

Start the app once (see step 5), then call the init endpoint:

```bash
curl -X POST http://localhost:8000/api/admin/init-db
```

This creates all tables idempotently using SQLAlchemy's `create_all`. It is safe to call repeatedly.

### 5. Run the server

```bash
uvicorn main:app --reload
```

The app is available at `http://localhost:8000`.

---

## Using the app

### Browser UI

Open `http://localhost:8000` in a browser. The UI uses `X-User-Id` (a UUID you supply or that is generated on first load) to identify you. All requests are scoped to that user.

### Pomodoro timer

1. Create a task from the UI or API.
2. Click **Start** on a task (or `POST /api/pomodoro/start` with `{"task_id": "<uuid>"}`).
3. Poll `GET /api/pomodoro/status` to see remaining seconds — the UI does this automatically every second.
4. Use **Pause** / **Stop** as needed.
5. When the work phase finishes, the timer auto-advances to break, then back to work. Each completed work phase increments the task's Pomodoro counter.

---

## API endpoint summary

All endpoints are prefixed with `/api`. The `X-User-Id` header (UUID) is required on all user-scoped endpoints.

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Returns `{"status": "ok"}`. |

### Admin

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/admin/init-db` | Create all DB tables (idempotent). |

### Projects

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/projects` | List all projects for the user. |
| `POST` | `/api/projects` | Create a project. Body: `{"name": "..."}`. |
| `GET` | `/api/projects/{id}` | Get a single project. |
| `PUT` | `/api/projects/{id}` | Rename a project. |
| `DELETE` | `/api/projects/{id}` | Delete project (cascades to tasks). |

### Tasks

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/tasks` | List tasks. Optional query params: `user_id`, `due_bucket`, `project_id`, `status`. |
| `POST` | `/api/tasks` | Create a task. |
| `GET` | `/api/tasks/{id}` | Get a task (includes subtasks). |
| `PUT` | `/api/tasks/{id}` | Update a task (partial fields). |
| `DELETE` | `/api/tasks/{id}` | Delete a task. |
| `POST` | `/api/tasks/{id}/complete` | Quick-complete shortcut. |

### Subtasks

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/tasks/{task_id}/subtasks` | Add a subtask. Body: `{"title": "..."}`. |
| `PUT` | `/api/tasks/{task_id}/subtasks/{id}` | Update title or `completed` flag. |
| `DELETE` | `/api/tasks/{task_id}/subtasks/{id}` | Remove a subtask. |

### Pomodoro

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/pomodoro/settings` | Get current work/break durations. |
| `PUT` | `/api/pomodoro/settings` | Update durations. Body: `{"work_minutes": 25, "break_minutes": 5}`. |
| `POST` | `/api/pomodoro/start` | Start or resume a session. Body: `{"task_id": "<uuid>"}`. |
| `POST` | `/api/pomodoro/pause` | Pause the active session. |
| `GET` | `/api/pomodoro/status` | Get current session state and remaining seconds. |
| `POST` | `/api/pomodoro/stop` | Interrupt and discard the active session. |

Interactive documentation is available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

---

## Running tests

Tests run entirely in-process — no PostgreSQL connection required.

```bash
pip install -r requirements-dev.txt
pytest
```

The suite covers:

| File | What is tested |
|---|---|
| `tests/test_due_bucket.py` | `bucket_epoch` helper: all four buckets, boundary dates (Sunday, month-end). |
| `tests/test_schemas.py` | Pydantic validation: single-line titles, repeat pair consistency, enum fields. |
| `tests/test_pomodoro_logic.py` | `compute_remaining_seconds`: phase start, partial elapsed, pause freeze, accumulated pauses, custom durations. |

