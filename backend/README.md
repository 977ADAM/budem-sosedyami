# Backend

Локальный FastAPI API для демо-соседей. Вызовы DeepSeek выполняются через
LangChain `ChatOpenAI` и OpenAI-совместимый API. Python-зависимости и виртуальное
окружение управляются через `uv`; `requirements.txt` не используется.

## Подготовка

```sh
cd backend
uv sync
cp .env.example .env
```

Добавьте `DEEPSEEK_API_KEY` в `.env`. Без ключа сервер запустится, но запросы
к модели будут отвечать ошибкой `503`.

## Запуск

```sh
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API будет доступен только на локальном компьютере по адресу
`http://127.0.0.1:8000`. Проверка состояния: `http://127.0.0.1:8000/health`.
`uv run` использует версии библиотек из `uv.lock`; после изменения зависимостей
обновите lock-файл командой `uv lock` и окружение командой `uv sync`.

## Чат API

Для каждого вымышленного соседа предусмотрен отдельный endpoint:

- `POST /api/agents/anton/chat`
- `POST /api/agents/marina/chat`
- `POST /api/agents/pavel/chat`
- `POST /api/agents/vera/chat`

Пример тела запроса:

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

`question_id` и IDs в `history` должны соответствовать готовым вопросам
выбранного персонажа. На первом ходу передавайте пустой массив `history`.
Историю держит frontend в памяти страницы и отправляет с каждым запросом;
backend не сохраняет реплики и возвращает только `{"reply": "..."}`.
