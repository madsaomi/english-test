# 📋 PLAN-015: Безопасность экспорта лидов + персистентность лидов в проде

**Статус:** ✅ COMPLETED (ожидает коммита)
**Дата:** 2026-09-26
**Утверждено:** «делай» (пользователь подтвердил приоритет дыр №1 и №2)

## 🔍 Найденные дыры (аудит 2026-09-26)

| # | Дыра | Файл | Риск |
|---|---|---|---|
| 1 | `GET /api/export/leads` без авторизации — отдаёт имена, телефоны, @username, результаты | `backend/main.py:333` | 🔴 PII публично |
| 2 | `data/` в `.dockerignore` + нет volume на Railway → лиды исчезают при каждом рестарте/деплое | `.dockerignore:22`, `railway.json` | 🔴 Потеря данных |

## 📋 Шаги

| # | Шаг | Файлы | Статус |
|---|---|---|---|
| 1 | `config.py`: `EXPORT_API_KEY`, `DATA_DIR` из env | `backend/config.py` | ✅ |
| 2 | `lead_store.py`: использовать `DATA_DIR` из config (настраиваемый путь) | `backend/lead_store.py` | ✅ |
| 3 | Закрыть `/api/export/leads`: заголовок `X-API-Key`; если ключ не задан → 503 | `backend/main.py` | ✅ |
| 4 | `export_results.py`: передавать `X-API-Key` из env/аргумента | `agents/tools/export_results.py` | ✅ |
| 5 | `railway.json`: volume для `/app/data` | `railway.json` | ✅ |
| 6 | `.env.example`: `EXPORT_API_KEY`, `DATA_DIR` | `.env.example` | ✅ |
| 7 | Тесты: ключ в env + негативные кейсы (401/401/200) | `agents/testing/test_api_http.py` | ✅ |
| 8 | `check_integrity.py`: раздел 6 — security-чеки | `agents/tools/check_integrity.py` | ✅ |
| 9 | Документация: баг-репорт, runbook, STATUS, этот план | `agents/` | ✅ |
| 10 | Верификация: integrity, api_http, multi_suites, review, live smoke | — | ✅ |
| 11 | Коммит + push | — | ⏳ ждать «да» |

## 🔒 Инварианты

- `ClientQuestion` не получает `correct_option`/`correct_text` (антипаттерн №1)
- Никаких `time.sleep` (антипаттерн №2)
- Секреты только в `.env` (антипаттерн №4)
- Существующие 7 эндпоинтов и их контракты не меняются, кроме защиты `/api/export/leads`
- Frontend (`static/`) не трогаем в этом плане

## ✅ Верификация

1. `python agents/tools/check_integrity.py` → 100% + новый раздел 6
2. `python agents/testing/test_api_http.py` → 14 PASSED (добавлен `test_export_requires_api_key`)
3. `python agents/testing/test_multi_suites.py` → 4/4
4. `python agents/testing/test_review_feature.py` → PASSED
5. Live smoke :8000 → 50/50, `GET /api/export/leads` без ключа → 401

## ✅ Фактическая верификация (2026-09-26)

| Проверка | Результат |
|---|---|
| `check_integrity.py` | 100% — включая новый **раздел 6** (7 security-чеков) |
| `test_api_http.py` | **14/14** PASSED (добавлен `test_export_leads_requires_api_key`) |
| `test_multi_suites.py` | 4/4 PASSED |
| `test_review_feature.py` | PASSED |
| Live smoke :8000 | 50/50, score 100, level Advanced |
| Live `/api/export/leads` без ключа | 200 — ⚠️ сервер запущен **до** правок, требуется рестарт uvicorn |

**Важно:** локальный сервер на :8000 работает на старом коде. После рестарта
`uvicorn` ожидаемое поведение: без `X-API-Key` → 401 (или 503, если ключ не задан в `.env`).

**Известный долг (не в этом плане):** дыры №3–№9 из аудита — rate limiting, CORS `*`
в проде, обход анти-спуфинга `initData`, лимит `time_spent_seconds`, `active_sessions`
в `/api/health`, `og:url`.

1. Переменная `EXPORT_API_KEY=<случайная строка>` (Variables)
2. Volume: имя `lead-data`, mount path `/app/data` (Volumes)
3. Старую копию лидов (если была) перенести в volume вручную
