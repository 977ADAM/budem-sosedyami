import { askAgent, clearSession, getAgentHistory, startSession } from "./agent-api.js";

const people = {
  anton: {
    id: "anton",
    name: "Антон",
    role: "Продуктовый дизайнер · работает из дома",
    kind: "anton",
    age: "31",
    cardLabel: "городской ритм",
    cardEyebrow: "РАБОТА И ГОРОД",
    intro:
      "Я люблю, когда город рядом, но дома тихо. Утром обычно бегаю, а потом работаю у окна — так день начинается совсем по-другому.",
    card: "Работает из дома, бегает по утрам и знает, где в районе хороший кофе.",
    questions: [
      {
        id: "work",
        label: "Где ты работаешь и как устроил рабочее место?",
        topic: "Работа",
        answer:
          "Я дизайнер, почти всегда работаю из дома. В квартире выделил угол у окна: естественный свет помогает, а закрытая дверь — не отвлекаться на созвоны. В будни особенно ценю, что за кофе можно выйти пешком и проветрить голову.",
      },
      {
        id: "sport",
        label: "Где ты бегаешь по утрам?",
        topic: "Спорт",
        answer:
          "Есть зелёный маршрут вдоль тихих улиц — минут десять от дома, и уже можно бежать без светофоров. Обычно делаю круг до небольшого сквера. В выходные там почти никого.",
      },
      {
        id: "coffee",
        label: "Куда идёшь за кофе?",
        topic: "Кофе и прогулки",
        answer:
          "За углом открылась маленькая пекарня. Там знают постоянных гостей, и можно взять кофе с собой, а потом пройтись через сквер. Не план на весь день, а приятная пауза между делами.",
      },
      {
        id: "transport",
        label: "Удобно ли отсюда добираться?",
        topic: "Транспорт",
        answer:
          "До метро я обычно дохожу пешком за пятнадцать минут, а если спешу — рядом есть остановка. В центр выбираюсь пару раз в неделю. Мне нравится, что повседневные дела не требуют каждый раз садиться в машину.",
      },
    ],
    project: "Сосновый берег",
    developer: "Демо-проект · северный район",
    feature:
      "Спокойный городской квартал рядом с зелёным маршрутом и повседневной инфраструктурой.",
    quote: "Мой идеальный район — тот, где в обычный вторник тоже есть куда выйти.",
    apartment: {
      title: "Однокомнатная с отдельной рабочей нишей",
      area: "42,6 м²",
      rooms: "1 комната",
      detail:
        "Планировка с местом для компактного рабочего стола у окна — для тех, кому важно разделять дела и отдых.",
    },
    apartmentHeadline: "Начнём с пространства<br />для вашей жизни.",
    matchCopy: {
      Работа:
        "Вы рассказали, что домашний рабочий угол и прогулки между делами важны для вашего ритма. В этой демо-истории район сочетает спокойное место для работы дома с коротким выходом к зелёному маршруту.",
      Спорт:
        "Вас заинтересовали утренние пробежки и зелёные маршруты. В этой демо-истории рядом есть место, куда можно выйти размяться до начала дня.",
      "Кофе и прогулки":
        "Вас заинтересовали прогулки и места, куда можно заглянуть между делами. В этой демо-истории повседневные маршруты проходят через сквер и небольшие кафе.",
      Транспорт:
        "Вы спрашивали о дороге и повседневных перемещениях. В этой демо-истории можно сочетать пешие дела рядом с домом и поездки на общественном транспорте.",
    },
  },
  marina: {
    id: "marina",
    name: "Марина",
    role: "Редактор · мама дочки-первоклассницы",
    kind: "marina",
    age: "34",
    cardLabel: "семейный ритм",
    cardEyebrow: "СЕМЬЯ И ПОВСЕДНЕВНОСТЬ",
    intro:
      "У нас с дочкой насыщенные будни: школа, кружок, прогулка и ужин. Я люблю, когда нужное рядом и можно не превращать обычный день в логистический квест.",
    card: "Воспитывает дочку, любит пешие маршруты и выбирает места, где удобно всей семье.",
    questions: [
      {
        id: "school",
        label: "Как устроены ваши будни со школой?",
        topic: "Школа и дети",
        answer:
          "До школы мы идём пешком по спокойной улице. Это наше время поговорить перед началом дня. После уроков рядом есть секция рисования — дочка ходит сама с моей небольшой помощью, а я могу успеть на работу.",
      },
      {
        id: "yard",
        label: "Где вы гуляете после школы?",
        topic: "Двор и прогулки",
        answer:
          "Во дворе есть место, где дети играют, а взрослые могут посидеть неподалёку. Если хочется сменить обстановку, идём в сквер — там широкие дорожки и небольшой пруд. Дочка каждый раз кормит голубей, хотя я напоминаю, что лучше просто наблюдать.",
      },
      {
        id: "shops",
        label: "Что есть рядом на каждый день?",
        topic: "Инфраструктура",
        answer:
          "Магазин, аптека и пекарня находятся по пути домой. Это здорово упрощает будни: можно забрать хлеб, купить продукты на ужин и не планировать отдельную поездку.",
      },
      {
        id: "weekend",
        label: "Как вы проводите выходные?",
        topic: "Отдых и семья",
        answer:
          "Часто никуда далеко не едем: завтракаем, берём самокаты и идём гулять по району. Иногда встречаемся с друзьями в кафе у сквера. Для нас хороший выходной — когда не нужно успеть всё.",
      },
    ],
    project: "Тихий двор",
    developer: "Демо-проект · юго-западный район",
    feature: "Семейный квартал с тихими прогулочными маршрутами и нужными местами рядом.",
    quote:
      "Когда ребёнку удобно гулять, у родителей тоже становится на один повод для тревоги меньше.",
    apartment: {
      title: "Двухкомнатная с местом для семейных дел",
      area: "58,3 м²",
      rooms: "2 комнаты",
      detail:
        "Планировка с общей кухней-гостиной и отдельной спальней — чтобы было место и для встреч, и для тишины.",
    },
    apartmentHeadline: "Место для вас<br />и вашей семьи.",
    matchCopy: {
      "Школа и дети":
        "Вы спросили про школу и занятия после уроков. В этой демо-истории семейные маршруты устроены так, чтобы часть дел можно было сделать пешком.",
      "Двор и прогулки":
        "Для вас важны двор и прогулки рядом с домом. В этой демо-истории есть место для игры во дворе и спокойный сквер неподалёку.",
      Инфраструктура:
        "Вы обратили внимание на повседневные дела рядом. В этой демо-истории магазин, аптека и пекарня попадают в привычный маршрут домой.",
      "Отдых и семья":
        "Вам близок неторопливый семейный выходной. В этой демо-истории можно провести время рядом с домом, не планируя долгую поездку.",
    },
  },
  pavel: {
    id: "pavel",
    name: "Павел",
    role: "Операционный менеджер · часто ездит по делам",
    kind: "pavel",
    age: "38",
    cardLabel: "ритм поездок",
    cardEyebrow: "ДЕЛА И ТРАНСПОРТ",
    intro:
      "У меня каждый день разный: утром встреча в одном конце города, после обеда — в другом. Я выбирал район, откуда удобно выезжать по делам и приятно возвращаться домой.",
    card: "Часто бывает в разъездах, ценит удобные пересадки и места рядом на случай между встречами.",
    questions: [
      {
        id: "route",
        label: "Как ты обычно добираешься по городу?",
        topic: "Транспорт",
        answer:
          "Чаще всего еду на метро: пересадка рядом, а время в пути предсказуемое. Если встреча недалеко, иду пешком — по дороге можно забрать заказ или выпить кофе.",
      },
      {
        id: "morning",
        label: "Как выглядит твоё обычное утро?",
        topic: "Повседневные дела",
        answer:
          "Смотрю календарь, беру кофе в пекарне у дома и еду на первую встречу. Хорошо, когда основные дела можно начать без долгих сборов и пробок.",
      },
      {
        id: "between",
        label: "Где бываешь между встречами?",
        topic: "Инфраструктура",
        answer:
          "Иногда между встречами появляется час. Тогда выручает тихое кафе или небольшое пространство, где можно открыть ноутбук и спокойно ответить на письма.",
      },
      {
        id: "evening",
        label: "Как отдыхаешь после насыщенного дня?",
        topic: "Отдых и прогулки",
        answer:
          "Стараюсь пройтись пешком хотя бы немного. В районе есть бульвар с деревьями — там легко переключиться после бесконечных списков дел.",
      },
    ],
    project: "Городской ритм",
    developer: "Демо-проект · рядом с метро и маршрутами города",
    feature:
      "Квартал с удобными пересадками, повседневными сервисами и местом для коротких прогулок.",
    quote: "Когда город большой, особенно ценишь район, из которого просто добраться куда угодно.",
    apartment: {
      title: "Двухкомнатная с отдельной спальней",
      area: "49,8 м²",
      rooms: "2 комнаты",
      detail:
        "Компактная кухня-гостиная и отдельная спальня — удобно вернуться домой после насыщенного дня и переключиться.",
    },
    apartmentHeadline: "Дом, в который<br />приятно возвращаться.",
    matchCopy: {
      Транспорт:
        "Вы спрашивали о поездках. В этой демо-истории рядом есть метро и несколько маршрутов общественного транспорта, чтобы планировать день без лишних пересадок.",
      "Повседневные дела":
        "Для вас важен быстрый старт дня. В этой демо-истории кофе, магазин и другие повседневные дела можно включить в маршрут от дома.",
      Инфраструктура:
        "Вас заинтересовали места для дел между встречами. В этой демо-истории рядом есть кафе и повседневные сервисы, где можно ненадолго остановиться.",
      "Отдых и прогулки":
        "Вы ищете способ переключаться после дел. В этой демо-истории рядом с домом есть бульвар для коротких прогулок.",
    },
  },
  vera: {
    id: "vera",
    name: "Вера",
    role: "Фотограф · исследует город пешком",
    kind: "vera",
    age: "29",
    cardLabel: "город для себя",
    cardEyebrow: "ПРОГУЛКИ И КУЛЬТУРА",
    intro:
      "Я часто гуляю без маршрута и замечаю детали: старую вывеску, новый двор, маленькую выставку. Мне нравится жить там, где обычный вечер может стать маленьким открытием.",
    card: "Открывает новые места в районе, любит парки, маленькие выставки и долгие прогулки.",
    questions: [
      {
        id: "park",
        label: "Где тебе нравится гулять?",
        topic: "Парки и прогулки",
        answer:
          "Я часто иду в парк по тихим улицам. Там можно выбрать длинный маршрут, а можно просто посидеть у воды и посмотреть, как меняется свет.",
      },
      {
        id: "culture",
        label: "Что интересного есть рядом?",
        topic: "Культура",
        answer:
          "Недавно нашла небольшую галерею и мастерскую керамики. Люблю, когда культурные места не обязательно искать в центре — иногда они совсем рядом с домом.",
      },
      {
        id: "coffee",
        label: "Куда ходишь вечером?",
        topic: "Кафе и события",
        answer:
          "Захожу в камерное кафе с книжной полкой. По выходным там иногда проходят встречи и кинопоказы — можно познакомиться с людьми, которые тоже живут неподалёку.",
      },
      {
        id: "way",
        label: "Удобно ли отсюда выбираться в центр?",
        topic: "Транспорт",
        answer:
          "Да, до метро можно дойти пешком, а вечером я нередко возвращаюсь на автобусе. Но для большинства обычных дел мне даже не нужно уезжать далеко.",
      },
    ],
    project: "Квартал у парка",
    developer: "Демо-проект · рядом с зелёными и культурными маршрутами",
    feature:
      "Городской квартал с парком, небольшими культурными местами и кафе в пешей доступности.",
    quote: "Мне нравится, когда знакомый путь домой каждый раз открывает что-то новое.",
    apartment: {
      title: "Однокомнатная с местом для творчества",
      area: "39,4 м²",
      rooms: "1 комната",
      detail:
        "Пространство с удобной зоной у окна — для работы над фотографиями, чтения или неспешного завтрака.",
    },
    apartmentHeadline: "Пространство для<br />вашего города.",
    matchCopy: {
      "Парки и прогулки":
        "Вы выбрали прогулки. В этой демо-истории рядом есть парк и спокойные улицы, по которым можно составить собственный маршрут.",
      Культура:
        "Вам интересны культурные места. В этой демо-истории рядом с домом работают небольшие галерея и мастерская.",
      "Кафе и события":
        "Вы спрашивали о местах для встреч. В этой демо-истории есть камерное кафе, где проходят небольшие события.",
      Транспорт:
        "Вам важно сочетать прогулки и поездки. В этой демо-истории до метро можно дойти пешком, а рядом есть остановка автобуса.",
    },
  },
};

