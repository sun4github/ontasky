--
-- PostgreSQL database dump
--

\restrict iKr3iFFyzMc9cqp5AOn5YwphfgbmqRY8Bm7zMw5OYtH4cUMOiwSCEM2IrB62irE

-- Dumped from database version 15.16 (Debian 15.16-0+deb12u1)
-- Dumped by pg_dump version 15.16 (Debian 15.16-0+deb12u1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA public;


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS 'standard public schema';


--
-- Name: repeat_unit; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.repeat_unit AS ENUM (
    'day',
    'week',
    'month',
    'year'
);


--
-- Name: task_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.task_status AS ENUM (
    'pending',
    'in_progress',
    'completed'
);


--
-- Name: user_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.user_type AS ENUM (
    'human',
    'agent'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: app_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_user (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    username text,
    name text,
    user_type public.user_type DEFAULT 'human'::public.user_type NOT NULL,
    CONSTRAINT app_user_username_format_chk CHECK (((username IS NULL) OR (username ~ '^[A-Za-z0-9_.-]{3,50}$'::text)))
);


--
-- Name: pomodoro_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pomodoro_session (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    task_id uuid NOT NULL,
    started_at timestamp with time zone NOT NULL,
    ended_at timestamp with time zone,
    work_seconds integer NOT NULL,
    break_seconds integer NOT NULL,
    completed boolean DEFAULT false NOT NULL,
    CONSTRAINT pomodoro_session_break_seconds_check CHECK ((break_seconds >= 0)),
    CONSTRAINT pomodoro_session_work_seconds_check CHECK ((work_seconds > 0))
);


--
-- Name: project; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    path text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT project_path_check CHECK ((path <> ''::text)),
    CONSTRAINT project_path_check1 CHECK ((path !~ '(^/|/$|//)'::text))
);


--
-- Name: subtask; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subtask (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    task_id uuid NOT NULL,
    title text NOT NULL,
    is_completed boolean DEFAULT false NOT NULL,
    sort_order integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    CONSTRAINT subtask_title_check CHECK ((title !~ '[\r\n]'::text))
);


--
-- Name: task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.task (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    project_id uuid,
    title text NOT NULL,
    note text,
    status public.task_status DEFAULT 'pending'::public.task_status NOT NULL,
    pomodoro_count integer DEFAULT 0 NOT NULL,
    due_on date,
    repeat_every smallint,
    repeat_unit public.repeat_unit,
    extra jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    created_by_user_id uuid,
    started_at timestamp with time zone,
    tokens_consumed integer,
    model_used text,
    CONSTRAINT task_check CHECK ((((repeat_every IS NULL) AND (repeat_unit IS NULL)) OR ((repeat_every IS NOT NULL) AND (repeat_unit IS NOT NULL)))),
    CONSTRAINT task_pomodoro_count_check CHECK ((pomodoro_count >= 0)),
    CONSTRAINT task_repeat_every_check CHECK (((repeat_every >= 1) AND (repeat_every <= 10))),
    CONSTRAINT task_title_check CHECK ((title !~ '[\r\n]'::text)),
    CONSTRAINT task_tokens_consumed_check CHECK (((tokens_consumed IS NULL) OR (tokens_consumed >= 0)))
);


--
-- Name: user_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_settings (
    user_id uuid NOT NULL,
    alert_sound text DEFAULT 'reward.wav'::text NOT NULL,
    pomodoro_mins smallint DEFAULT 25 NOT NULL,
    break_mins smallint DEFAULT 5 NOT NULL,
    timezone text DEFAULT 'UTC'::text NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT user_settings_break_mins_check CHECK (((break_mins >= 1) AND (break_mins <= 120))),
    CONSTRAINT user_settings_pomodoro_mins_check CHECK (((pomodoro_mins >= 1) AND (pomodoro_mins <= 180)))
);


--
-- Name: app_user app_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_pkey PRIMARY KEY (id);


--
-- Name: app_user app_user_username_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_username_unique UNIQUE (username);


--
-- Name: pomodoro_session pomodoro_session_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pomodoro_session
    ADD CONSTRAINT pomodoro_session_pkey PRIMARY KEY (id);


--
-- Name: project project_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project
    ADD CONSTRAINT project_pkey PRIMARY KEY (id);


--
-- Name: project project_user_id_path_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project
    ADD CONSTRAINT project_user_id_path_key UNIQUE (user_id, path);


--
-- Name: subtask subtask_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subtask
    ADD CONSTRAINT subtask_pkey PRIMARY KEY (id);


--
-- Name: task task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task
    ADD CONSTRAINT task_pkey PRIMARY KEY (id);


--
-- Name: user_settings user_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_pkey PRIMARY KEY (user_id);


--
-- Name: idx_project_user_path; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_user_path ON public.project USING btree (user_id, path);


--
-- Name: idx_subtask_user_task_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_subtask_user_task_order ON public.subtask USING btree (user_id, task_id, sort_order);


--
-- Name: idx_task_extra_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_task_extra_gin ON public.task USING gin (extra);


--
-- Name: idx_task_user_due_on; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_task_user_due_on ON public.task USING btree (user_id, due_on) WHERE (status <> 'completed'::public.task_status);


--
-- Name: idx_task_user_project_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_task_user_project_status ON public.task USING btree (user_id, project_id, status);


--
-- Name: idx_task_user_title_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_task_user_title_search ON public.task USING btree (user_id, lower(title));


--
-- Name: idx_task_user_status_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_task_user_status_created ON public.task USING btree (user_id, status, created_at DESC);


--
-- Name: idx_project_user_leaf_title_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_user_leaf_title_search ON public.project USING btree (user_id, lower(split_part(path, '/', array_length(string_to_array(path, '/'), 1))));


--
-- Name: pomodoro_session pomodoro_session_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pomodoro_session
    ADD CONSTRAINT pomodoro_session_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.task(id) ON DELETE CASCADE;


--
-- Name: pomodoro_session pomodoro_session_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pomodoro_session
    ADD CONSTRAINT pomodoro_session_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_user(id) ON DELETE CASCADE;


--
-- Name: project project_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project
    ADD CONSTRAINT project_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_user(id) ON DELETE CASCADE;


--
-- Name: subtask subtask_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subtask
    ADD CONSTRAINT subtask_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.task(id) ON DELETE CASCADE;


--
-- Name: subtask subtask_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subtask
    ADD CONSTRAINT subtask_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_user(id) ON DELETE CASCADE;


--
-- Name: task task_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task
    ADD CONSTRAINT task_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.app_user(id);


--
-- Name: task task_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task
    ADD CONSTRAINT task_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.project(id) ON DELETE SET NULL;


--
-- Name: task task_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task
    ADD CONSTRAINT task_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_user(id) ON DELETE CASCADE;


--
-- Name: user_settings user_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_user(id) ON DELETE CASCADE;

-- Assigner credentials: store hashed keys for authentication
CREATE TABLE assigner_credential (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assigner_user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    key_hash TEXT NOT NULL,
    label TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT assigner_credential_label_check CHECK (char_length(label) > 0 AND char_length(label) <= 100),
    CONSTRAINT assigner_credential_key_hash_check CHECK (char_length(key_hash) > 0)
);

CREATE INDEX idx_assigner_credential_user_id 
    ON assigner_credential(assigner_user_id);

CREATE INDEX idx_assigner_credential_user_active 
    ON assigner_credential(assigner_user_id) 
    WHERE revoked_at IS NULL;


-- Assignment grants: authorize assigners to create tasks for users
CREATE TABLE task_assigner_grant (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    assigner_user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    permissions JSONB NOT NULL DEFAULT '{"create_task": true}'::jsonb,
    expires_at TIMESTAMP WITH TIME ZONE,
    granted_by_user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    revoked_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT task_assigner_grant_permissions_check 
        CHECK (jsonb_typeof(permissions) = 'object'),
    CONSTRAINT task_assigner_grant_unique 
        UNIQUE (user_id, assigner_user_id)
);

CREATE INDEX idx_task_assigner_grant_user_id 
    ON task_assigner_grant(user_id);

CREATE INDEX idx_task_assigner_grant_assigner_id 
    ON task_assigner_grant(assigner_user_id);

CREATE INDEX idx_task_assigner_grant_active 
    ON task_assigner_grant(user_id, assigner_user_id) 
    WHERE revoked_at IS NULL;

--
-- PostgreSQL database dump complete
--

\unrestrict iKr3iFFyzMc9cqp5AOn5YwphfgbmqRY8Bm7zMw5OYtH4cUMOiwSCEM2IrB62irE

