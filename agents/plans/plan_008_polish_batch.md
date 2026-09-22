# 📋 План PLAN-008: Пакетная полировка UI (задачи 4, 6, 7, 8, 10, 12, 13, 14, 15 + гигиена CSS)

- **Дата:** 2026-09-22
- **Статус:** ✅ COMPLETED (Выполнен)
- **Автор:** opencode (opencode/big-pickle)
- **Код до одобрения НЕ пишется.**

---

## 🎯 Общая цель
Разом закрыть все оставшиеся визуальные задачи из списка пользователя (кроме вынесенных ниже), не трогая бэкенд: таймер, скелетоны каталога, спиннеры в кнопках, SVG-иконки вместо эмодзи, маска телефона, микро-стили (selection/scrollbar/focus), favicon/OG, тост вместо alert, контейнер 720px и вычистка мёртвого CSS (~50% файла).

---

## 📌 Исследование (ключевые факты)
- Таймер — **секундомер вверх** (`app.js:240-262`), timeout-а нет; в HTML статичный `00:30` (`index.html:62-64`), класс `.timer-icon` без стилей.
- Каталог: `loadTestSuites()` (`app.js:106-119`) без loading-state; `#test-cards-grid` пустая (`index.html:41-43`); спиннеров нет.
- Кнопки сети: `#btn-start-test` (restore в `finally` ✓), `#btn-send-tg` (восстановление **только в catch** — баг: после успеха на 2-м прогоне текст «Отправка...» остаётся, `app.js:444-445,464-465,394`).
- Эмодзи в HTML: `⏱` (:62), `📱` (:90), `✈️` (:115), `🔄` (:133); в JS: `✈️` при restore (`app.js:475`), `🎯💼⚡🌱📝⏱` в fallback-карточках (`app.js:130-189`); `→`/`✓` — текстовые символы, оставляем.
- Телефон: `index.html:104-105`, без маски/`inputmode`/`maxlength`; валидация `^\+?[\d\s\-()]{10,}$` (`app.js:435-438`).
- Мёртвый CSS: **~16 групп / ~750 строк из 1493** (Review 316, Skills 67, Recommendations 36, Result-бейджи 86, Features 43, и пр.) — нет ни в HTML, ни в JS.
- `alert()` — ровно 3 (`app.js:286,380,473`); тостов нет.
- Контейнер: `.app-container { max-width: 900px }` (`style.css:79`); `.container` не существует; media ≤768px контейнер не трогает → 720px безопасно.
- Нет: `::selection`, `::-webkit-scrollbar`, `:focus-visible`, favicon, `og:*`; изображений в репо нет.
- viewport: `maximum-scale=1.0, user-scalable=no` (`index.html:5`) — а11y-проблема.

---

## 🛠️ Шаги реализации

### ✅ Шаг 1 (№4): Таймер — оставить секундомер, привести в порядок
- `index.html:64`: статичный `00:30` → `00:00` (до первого рендера).
- `⏱` → SVG clock (см. шаг 4), класс `.timer-icon` — стилизовать под бейдж.
- **Countdown с авто-ответом НЕ делаем** — меняет семантику CAT (сервер учитывает только `time_spent_seconds`); если нужен лимит — отдельная задача с бэкендом.

### ✅ Шаг 2 (№6): Скелетоны каталога
- В `#test-cards-grid` при старте рендерить 4 скелетон-карточки (`.test-card.skeleton` + пульс placeholder-полос).
- В `loadTestSuites()` после fetch (успех и fallback) скелетоны заменяются реальным рендером (`renderTestCards`/`renderDefaultTestCards`).
- CSS: `@keyframes skeletonPulse` (opacity 0.5↔1), классы `.skeleton-line`, размеры совпадают с `.test-card`.

### ✅ Шаг 3 (№7): Спиннеры в кнопках + починка restore
- CSS: `.btn-spinner` — вращающийся SVG-circle (border), правило пока кнопка `.is-loading`.
- `#btn-start-test`: вместо plain-text «Запуск теста...» — `<span class="btn-spinner"></span> Запуск теста...` (класс `is-loading` на кнопку).
- `#btn-send-tg`: то же для «Отправка в Telegram...»; **багфикс**: сохранять `originalTgBtnContent` при загрузке и восстанавливать его в `renderResult()` (не только `disabled=false`), чтобы 2-й прогон не начинался со «Загрузка...».
- Синхронные `#btn-restart-test` и выбор варианта — без спиннера.

### ✅ Шаг 4 (№8): SVG-иконки вместо эмодзи
- В HTML заменить на inline-SVG (currentColor, 18-20px): `⏱` (часы, шаг 1), `📱` (телефон/telegram-badge, белый на `#0088cc`), `✈️` (paper-plane в кнопке), `🔄` (refresh в «Пройти заново»).
- В `app.js`: `✈️` при restore кнопки → та же SVG-строка (вынести в `const ICON_TELEGRAM`); fallback-карточек `🎯💼⚡🌱📝⏱` → 4-6 нейтральных inline-SVG (таргет, брифинг, молния, рост, документ, часы) — только внутри `renderTestCards`-путей, данные API не трогаем.
- `→` и `✓` остаются текстовыми (стабильны на всех платформах).

### ✅ Шаг 5 (№10): Маска телефона
- `index.html`: `inputmode="tel"`, `maxlength="18"` на `#input-user-phone`.
- `app.js`: input-маска по шаблону плейсхолсера `+7 (999) 000-00-00` (только российские; при вводе без `+`/`8` — авто-проставление `+7`; Backspace стирает форматируемые символы).
- Валидация: после маски — минимум **11 цифр** и префикс `+7` (текущий regex ослабить до проверки цифр, чтобы маска не конфликтовала); сообщение «Введите корректный телефон» не меняем.
- Маска НЕ ломает существующую авто-очистку ошибки по `input` (`app.js:80-89`).