const state = {
  screen: "neighbors",
  activePerson: "anton",
  selectedPerson: null,
  choices: Object.fromEntries(Object.keys(people).map((id) => [id, new Set()])),
  conversations: Object.fromEntries(Object.keys(people).map((id) => [id, []])),
  dialogueRevisions: Object.fromEntries(Object.keys(people).map((id) => [id, 0])),
  pendingQuestion: null,
};
const MATCH_GOAL = 3;
const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
function answeredCount() {
  return Object.values(state.choices).reduce((sum, answers) => sum + answers.size, 0);
}

function portrait(personId) {
  if (personId === "marina")
    return `<svg viewBox="0 0 150 220" role="img" aria-label="Иллюстрация Марины"><circle cx="76" cy="65" r="37" fill="#bc755b"/><path d="M36 68c2-38 20-56 43-53 25 2 39 24 35 57l-10-17-5-18c-17 14-37 20-63 20z" fill="#66483f"/><path d="M50 86h51l30 30v104H18V119z" fill="#657d69"/><path d="M59 89c2 20 11 31 20 31 11 0 21-12 22-31l-12-10H67z" fill="#b66f56"/><path d="m50 87 25 30-24 22-17-34zm51 0-26 30 26 22 21-33z" fill="#f0d4bd"/><circle cx="64" cy="68" r="2.5" fill="#45372f"/><circle cx="91" cy="68" r="2.5" fill="#45372f"/><path d="M69 82c5 4 12 4 17 0" stroke="#75473d" stroke-width="2" fill="none" stroke-linecap="round"/><path d="M18 184c17-6 30-8 48-7 19 1 39 0 64 8v35H18z" fill="#d4a078"/><path d="M52 143h48" stroke="#f0d4bd" stroke-width="3" stroke-linecap="round"/><circle cx="110" cy="167" r="11" fill="#e6c86b"/><path d="M110 156v22m-11-11h22" stroke="#fff8e8" stroke-width="2"/></svg>`;
  if (personId === "pavel")
    return `<svg viewBox="0 0 150 220" role="img" aria-label="Иллюстрация Павла"><circle cx="76" cy="65" r="36" fill="#d4a17d"/><path d="M40 62c1-30 17-48 39-48 24 0 39 19 36 50l-12-12-5-18c-15 16-33 24-58 28z" fill="#393d39"/><path d="M54 84h46l31 30v106H20V112z" fill="#65766f"/><path d="M59 89c2 19 9 29 18 29 10 0 18-11 19-29l-10-9H69z" fill="#c88f70"/><path d="m54 84 23 30-24 22-18-34zm46 0-23 30 24 22 20-32z" fill="#e8dfcf"/><circle cx="65" cy="66" r="2.5" fill="#403630"/><circle cx="91" cy="66" r="2.5" fill="#403630"/><path d="M68 80c5 3 11 3 16 0" stroke="#785348" stroke-width="2" fill="none" stroke-linecap="round"/><path d="M21 183c19-8 38-10 60-9 21 1 38 3 50 9v37H21z" fill="#435b53"/><path d="M52 143h48" stroke="#d8ded5" stroke-width="3" stroke-linecap="round"/><rect x="108" y="146" width="20" height="27" rx="3" fill="#d6a353"/><path d="M114 146v-5a4 4 0 0 1 8 0v5" fill="none" stroke="#fff5dd" stroke-width="2"/></svg>`;
  if (personId === "vera")
    return `<svg viewBox="0 0 150 220" role="img" aria-label="Иллюстрация Веры"><circle cx="76" cy="65" r="36" fill="#e0ad8b"/><path d="M38 73c-6-36 12-60 39-60 30 0 42 24 36 62l-10-12-2-25c-13 15-30 22-56 24l-2 14z" fill="#a86648"/><path d="M52 85h48l31 30v105H20V112z" fill="#718777"/><path d="M59 89c1 19 8 29 18 29 11 0 18-11 19-29l-10-9H69z" fill="#d69c7b"/><path d="m52 84 25 30-22 26-22-38zm48 0-23 30 25 25 19-37z" fill="#e8dbcc"/><circle cx="65" cy="67" r="2.5" fill="#46372f"/><circle cx="91" cy="67" r="2.5" fill="#46372f"/><path d="M68 81c5 4 12 4 17 0" stroke="#8b5949" stroke-width="2" fill="none" stroke-linecap="round"/><path d="M21 183c19-8 38-10 59-9 22 1 38 3 51 9v37H21z" fill="#a96850"/><path d="M53 145h46" stroke="#f0dec9" stroke-width="3" stroke-linecap="round"/><circle cx="111" cy="163" r="10" fill="#e6c86b"/><path d="m106 163 4 4 7-9" stroke="#fff8e8" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  return `<svg viewBox="0 0 150 220" role="img" aria-label="Иллюстрация Антона"><circle cx="77" cy="64" r="36" fill="#d7a17e"/><path d="M40 62c2-31 17-47 39-47 24 0 39 17 37 48-10-8-18-18-23-31-11 14-28 24-53 30z" fill="#514339"/><path d="M54 83h46l31 30v107H20V112z" fill="#667d69"/><path d="M60 87c1 20 7 31 17 31s18-12 19-31l-11-8H70z" fill="#d49a78"/><path d="m54 84 23 30-24 22-18-34zm46 0-23 30 24 22 20-32z" fill="#e9e1ce"/><circle cx="66" cy="65" r="2.5" fill="#403630"/><circle cx="91" cy="65" r="2.5" fill="#403630"/><path d="M69 79c4 3 11 3 15 0" stroke="#785348" stroke-width="2" fill="none" stroke-linecap="round"/><path d="M21 182c18-9 40-10 61-9 21 1 38 3 49 9v38H21z" fill="#526b5b"/><path d="M78 130v82m-19-45h38" stroke="#d9e4d5" stroke-width="3" stroke-linecap="round"/><circle cx="119" cy="148" r="10" fill="#e6c86b"/><path d="m114 148 4 4 7-9" stroke="#fff8e8" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}

