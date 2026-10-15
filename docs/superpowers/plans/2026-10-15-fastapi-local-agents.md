# Локальные ИИ-соседи на FastAPI — план реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Разделить локальное демо на `frontend/` (SvelteKit) и `backend/` (FastAPI), чтобы DeepSeek отвечал от лица четырёх вымышленных соседей.

**Architecture:** SvelteKit остаётся клиентом и хранит текущий разговор по каждому соседу в памяти. Vite проксирует `/api` к локальному FastAPI; FastAPI проверяет ID агента и готового вопроса, строит system prompt из серверного профиля и вызывает DeepSeek с ключом из `backend/.env`.

**Tech Stack:** Svelte 5, SvelteKit 2, Vite 6, Python 3.10+, FastAPI, Uvicorn, HTTPX, python-dotenv; без новых зависимостей фронтенда.

**Spec:** `docs/superpowers/specs/2026-10-15-fastapi-local-agents-design.md`

## Global Constraints

- Персонажи и сведения о ЖК остаются вымышленными и ограничены данными текущего демо.
- Игрок выбирает только готовые вопросы; свободный текстовый ввод не добавляется.
- DeepSeek API вызывается только из FastAPI на локальном компьютере; API-ключ хранится в `backend/.env`.
- При backend/DeepSeek ошибке, отсутствии ключа, таймауте или невалидном ответе игра использует прежний статичный `q.answer`.
- История чата хранится в памяти браузера, отдельно для каждого соседа; сервер не хранит сессии.
- Новые автоматические тесты не добавлять; проверять ручными сценариями и production build.

## Review Focus

- **Отсутствующий ключ:** FastAPI отвечает 503, фронтенд показывает fallback; проверить в Task 2 и Task 3.
- **Неизвестный `agent_id`/`question_id`:** backend не должен отправлять запрос модели; проверить в Task 2.
- **Ошибка/таймаут/невалидный ответ DeepSeek:** backend отдаёт корректную ошибку, frontend снимает ожидание и показывает fallback; проверить в Task 2 и Task 3.
- **Двойной клик на вопросе:** только один запрос и один ответ; проверить в Task 3.
- **Смена соседа во время запроса:** ответ сохраняется в историю исходного агента, чужой чат не меняется; проверить в Task 3.

---

### Task 1: Перенести существующий SvelteKit в `frontend/`

**Files:**
- Move: `src/` → `frontend/src/`
- Move: `static/` → `frontend/static/`
- Move: `package.json`, `package-lock.json`, `svelte.config.js`, `vite.config.js` → `frontend/`
- Modify: `.gitignore`
- Modify if present: `.openai/hosting.json`

**Interfaces:**
- Produces: frontend root `frontend/`, где `npm ci`, `npm run dev` и `npm run build` работают независимо от корня monorepo.
- Keeps: `README.md`, `docs/`, `.git/` и `.gitignore` в корне.

- [ ] **Step 1: Создать frontend-каталог и переместить SvelteKit файлы**

Перенести перечисленные выше исходники и package-файлы в `frontend/`; не копировать их, не дублировать исходные файлы в корне. Не перемещать корневые `README.md`, `docs/`, `.git/` и настройки Git.

- [ ] **Step 2: Обновить корневой `.gitignore` и hosting static path**

Игнорировать `frontend/node_modules/`, `frontend/.svelte-kit/`, `frontend/dist/`, `backend/.venv/`, `backend/.env`, `backend/__pycache__/` и `*.py[cod]`; сохранить игнорирование `.DS_Store`. Если `.openai/hosting.json` существует, изменить static directory с `dist` на `frontend/dist`.

- [ ] **Step 3: Установить frontend-зависимости и проверить сборку**

Выполнить из `frontend/`: `npm ci`, затем `npm run build`. Ожидается успешная статическая сборка в `frontend/dist/`.

### Task 2: Создать FastAPI backend с четырьмя агентами

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/agents.py`
- Create: `backend/app/main.py`
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`

**Interfaces:**
- `GET /health` → `{ "status": "ok" }`.
- `POST /api/chat` request: `{ "agent_id": str, "question_id": str, "history": [{ "role": "user" | "assistant", "content": str }] }`.
- `POST /api/chat` success: `{ "reply": str }`.
- Errors: unknown agent 404; unknown question 422; missing API key 503; upstream timeout 504; other upstream/network failure 502.

- [ ] **Step 1: Добавить backend dependencies и env template**

