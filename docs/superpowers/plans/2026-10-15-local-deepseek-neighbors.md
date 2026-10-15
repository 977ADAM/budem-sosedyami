# Локальные ИИ-соседи на DeepSeek — план реализации

> **Superseded:** заменён планом, который будет составлен по `docs/superpowers/specs/2026-10-15-fastapi-local-agents-design.md` после утверждения этой спецификации.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить локальные ответы DeepSeek для четырёх вымышленных соседей, сохранив игру про готовые вопросы и fallback на демо-ответы.

**Architecture:** Vite dev-only middleware принимает сообщения чата, добавляет API-ключ и модель из локального окружения и пересылает запрос в DeepSeek Chat Completions. Клиент хранит отдельную временную историю ответов для каждого персонажа, формирует persona prompt только из имеющихся демо-данных и при сбое показывает исходный статичный ответ.

**Tech Stack:** Svelte 5, SvelteKit 2, Vite 6, Node.js built-in `fetch`; без новых зависимостей.

**Spec:** `docs/superpowers/specs/2026-10-15-local-deepseek-neighbors-design.md`

## Global Constraints

- Персонажи и сведения о ЖК остаются вымышленными и ограничены данными, заложенными в демо.
- Игрок выбирает только готовые вопросы; свободный текстовый ввод не добавляется.
- DeepSeek API используется только при локальном запуске Vite dev server.
- API-ключ хранится в `.env.local`, не в браузере и не в production bundle.
- При ошибке API или отсутствии ключа показывается соответствующий статичный `q.answer` и игра остаётся проходимой.
- История чата хранится в памяти страницы, без серверного хранения.
- Не добавлять зависимости или автоматические тесты для этого прототипа.

## Review Focus

- **Пустой API-ключ:** локальный endpoint возвращает понятный 503, клиент показывает fallback; покрыть проверкой Task 1 и Task 2.
- **Ошибка/невалидный ответ DeepSeek:** не оставлять бесконечное ожидание; показать fallback; проверить на Task 2.
- **Сетевая ошибка или таймаут:** завершить ожидание с fallback; проверить на Task 1 и Task 2.
- **Повторный клик во время запроса:** не отправлять дубликаты и не нарушать порядок сообщений; проверить в Task 2.
- **Смена соседа во время запроса:** ответ сохранить у исходного соседа и не показать в чужом диалоге; проверить в Task 2.

---

### Task 1: Локальный Vite endpoint и настройка ключа

**Files:**
- Modify: `vite.config.js`
- Modify: `.gitignore`
- Create: `.env.example`
- Modify: `README.md`

**Interfaces:**
- Produces: dev-only `POST /api/deepseek/chat/completions`, вход JSON `{ messages: Array<{ role: 'system' | 'user' | 'assistant'; content: string }> }`, успешный ответ совместим с Chat Completions API; на отсутствующий ключ возвращает JSON-ошибку со статусом 503.
- Environment: `DEEPSEEK_API_KEY` required for live calls; `DEEPSEEK_MODEL` optional, default `deepseek-flash`.

- [ ] **Step 1: Добавить Vite dev middleware для endpoint**

В `vite.config.js` загрузить непубличные переменные через `loadEnv(mode, process.cwd(), '')`. Зарегистрировать dev-only Vite plugin с `configureServer`, который обрабатывает только `POST /api/deepseek/chat/completions`. Прочитать JSON body, добавить модель из `DEEPSEEK_MODEL` или `deepseek-flash`, отправить его через `fetch` на `https://api.deepseek.com/chat/completions` с `Authorization: Bearer <key>`, ограничить ожидание 30 секундами и вернуть клиенту JSON-тело и HTTP status от DeepSeek. Не добавлять middleware в `build` режим.

- [ ] **Step 2: Обработать локальные ошибки endpoint**

