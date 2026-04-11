# PostgreSQL Schema Summary (public)

- Database: ontasky_app
- Schema: public
- Generated: 2026-03-24 02:22:43 UTC

## Extensions
- pgcrypto
- plpgsql

## Enum Types
- repeat_unit: day, week, month, year
- task_status: pending, in_progress, completed
- user_type: human, agent

## Tables

### app_user

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | uuid | NO | gen_random_uuid() |
| created_at | timestamp with time zone | NO | now() |
| username | text | YES |  |
| name | text | YES |  |
| user_type | USER-DEFINED (user_type) | NO | 'human'::user_type |

Constraints:
- app_user_pkey [p]
- app_user_username_format_chk [c]
- app_user_username_unique [u]

Indexes:
- app_user_pkey: CREATE UNIQUE INDEX app_user_pkey ON public.app_user USING btree (id)
- app_user_username_unique: CREATE UNIQUE INDEX app_user_username_unique ON public.app_user USING btree (username)

### pomodoro_session

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | uuid | NO | gen_random_uuid() |
| user_id | uuid | NO |  |
| task_id | uuid | NO |  |
| started_at | timestamp with time zone | NO |  |
| ended_at | timestamp with time zone | YES |  |
| work_seconds | integer | NO |  |
| break_seconds | integer | NO |  |
| completed | boolean | NO | false |

Constraints:
- pomodoro_session_break_seconds_check [c]
- pomodoro_session_pkey [p]
- pomodoro_session_task_id_fkey [f]
- pomodoro_session_user_id_fkey [f]
- pomodoro_session_work_seconds_check [c]

Indexes:
- pomodoro_session_pkey: CREATE UNIQUE INDEX pomodoro_session_pkey ON public.pomodoro_session USING btree (id)

### project

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | uuid | NO | gen_random_uuid() |
| user_id | uuid | NO |  |
| path | text | NO |  |
| created_at | timestamp with time zone | NO | now() |

Constraints:
- project_path_check [c]
- project_path_check1 [c]
- project_pkey [p]
- project_user_id_fkey [f]
- project_user_id_path_key [u]

Indexes:
- idx_project_user_path: CREATE INDEX idx_project_user_path ON public.project USING btree (user_id, path)
- project_pkey: CREATE UNIQUE INDEX project_pkey ON public.project USING btree (id)
- project_user_id_path_key: CREATE UNIQUE INDEX project_user_id_path_key ON public.project USING btree (user_id, path)

### subtask

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | uuid | NO | gen_random_uuid() |
| task_id | uuid | NO |  |
| title | text | NO |  |
| is_completed | boolean | NO | false |
| sort_order | integer | NO | 0 |
| created_at | timestamp with time zone | NO | now() |
| completed_at | timestamp with time zone | YES |  |

Constraints:
- subtask_pkey [p]
- subtask_task_id_fkey [f]
- subtask_title_check [c]

Indexes:
- idx_subtask_task_order: CREATE INDEX idx_subtask_task_order ON public.subtask USING btree (task_id, sort_order)
- subtask_pkey: CREATE UNIQUE INDEX subtask_pkey ON public.subtask USING btree (id)

### task

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | uuid | NO | gen_random_uuid() |
| user_id | uuid | NO |  |
| project_id | uuid | YES |  |
| title | text | NO |  |
| note | text | YES |  |
| status | USER-DEFINED (task_status) | NO | 'pending'::task_status |
| pomodoro_count | integer | NO | 0 |
| due_on | date | YES |  |
| repeat_every | smallint | YES |  |
| repeat_unit | USER-DEFINED (repeat_unit) | YES |  |
| extra | jsonb | NO | '{}'::jsonb |
| created_at | timestamp with time zone | NO | now() |
| updated_at | timestamp with time zone | NO | now() |
| completed_at | timestamp with time zone | YES |  |
| created_by_user_id | uuid | YES |  |
| started_at | timestamp with time zone | YES |  |
| tokens_consumed | integer | YES |  |
| model_used | text | YES |  |

Constraints:
- task_check [c]
- task_created_by_user_id_fkey [f]
- task_pkey [p]
- task_pomodoro_count_check [c]
- task_project_id_fkey [f]
- task_repeat_every_check [c]
- task_title_check [c]
- task_tokens_consumed_check [c]
- task_user_id_fkey [f]

Indexes:
- idx_task_extra_gin: CREATE INDEX idx_task_extra_gin ON public.task USING gin (extra)
- idx_task_user_due_on: CREATE INDEX idx_task_user_due_on ON public.task USING btree (user_id, due_on) WHERE (status <> 'completed'::task_status)
- idx_task_user_project_status: CREATE INDEX idx_task_user_project_status ON public.task USING btree (user_id, project_id, status)
- idx_task_user_status_created: CREATE INDEX idx_task_user_status_created ON public.task USING btree (user_id, status, created_at DESC)
- task_pkey: CREATE UNIQUE INDEX task_pkey ON public.task USING btree (id)

### user_settings

| Column | Type | Nullable | Default |
|---|---|---|---|
| user_id | uuid | NO |  |
| alert_sound | text | NO | 'reward.wav'::text |
| pomodoro_mins | smallint | NO | 25 |
| break_mins | smallint | NO | 5 |
| timezone | text | NO | 'UTC'::text |
| updated_at | timestamp with time zone | NO | now() |

Constraints:
- user_settings_break_mins_check [c]
- user_settings_pkey [p]
- user_settings_pomodoro_mins_check [c]
- user_settings_user_id_fkey [f]

Indexes:
- user_settings_pkey: CREATE UNIQUE INDEX user_settings_pkey ON public.user_settings USING btree (user_id)
