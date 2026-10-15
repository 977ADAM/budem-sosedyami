# Будем соседями? — локальное демо ИИ-соседей

Демо-игра о знакомстве с четырьмя вымышленными соседями. Вопросы выбираются из готового списка, а FastAPI может отвечать от лица персонажей через DeepSeek API. Персонажи и сведения о районах вымышлены и заданы в самом демо.

## Стек

- Svelte 5
- SvelteKit 2
- Vite 6
- adapter-static
- FastAPI, Uvicorn, HTTPX
- `uv` для окружения и зависимостей Python

## Локальный запуск

### Backend

В первом терминале:

```sh
cd backend
uv venv
uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env
# Добавьте DEEPSEEK_API_KEY в backend/.env для ответов модели.
uv run --python .venv/bin/python uvicorn app.main:app --reload --port 8000 --env-file .env
```

Backend доступен локально на `http://127.0.0.1:8000`; проверка состояния: `/health`.

### Frontend

Во втором терминале:

```sh
cd frontend
npm ci
npm run dev
```

Vite проксирует `/api` на локальный FastAPI. Ключ DeepSeek остаётся только в `backend/.env`. Если backend, ключ или DeepSeek недоступны, демо показывает заранее подготовленный ответ.

## Сборка frontend

```sh
cd frontend
npm run build
```

Статический сайт собирается в `frontend/dist/`. Backend предназначен для локальной демонстрации и не хранит историю разговоров.

## Проверки frontend

Из каталога `frontend/`:

```sh
npm run lint
npm run format:check
npm run build
```

Для автоматического форматирования файлов используйте `npm run format`.
