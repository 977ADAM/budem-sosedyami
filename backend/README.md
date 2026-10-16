# Backend

FastAPI → LangGraph/LangChain → DeepSeek. Переписка не сохраняется в базе:
клиент передаёт зашифрованную историю в `context`.
[Контракт API](../README.md).

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
| `CONTEXT_SECRET` | Случайный ключ при старте |
| `CONTEXT_TTL_SECONDS` | `86400` — срок жизни каждого токена |
| `RATE_LIMIT` | `20/minute` на IP и URL соседа |
| `CORS_ORIGINS` | `http://127.0.0.1:3000,http://127.0.0.1:5173` |
| `LOG_LEVEL` | `INFO`; в `.env.example` задан `DEBUG` |

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
- `app/main.py` — сборка приложения: `create_app(settings, chat_model=None)`.

Чтобы добавить соседа, обновите `app/infrastructure/neighbor_catalog.py`;
для демо также добавьте переключатель и область чата в `frontend/index.html`.

Логи содержат ID запроса, статус, длительность, размеры сообщений, число реплик
и расход токенов. Вне запроса ID отображается как `-`. Обычные логи чата не пишут
текст переписки, но ошибки провайдера логируются вместе с текстом исключения.
`/health` логируется на DEBUG. Флаг `--no-access-log` убирает дубли uvicorn.

## Проверки

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
`STUB_RATE_LIMIT=1000000/minute`. Генератор выводит запросы/с, задержки, ошибки
и размеры `context`. Результаты зависят от машины и настроек; скорость DeepSeek
этот тест не измеряет.
