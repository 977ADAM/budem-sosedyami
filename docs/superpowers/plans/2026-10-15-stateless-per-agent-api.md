# Stateless Per-Agent API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove backend dialogue storage and expose a stateless chat endpoint for each fictional agent while preserving in-page conversational context.

**Architecture:** FastAPI defines four explicit route wrappers over one shared stateless chat function. Each request carries the current prepared question ID and the earlier turns from the frontend; the backend resolves question text from its fixed agent registry, invokes DeepSeek through LangChain's `ChatOpenAI` integration configured for DeepSeek's OpenAI-compatible API, and returns one reply without retaining session state. The frontend keeps game progress and reply history only in page memory.

**Tech Stack:** Python 3.14, FastAPI, Pydantic, LangChain `langchain-openai`, uv, SvelteKit, vanilla JavaScript.

**Spec:** `docs/superpowers/specs/2026-10-15-stateless-agent-endpoints-design.md`

## Global Constraints

- Keep the demo local and bind the backend to `127.0.0.1`.
- Use only the four fictional agents and their predefined facts and questions.
- Do not add free-text questions, persistence, or external integrations.
- Keep frontend ESLint, Prettier, and production build checks passing.
- Keep the DeepSeek API key in `backend/.env`; never put it in frontend requests.

## Review Focus

- Unknown current or historical question IDs and repeated/current IDs return 422 and never reach DeepSeek.
- Missing `history` is rejected as 422; the frontend always sends an array, including `[]` on the first turn.
- Empty or over-800-character historical replies return 422; valid history is kept in request order.
- Extra request fields return 422 because request models forbid extras.
- A follow-up reply uses the submitted earlier turns but no subsequent request can retrieve them from backend state.

---

## File Map

- `backend/app/main.py`: own Pydantic request models, four explicit agent routes, shared validation and LangChain DeepSeek call. No dialogue data is stored here.
- `backend/app/dialogues.py`: remove this process-local store module.
- `frontend/src/lib/agent-api.js`: map known IDs to four fixed URLs and pass request history.
- `frontend/src/lib/game-map-start.js`: assemble request-local history from the page's existing choices/answers; remove backend dialogue load/reset calls.
- `README.md`, `backend/README.md`: document the per-agent URLs, payload and no-persistence behavior.

## Tasks

### Task 1: Make backend chat stateless and agent-specific

**Files:**
- Modify: `backend/app/main.py`
- Delete: `backend/app/dialogues.py`

**Interfaces:**
- Produces `POST /api/agents/{agent_id}/chat` as four explicit routes for `anton`, `marina`, `pavel`, and `vera`.
- Request body is `{"question_id": string, "history": [{"question_id": string, "reply": string}]}`. `history` is required and may contain zero to three prior turns.
- Response remains `{"reply": string}`.
- Each history item is unique, belongs to the route's agent, and differs from the current question. Resolve its question text from `AGENTS`; preserve array order. Require a non-empty reply of at most 800 characters; reject extra fields.
- Route wrappers pass a fixed agent ID to a shared async handler so the URL cannot select an arbitrary profile.

- [ ] **Step 1: Define strict Pydantic request models**

  In `backend/app/main.py`, define a history-turn model with `extra="forbid"`, `question_id`, and a trimmed non-empty `reply` capped at 800 characters. Define a request model with `extra="forbid"`, a `question_id`, and a required list of zero to three history turns.

- [ ] **Step 2: Implement history validation and message construction**

  Add a shared helper that checks the current question and every historical question against the route agent's fixed registry, rejects duplicate/history-current IDs with 422, and constructs ordered `user`/`assistant` messages. Only question text from `AGENTS` is used; history replies provide continuity but do not extend the system's allowed facts.

- [ ] **Step 3: Invoke DeepSeek through LangChain**

  Add `langchain-openai` with `uv`, configure `ChatOpenAI` with the DeepSeek-compatible base URL, `DEEPSEEK_API_KEY`, and `DEEPSEEK_MODEL`, then call it asynchronously with LangChain message objects. Preserve the existing 504 timeout and 502 upstream error semantics.

- [ ] **Step 4: Add four explicit FastAPI route wrappers**

  Add `POST /api/agents/anton/chat`, `/marina/chat`, `/pavel/chat`, and `/vera/chat`. Each wrapper calls the shared handler with its fixed agent ID. Keep existing DeepSeek timeout/upstream error behavior and response model. Remove `/api/chat`, `GET /api/dialogue/{agent_id}`, `POST /api/dialogue/reset`, and all imports/calls to the dialogue store.

