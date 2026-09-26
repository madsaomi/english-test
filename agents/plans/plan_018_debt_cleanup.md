# 📋 PLAN-018: Закрытие остатка техдолга (OG-превью, метрики, time_spent, мёртвый CSS)

**Статус:** ✅ COMPLETED (ожидает коммита)
**Дата:** 2026-09-26
**Утверждено:** «да» (пользователь выбрал «Закрыть весь остаток долга»)

## 📋 Шаги

| # | Шаг | Файлы | Статус |
|---|---|---|---|
| 1 | **OG-превью:** абсолютные `og:url` / `og:image` / `twitter:*` через `location.origin` (работает на любом домене без правки сборки); `twitter:card=summary_large_image` | `static/index.html`, `static/js/app.js` | ✅ |
| 2 | **Метрики:** `active_sessions` скрыт по умолчанию, флаг `SHOW_INTERNAL_METRICS` | `backend/config.py`, `backend/main.py`, `.env.example` | ✅ |
| 3 | **`time_spent_seconds`:** валидация диапазона `0..3600` → 422 на мусор | `backend/models.py` | ✅ |
| 4 | **Мёртвый CSS:** удалить `.option-key` (основной + mobile + theme-dark) | `static/css/style.css` | ✅ |
| 5 | **Тесты:** `test_health_hides_internal_metrics_by_default`, `test_time_spent_out_of_range_rejected`, проверка OG-метов | `agents/testing/test_api_http.py`, `agents/tools/check_integrity.py` | ✅ |
| 6 | **Документация:** BUG_006 не нужен (не баг, а долг) → обновить `STATUS.md`, этот план | `agents/` | ✅ |
| 7 | Верификация: integrity, api_http, multi_suites, review, live smoke | — | ✅ |
| 8 | Коммит + push | — | ⏳ ждать «да» |

## 🔒 Инварианты

- 22 критичных id, 7 эндпоинтов и их контракты не меняются
- Никаких новых зависимостей
- `/api/health` остаётся **200** и по-прежнему отдаёт `status`, `total_questions_in_bank`
- Тесты, гоняющие 50 POST подряд, не должны ловить 429 (лимит отключён через env)
- Антипаттерн №1: `correct_option`/`correct_text` по-прежнему не уходят в клиент

## ✅ Фактическая верификация (2026-09-26)

| Проверка | Результат |
|---|---|
| `check_integrity.py` | **100%**, раздел 6 = **15 security-чеков** (было 11) |
| `test_api_http.py` | **19/19** PASSED (было 17) |
| `test_multi_suites.py` | 4/4 PASSED |
| `test_review_feature.py` | PASSED |
| Live: `/api/health` | `active_sessions` **отсутствует** ✅ |
| Live: полный прогон | **50/50**, score 100, level Advanced |
| Live: 22 критичных id | все на месте |
| Live: OG-меты | `og:url=/`, `og:image=/logo.png`, `twitter:card=summary_large_image` (JS абсолютизирует через `location.origin`) |
| Live: CSS | `option-key` = **0**, скобки сбалансированы, `.option-card.selected .option-text` корректно перекрывает базовое правило |
| Временный сервер | погашен, порт 8765 свободен |

## ⚠️ Регрессия, пойманная и исправленная по ходу

Массовое удаление мёртвого CSS регуляркой повредило **два селектора**:
`.option-card:hover .option-key, .option-card.selected .option-text {…}` и
`body.theme-dark body.theme-dark .option-card:hover .option-key, …`.

Исправлено: восстановлен базовый `.option-text`, а правило
`.option-card.selected .option-text { padding-right: 34px }` перенесено **после** него
(иначе базовое правило перекрывало бы отступ под галочку). Проверено скобками и порядком.

**Урок:** массовое редактирование CSS регулярками опасно — после любой такой правки
обязательна проверка баланса скобок **и** порядка перекрывающихся правил.
