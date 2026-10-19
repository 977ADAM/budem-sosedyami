# Backend

FastAPI → OpenAI SDK (`AsyncOpenAI`) → DeepSeek. Переписка не сохраняется в базе:
клиент передаёт зашифрованную историю в `context`.
[Контракт API](../README.md).

Для сервера: [Docker Compose](../README.md#деплой-docker-compose).
Compose запускает один процесс backend. Статические файлы фронтенда раздаются отдельно.

## Запуск

Нужны Python 3.11+ и `uv`.

```sh
cd backend
uv sync
cp .env.example .env
# Заполните DEEPSEEK_API_KEY и CONTEXT_SECRET в .env
uv run uvicorn app.main:app --reload --no-access-log --host 127.0.0.1 --port 8000
```

Документация: `http://127.0.0.1:8000/docs`.
`GET /health` возвращает `{"status":"ok"}`; доступность DeepSeek не проверяет.

## Настройки

Переменные окружения имеют приоритет над `backend/.env`.

| Переменная | По умолчанию |
| --- | --- |
| `DEEPSEEK_API_KEY` | Пусто — чат возвращает 503 |
| `DEEPSEEK_MODEL` | `deepseek-flash` |
| `DEEPSEEK_MAX_TOKENS` | `1000` токенов ответа |
| `DEEPSEEK_TIMEOUT_SECONDS` | `30`; держите меньше `proxy_read_timeout` (120 с) в [angie](../deploy/angie-sosedyami.locations.inc) |
| `CONTEXT_SECRET` | Случайный ключ при старте |
| `CONTEXT_TTL_SECONDS` | `86400` — срок жизни каждого токена |
| `RATE_LIMIT` | `20/minute` на IP и URL соседа |
| `CORS_ORIGINS` | `http://127.0.0.1:3000,http://localhost:3000` |
| `LOG_LEVEL` | `INFO`; в `.env.example` задан `DEBUG` |

Клиент обращается напрямую к `https://api.deepseek.com` через OpenAI-совместимый API.
`MAX_RETRIES` задаёт число повторных попыток SDK (по умолчанию 2).
Лимит токенов, таймаут и TTL должны быть больше нуля; таймаут также должен быть
конечным числом. `MAX_RETRIES=0` отключает повторные попытки. Некорректные значения
останавливают запуск с ошибкой, содержащей имя переменной окружения.
`RATE_LIMIT` также проверяется при запуске: например, `20/minute` или
`100 per 5 minutes`. Количество запросов и длительность окна должны быть положительными.

Для продакшена задайте постоянный `CONTEXT_SECRET`, одинаковый для всех процессов.
Без него история сбрасывается после перезапуска и не переносится между процессами.
Смена ключа тоже сбрасывает историю. Сгенерировать секрет:

```sh
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Лимиты хранятся отдельно в памяти каждого процесса. За обратным прокси настройте
доверенные адреса через `--proxy-headers` и `--forwarded-allow-ips`, чтобы получать
IP клиента. В `CORS_ORIGINS` указывайте полные адреса сайтов через запятую.

## Код и логи

- `app/domain/` — профили и история; после превышения 30 пар остаются последние 15.
- `app/application/` — сценарий чата, промпт и интерфейсы зависимостей.
- `app/infrastructure/` — DeepSeek, Fernet, каталог соседей и настройки.
- `app/presentation/` — HTTP, валидация, ошибки и логирование запросов.
- `app/main.py` — последовательная сборка приложения на уровне модуля; настройки
  доступны через `app.state.settings`.
  Логирование настраивается в `lifespan`, поэтому импорт `app.main` не меняет
  настройки логов процесса, который его импортирует.

Чтобы добавить соседа, обновите `app/infrastructure/neighbor_catalog.py`;
для демо также добавьте переключатель и область чата в `frontend/index.html`.

Логи содержат ID запроса, статус, длительность, размеры сообщений, число реплик
и расход токенов. Вне запроса ID отображается как `-`. Обычные логи чата не пишут
текст переписки, но ошибки провайдера логируются вместе с текстом исключения.
Необработанные исключения логируются с трассировкой, а клиент получает `500`
в формате `detail` с тем же `X-Request-ID`.
`/health` логируется на DEBUG. Флаг `--no-access-log` убирает дубли uvicorn.

## Проверки

`uv sync` устанавливает Ruff и mypy вместе с dev-зависимостями. Из корня проекта:

```sh
make lint       # Ruff: app, tests и loadtest
make typecheck  # mypy: app и loadtest
make test       # unittest
make check      # все проверки
```

Настройки находятся в `backend/pyproject.toml`; версии закреплены в `uv.lock`.
GitHub Actions запускает `make check` при push и pull request на Python 3.11 и 3.14.

Из папки `backend` — тесты с подставной моделью, без запросов к DeepSeek:

```sh
uv run python -m unittest discover -s tests
```

Из корня проекта — нагрузочный тест с заглушкой:

```sh
make loadtest-server             # терминал 1
make loadtest USERS=100 TURNS=35  # терминал 2
```

Заглушка на порту 8100 по умолчанию отвечает за 0,5–1,5 секунды.
Настройки сервера: `STUB_LATENCY=1.0`, `STUB_REPLY_CHARS=800`,
`STUB_RATE_LIMIT=1000000/minute`, `LOG_LEVEL=WARNING`. Генератор выводит
запросы/с, задержки, ошибки
и размеры `context`. Результаты зависят от машины и настроек; скорость DeepSeek
этот тест не измеряет.