- [ ] **Step 5: Remove the dialogue store module**

  Delete `backend/app/dialogues.py`; verify there are no remaining imports or `DIALOGUES` / generation references in backend source.

- [ ] **Step 6: Manually verify backend request contract**

  From `backend/`, run `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`. Use local HTTP requests with fictional demo data to check health, successful first and follow-up requests, each of the four paths, 404 for an unknown path, and 422 for an unknown/current/duplicate question, missing history, invalid reply, and extra fields. Confirm responses do not create a dialogue retrieval/reset API or server-side history.

- [ ] **Step 7: Commit the backend change**

  ```bash
  git add backend/app/main.py backend/app/dialogues.py
  git commit -m "refactor: make agent chat stateless"
  ```

### Task 2: Send conversation context from the frontend

**Files:**
- Modify: `frontend/src/lib/agent-api.js`
- Modify: `frontend/src/lib/game-map-start.js`

**Consumes:** The Task 1 request contract and four route URLs.

**Produces:** `askAgent(agentId, questionId, history)` calls the fixed path for `agentId` with `{ question_id, history }`.

- [ ] **Step 1: Replace generic API helpers with a fixed agent route map**

  In `agent-api.js`, map `anton`, `marina`, `pavel`, and `vera` to their explicit `/api/agents/<id>/chat` paths. Change `askAgent` to accept history and include it in the JSON body. Remove `loadDialogue` and `resetDialogues` exports.

- [ ] **Step 2: Build ordered history before each question request**

  In `game-map-start.js`, before calling `askAgent`, map the agent's previously selected question IDs in `state.choices[personId]` order to `{ question_id, reply }`. Use the answer held in `state.answers`; if absent, use that prepared question's existing fallback `answer`. Exclude the current question ID. Pass the resulting array with the current question.

- [ ] **Step 3: Remove backend hydration and reset calls**

  Remove `loadDialogue`/`refreshDialogue` use when opening a chat. Keep `state.choices` and `state.answers` as the sole in-page source for rendering. Reset clears those local values and does not call a backend reset endpoint. Preserve the existing fallback behavior when a model request fails.

- [ ] **Step 4: Manually verify the browser flow**

  Ask two or more prepared questions of one agent and confirm the follow-up answer receives earlier context; ask another agent and confirm it starts with empty history. Reset and confirm the UI is empty. Reload and confirm the page has no prior dialogue. Confirm that no user-visible flow permits arbitrary questions.

- [ ] **Step 5: Run frontend checks and commit**

  From `frontend/`, run `npm run lint`, `npm run format:check`, and `npm run build`.

  ```bash
  git add frontend/src/lib/agent-api.js frontend/src/lib/game-map-start.js
  git commit -m "refactor: send agent history from frontend"
  ```

### Task 3: Update API documentation and final review

**Files:**
- Modify: `README.md`
- Modify: `backend/README.md`

**Consumes:** The request/response contract from Task 1 and frontend behavior from Task 2.

- [ ] **Step 1: Document the four chat routes and example payload**

  Replace references to `/api/chat`, `/api/dialogue/{agent_id}`, and `/api/dialogue/reset` with the four explicit URLs. Include a JSON example containing `question_id` and `history`, and state that history exists only in frontend page memory and is sent per request.

- [ ] **Step 2: Keep the uv startup instructions accurate**

  Ensure backend docs continue to use `uv sync` and `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`; retain instructions that the key remains in `backend/.env`.

- [ ] **Step 3: Review the full diff and commit documentation**

  Run `git diff --check`, search backend/frontend code and current user-facing READMEs for obsolete endpoints, then commit the documentation. Historical specs and plans may retain the old contract as a description of prior state.

  ```bash
  git add README.md backend/README.md
  git commit -m "docs: describe stateless per-agent API"
  ```

### Task 4: Route DeepSeek calls through LangChain

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/uv.lock`

**User steering:** Added after Task 1: use LangChain for the backend.

- [ ] Add `langchain-openai` through `uv`, use `ChatOpenAI.ainvoke()` with the DeepSeek OpenAI-compatible base URL, and retain the existing API error mapping.
- [ ] Verify import/route startup and make a fictional-data request through the local UI.
- [ ] Commit with `feat: use LangChain for DeepSeek requests`.
