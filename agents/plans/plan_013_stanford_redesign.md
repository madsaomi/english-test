# 📋 PLAN-013: Редизайн UI под Stanford Language Center

**Статус:** ✅ COMPLETED (ожидает коммита)
**Дата:** 2026-09-23
**Утверждено:** «да» + «Stanford Language Center» как бренд

## Контекст
Пользователь передал mock `stanford-english-test/` (yellow/black/cream, DM Sans + Playfair, лендинг). Задача: перенести дизайн в `static/`, сохранить живой API-флоу (50Q, text, contact, Telegram), затем удалить mock.

## Шаги

| # | Шаг | Файлы | Статус |
|---|---|---|---|
| 1 | `logo.png` → `static/logo.png` | asset | ✅ |
| 2 | HTML: header Stanford, hero/benefits/levels/about, catalog, question, result — **все id app.js сохранены** | `static/index.html` | ✅ |
| 3 | CSS: палитра `#ffba08/#101010/#fffdf7`, шрифты DM Sans + Playfair, полный редизайн экранов | `static/css/style.css` | ✅ |
| 4 | `app.js` — без изменений (логика/API/ошибки нетронуты) | `static/js/app.js` | ✅ |
| 5 | meta/OG/title → Stanford Language Center | `static/index.html` | ✅ |
| 6 | Верификация: integrity, api_http, multi_suites, live smoke :8000 (50/50) | — | ✅ |
| 7 | Удалить `stanford-english-test/` | — | ✅ |
| 8 | **Упрощение по фидбеку:** убрать лендинг (nav/hero/benefits/levels/about), оставить только header + welcome/question/result + footer | `static/index.html`, `static/css/style.css` | ✅ |
| 9 | **Полировка UI:** logo-chip в cream, жёлтая линия header, карточки options, убрать 50 точек (только bar), fix `--accent-cyan` → `.gap-blank`, формы/кнопки | `static/index.html`, `static/css/style.css`, `static/js/app.js` (1 строка) | ✅ |
| 10 | **Research pass (Babbel/EF SET/NN-g/mobile exam):** welcome-meta chips, aria-progressbar, focus management, tap ≥52px, single-test card, role=button options | `static/index.html`, `static/css/style.css`, `static/js/app.js` | ✅ |
| 11 | **Фидбек:** убрать текстовые подсказки («Выберите один вариант…», «Клавиши A–D…»); welcome-copy короче (`hero-subtitle`, `action-note`) | `static/index.html` (+ CSS/JS без hints) | ✅ |
| 12 | **Visual pass (только визуал):** premium cards/shadows, hero glow + highlight bar, meta-chip accent, option-key squares, black timer, black footer + yellow border, brand wordmark ≥640px, eyebrow rules | `static/css/style.css`, `static/index.html` | ✅ |
| 13 | **Упростить welcome:** убрать `hero-subtitle`, `action-note`, видимый каталог («Выберите тест»); `#test-cards-grid` скрыт через `.is-hidden` (id нужен app.js) | `static/index.html`, `static/css/style.css` | ✅ |
| 14 | Верификация: integrity, api_http, live index | — | ✅ |
| 15 | Коммит + push | — | ⏳ ждать «да» |

## Верификация
- [x] Все критичные id на месте (21/21 + `timer-badge`)
- [x] Лендинг-секции убраны; CSS от них вычищен
- [x] Полировка: logo-chip, без 50 точек, `gap-blank`, единая ширина карточек
- [x] Research: chips, aria progress, focus, tap-targets, single card, keyboard options (role=button)
- [x] Подсказки options-hint/keyboard-hint отсутствуют в HTML/CSS/JS
- [x] Welcome-copy короче: «Узнайте уровень…», «Без регистрации»
- [x] `check_integrity` 100%
- [x] `test_api_http` 13/13
- [x] `test_multi_suites` 4/4
- [x] `test_review_feature` PASSED
- [x] Live :8000 — index/css/logo/app.js 200, full run 50/50 score 100, stale 404, ids OK, no hints
- [x] Папка mock удалена
