# Persistent agent sessions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist anonymous agent conversations in PostgreSQL through LangGraph checkpoints, isolated by session and agent.

**Architecture:** The backend issues an opaque HttpOnly cookie, stores only its hash in a PostgreSQL session table, and derives a LangGraph thread ID from the server-side session UUID and agent ID. A `MessagesState` graph adds the fixed persona prompt at invocation time and checkpoints only conversation messages; the frontend loads history from the backend and sends only the new turn.

**Tech Stack:** FastAPI, LangChain `ChatOpenAI`, LangGraph `StateGraph` and `AsyncPostgresSaver`, SQLAlchemy AsyncEngine for application tables, PostgreSQL via psycopg for LangGraph checkpoints, Svelte frontend.

**Spec:** `docs/superpowers/specs/2026-10-15-persistent-agent-sessions.md`

## Global Constraints

- Use `uv` for Python dependency management.
- Use PostgreSQL, not process-local memory, for production session and graph state.
- Session tokens are random, HttpOnly, hashed before persistence, and expire after 30 days of inactivity.
- The client never supplies a LangGraph thread ID or conversation history.
- The fixed profile remains the only source of agent facts.
- Respect the explicit local CORS origins by default and allow production origins only through configuration.

## Review Focus

- Forged or expired cookie: rejected as an identity and replaced with a new session.
- Cross-agent or cross-session access: isolated by server-derived thread ID.
- Failed model call: remove the pending user turn from graph state so the next turn has valid history.
- Session reset/expiry: remove both the session record and each agent's checkpoint.
- Cross-origin browser request: credentials are allowed only for configured exact origins.

---

### Task 1: Add PostgreSQL anonymous session storage

**Files:**
- Create: `backend/app/session_store.py`
- Modify: `backend/pyproject.toml`, `backend/uv.lock`, `backend/.env.example`

**Interfaces:** `SessionStore.open(database_url)`, `resolve(token) -> (session_uuid, new_token | None)`, `revoke(session_uuid)`, `delete_expired()`, `close()`.

- [x] Add `langgraph`, `langgraph-checkpoint-postgres`, `psycopg[pool]`, and Alembic through `uv`.
- [x] Add an Alembic-managed sessions table with UUID, unique token hash, timestamps, expiry, and cleanup state.
- [x] Store a SHA-256 digest of each opaque token; refresh a 30-day sliding expiry only for active sessions.
- [x] Add a SQLAlchemy AsyncEngine session store and expired-session cleanup support.
- [x] Update environment example with `DATABASE_URL`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_SAMESITE`, and `CORS_ORIGINS`.

### Task 2: Build the stateful LangGraph chat

**Files:**
- Create: `backend/app/chat_graph.py`
- Modify: `backend/app/main.py`, `backend/app/agents.py`

**Interfaces:** `build_chat_graph(model, checkpointer)`, `thread_id_for(session_uuid, agent_id)`, `invoke_chat(graph, session_uuid, agent_id, message, question_id)`, `load_history(graph, session_uuid, agent_id)`, `clear_session_threads(graph, session_uuid)`.

- [x] Build a `StateGraph(MessagesState)` with one async model node and `AsyncPostgresSaver` checkpointer.
- [x] Prepend the server-built system prompt only to model input; persist no client-supplied system prompt or thread identifier.
- [x] Add the user message and optional preset ID to graph state, then return the assistant text.
- [x] Extract completed human/assistant pairs from graph state for history restoration.
- [x] Roll back a failed user turn using LangGraph state update/removal APIs, preserving earlier completed turns.
- [x] Derive each thread ID as a one-way digest of session UUID and agent ID.

### Task 3: Add session-aware API and lifecycle

**Files:**
- Modify: `backend/app/main.py`, `backend/app/session_store.py`

- [x] Initialize model, PostgreSQL pool, and `AsyncPostgresSaver`; close resources at shutdown without applying schemas.
- [x] Add a separate Alembic CLI migration for app tables and a separate CLI command for LangGraph's package-owned migrations.
- [x] Add `POST /api/session` to create/refresh a session and set the opaque token cookie.
- [x] Change chat request to accept only `message` and optional `question_id`; resolve session from cookie and invoke the graph.
- [x] Add `GET /api/agents/{agent_id}/history` to return persisted completed turns.
- [x] Add `DELETE /api/session` to delete all agent threads, revoke its database row, and clear the cookie.
- [x] Add periodic expired-session cleanup that deletes associated LangGraph threads before removing expired session rows.
- [x] Configure credentialed CORS with exact environment origins and local defaults.

### Task 4: Hydrate frontend from backend history

**Files:**
- Modify: `frontend/src/lib/agent-api.js`, `frontend/src/lib/game-map-start.js`

- [x] Add cookie-credentialed session, history, chat, and reset API calls.
- [x] At startup, ensure the backend session and restore all four agent histories and preset progress.
- [x] Remove the frontend `history` payload; submit only the current message and optional question ID.
- [x] Reset the backend session when the user restarts the experience, then clear local UI state.

### Task 5: Document production configuration and inspect the final diff

**Files:**
- Modify: `README.md`, `backend/README.md`

- [x] Document PostgreSQL, environment variables, CLI migrations, cookies/CORS, and session reset behavior.
- [x] Inspect the API contract, resource lifecycle, thread isolation, and frontend state transitions against the spec.
- [x] Run frontend format/lint/build, Alembic revision discovery, Python compilation, and whitespace checks; no tests run.
