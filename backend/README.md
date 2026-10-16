# Backend

FastAPI API для диалогов с вымышленными соседями через DeepSeek и LangGraph.
Сервер не хранит переписку: история возвращается клиенту в зашифрованном
поле `context` и приходит обратно со следующим сообщением. Контракт API
для фронтенда описан в [корневом README](../README.md).

## Запуск

```sh
cd backend
uv sync
cp .env.example .env
# Задайте DEEPSEEK_API_KEY и CONTEXT_SECRET в .env
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Документация: `http://127.0.0.1:8000/docs`. Проверка состояния: `GET /health`.

## Настройки (`.env`)

| Переменная | По умолчанию | Что это |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | — | Ключ DeepSeek. Без него чат отвечает 503 |
| `DEEPSEEK_MODEL` | `deepseek-flash` | Модель DeepSeek |
| `DEEPSEEK_MAX_TOKENS` | `1000` | Максимальная длина ответа модели |
| `CONTEXT_SECRET` | случайный при старте | Ключ шифрования `context` |
| `CONTEXT_TTL_SECONDS` | `86400` | Сколько живёт `context` |
| `RATE_LIMIT` | `20/minute` | Лимит сообщений с одного IP |
| `CORS_ORIGINS` | `127.0.0.1:3000`, `:5173` | Сайты, которым разрешено обращаться к API |

`CONTEXT_SECRET` обязателен для продакшена: без него ключ создаётся заново при
каждом старте, и все разговоры начинаются сначала. Смена ключа делает то же самое,
ошибок у клиентов при этом не будет. Сгенерировать ключ:
`python3 -c "import secrets; print(secrets.token_urlsafe(32))"`.

Лимит запросов хранится в памяти процесса и считается по IP подключения. За
обратным прокси (nginx, балансировщиком) все клиенты будут выглядеть как один
IP — запускайте uvicorn с `--proxy-headers` и настройте `--forwarded-allow-ips`.

## Структура

Чистая архитектура: зависимости направлены только внутрь, внутренние слои не знают
про FastAPI, DeepSeek, LangGraph и шифрование.

```text
app/
  domain/          Сосед и разговор, правило обрезки истории. Без зависимостей.
  application/     Сценарий ChatWithNeighbor, промпт, порты (интерфейсы) и ошибки.
  infrastructure/  Реализации портов: каталог соседей, DeepSeek, Fernet, настройки.
  presentation/    HTTP: схемы, маршрут, ошибки → коды ответа, лимит запросов.
  main.py          Точка сборки: create_app(settings, chat_model=None).
```

Добавить соседа — `infrastructure/neighbor_catalog.py`. Сменить модель — новая
реализация `ChatModel` из `application/ports.py` и одна строка в `main.py`.
Тесты подставляют `FakeChatModel` через `create_app`, без патчинга модулей.

## Как устроена история

- В модель уходят системный профиль соседа, история из `context` и новое сообщение.
- История хранит до 30 пар реплик. При переполнении старая половина отбрасывается
  целиком, а не по одной реплике: так начало запроса к DeepSeek долго остаётся
  одинаковым и срабатывает [кэш контекста](https://api-docs.deepseek.com/guides/kv_cache).
- В лог пишется расход токенов, включая взятые из кэша (`cached_tokens`).
- Если модель не ответила, клиент получает ошибку и продолжает со старым `context`.

## Проверки

```sh
uv run python -m unittest discover -s tests
cd ../frontend && node --test
```
