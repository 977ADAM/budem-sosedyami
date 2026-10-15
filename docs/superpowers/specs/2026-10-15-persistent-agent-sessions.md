# Persistent agent sessions design

## Goal

Keep each anonymous browser session's conversations on the backend using a
LangGraph Postgres checkpointer. Conversation history survives page reloads,
backend restarts, and separate backend workers, while each agent and session
remain isolated.

## Identity and persistence

- `POST /api/session` creates or refreshes the anonymous session.
- The backend sets a random bearer token in an HttpOnly cookie and stores only
  its SHA-256 hash with a server-generated UUID and a 30-day sliding expiry.
- Session cookies use `SameSite=Lax`; `Secure` defaults on and may be disabled
  for local HTTP development. Cross-origin frontend requests include cookies.
- Conversation thread IDs are derived server-side from session UUID and agent
  ID; callers cannot choose another thread ID.
- Application-owned session records use SQLAlchemy's async engine. LangGraph's
  checkpointer uses its supported psycopg integration for checkpoint tables.
- PostgreSQL stores conversation state through LangGraph's
  `AsyncPostgresSaver`. The graph receives only new messages; the frontend
  never sends dialogue history.

## API contract

- `POST /api/session`: create or refresh cookie/session; empty JSON response.
- `POST /api/agents/{agent_id}/chat`: body has `message` and optional
  `question_id`; returns `reply`.
- `GET /api/agents/{agent_id}/history`: returns completed `{message, reply,
  question_id}` turns for the current browser session.
- `DELETE /api/session`: delete all four agent threads, revoke the session,
  and clear the cookie.

Invalid or expired cookies create a fresh session on `POST /api/session`.
Session expiration is enforced in PostgreSQL and expired records and graph
threads are periodically removed. Unknown agent IDs remain rejected by the
typed route parameter. Chat prompts continue to treat all user messages and
history as untrusted and use only the fixed fictional agent profile as facts.

## Frontend behavior

Opening the app initializes a session and loads the four histories from the
backend. The frontend reconstructs transcript and preset-question progress from
those turns. Sending a message sends only that message and optional preset ID.
Resetting the game calls `DELETE /api/session` before clearing local state.

## Components

- `backend/app/session_store.py`: SQLAlchemy async PostgreSQL session records, cookie
  token hashing, expiry refresh, revocation, and expired-session cleanup.
- `backend/app/chat_graph.py`: LangGraph message graph, prompt composition,
  session/agent thread IDs, transcript extraction, and failed-turn rollback.
- `backend/app/main.py`: Postgres/checkpointer lifespan, cookie and CORS
  settings, and session/history/chat routes.
- `frontend/src/lib/agent-api.js`: cookie-aware requests and new session,
  history, chat, and reset functions.
- `frontend/src/lib/game-map-start.js`: hydrate conversation state and progress
  from backend history; do not send history in chat requests.
- Backend dependencies and READMEs document PostgreSQL and cookie settings.

## Operational constraints

- Configure `DATABASE_URL` to a dedicated production PostgreSQL database.
- Run Alembic revisions and LangGraph's checkpoint `setup()` as separate CLI
  operations before application startup; the app must never change schemas.
- Set `COOKIE_SECURE=true` behind HTTPS and configure `CORS_ORIGINS` with exact
  deployed frontend origins. Defaults remain the two local development origins.
- Pass `allowed_msgpack_modules=None` explicitly to LangGraph's serializer so
  checkpoint deserialization uses its built-in safe-type allowlist regardless
  of process environment or import order.
- Keep existing per-message length limits and fictional-profile grounding.