В `requirements.txt` перечислить `fastapi`, `uvicorn[standard]`, `httpx`, `python-dotenv`. В `.env.example` добавить `DEEPSEEK_API_KEY=` и `DEEPSEEK_MODEL=deepseek-flash` без настоящих секретов.

- [ ] **Step 2: Добавить серверный реестр агентов**

В `agents.py` создать `AGENTS` для `anton`, `marina`, `pavel`, `vera`. Для каждого перенести только существующие из frontend биографические и районные факты, persona voice, полный список текущих `question_id` и текстов вопросов, плюс существующие заготовленные ответы для знаний. Добавить `build_system_prompt(agent_id: str) -> str`, который запрещает выдавать факты за пределами профиля и велит честно говорить о неизвестном. Не добавлять новые факты.

- [ ] **Step 3: Реализовать FastAPI schemas и endpoint**

В `main.py` загрузить `backend/.env` через `load_dotenv`, создать `app = FastAPI()`, Pydantic-модели запроса/истории/ответа и `GET /health`. Для `POST /api/chat` проверить агент и вопрос, затем вызвать DeepSeek Chat Completions через `httpx.AsyncClient(timeout=30.0)` по адресу `https://api.deepseek.com/chat/completions`, передав model из `DEEPSEEK_MODEL` или `deepseek-flash`, system prompt, переданную history и текст выбранного вопроса. Заголовок Bearer формировать только на backend. Возвращать `{ "reply": ... }`; ошибки преобразовать в статусы из Interfaces.

- [ ] **Step 4: Установить backend и проверить endpoint вручную**

Из `backend/` создать venv и установить `requirements.txt`; скопировать `.env.example` в `.env` без ключа и запустить `uvicorn app.main:app --reload --port 8000 --env-file .env`. Проверить `GET /health`, `POST /api/chat` без ключа → 503, неизвестного агента → 404, неизвестного вопроса → 422. При наличии у пользователя настроенного ключа проверить успешный ответ; не создавать и не запрашивать ключ автоматически.

### Task 3: Подключить фронтенд к FastAPI и описать локальный запуск

**Files:**
- Modify: `frontend/vite.config.js`
- Modify: `frontend/src/lib/game-map-start.js`
- Modify: `README.md`

**Interfaces:**
- Consumes: `POST /api/chat` request/response из Task 2.
- Produces: локальный пользовательский путь, использующий AI-ответы при доступном backend и `q.answer` fallback во всех ошибочных сценариях.

- [ ] **Step 1: Настроить Vite dev proxy к FastAPI**

В `frontend/vite.config.js` проксировать `/api` на `http://127.0.0.1:8000`. Не хранить DeepSeek ключ или агентский system prompt во frontend.

- [ ] **Step 2: Добавить per-agent ответы и историю в игровое состояние**

В `game-map-start.js` рядом с `choices` добавить `answers` (по agent ID и question ID) и `pendingQuestion`. Сохранять order вопросов через существующие `Set` в `choices`. Сформировать history из предыдущих user-вопросов и реально сохранённых assistant AI-ответов этого же агента; не включать fallback в историю модели и не включать текущий вопрос дважды.

- [ ] **Step 3: Запрашивать FastAPI при выборе готового вопроса**

При `action === 'question'` отправить `{ agent_id, question_id, history }` на `/api/chat`. Выбранный вопрос продолжает увеличивать прогресс сразу. Блокировать новые вопросы пока текущий pending. При успешном `{ reply }` сохранить ответ; при non-2xx, отсутствии/пустом reply, ошибке JSON или сети использовать прежний `q.answer` и показать уведомление о fallback.

- [ ] **Step 4: Отобразить ожидание и безопасно обработать смену экрана**

Во время запроса отобразить индикатор ожидания и отключить вопросные кнопки. При завершении очистить pending независимо от результата. Сохранить ответ у исходного agent ID; перерисовывать чат только если он всё ещё активен, чтобы ответ не попал в чужой диалог. Сброс игры также очищает историю ответов.

- [ ] **Step 5: Обновить README и пройти локальный сценарий вручную**

Добавить команды установки и запуска двух процессов из отдельных терминалов. Запустить FastAPI и frontend, пройти вопросы у нескольких соседей, убедиться в раздельных историях, fallback без ключа и возможности выбрать соседа/посмотреть результат. Проверить production build командой `cd frontend && npm run build`.
