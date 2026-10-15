# Будем соседями? — локальное демо ИИ-соседей

Демо-игра о знакомстве с четырьмя вымышленными соседями. Можно выбрать готовый вопрос или написать свой; FastAPI передаёт сообщение в DeepSeek через LangChain. Персонажи и сведения о районах вымышлены и заданы в самом демо.

## Стек

- Svelte 5
- SvelteKit 2
- Vite 6
- adapter-static
- FastAPI, Uvicorn, LangChain (`langchain-openai`), SQLAlchemy, Alembic
- `uv` для окружения и зависимостей Python

## Локальный запуск

### Backend

В первом терминале:

```sh
cd backend
uv sync
cp .env.example .env
# Добавьте DEEPSEEK_API_KEY в backend/.env для ответов модели.
uv run alembic upgrade head
uv run python scripts/migrate_checkpoints.py
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend доступен локально на `http://127.0.0.1:8000`; проверка состояния: `/health`.

### Frontend

Во втором терминале:

```sh
cd frontend
npm ci
npm run dev
```

Vite проксирует `/api` на локальный FastAPI. Backend вызывает DeepSeek через LangChain и OpenAI-совместимый API. Ключ DeepSeek остаётся только в `backend/.env`.

Перед запуском примените миграции двумя CLI-командами (выше). Первая управляет
таблицей анонимных сессий приложения через Alembic; вторая создаёт служебную
схему LangGraph. Сервер миграции не запускает.

У каждого соседа отдельные endpoints:

- `POST /api/agents/{agent_id}/chat` (`anton`, `marina`, `pavel` или `vera`)

Запрос содержит новое сообщение и необязательный ID готового вопроса:

```json
{
  "message": "Где ты обычно бегаешь?",
  "question_id": "sport"
}
```

Backend хранит диалоги в PostgreSQL, отдельно по анонимной cookie-сессии и
соседу. История доступна через `GET /api/agents/{agent_id}/history`, а
`DELETE /api/session` сбрасывает текущую сессию. Frontend не отправляет прошлые
реплики. Агент отвечает только по вымышленному профилю; не вводите в чат личные
данные. Если модель недоступна, готовые вопросы показывают заранее подготовленный
ответ, а свободное сообщение можно отправить повторно.

## Сборка frontend

```sh
cd frontend
npm run build
```

Статический сайт собирается в `frontend/dist/`. Backend предназначен для
локальной демонстрации и не хранит историю диалогов между запросами.

## Проверки frontend

Из каталога `frontend/`:

```sh
npm run lint
npm run format:check
npm run build
```

Для автоматического форматирования файлов используйте `npm run format`.
