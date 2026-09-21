# 📐 Implementation Plan: Минималистичный интерфейс без подсказок (TASK-007)

- **ID плана:** PLAN-005
- **Дата создания:** 2026-09-22
- **Статус:** ✅ COMPLETED (Выполнен)
- **Цель:** Убрать с экрана теста все «подсказки» (название теста, уровень сложности, категория, тема) и сделать интерфейс минималистичным и аккуратным — без шума и отвлекающих элементов.

---

## 📌 Чек-лист реализации

### ✅ Шаг 1: Удаление подсказок (`static/index.html`)
- Экран вопроса:
  - Удалить бейдж названия теста `#q-test-title` (`test-suite-tag`).
  - Удалить плашку уровня `#q-level-badge` с `#current-eval-label` («B1 (Intermediate)»).
  - Удалить блок `#question-meta` с тегами `#q-category` («Grammar») и `#q-topic` («Present Perfect vs Past Simple»).
  - Удалить «💡 Подсказка: Выберите один...» (`#card-footer-tip`).
  - Оставить: `#q-counter` («Вопрос 2 из ~14») + таймер + прогресс-бар + текст вопроса + варианты.
- Экран результата:
  - Удалить тег `#result-test-name` («CEFR General Adaptive Test») из шапки.
  - Оставить один заголовок «Тестирование завершено» + форма ФИО/телефон.

### ✅ Шаг 2: Минималистичное оформление (шум → чистота)
- Welcome-экран:
  - Убрать `hero-pill` («✨ Компьютерное адаптивное тестирование (CEFR)»).
  - Убрать декоративную сетку `#features-grid` (3 карточки-фичи) — маркетинговый шум.
  - Убрать `#header-status` («AI Adaptive Engine») из шапки — остаётся только логотип.
  - Сократить `hero-subtitle` до одной короткой строки.
  - Каталог тестов: убрать с карточек бейджи уровня и режима (`test-card-level`, `test-card-mode`); оставить иконку, название, краткое описание, время/вопросы; выбор подсвечивать рамкой + галочкой.
- Кнопка старта: вместо «Пройти: <длинное название>» — короткое «Начать тест».

### ✅ Шаг 3: `static/js/app.js`
- Удалить лакапы и записи для удалённых элементов: `qTestTitle`, `qLevelBadge`, `currentEvalLabel`, `qCategory`, `qTopic`, `resultTestName`.
- `renderQuestion`: убрать вывод уровня/категории/темы.
- `renderResult`: убрать запись названия теста (заголовок статичный в HTML).
- `startTest`: убрать запись `qTestTitle`/`resultTestName`.
- `renderTestCards`/`updateStartButtonForTest`: упростить разметку карточек и тексты кнопки/подсказки.
- `currentTestTitle` остаётся во внутреннем состоянии (используется только в память), вывода больше нет.

### ✅ Шаг 4: `static/css/style.css`
- Подогнать стили под новую «пустую» разметку: шапка вопроса (одна строка: счётчик + таймер), вопрос без меты, карточки каталога чище, заголовки велком-экрана компактнее.
- Мёртвые классы (`.q-level-badge`, `.category-tag`, `.topic-pill` и т.п.) не удаляем — безвредны, вычистим отдельной задачей (это снижает риск).

### ✅ Шаг 5: Документация
- `agents/tasks/active_task.md` (TASK-007), `agents/STATUS.md`, журнал сессии 12, план → COMPLETED.

---

## 🧪 План верификации
1. `python agents/tools/check_integrity.py` → 100% OK.
2. `python agents/testing/test_api_http.py` → ALL PASSED (бэкенд не меняется).
3. `python -m backend.test_simulation` → 3/3.
4. Live smoke (uvicorn): в HTML/JS отсутствуют `q-category`, `q-topic`, `q-level-badge`, `q-test-title`, `result-test-name`, `features-grid`, `currentEvalLabel`.

## 📁 Затрагиваемые файлы
- `static/index.html`, `static/js/app.js`, `static/css/style.css`
- `agents/tasks/active_task.md`, `agents/STATUS.md`, `agents/history/` (новый журнал)

## ⚠️ Риски и меры
- Только фронтенд; API/CAT/lead store/Telegram не трогаются.
- Удаление DOM-элементов идёт синхронно с JS (лакапы и записи), чтобы не было null-ошибок.
- `#q-counter` (счётчик вопросов) сохраняется как нужная ориентация по прогрессу; таймер сохраняется (нужен бэку для времени на вопрос).