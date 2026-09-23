# 📋 PLAN-012: Диагностика и фикс 404 mid-test на Railway

**Статус:** ✅ COMPLETED (ожидает коммита)
**Дата:** 2026-09-23
**Утверждено пользователем:** «да» (2026-09-23)

## Контекст
На Railway после перезапуска контейнера клиент шлёт ответы со старым in-memory `session_id` → `POST /api/test/answer` 404 → generic-тост «Ошибка связи…». Лог подтверждён: `Starting Container` + серия `404 Not Found`. Вопрос 29 — случайность по времени.

## Шаги

| # | Шаг | Файлы | Статус |
|---|---|---|---|
| 1 | Helper `postAnswer`: читает JSON `detail`, классифицирует 404/400/5xx/network | `static/js/app.js` | ✅ |
| 2 | 404 «Сессия…» → тост + `resetToWelcome()` | `static/js/app.js` | ✅ |
| 3 | Retry ×1 только при network / 502 / 503 (не 4xx) | `static/js/app.js` | ✅ |
| 4 | `logger.warning` sid/qid на 404 answer | `backend/main.py` | ✅ |
| 5 | Верификация: integrity + api_http + multi_suites | — | ✅ |
| 6 | Коммит + push | — | ⏳ ждать «да» |

## Не меняется
- Движок, JSON тестов, схемы API, docker/railway конфиги
- Персист сессий (без volume на free Railway не спасает)

## Верификация
- [x] `check_integrity` — 100%
- [x] `test_api_http` — 13/13
- [x] `test_multi_suites` — 4/4
