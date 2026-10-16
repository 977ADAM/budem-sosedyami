# «Будем соседями?» на dev.coresmart.tech.
#
# Подключается изнутри server-блока dev.coresmart.tech (файл
# /etc/angie/http.d/clustering.conf):
#
#     include /etc/angie/sosedyami.locations.inc;
#
# Отдельный server{} с тем же server_name angie не примет, поэтому здесь
# только локации. auth_basic / auth_request / satisfy any наследуются от
# server, то есть демо закрыто тем же паролем admin или API-ключом.
#
# Бэкенд слушает 127.0.0.1:8010 (BACKEND_PORT в /opt/budem-sosedyami/.env).
# Обновление: cd /opt/budem-sosedyami && git pull && docker compose up -d --build --wait

location = /sosedyami {
    # Слэш обязателен: относительные запросы фронтенда (./api/…) должны
    # попадать в /sosedyami/api/…, а не в /api/… — там живёт clustering.
    return 301 /sosedyami/;
}

location ^~ /sosedyami/api/ {
    proxy_pass http://127.0.0.1:8010/api/;
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    # Бэкенд запущен с --proxy-headers: лимит считается по этому IP.
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
    proxy_http_version 1.1;
    # Модель отвечает до DEEPSEEK_TIMEOUT (30 с) плюс запас на сеть.
    proxy_read_timeout 120s;
}

location ^~ /sosedyami/ {
    alias /opt/budem-sosedyami/frontend/;
    index index.html;
}
