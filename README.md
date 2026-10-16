# Будем соседями?

Чат с четырьмя вымышленными соседями: `anton`, `marina`, `pavel`, `vera`.
Ответы генерирует DeepSeek. Промпт ограничивает ответы профилем соседа,
но модель может ошибаться.

## API

```http
POST /api/agents/{agent_id}/chat
Content-Type: application/json

{"message": "Где вы гуляете?", "context": null}
```

Ответ `200`:

```json
{"reply": "Во дворе есть место для прогулок…", "context": "gAAAAAB…"}
```

- `message` — обязательная строка, 1–500 символов; одни пробелы запрещены.
- `context` — необязательная строка до 300 000 символов или `null`.
- Дополнительные поля запрещены. Неверный запрос возвращает `422`.

Сохраняйте `context` из ответа отдельно для каждого соседа и отправляйте со
следующим сообщением. Без него начинается новый разговор. История зашифрована;
при превышении 30 пар реплик остаются последние 15.

Токен действует 24 часа по умолчанию; каждый успешный ответ выдаёт новый.
Просроченный, повреждённый или выданный другому соседу токен начинает новый
разговор. Неверный тип или превышение длины `context` возвращает `422`.

## Подключение к фронтенду

1. Запустите backend по [инструкции](backend/README.md).
2. Добавьте адрес фронтенда в `CORS_ORIGINS` в `backend/.env`, например
   `CORS_ORIGINS=http://localhost:5173`, и перезапустите backend.
   `localhost` и `127.0.0.1` — разные origins.
3. Укажите адрес backend в `API_URL` и вызывайте функцию ниже при отправке формы.
   Ключ DeepSeek остаётся на сервере; на фронтенде он не нужен.

```js
const API_URL = "http://127.0.0.1:8000"; // В продакшене — HTTPS-адрес API
const contexts = {}; // Отдельный токен для каждого соседа

async function sendMessage(agentId, message) {
  let response;
  try {
    response = await fetch(`${API_URL}/api/agents/${agentId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, context: contexts[agentId] ?? null }),
    });
  } catch {
    throw new Error("Не удалось связаться с API. Проверьте сеть, адрес и CORS.");
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const requestId = response.headers.get("X-Request-ID");
    const detail = typeof data?.detail === "string"
      ? data.detail
      : `Ошибка сервера (${response.status})`;
    throw new Error(detail + (requestId ? ` [ID: ${requestId}]` : ""));
  }
  if (typeof data?.reply !== "string" || typeof data?.context !== "string") {
    throw new Error("API вернул некорректный ответ");
  }

  contexts[agentId] = data.context; // Обновляем только после успеха
  return data.reply;
}

// В обработчике отправки формы:
try {
  const reply = await sendMessage("marina", "Где вы гуляете?");
  document.querySelector("#reply").textContent = reply;
} catch (error) {
  document.querySelector("#reply").textContent = error.message;
}
```

Добавьте на страницу `<div id="reply"></div>` для этого примера. Пока запрос
выполняется, блокируйте повторную отправку и показывайте «печатает…»; после
завершения возвращайте кнопку в рабочее состояние через `finally`.
Ответы отображайте через `textContent`.

Для нового разговора выполните `delete contexts.marina` (или удалите токен
другого соседа). В примере токены живут до перезагрузки страницы; для сохранения
между перезагрузками записывайте их в `sessionStorage` и восстанавливайте при старте.
Готовый пример формы — в [frontend/app.js](frontend/app.js).

## Ошибки

Ошибки чата возвращаются как `{"detail": "текст на русском"}`:

| Код | Причина |
| --- | --- |
| 422 | Неверный запрос или неизвестный сосед |
| 429 | Превышен лимит для IP и URL соседа; по умолчанию 20 запросов в минуту |
| 500 | Непредвиденная ошибка сервера |
| 502 | Ошибка модели |
| 503 | Модель не настроена |
| 504 | Таймаут обращения к модели; по умолчанию 30 секунд |

При ошибке сохраняйте прежний `context`: запрос можно повторить, пока токен
действует. Ответы `500` и ошибки валидации приходят в том же формате `detail`;
ошибки CORS может вернуть прокси или браузер обычным текстом.
Клиент должен обрабатывать сбой сети и неудачный разбор JSON.

Для диагностики передавайте владельцу API заголовок ответа `X-Request-ID`: он
есть у любого ответа API, включая `500`. Можно отправить свой ID:
1–64 символа из латиницы, цифр, `.`, `_`, `-`.

## Деплой: Docker Compose

Нужен Docker с Compose. Из корня репозитория:

```sh
cp backend/.env.example backend/.env
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

В `backend/.env` задайте `DEEPSEEK_API_KEY`, сгенерированный `CONTEXT_SECRET`
и `LOG_LEVEL=INFO`. Сохраняйте секрет при обновлениях, чтобы не сбрасывать диалоги.

```sh
docker compose up -d --build --wait
curl http://127.0.0.1:8000/health
```

Порт на хосте задаётся `BACKEND_PORT` (по умолчанию 8000) в корневом `.env`
рядом с `compose.yaml` — на общем сервере выберите свободный порт.

Фронтенд — готовые статические файлы в `frontend/`, сборка не нужна.
Раздавайте их вместе с API с одного домена под общим префиксом: страница
`<префикс>/` и запросы `<префикс>/api/` (фронтенд вызывает API относительно
страницы). Прокси направляет `<префикс>/api/` на `http://127.0.0.1:${BACKEND_PORT}`
с сохранением пути; HTTPS настраивается на прокси, CORS для такой схемы не нужен.

Порт backend доступен только на `127.0.0.1`. Он доверяет заголовкам прокси,
поэтому не открывайте этот порт наружу. Серверный прокси должен перезаписывать
`X-Forwarded-For` реальным IP клиента и `X-Forwarded-Proto` схемой запроса:
от `X-Forwarded-For` зависит лимит запросов на IP. Секреты и локальная `.venv`
не попадают в образ.

Логи: `docker compose logs -f backend`. Остановка: `docker compose down`.
После обновления кода повторите сборку; статику прокси раздаёт из `frontend/`.

Боевая площадка `dev.coresmart.tech` (angie, префикс `/sosedyami/`, доступ по
basic-auth) описана в [deploy/README.md](deploy/README.md).

## Локальное демо

Запустите backend по [инструкции](backend/README.md), затем из корня проекта:

```sh
make dev-frontend
```

Откройте `http://127.0.0.1:3000`. Фронтенд обращается к
`http://127.0.0.1:8000`; адрес задан в `frontend/app.js`.
После обновления страницы диалоги сбрасываются.

Для другого сайта настройте `CORS_ORIGINS` на сервере.
Не вводите личные данные: сообщения отправляются в DeepSeek.

Документация API: `/docs`. OpenAPI-схема: `/openapi.json`.