### ✅ Шаг 6 (№12): Микро-стили
- `::selection` — индиго-фон/белый текст.
- `::-webkit-scrollbar` + `scrollbar-color/width` — тонкая бумажная полоса, thumb `rgba(28,25,23,0.25)`.
- `:focus-visible` — обводка `2px` `var(--primary)` с offset для `.btn`, `.option-card`, ссылок, инпутов (input-`:focus` не трогаем, чтобы не задвоить).
- Доступность (в рамках №13): из viewport убрать `maximum-scale=1.0, user-scalable=no`.

### ✅ Шаг 7 (№13): Favicon + OG
- Создать `static/favicon.svg` — простая SVG в бумажном стиле (скруглённый лист `#f3f1ec` + индиго-галочка/«A»), без внешних ассетов.
- `<head>`: `<link rel="icon" type="image/svg+xml" href="/favicon.svg">`.
- `og:title`, `og:description`, `og:type=website`, `og:locale=ru_RU`, `twitter:card=summary` — текстовые, **без `og:image`/`og:url`** (нет прод-домена и картинки — добавим отдельной задачей, когда будет домен).
- Проверить, что FastAPI отдаёт `/favicon.svg` из `static/` (StaticFiles — ожидаемо да; smoke подтвердит).

### ✅ Шаг 8 (№14): Тост вместо alert
- HTML: `<div id="toast" class="toast hidden" role="alert" aria-live="assertive"></div>` (в конец `body`).
- CSS: `.toast` — фикс. снизу по центру, frosted-бумага, `border-left: 4px` (error — `#be123c`, info — `var(--primary)`), fadeIn/slideUp + авто-hide.
- `app.js`: `showToast(message, type='error')` (перекрывает предыдущий таймер, `hidden` через ~4с); заменить все 3 `alert()` на `showToast(...)`.
- Успешная отправка формы и валидация полей — как сейчас (inline), тост только для сетевых ошибок.

### ✅ Шаг 9 (№15): Контейнер 720px
- `style.css:79`: `.app-container max-width: 900px` → `720px`.
- Проверить визуально: карточка вопроса, каталог (2 колонки ≤768 → 1), форма, success. Media-query правок не требуется.

### ✅ Шаг 10: Гигиена — удалить мёртвый CSS (~750 строк)
Удалить правила (и связанные media/@keyframes), подтверждённые grep-ом как отсутствующие в HTML/JS:
- `.header-status`, `.status-dot`, `@keyframes pulse-dot`
- `.hero-pill`
- `.features-grid/.feature-item/.feature-icon/.feature-body` (+ media)
- `.test-meta-hint`
- `.q-level-badge`, `.badge-dot`
- `.question-meta`, `.category-tag`, `.topic-pill`
- `.card-footer-tip`
- `.result-top-badge-row/.result-test-tag/.test-suite-tag/.result-celebration-badge/.result-header/.cefr-badge-large/.cefr-code/.cefr-level-tag` (+ media)
- `.result-summary/.score-pill-row/.score-pill` (+ media)
- `.section-title-wrap/.skills-grid/.skill-*` (+ media)
- `.weak-topics-box/.weak-tags/.weak-tag`
- `.recommendations-box/.recommendations-list`
- весь блок Review (`.review-*`, `.gap-highlight`, `.explanation-*`, `.review-empty-state`, `.empty-icon`, dead `@media (min-width:600px)`)
- `.catalog-badge`, `.catalog-subtitle`
- `.test-card-badges/.test-card-level/.test-card-mode`
- **Перед удалением** — финальный grep по каждому классу; `.success-icon` в CSS нет — ничего не удалять «вслепую».
- Ожидание: ~1493 → ~750 строк, живые стили не меняются.

---

## ⛔ Вне scope (намеренно НЕ делаем)
- Countdown-таймер с авто-ответом (нужен бэкенд/продуктовое решение).
- `og:image` / `og:url` (нет домена и ассета).
- Меню/логика теста, API, CAT, Telegram, lead store — не трогаем.
- Замена иконок, приходящих из API как строки (`test.icon`) на сервере.

---

## ✅ План верификации
1. `python agents/tools/check_integrity.py` → 100%.
2. `python agents/testing/test_api_http.py` → 10/10 PASSED.
3. `python -m backend.test_simulation` → 3/3 PASSED.
4. Live smoke (uvicorn :8764), проверить в ответах:
   - `/` → `00:00`, `inputmode="tel"`, `maxlength`, нет эмодзи `⏱📱✈️🔄`, есть `og:title`, `favicon.svg`, `toast`, нет `user-scalable=no`.
   - `/css/style.css` → нет `.review-section`/`.skills-grid`/`.hero-pill` и др.; есть `.skeleton`, `.btn-spinner`, `.toast`, `::selection`, `:focus-visible`, `max-width: 720px`.
   - `/js/app.js` → `showToast`, маска, `skeleton`, нет `alert(`.
   - `/favicon.svg` → 200.
5. Ручной прогон в браузере: скелетоны → карточки; спиннер при «Начать тест» и «Отправка»; маска телефона; тост при оффлайн-ошибке; 2-й прогон теста — кнопка отправки без «Загрузка...».

## 📚 Документация после выполнения
- `agents/tasks/active_task.md` → TASK-010, COMPLETED.
- `agents/STATUS.md` → обновить фазу и строку веб-интерфейса.
- `agents/history/session_2026-09-22_15_ui_batch_polish.md`.
- `agents/plans/plan_008_polish_batch.md` → COMPLETED.
- Коммит + пуш — только после отдельного «да» пользователя.
