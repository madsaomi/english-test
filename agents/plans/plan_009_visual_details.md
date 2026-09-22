# 📋 План PLAN-009: Визуальные детали и характер бумажного стиля (пункты 1–13)

- **Дата:** 2026-09-22
- **Статус:** ✅ COMPLETED (Выполнен)
- **Автор:** opencode (opencode/big-pickle)
- **Код до одобрения НЕ пишется.**

---

## 🎯 Общая цель
Довести интерфейс до «продуманной детальности»: микро-полировка типографики и состояний (1–6), декоративный характер бумажного стиля (7–10) и навигационные состояния (11–13). Только HTML/CSS/JS фронтенд, бэкенд не трогается.

---

## 📌 Исходные факты (уже исследовано)
- `static/index.html` (~155 строк), `static/css/style.css` (~900 строк после PLAN-008), `static/js/app.js` (~570 строк).
- Таймер: `#timer-text` в `.timer-badge`; прогресс: `.progress-bar-fill#progress-fill`; рендер вопроса: `renderQuestion()` + класс `.q-enter`; выбор варианта: `selectOption()` → `setTimeout(350)` → следующий вопрос.
- Скелетоны уже есть (`renderSkeletons`, `.skeleton-line`); карточки рендерятся `renderTestCards()` без fade-in.
- Экран успеха: `#tg-success-message` с анимированной SVG-галочкой; `.result-card` без overflow-hidden (нужен для watermark).
- Переменные: `--primary #4f46e5`, `--accent-rose #be123c`, `--bg-color #f3f1ec`, радиусы/тени в `:root`.
- `og:image`/`og:url` — **вне scope** (нужен прод-домен и ассет).
- PDF-сертификат — отменён навсегда (даже не упоминать).

---

## 🛠️ Шаги реализации

### ✅ Шаг 1 (микро №1): Табличные цифры таймера
- CSS: `.timer-badge { font-variant-numeric: tabular-nums; font-feature-settings: 'tnum'; }` — цифры MM:SS не «скачут» при смене.

### ✅ Шаг 2 (микро №2): Красивые переносы
- CSS: `text-wrap: balance` для `.hero-title`, `.question-text`, `.result-title`, `.catalog-title`, `.tg-box-header h3`, `.logo-text` (где уместно). Браузеры без поддержки игнорируют — безопасно.

### ✅ Шаг 3 (микро №3): `prefers-reduced-motion`
- Один глобальный media-query в конце CSS: при `prefers-reduced-motion: reduce` — `animation-duration/transition-duration → 0.01ms`, `animation-iteration-count → 1`, `scroll-behavior → auto` (базовое правило из UAG). Функциональность не ломается: спиннер/скелетон останутся видимыми (первый кадр отрисуется), тост будет показан мгновенно.

### ✅ Шаг 4 (микро №4): Shimmer прогресс-бара
- CSS: `.progress-bar-fill::after` — тонкий бегущий белый блик (`linear-gradient` прозрачный→белый 35%→прозрачный, `translateX` по keyframes `progressShimmer` ~1.8s infinite). `overflow:hidden` уже на контейнере; `position:relative` на fill.

### ✅ Шаг 5 (микро №5): Fade-in карточек после скелетонов
- CSS: `.test-card` — `animation: cardIn 0.35s ease backwards`; задержки через `nth-child(1..4) { animation-delay: 0/50/100/150ms }` — карточки мягко появляются вместо резкой замены скелетонов. Ключевые кадры: opacity 0→1, translateY 8px→0.

### ✅ Шаг 6 (микро №6): Подтверждение выбранного варианта
- CSS: `.option-card.selected` дополнительно `animation: optionConfirm 0.3s ease;` — короткая «волна»: лёгкий scale(1.01)→1 + вспышка индиго-фона, пока идёт пауза 350ms до следующего вопроса. На `:active` существующие стили не трогаем.

### ✅ Шаг 7 (характер №7): Rubber-stamp «Тест пройден»
- HTML (в `#tg-success-message` или рядом, при показе успеха): inline-SVG/HTML-штамп — двойная рамка (внешняя 3px, внутренняя пунктир), текст `ПРОЙДЕНО` + мелкий `LinguaAdaptive`, поворот −8°, цвет `--primary` с opacity 0.9, `mix-blend-mode: multiply` (эффект краски на бумаге).
- CSS + анимация «удара штампа»: scale(1.7→1) + opacity(0→0.9) за 250ms при снятии `.hidden`.
- Размещение: под SVG-галочкой/текстом успеха, по центру. Не мешает тексту (margin-top небольшой).