function miniAvatar(personId) {
  return `<span class="mini-avatar ${personId}">${portrait(personId)}</span>`;
}
function renderMapAgents() {
  const layer = $("#map-agent-layer");
  if (!layer) return;
  layer.innerHTML = Object.values(people)
    .map(
      (person) =>
        `<div class="map-home map-home-${person.id}" aria-hidden="true"><span>Дом соседа</span></div><button type="button" class="map-agent-marker ${person.id}" data-action="chat" data-person="${person.id}" aria-label="Открыть диалог с ${person.name}, соседом"><span class="map-marker-avatar">${portrait(person.id)}</span><i aria-hidden="true"></i><span class="map-marker-label"><strong>${person.name}</strong><small>Сосед рядом</small></span></button>`,
    )
    .join("");
  $$(".map-agent-marker svg", layer).forEach((svg) => {
    svg.setAttribute("viewBox", "27 7 100 100");
    svg.setAttribute("aria-hidden", "true");
    svg.removeAttribute("role");
    svg.removeAttribute("aria-label");
  });
}
renderMapAgents();

const mapViewport = $(".city-map-viewport");
const mapCanvas = $(".city-map-canvas");
const mapState = { scale: 1, x: 0, y: 0, pointer: null };
function updateMapTransform() {
  if (!mapCanvas) return;
  mapCanvas.style.setProperty("--map-scale", mapState.scale.toFixed(2));
  mapCanvas.style.width = `${mapViewport.clientWidth}px`;
  mapCanvas.style.height = `${mapViewport.clientHeight}px`;
  mapCanvas.style.left = `${mapState.x}px`;
  mapCanvas.style.top = `${mapState.y}px`;
}
function fitMap() {
  if (!mapViewport || !mapCanvas) return;
  mapState.scale = 1;
  mapState.x = 0;
  mapState.y = 0;
  updateMapTransform();
}
if (mapViewport) {
  fitMap();
  window.addEventListener("resize", fitMap);
  mapViewport.addEventListener("pointerdown", (event) => {
    if (event.target.closest("button")) return;
    mapState.pointer = {
      id: event.pointerId,
      x: event.clientX,
      y: event.clientY,
      originX: mapState.x,
      originY: mapState.y,
    };
    mapViewport.classList.add("is-dragging");
    mapViewport.setPointerCapture(event.pointerId);
  });
  mapViewport.addEventListener("pointermove", (event) => {
    if (!mapState.pointer || mapState.pointer.id !== event.pointerId) return;
    mapState.x = mapState.pointer.originX + event.clientX - mapState.pointer.x;
    mapState.y = mapState.pointer.originY + event.clientY - mapState.pointer.y;
    updateMapTransform();
  });
  const endPan = (event) => {
    if (mapState.pointer?.id !== event.pointerId) return;
    mapState.pointer = null;
    mapViewport.classList.remove("is-dragging");
  };
  mapViewport.addEventListener("pointerup", endPan);
  mapViewport.addEventListener("pointercancel", endPan);
}
document.addEventListener("click", (event) => {
  const zoom = event.target.closest("[data-map-zoom]");
  if (zoom) {
    mapState.scale = Math.max(
      0.35,
      Math.min(1.8, mapState.scale + (zoom.dataset.mapZoom === "in" ? 0.12 : -0.12)),
    );
    updateMapTransform();
  }
  if (event.target.closest("[data-map-reset]")) fitMap();
});
function showScreen(name) {
  state.screen = name;
  $$(".screen").forEach((screen) => {
    const active = screen.id === `screen-${name}`;
    screen.hidden = !active;
    screen.classList.toggle("is-active", active);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
  $("#app").focus({ preventScroll: true });
  if (name === "neighbors") {
    renderNeighbors();
    fitMap();
  }
  if (name === "chat") {
    renderChat();
  }
  if (name === "choice") renderChoice();
  if (name === "reveal") renderReveal();
}
function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("visible");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("visible"), 2400);
}
function escapeHtml(value) {
  return String(value).replace(
    /[&<>"']/g,
    (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char],
  );
}

function renderNeighbors() {
  const found = Math.min(answeredCount(), MATCH_GOAL);
  const ready = found >= MATCH_GOAL;
  $("#choose-from-list").disabled = !ready;
  $("#choose-from-list").innerHTML =
    `${ready ? "Выбрать соседа" : "Собрать совпадения"} <span aria-hidden="true">→</span>`;
  $("#mission-progress-count").textContent = `${found} / ${MATCH_GOAL}`;
  $("#mission-title").textContent = ready ? "Все совпадения найдены!" : "Найдите 3 совпадения";
  $("#mission-hint").textContent = ready
    ? "Теперь выберите, с кем вам по пути"
    : "Выбирайте вопросы у соседей на карте";
  $("#mission-bottom-note").textContent = ready
    ? "Цель выполнена — можно выбирать"
    : `Осталось найти ${MATCH_GOAL - found} ${MATCH_GOAL - found === 1 ? "совпадение" : "совпадения"}`;
  $$(".mission-pips i").forEach((pip, index) => pip.classList.toggle("is-found", index < found));
  $$(".map-agent-marker").forEach((marker) =>
    marker.classList.toggle("has-clue", state.choices[marker.dataset.person].size > 0),
  );
}

function chatHistory(personId) {
  const person = people[personId];
  const greeting = `<div class="message"><small>${person.name.toUpperCase()} · СЕЙЧАС</small>${escapeHtml(person.intro)}</div>`;
  const turns = state.conversations[personId]
    .map((turn) => {
      const userMessage = `<div class="message user"><small>ВЫ</small>${escapeHtml(turn.message)}</div>`;
      if (turn.reply)
        return `${userMessage}<div class="message"><small>${person.name.toUpperCase()}</small>${escapeHtml(turn.reply)}</div>`;
      if (turn.error)
        return `${userMessage}<div class="message" role="status"><small>${person.name.toUpperCase()}</small>${escapeHtml(turn.error)}</div>`;
      return `${userMessage}<div class="message" role="status"><small>${person.name.toUpperCase()}</small>Подбираю ответ…</div>`;
    })
    .join("");
  return greeting + turns;
}
function renderChat() {
  const person = people[state.activePerson];
  const asked = state.choices[person.id];
  $("#chat-title").innerHTML = `Познакомимся<br /><em>поближе?</em>`;
  $("#chat-name-label").textContent = person.name;
  $("#chat-profile-mini").innerHTML =
    `${miniAvatar(person.id)}<div><strong>${person.name}, ${person.age}</strong><span>${person.role}</span></div>`;
  $("#chat-messages").innerHTML = chatHistory(person.id);
  $("#question-options").innerHTML = person.questions
    .map(
      (q) =>
        `<button class="question-chip" data-action="question" data-question="${q.id}" ${asked.has(q.id) || state.pendingQuestion ? "disabled" : ""}>${asked.has(q.id) ? "✓ " : "+ "}${escapeHtml(q.label)}</button>`,
    )
    .join("");
  $("#chat-input").disabled = Boolean(state.pendingQuestion);
  $("#chat-send").disabled = Boolean(state.pendingQuestion);
  const found = Math.min(answeredCount(), MATCH_GOAL);
  $("#chat-progress-label").textContent = "СОВПАДЕНИЯ НАЙДЕНЫ";
  $("#chat-progress-count").textContent = `${found} / ${MATCH_GOAL}`;
  $("#chat-progress-bar").style.width = `${(found / MATCH_GOAL) * 100}%`;
  $("#chat-messages").scrollTop = $("#chat-messages").scrollHeight;
}

async function askMessage(personId, message, question = null) {
  const turn = { message, reply: null, error: null };
  state.conversations[personId].push(turn);
  if (question) state.choices[personId].add(question.id);
  const revision = ++state.dialogueRevisions[personId];
  const pending = { agentId: personId, questionId: question?.id ?? null, turn };
  state.pendingQuestion = pending;
  renderNeighbors();
  if (state.screen === "chat" && state.activePerson === personId) renderChat();
  if (question && answeredCount() === MATCH_GOAL)
    showToast("Три совпадения найдены — цель выполнена!");
  let fallback = false;
  let cancelled = false;
  try {
    const reply = await askAgent(personId, message, question?.id ?? null);
    if (state.pendingQuestion !== pending || revision !== state.dialogueRevisions[personId]) return;
    turn.reply = reply;
  } catch {
    if (question) {
      turn.reply = question.answer;
      fallback = true;
    } else {
      turn.error = "ИИ сейчас недоступен. Попробуйте отправить сообщение ещё раз.";
    }
  } finally {
    if (state.pendingQuestion === pending) {
      state.pendingQuestion = null;
      renderNeighbors();
      if (state.screen === "chat" && state.activePerson === personId) renderChat();
    } else cancelled = true;
  }
  if (fallback && !cancelled) showToast("ИИ сейчас недоступен — показан ответ из демо");
}

function renderChoice() {
  const available = Object.values(people).filter((p) => state.choices[p.id].size > 0);
  if (!available.length) {
    showScreen("neighbors");
    showToast("Сначала познакомьтесь хотя бы с одним соседом");
    return;
  }
  if (!available.some((p) => p.id === state.selectedPerson)) state.selectedPerson = available[0].id;
  $("#choice-grid").innerHTML = available
    .map(
      (person) =>
        `<button class="choice-card ${state.selectedPerson === person.id ? "selected" : ""}" data-action="select-person" data-person="${person.id}">${miniAvatar(person.id)}<span><strong>${person.name}</strong><small>${person.role}</small></span><span class="choice-check">${state.selectedPerson === person.id ? "✓" : ""}</span></button>`,
    )
    .join("");
  $("#reveal-button").disabled = !state.selectedPerson;
}

function getMatch(person) {
  const asked = [...state.choices[person.id]];
  const selectedTopics = asked
    .map((id) => person.questions.find((question) => question.id === id)?.topic)
    .filter(Boolean);
  const topics = [...new Set(selectedTopics)];
  const copy =
    topics
      .map((topic) => person.matchCopy[topic])
      .filter(Boolean)
      .join(" ") ||
    "Вы выбрали темы, которые важны именно для вашего ритма. В этой демо-истории можно представить, как повседневная жизнь складывается рядом с домом.";
  return { topics, copy };
}

function floorplan() {
  return `<svg class="floorplan" viewBox="0 0 270 150" role="img" aria-label="Демонстрационная схема квартиры"><rect class="room-fill" x="15" y="12" width="240" height="126"/><path d="M165 12v126M15 82h96V12M111 82v56M165 78h90M210 78v60M111 99h54"/><path d="M44 12v22m0 0h43M190 138v-20m0 0h42M15 55h18m0 0v27M255 42h-15m0 0v36"/><text x="43" y="59">КОМНАТА</text><text x="181" y="52">КУХНЯ</text><text x="38" y="116">РАБОТА</text><text x="180" y="111">ПРИХОЖАЯ</text><text x="115" y="132">С/У</text></svg>`;
}

function renderReveal() {
  const person = people[state.selectedPerson];
  const match = getMatch(person);
  $("#reveal-person").innerHTML = `<strong>${person.name}</strong> живёт в ЖК`;
  $("#project-card").innerHTML =
    `<span class="project-icon" aria-hidden="true">⌂</span><div><small>${person.developer.toUpperCase()}</small><strong>ЖК «${person.project}»</strong><span>${person.feature}</span></div>`;
  $("#match-copy").textContent = match.copy;
  $("#interest-tags").innerHTML = match.topics
    .map((topic) => `<span class="interest-tag">${topic}</span>`)
    .join("");
  $("#neighbor-quote").innerHTML =
    `“${person.quote}”<cite>— ${person.name}, ваш будущий сосед</cite>`;
  $("#apartment-title").innerHTML = person.apartmentHeadline;
  $("#apartment-card").innerHTML =
    `<div class="plan-art">${floorplan()}</div><div class="apartment-info"><small>ДЕМО-ПЛАНИРОВКА · ЖК «${person.project}»</small><h4>${person.apartment.title}</h4><p>${person.apartment.detail}</p><div class="apartment-meta"><span>${person.apartment.area}</span><span>${person.apartment.rooms}</span></div></div>`;
}

function openModal(content) {
  $("#modal-content").innerHTML = content;
  $("#modal").hidden = false;
  $(".modal-close").focus();
}
function closeModal() {
  $("#modal").hidden = true;
}
function showApartmentModal() {
  const person = people[state.selectedPerson];
  openModal(
    `<p class="eyebrow"><span class="eyebrow-line"></span>ДЕМО-ПЛАНИРОВКА</p><h3>${person.apartment.title}</h3><p>${person.apartment.detail}</p><div class="modal-detail"><span>Площадь<strong>${person.apartment.area}</strong></span><span>Комнат<strong>${person.apartment.rooms}</strong></span></div><p class="form-note">В реальном проекте здесь откроется карточка квартиры. В демо эта планировка — пример.</p><button class="button button-dark" data-action="close-modal">Вернуться к истории <span aria-hidden="true">↗</span></button>`,
  );
}
function showContactModal() {
  const person = people[state.selectedPerson];
  openModal(
    `<p class="eyebrow"><span class="eyebrow-line"></span>СЛЕДУЮЩИЙ ШАГ</p><h3>Поговорим о вашем доме?</h3><p>Оставьте данные в демонстрационной форме — они никуда не отправятся.</p><form id="contact-form"><label class="form-field"><span>Как к вам обращаться</span><input name="name" autocomplete="name" placeholder="Ваше имя" required /></label><label class="form-field"><span>Телефон</span><input name="phone" type="tel" autocomplete="tel" placeholder="+7 ___ ___-__-__" required minlength="6" /></label><p class="form-note">Форма работает только для показа сценария. Отправка заявки отключена.</p><button class="button button-dark" type="submit">Показать финал <span aria-hidden="true">→</span></button></form><p class="form-note">Ваш сосед ${person.name} уже знает, что вам интересно.</p>`,
  );
}

document.addEventListener("click", (event) => {
  const target = event.target.closest("[data-action]");
  if (!target) return;
  const action = target.dataset.action;
  if (action === "home" || action === "restart") {
    clearSession().catch(() => showToast("Не удалось очистить историю диалога"));
    Object.values(state.choices).forEach((set) => set.clear());
    Object.values(state.conversations).forEach((turns) => turns.splice(0));
    Object.keys(state.dialogueRevisions).forEach((id) => state.dialogueRevisions[id]++);
    state.pendingQuestion = null;
    state.selectedPerson = null;
    state.activePerson = "anton";
    closeModal();
    showScreen("neighbors");
  }
  if (action === "start") showScreen("neighbors");
  if (action === "chat") {
    state.activePerson = target.dataset.person;
    showScreen("chat");
  }
  if (action === "question") {
    const person = people[state.activePerson];
    const q = person.questions.find((item) => item.id === target.dataset.question);
    if (q && !state.pendingQuestion && !state.choices[person.id].has(q.id))
      askMessage(person.id, q.label, q);
  }
  if (action === "send-message") {
    const input = $("#chat-input");
    const message = input.value.trim();
    if (!message || state.pendingQuestion) return;
    input.value = "";
    askMessage(state.activePerson, message);
  }
  if (action === "neighbors") showScreen("neighbors");
  if (action === "to-choice") {
    if (answeredCount() < MATCH_GOAL) {
      showToast(`Найдите ещё ${MATCH_GOAL - answeredCount()} совпадения`);
      return;
    }
    showScreen("choice");
  }
  if (action === "select-person") {
    state.selectedPerson = target.dataset.person;
    renderChoice();
  }
  if (action === "reveal") {
    if (state.selectedPerson) showScreen("reveal");
  }
  if (action === "apartment") showApartmentModal();
  if (action === "contact") showContactModal();
  if (action === "close-modal") closeModal();
});

document.addEventListener("submit", (event) => {
  if (event.target.id !== "contact-form") return;
  event.preventDefault();
  const form = event.target;
  if (!form.reportValidity()) return;
  const name = new FormData(form).get("name").toString().trim();
  openModal(
    `<div class="success-mark">✓</div><p class="eyebrow"><span class="eyebrow-line"></span>ДЕМО ЗАВЕРШЕНО</p><h3>Спасибо, ${name}!</h3><p>В настоящем спецпроекте здесь бы связался менеджер. В этой демо-истории данные не сохраняются и никому не отправляются.</p><button class="button button-dark" data-action="close-modal">Вернуться к истории <span aria-hidden="true">↗</span></button>`,
  );
});

$("#modal").addEventListener("click", (event) => {
  if (event.target.id === "modal") closeModal();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && event.target.id === "chat-input") {
    event.preventDefault();
    $("#chat-send").click();
  }
  if (event.key === "Escape" && !$("#modal").hidden) closeModal();
});
async function initializeAgentSession() {
  try {
    await startSession();
    const histories = await Promise.all(
      Object.keys(people).map(async (personId) => [personId, await getAgentHistory(personId)]),
    );
    for (const [personId, turns] of histories) {
      state.conversations[personId] = turns;
      for (const turn of turns) {
        if (turn.question_id) state.choices[personId].add(turn.question_id);
      }
    }
  } catch {
    showToast("Не удалось загрузить историю диалогов");
  }
  showScreen("neighbors");
}

initializeAgentSession();
