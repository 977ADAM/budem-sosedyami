#!/usr/bin/env bash
# Деплой «Будем соседями?» на dev.coresmart: пересборка backend + health-gate.
# Запускается из CI в /opt/budem-sosedyami после `git reset` на нужный ref;
# вручную: cd /opt/budem-sosedyami && bash deploy/deploy.sh
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")/.."

test -f frontend/index.html && test -f frontend/app.js || {
  echo "нет статики фронтенда (frontend/index.html, frontend/app.js)"
  exit 1
}

echo "пересобираю backend…"
docker compose up -d --build --wait

port="$(sed -n 's/^BACKEND_PORT=//p' .env 2>/dev/null | head -1)"
port="${port:-8000}"

code=""
for _ in $(seq 1 20); do
  code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${port}/health" || true)
  [ "$code" = "200" ] && break
  sleep 2
done
if [ "$code" != "200" ]; then
  echo "backend /health != 200 (${code})"
  docker compose logs --tail=50 backend
  exit 1
fi

contract="$(curl -s -o /dev/null -w '%{http_code}' \
  -X POST -H 'Content-Type: application/json' \
  -d '{"message":"Проверка деплоя"}' \
  "http://127.0.0.1:${port}/api/agents/nobody/chat" || true)"
if [ "$contract" != "422" ]; then
  echo "контракт API: неизвестный сосед вернул ${contract}, ожидался 422"
  docker compose logs --tail=50 backend
  exit 1
fi

echo "deploy OK: $(git rev-parse --short HEAD)"
