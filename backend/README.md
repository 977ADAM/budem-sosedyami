# Backend

FastAPI API для диалогов с вымышленными соседями. DeepSeek подключён через
LangChain `ChatOpenAI`, история сессий хранится в PostgreSQL через SQLAlchemy
AsyncEngine, а состояние диалогов — через LangGraph checkpoint. Python-зависимости
управляются через `uv`.

## Подготовка

```sh
cd backend
uv sync
cp .env.example .env
```

Задайте `DATABASE_URL` и `DEEPSEEK_API_KEY` в `.env`. Для локального HTTP оставьте
`SESSION_COOKIE_SECURE=false`; в HTTPS окружении включите его. Укажите разрешённые
адреса frontend в `CORS_ORIGINS`.

## Миграции

Перед запуском приложения выполните обе команды из папки `backend`:

```sh
uv run alembic upgrade head
uv run python -m app.migrate_checkpoints
```

Alembic управляет таблицей анонимных сессий приложения. Отдельный CLI-модуль
`app.migrate_checkpoints` применяет внутренние миграции LangGraph и не запускается
при старте сервера.
Новые миграции приложения добавляйте в `migrations/versions` и применяйте
командой Alembic.

Checkpointer использует встроенный безопасный allowlist LangGraph для
десериализации checkpoint-данных; пользовательские типы в состояние графа не
добавляйте без отдельной явной настройки allowlist.

## Запуск

```sh
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API будет доступен только на локальном компьютере по адресу
`http://127.0.0.1:8000`. Проверка состояния: `http://127.0.0.1:8000/health`.
`uv run` использует версии библиотек из `uv.lock`; после изменения зависимостей
обновите lock-файл командой `uv lock` и окружение командой `uv sync`.

## Чат API

Для чата используется один endpoint; ID агента задаётся в пути:

- `POST /api/agents/{agent_id}/chat` (`anton`, `marina`, `pavel` или `vera`)

Запрос содержит только новое сообщение и необязательный ID готового вопроса:

```json
{
  "message": "Где ты обычно бегаешь?",
  "question_id": "sport"
}
```

Сессия создаётся запросом `POST /api/session` и хранится в HttpOnly cookie.
Frontend отправляет cookie с каждым запросом; история и прогресс готовых вопросов
восстанавливаются через `GET /api/agents/{agent_id}/history`. `DELETE /api/session`
удаляет сессию и диалоги. Агент отвечает только по вымышленному профилю; не
передавайте в чат личные данные.
