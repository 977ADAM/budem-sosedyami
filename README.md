# Будем соседями? — локальное демо ИИ-соседей

Демо-игра о знакомстве с четырьмя вымышленными соседями. Вопросы выбираются из готового списка, а FastAPI может отвечать от лица персонажей через DeepSeek API. Персонажи и сведения о районах вымышлены и заданы в самом демо.

## Стек

- Svelte 5
- SvelteKit 2
- Vite 6
- adapter-static
- FastAPI, Uvicorn, LangChain (`langchain-openai`)
- `uv` для окружения и зависимостей Python

## Локальный запуск

### Backend

В первом терминале:

```sh
cd backend
uv sync
cp .env.example .env
# Добавьте DEEPSEEK_API_KEY в backend/.env для ответов модели.
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

У каждого соседа отдельный endpoint:

- `POST /api/agents/anton/chat`
- `POST /api/agents/marina/chat`
- `POST /api/agents/pavel/chat`
- `POST /api/agents/vera/chat`

Запрос содержит ID выбранного готового вопроса и предыдущие реплики этого
диалога:

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

Историю в памяти текущей страницы собирает frontend и передаёт в каждом
запросе. Backend использует её только для одного вызова модели и ничего не
сохраняет. После перезагрузки страницы история начинается заново. Вопросы и
профили соседей заданы в демо; свободный ввод не используется. Если backend,
ключ или DeepSeek недоступны, демо показывает заранее подготовленный ответ.

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
