<script>
  import { onMount } from "svelte";
  import "../app.css";

  onMount(() => {
    import("$lib/game-map-start.js");
  });
</script>

<svelte:head>
  <meta name="theme-color" content="#f4efe6" />
  <meta
    name="description"
    content="Познакомьтесь с будущими соседями и узнайте, какой район подойдёт именно вам."
  />
  <title>Будем соседями?</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
  <link
    href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap"
    rel="stylesheet"
  />
</svelte:head>

<div class="site-shell">
  <header class="topbar">
    <a class="brand" href="#top" aria-label="Будем соседями, на главную" data-action="home">
      <span class="brand-mark" aria-hidden="true"
        ><svg viewBox="0 0 38 38"
          ><path d="M4 18.2 19 6l15 12.2v14H4z" /><path
            d="M14 32V20h10v12M8 17.5 19 8.4l11 9.1"
          /></svg
        ></span
      >
      <span>будем<br />соседями?</span>
    </a>
    <div class="topbar-right">
      <span class="demo-pill"><i></i>РАЙОН 01 · 4 СОСЕДА</span><button
        class="text-button"
        data-action="restart">Сбросить игру <span aria-hidden="true">↻</span></button
      >
    </div>
  </header>

  <main id="app" tabindex="-1">
    <section class="screen" id="screen-home" aria-labelledby="hero-title" hidden>
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow"><span class="eyebrow-line"></span>ИНТЕРАКТИВНОЕ ЗНАКОМСТВО</p>
          <h1 id="hero-title">Будем<br /><em>соседями?</em></h1>
          <p class="hero-lead">
            Дом — это не только стены. Это люди, места и маленькие привычки, из которых складывается
            ваш день.
          </p>
          <p class="hero-note">
            Познакомьтесь с четырьмя соседями и узнайте, как устроена их жизнь. Адреса пока
            останутся в секрете.
          </p>
          <button class="button button-dark" data-action="start"
            >Познакомиться <span aria-hidden="true">↗</span></button
          >
          <p class="micro-note">4 соседа · 3 минуты · без правильных ответов</p>
        </div>
        <div
          class="hero-art"
          aria-label="Многоквартирный жилой комплекс в большом городе"
          role="img"
        >
          <img class="neighborhood-image" src="/urban-apartment-complex.png" alt="" />
          <div class="art-caption art-caption-top">ваш будущий район</div>
          <div class="art-caption art-caption-bottom">
            <span>01 — 04</span><span>истории рядом</span>
          </div>
          <div class="art-sticker"><span>⌂</span><span>всё начинается<br />с разговора</span></div>
        </div>
      </div>
      <div class="home-footer">
        <span>СОСЕДОМ МОЖЕТ СТАТЬ КАЖДЫЙ</span><span>ЛИСТАЙТЕ СВОЮ ИСТОРИЮ <b>↓</b></span>
      </div>
    </section>

    <section
      class="screen neighbors-screen is-active"
      id="screen-neighbors"
      aria-labelledby="neighbors-title"
    >
      <div class="section-heading">
        <div>
          <p class="eyebrow"><span class="eyebrow-line"></span>СНАЧАЛА — ЛЮДИ</p>
          <h2 id="neighbors-title">С кем вам<br /><em>по пути?</em></h2>
        </div>
        <p class="heading-aside">
          У каждого свой ритм и свои любимые места. Выберите, с кем познакомиться, — адреса пока
          останутся тайной.
        </p>
      </div>
      <div class="city-map-card">
        <div class="city-map-viewport" aria-label="Карта района с домами будущих соседей">
          <div class="city-map-canvas">
            <img
              class="city-map-image"
              src="/city-aerial-map.png"
              alt="Большой жилой район мегаполиса с высоты птичьего полёта."
              draggable="false"
            />
            <div class="map-agent-layer" id="map-agent-layer"></div>
          </div>
        </div>
        <div class="game-mission" aria-live="polite">
          <span class="game-mission-kicker">ВАША ЦЕЛЬ</span>
          <strong id="mission-title">Найдите 3 совпадения</strong>
          <div class="mission-progress">
            <span id="mission-progress-count">0 / 3</span>
            <div class="mission-pips" aria-hidden="true"><i></i><i></i><i></i></div>
          </div>
          <small id="mission-hint">Выбирайте вопросы у соседей на карте</small>
        </div>
        <div class="city-map-tools" aria-label="Управление картой">
          <button type="button" data-map-zoom="in" aria-label="Приблизить карту">+</button>
          <button type="button" data-map-zoom="out" aria-label="Отдалить карту">−</button>
          <button type="button" data-map-reset aria-label="Показать всю карту">↗</button>
        </div>
        <span class="city-map-caption">ПЕРЕТАЩИТЕ КАРТУ · НАЖМИТЕ НА АВАТАР СОСЕДА</span>
      </div>
      <div class="section-bottom">
        <span class="micro-note" id="mission-bottom-note"
          >Поговорите с соседями и найдите 3 совпадения</span
        ><button class="button button-dark" data-action="to-choice" id="choose-from-list" disabled
          >Собрать совпадения <span aria-hidden="true">→</span></button
        >
      </div>
    </section>

    <section class="screen" id="screen-chat" aria-labelledby="chat-title" hidden>
      <div class="chat-layout">
        <aside class="chat-aside">
          <button class="back-button" data-action="neighbors"
            ><span aria-hidden="true">←</span> К соседям</button
          >
          <p class="eyebrow"><span class="eyebrow-line"></span>ВАШ РАЗГОВОР</p>
          <h2 id="chat-title">Познакомимся<br /><em>поближе?</em></h2>
          <p class="chat-aside-copy">
            Выберите готовый вопрос или напишите свой — сосед ответит в рамках своей демо-истории.
          </p>
          <div class="chat-profile-mini" id="chat-profile-mini"></div>
          <div class="chat-progress">
            <span id="chat-progress-label">ЗАДАНО ВОПРОСОВ</span>
            <div class="progress-track"><i id="chat-progress-bar"></i></div>
            <b id="chat-progress-count">0</b>
          </div>
        </aside>
        <div class="chat-card">
          <div class="chat-card-head">
            <span class="online-dot"></span><span id="chat-name-label">Антон</span><span
              class="chat-status">демо-режим</span
            >
          </div>
          <div class="chat-messages" id="chat-messages" aria-live="polite"></div>
          <div class="question-area">
            <p>Выберите вопрос или напишите свой</p>
            <div class="question-options" id="question-options"></div>
            <div class="chat-compose" id="chat-compose">
              <label class="visually-hidden" for="chat-input">Ваш вопрос соседу</label>
              <textarea
                id="chat-input"
                name="message"
                maxlength="500"
                rows="2"
                placeholder="Напишите сообщение…"></textarea>
              <button
                class="button button-dark"
                type="button"
                data-action="send-message"
                id="chat-send"
              >
                Отправить
              </button>
              <small class="chat-privacy-note"
                >Ответ основан на вымышленной истории соседа. Не вводите личные данные — сообщение
                отправится в DeepSeek.</small
              >
            </div>
          </div>
          <div class="chat-card-foot">
            <button class="text-button" data-action="neighbors"
              >Познакомиться с другим <span aria-hidden="true">↗</span></button
            ><span>ВЫБЕРИТЕ ТЕМУ ДЛЯ РАЗГОВОРА</span>
          </div>
        </div>
      </div>
    </section>

    <section class="screen" id="screen-choice" aria-labelledby="choice-title" hidden>
      <div class="choice-wrap">
        <p class="eyebrow"><span class="eyebrow-line"></span>ВАШЕ РЕШЕНИЕ</p>
        <h2 id="choice-title">С кем бы вы<br /><em>жили рядом?</em></h2>
        <p class="choice-intro">
          Вспомните ваш разговор. Выберите человека, чей ритм жизни вам ближе.
        </p>
        <div class="choice-grid" id="choice-grid"></div>
        <button
          class="button button-dark choice-submit"
          data-action="reveal"
          id="reveal-button"
          disabled>Узнать, где он живёт <span aria-hidden="true">→</span></button
        >
      </div>
    </section>

    <section class="screen" id="screen-reveal" aria-labelledby="reveal-title" hidden>
      <div class="reveal-layout">
        <div class="reveal-main">
          <p class="eyebrow"><span class="eyebrow-line"></span>ТЕПЕРЬ МОЖНО РАССКАЗАТЬ</p>
          <div class="reveal-stamp">ваш<br />выбор</div>
          <h2 id="reveal-title">Кажется, вы<br />могли бы стать<br /><em>соседями.</em></h2>
          <p class="reveal-person" id="reveal-person"></p>
          <div class="project-card" id="project-card"></div>
        </div>
        <aside class="reveal-side">
          <div class="match-note">
            <span class="match-icon">✳</span>
            <p class="eyebrow">ПОЧЕМУ ВАМ МОЖЕТ ПОДОЙТИ</p>
            <p id="match-copy"></p>
            <div class="interest-tags" id="interest-tags"></div>
          </div>
          <div class="neighbor-quote" id="neighbor-quote"></div>
        </aside>
      </div>
      <div class="apartment-section">
        <div class="apartment-heading">
          <div>
            <p class="eyebrow"><span class="eyebrow-line"></span>МОЖЕТ БЫТЬ, ВАША КВАРТИРА</p>
            <h3 id="apartment-title">Начнём с пространства<br />для вашей жизни.</h3>
          </div>
          <p class="heading-aside">Демонстрационная планировка<br />для этой истории</p>
        </div>
        <div class="apartment-card" id="apartment-card"></div>
      </div>
      <div class="next-step">
        <div>
          <span class="eyebrow">ХОТИТЕ ПРОДОЛЖИТЬ?</span>
          <p>
            В реальном проекте здесь можно было бы посмотреть квартиры или поговорить с менеджером.
          </p>
        </div>
        <div class="next-actions">
          <button class="button button-dark" data-action="apartment"
            >Посмотреть квартиру <span aria-hidden="true">↗</span></button
          ><button class="button button-outline" data-action="contact">Попросить связаться</button>
        </div>
      </div>
      <footer class="demo-disclaimer">
        Демо-история: герои, ответы, жилые комплексы и планировки подготовлены для показа и не
        описывают реальные объекты. В рабочем спецпроекте каждый сосед будет отдельным AI-агентом с
        базой знаний о своём ЖК и районе.
      </footer>
    </section>
  </main>
</div>

<div class="modal-backdrop" id="modal" hidden>
  <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <button class="modal-close" data-action="close-modal" aria-label="Закрыть">×</button>
    <div id="modal-content"></div>
  </div>
</div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
