# 🔒 PLAN-033: H1-утечка is_correct + M2-минимизация PII в leads.json

**Статус:** ✅ COMPLETED
**Дата:** 2026-09-27
**Основание:** Аудит безопасности 2026-09-27 (agents/audits/audit_2026-09-27_full_security.md).
Решения владельца по пунктам H1 и M2 (самые ценные и безболезненные).

## 1. H1 — убрать `is_correct` из ответа `/api/test/answer`

Проблема: каждый ответ возвращает клиенту `is_correct` (backend/main.py:260, 309, 320, 329),
а фронтенд этот флаг **не читает** → скрипт перебором 4 вариантов собирает ключ ответов
за ~200 запросов.

| # | Шаг | Файл | Статус |
|---|---|---|---|
| 1 | Удалить поле `is_correct` из `AnswerResponse` | backend/main.py:258-263 | ✅ |
| 2 | Убрать `is_correct=…` в 3 местах формирования ответа | backend/main.py:307-309, 318-320, 327-329 | ✅ |
| 3 | Убрать неиспользуемую локальную переменную `is_correct` | backend/main.py:295 | ✅ |
| 4 | Тесты: `is_correct` больше не должен присутствовать в теле ответа (новая защита вместо использования) | agents/testing/test_api_http.py:104, 173, 535 | ✅ |
| 5 | `test_multi_suites.test_04`: регистр текстовых ответов проверяется финальным `correct_count` (49 vs 50), без чтения `is_correct` | agents/testing/test_multi_suites.py:105-133 | ✅ |
| 6 | `backend/test_e2e.py`: убрать `is_correct` из вывода; заодно починить телефон (998) и убрать невалидный `tg_user_id` (тест уже был сломан) | backend/test_e2e.py | ✅ |

## 2. M2 — минимизация PII в data/leads.json + атомарная запись

Факт: 106 лидов / 3.4 МБ / у каждого полный `review` на 50 вопросов с
`correct_option`/`correct_text`/`explanation` и `tg_user_id` — данные нигде не
используются (админу идёт только сводка; кандидату ничего; экспорт их не содержит).

| # | Шаг | Файл | Статус |
|---|---|---|---|
| 7 | `LeadRecord.to_dict()`: не сериализовать `result.review` (полный разбор) и `tg_user_id` | backend/lead_store.py:43-54 | ✅ |
| 8 | Атомарная запись: write → tmp → `os.replace` (защита от порчи при краше, BUG_004) | backend/lead_store.py:89-96 | ✅ |
| 9 | Одноразовый purge при старте: `_persist()` после загрузки переписывает файл без чувствительных полей (самоочистка старых данных) | backend/lead_store.py:87 | ✅ |
| 10 | `.gitignore`: добавить `data/leads.json.tmp` (временный файл атомарной записи) | .gitignore | ✅ |

## 3. Не трогаем (сознательно)
- `review` остаётся в **памяти** сессии (`/api/test/result/{id}`) — пока существует
  как источник для будущего экрана разбора в UI; на диск не пишется.
- Экспорт `/api/export/leads` не меняется (поля прежние).
- `format_compact_lead_card`, `format_unified_lead_card` не меняются.
- Остальные пункты аудита (M1/M3/M4/M5/L*) — последующие планы.

## 4. Верификация
- `python agents/testing/test_api_http.py` — 19/19 | `test_multi_suites` — 4/4
- `test_review_feature` PASSED | `check_integrity` — 100%
- `data/leads.json` после первого старта не содержит `review.*.correct_*` и `tg_user_id`
- Ответ `/api/test/answer` не содержит ключа `is_correct`