### ✅ Шаг 8 (характер №8): Скрепка на hero-карточке
- HTML: декоративный inline-SVG paperclip, `position:absolute; top:-14px; right:28px; transform: rotate(12deg);` на `.hero-card` (у неё уже `position:relative; overflow:hidden` — **нужно** снять overflow:hidden или вынести скрепку, иначе обрежется; решение: скрепку разместить **внутри** верхнего края, `top:12px`, либо убрать `overflow:hidden` — у hero нет нужды в hidden кроме градиентов, проверить `gradient-text`).
- Решение по плану: скрепка внутри карточки (`top:14px; right:22px`), overflow не трогаем. `aria-hidden="true"`, `pointer-events:none`, opacity 0.55, обводка `--text-muted`.
- Дублируется в HTML один раз (элемент на экране welcome только один).

### ✅ Шаг 9 (характер №9): Линовка блока вариантов
- CSS: вертикальная «поле тетради» — на `.question-card` слева от контента тонкая линия `rgba(190,18,60,0.25)` (чернильно-розовая, как в тетради): `border-left: 2px solid` на внутреннем контенте **или** `box-shadow: inset 18px 0 0 -16px rgba(190,18,60,0.28)` — выбираем inset-shadow (не ломает layout, не требует HTML).
- Проверить на мобильном (≤768px padding 1.25rem) — линия не должна упираться в текст; inset от края карточки, текст имеет padding — ок.

### ✅ Шаг 10 (характер №10): Водяной знак на result-экране
- CSS: `.result-card { position:relative; overflow:hidden; }` + `.result-card::before` — крупный SVG/текст «CAT» (или галочка) `font-family: var(--font-heading)`, размер ~180px, opacity 0.04, поворот −18°, по центру, `pointer-events:none; user-select:none; z-index:0`.
- Контент result-card должен быть выше: `z-index:1` для прямых children (или `isolation`). Проверить, что `.telegram-action-box` и форма кликабельны (pointer-events на псевдоэлементе отключены — ок).

### ✅ Шаг 11 (навигация №11): Точки прогресса
- HTML: `<div class="progress-dots" id="progress-dots" aria-hidden="true"></div>` между topbar и progress-bar.
- JS в `renderQuestion()`: строить `q.total_estimated` точек (или минимум 12); классы: `.done` (индекс < number-1), `.current` (=== number-1), остальные пустые. Пересоздание каждый вопрос — просто и надёжно.
- CSS: flex, gap 6px, точки 7px, border-radius 50%; `done` — `rgba(79,70,229,0.35)`, `current` — `--primary` с scale 1.15, pending — outline `rgba(28,25,23,0.15)`; transition 0.2s.
- `aria-hidden` — вспомогательная декорация (счётчик уже есть в `#q-counter`).

### ✅ Шаг 12 (навигация №12): Нажатие на тест-карточку
- CSS: `.test-card:active:not(.skeleton) { transform: translateY(-2px) scale(0.98); }` — «вдавливание» при тапе; к hover-состоянию не цепляется.

### ✅ Шаг 13 (навигация №13): Пустое состояние каталога
- JS: в `renderTestCards()` при `tests.length === 0` — рендерить `.catalog-empty` (бумажная записка: «Тесты временно недоступны» + подпись), вместо пустой сетки.
- CSS: `.catalog-empty` — центр, пунктирная рамка как на бланке, muted-текст.

---

## ⛔ Вне scope
- `og:image`/`og:url` (домен), PDF (отменён), бэкенд/API/CAT/Telegram.
- Тёмная тема, i18n, новые экраны.

## ✅ План верификации
1. `python agents/tools/check_integrity.py` → 100%.
2. `python agents/testing/test_api_http.py` → 10/10.
3. `python -m backend.test_simulation` → 3/3.
4. Live smoke (uvicorn :8764):
   - CSS: `tabular-nums`, `text-wrap: balance`, `prefers-reduced-motion`, `progressShimmer`, `cardIn`, `optionConfirm`, `stamp`, `paperclip`, `progress-dots`, `catalog-empty`, `.test-card:active`, watermark.
   - HTML: paperclip SVG, `#progress-dots`, stamp markup.
   - JS: генерация точек в `renderQuestion`, пустое состояние в `renderTestCards`.
5. Ручной прогон: таймер не дрожит, карточки всплывают после скелетонов, штамп «ударяется» на успехе, точки бегут по вопросам.

## 📚 Документация после выполнения
- `agents/tasks/active_task.md` → TASK-011, COMPLETED.
- `agents/STATUS.md` → фаза и строка веб-интерфейса.
- `agents/history/session_2026-09-22_16_visual_details.md`.
- `agents/plans/plan_009_visual_details.md` → COMPLETED.
- Коммит + пуш — только после отдельного «да» пользователя.
