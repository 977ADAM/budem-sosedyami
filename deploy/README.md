# Деплой на dev.coresmart.tech

Боевая площадка — сервер `dev.coresmart.tech` (SSH-хост `myserver`). TLS
терминирует внешний балансировщик, поэтому на хосте работает только angie
на порту 80; сертификаты и certbot здесь не нужны.

Схема:

```
браузер → HTTPS (внешний балансировщик) → angie :80
                                          ├── /sosedyami/      → статика /opt/budem-sosedyami/frontend
                                          └── /sosedyami/api/  → backend 127.0.0.1:8010 (Docker Compose)
```

Демо закрыто тем же basic-auth (`admin`) или API-ключом angie, что и
clustering: локации наследуют `auth_basic` / `auth_request` / `satisfy any`
из общего server-блока.

Порт 8010 выбран потому, что 8000 занят `ai-tracker-backend`, а 3000/3001/
8004/8080/8081 — другими проектами. Список занятых портов:

```sh
ssh myserver 'ss -tln | grep -E "127\.0\.0\.1:(8000|8010)"'
```

## Предусловия

- SSH-доступ на сервер (`ssh myserver`), права root.
- Docker 29 + Compose v5 (уже установлены).
- Репозиторий публичный, ключи для `git clone` не нужны.
- Ключ DeepSeek и постоянный `CONTEXT_SECRET`.
- Файлы из этого каталога: `angie-sosedyami.locations.inc`.

## Первичная установка

1. Клон и настройки:

   ```sh
   ssh myserver
   git clone https://github.com/977ADAM/budem-sosedyami.git /opt/budem-sosedyami
   cd /opt/budem-sosedyami

   printf 'BACKEND_PORT=8010\n' > .env
   chmod 600 .env

   cp backend/.env.example backend/.env
   python3 -c 'import secrets; print(secrets.token_urlsafe(32))'   # CONTEXT_SECRET
   ${EDITOR:-vi} backend/.env
   chmod 600 backend/.env
   ```

   В `backend/.env` обязательны `DEEPSEEK_API_KEY`, сгенерированный
   `CONTEXT_SECRET` и `LOG_LEVEL=INFO`. `CONTEXT_SECRET` сохраняйте при
   обновлениях: смена ключа сбрасывает все текущие диалоги.

2. Запуск бэкенда:

   ```sh
   docker compose up -d --build --wait
   curl -fsS http://127.0.0.1:8010/health   # {"status":"ok"}
   ```

3. Локации angie (один раз):

   ```sh
   cp /etc/angie/http.d/clustering.conf /etc/angie/http.d/clustering.conf.bak-$(date +%s)
   scp deploy/angie-sosedyami.locations.inc myserver:/etc/angie/sosedyami.locations.inc   # с локальной машины
   ```

   Внутри `server { ... }` файла `/etc/angie/http.d/clustering.conf` добавить
   одну строку:

   ```angie
   include /etc/angie/sosedyami.locations.inc;
   ```

   Затем проверить и применить:

   ```sh
   angie -t && angie -s reload
   ```

   Файл намеренно назван `*.inc`, а не `*.conf`: `angie.conf` подключает
   `/etc/angie/http.d/*.conf` на уровне `http`, где `location` недопустим.

4. Проверка снаружи: `https://dev.coresmart.tech/sosedyami/` (логин `admin`).

## Обновление кода

```sh
ssh myserver 'cd /opt/budem-sosedyami && git pull && docker compose up -d --build --wait && curl -fsS http://127.0.0.1:8010/health'
```

Конфиг angie меняется только при изменении маршрутов или порта; после правки
`/etc/angie/sosedyami.locations.inc` — `angie -t && angie -s reload`.

Смена версии фронтенда отдельного шага не требует: angie отдаёт файлы прямо из
`/opt/budem-sosedyami/frontend`, сборки нет.

## Откат

```sh
ssh myserver 'cd /opt/budem-sosedyami && git log --oneline -5'   # выбрать коммит
ssh myserver 'cd /opt/budem-sosedyami && git checkout <commit> && docker compose up -d --build --wait'
ssh myserver 'git -C /opt/budem-sosedyami checkout main'
```

Полное снятие с площадки:

```sh
ssh myserver 'cd /opt/budem-sosedyami && docker compose down'
# затем убрать include из /etc/angie/http.d/clustering.conf
ssh myserver 'angie -t && angie -s reload'
```

## Диагностика

```sh
ssh myserver 'docker compose -f /opt/budem-sosedyami/compose.yaml logs -f backend'
ssh myserver 'docker compose -f /opt/budem-sosedyami/compose.yaml ps'
ssh myserver 'curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8010/health'
ssh myserver 'tail -50 /var/log/angie/error.log'
```

- `502/504` в браузере при живом контейнере — смотреть логи backend и
  `DEEPSEEK_API_KEY` / сеть до `api.deepseek.com`.
- `401` — basic-auth: пароль из `/etc/angie/.htpasswd`, пользователь `admin`.
- Ответы `429` у всех сразу означают, что до бэкенда не доходит реальный IP
  клиента: проверьте, что балансировщик заполняет `X-Forwarded-For`.
- Диалоги сбрасываются после перезапуска — изменился или потерялся
  `CONTEXT_SECRET` в `backend/.env`.