При пустом `DEEPSEEK_API_KEY` вернуть `503` с JSON `{ error: { message: 'DEEPSEEK_API_KEY is not configured' } }`. Для ошибки сети или таймаута вернуть `502`/`504` с тем же форматом JSON и нейтральным сообщением. Не возвращать ключ или значение Authorization ни в одном ответе или логе.

- [ ] **Step 3: Исключить локальные секреты из Git и описать настройку**

В `.gitignore` игнорировать `.env` и `.env.*`, разрешив `.env.example`. Создать `.env.example` с пустым `DEEPSEEK_API_KEY=` и `DEEPSEEK_MODEL=deepseek-flash`. Дополнить README инструкцией скопировать шаблон в `.env.local`, добавить ключ и перезапустить `npm run dev`; указать, что AI-ответы работают только в dev.

- [ ] **Step 4: Проверить endpoint вручную**

Запустить `npm run dev`, отправить локальный POST с одной парой `messages` с настроенным ключом и убедиться, что приходит Chat Completions JSON. Повторить без ключа и убедиться в статусе 503. Убедиться, что production build конфигурация не регистрирует endpoint.

### Task 2: Ответы персонажей в чате и fallback

**Files:**
- Modify: `src/lib/game-map-start.js`
- Optionally modify: `src/routes/+page.svelte`
- Optionally modify: `src/app.css`

**Interfaces:**
- Consumes: endpoint из Task 1: `POST /api/deepseek/chat/completions` с `{ messages }`, ответ `choices[0].message.content`.
- Produces: на каждый person ID отдельное хранилище фактических ответов по question ID; на один момент времени не более одного ожидающего вопроса; `chatHistory(personId)` показывает сохранённый AI-ответ или `q.answer` fallback.

- [ ] **Step 1: Добавить отдельный стейт ответов и ожидания**

Рядом с `state.choices` создать `state.answers`, объект по каждому person ID с пустым объектом ответов. Добавить `state.pendingQuestion`, изначально `null`, содержащий `{ personId, questionId }` во время запроса. Не менять `state.choices` как источник количества найденных совпадений.

- [ ] **Step 2: Сформировать persona prompt и сообщения**

Добавить функции в `src/lib/game-map-start.js`, которые для `personId` формируют системную инструкцию только из существующих полей `people[personId]` (роль, вступление, карточка, вопросы/ответы, сведения о проекте, особенности, цитата). Инструкция задаёт голос персонажа, запрещает придумывать сведения о проекте/районе и предписывает честно говорить, когда ответа нет. Собрать `messages`: system, assistant greeting из `person.intro`, затем каждую ранее отвеченную пару в порядке `state.choices[personId]`, и текущий вопрос последним. Не включать текущий вопрос в историю дважды.

- [ ] **Step 3: Подключить async запрос при выборе готового вопроса**

В обработчике `action === 'question'` сохранить существующее поведение выбора вопроса и счётчика, установить `state.pendingQuestion`, обновить чат с индикатором ожидания, затем выполнить `fetch('/api/deepseek/chat/completions', ...)`. При успехе сохранить `choices[0].message.content` в `state.answers[personId][questionId]`; при любом non-2xx, ошибке разбора или сети оставить fallback `q.answer`. В обоих случаях очистить pending state и перерисовать правильный экран.

- [ ] **Step 4: Показать ответы и состояния чата**

В `chatHistory(personId)` показывать `state.answers[personId][q.id] ?? q.answer`. Пока запрос активен, добавить короткое состояние ожидания, блокировать все кнопки вопросов и показывать понятное уведомление о fallback при ошибке. Если пользователь сменил экран или соседа во время запроса, сохранить ответ исходному персонажу и не вставлять его в чужой чат. Оставить текущий fallback текст без изменений.

- [ ] **Step 5: Проверить полный пользовательский путь вручную**

С ключом пройти разговоры с разными соседями и проверить, что ответы и контекст не смешиваются, затем набрать три совпадения, выбрать человека и раскрыть результат. Проверить недоступность endpoint, двойной клик и смену соседа во время ожидания: игра должна продолжаться со статичными ответами без зависшего состояния.
