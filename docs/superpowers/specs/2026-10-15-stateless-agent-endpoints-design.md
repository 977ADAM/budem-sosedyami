# Stateless agent endpoints design

## Goal

Remove all dialogue storage from the FastAPI process and expose a distinct chat
endpoint for each of the four fictional agents. Preserve conversational context
by having the frontend send the current session's earlier turns with each
request. The backend uses that history only to construct one DeepSeek request
and discards it when the request completes.

The demo remains local, uses only its fictional profiles and prepared questions,
and does not add persistence, free-text questions, or external integrations.

## API contract

Expose four explicit endpoints:

- `POST /api/agents/anton/chat`
- `POST /api/agents/marina/chat`
- `POST /api/agents/pavel/chat`
- `POST /api/agents/vera/chat`

Each endpoint accepts a `question_id` and a request-local `history` array. Each
history item contains the `question_id` of an earlier prepared question and the
answer returned to the frontend for that turn. The current question is sent as
the top-level `question_id`, not repeated in `history`.

For example, a follow-up question can be sent as:

```json
{
  "question_id": "sport",
  "history": [
    {
      "question_id": "work",
      "reply": "Я дизайнер и работаю из дома у окна."
    }
  ]
}
```

The shared handler validates that all question IDs belong to the route's agent,
that history has no duplicate/current question, and that each supplied reply is
a non-empty bounded string. Extra request fields are rejected. It reconstructs
question text from the server's fixed question registry, then sends the system
prompt, earlier turns, and current prepared question to DeepSeek. It returns
only the new reply and keeps no session state after responding. Client-supplied
history is conversational context, not a source of facts: the system prompt
remains authoritative and the model must not treat conflicting history as new
knowledge.

Unknown agent paths return 404; an unknown question or invalid history returns
422; missing API key returns 503; DeepSeek timeout returns 504 and other
upstream/response errors return 502. Existing response semantics remain.

## Frontend behavior

The frontend remains the owner of in-page game state. Before asking a new
question, it builds history from that agent's previously selected questions and
the corresponding model replies already held in frontend state. If a reply is
missing because the backend was unavailable, the existing prepared fallback
answer is used for that history item.

Opening an agent no longer loads dialogue from the backend. Reset clears local
choices and answers without calling the backend. Reloading the page clears the
in-memory frontend conversation, which matches the current demo's non-persistent
session behavior.

The API client maps each known agent ID to its explicit route. It does not
accept arbitrary route fragments. No free-text question input is introduced.

## Components and changes

- `backend/app/main.py`: replace the generic `/api/chat` route with four thin
  route functions that call a shared stateless chat handler; remove dialogue
  retrieval and reset routes.
- `backend/app/dialogues.py`: delete process-local dialogue and generation
  storage.
- `frontend/src/lib/agent-api.js`: call the explicit per-agent route and send
  history; remove backend load/reset helpers.
- `frontend/src/lib/game-map-start.js`: construct history from in-page state and
  remove backend hydration/reset calls while preserving local UI/game progress.
- `README.md` and `backend/README.md`: document the stateless request contract,
  routes, and `uv` workflow.

## Verification

Run the existing frontend ESLint, Prettier check, and production build. Verify
with the local UI that two or more prepared questions to one agent produce a
context-aware response, that history is absent from backend process state, and
that reset clears the UI. Check every agent route, invalid question/history
responses, health, missing-key behavior, and DeepSeek success using only the
fictional demo data. No real estate, CRM, or other external integration is part
of this change.
