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
    # Реальный IP клиента. Балансировщик дописывает его в конец
    # X-Forwarded-For, а всё, что клиент прислал сам, остаётся в начале;
    # realip берёт последний недоверенный адрес и игнорирует начало.
    # Без этого бэкенд видит первое значение XFF (его подставляет любой
    # клиент) — лимит 20/мин обходится подменой заголовка, а в логах
    # оказывается выдуманный IP.
    set_real_ip_from 192.168.100.0/24;   # подсеть балансировщика
    real_ip_header X-Forwarded-For;
    real_ip_recursive on;

    proxy_pass http://127.0.0.1:8010/api/;
    proxy_set_header Host              $host;
    proxy_set_header X-Real-IP         $remote_addr;
    # Только проверенный IP: у uvicorn (--proxy-headers) первое значение XFF
    # становится ключом лимита и полем client= в логах.
    proxy_set_header X-Forwarded-For   $remote_addr;
    proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
    proxy_http_version 1.1;
    # Модель отвечает до DEEPSEEK_TIMEOUT (30 с) плюс запас на сеть.
    proxy_read_timeout 120s;
}

location ^~ /sosedyami/ {
    alias /opt/budem-sosedyami/frontend/;
    index index.html;
}
