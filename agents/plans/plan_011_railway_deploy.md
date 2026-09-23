# 📋 PLAN-011: Настройка деплоя на Railway

**Статус:** ✅ COMPLETED (код ожидает коммита после «да»)
**Дата:** 2026-09-23
**Утверждено пользователем:** «да» (2026-09-23)

## Контекст
Репо уже содержит валидный `railway.json` (Dockerfile + healthcheck `/api/health`) и `Dockerfile` с `${PORT:-8000}` и `COPY tests_data/` (фикс `6c8dc8b`). Нужно довести env/dockerignore/docs под Railway. Баны аккаунта Railway — risk-score, не код (аудит чистый).

## Шаги

| # | Шаг | Файлы | Статус |
|---|---|---|---|
| 1 | `.dockerignore`: исключить `.env`, `data/`, `exports/`, `.github/`, `*.docx`, `render.yaml`, `railway.json`, `docker-compose.yml` (не трогать `agents/` и `AGENTS.md` — их копирует Dockerfile) | `.dockerignore` | ✅ |
| 2 | `.env.example`: добавить `ALLOWED_ORIGINS=` | `.env.example` | ✅ |
| 3 | Runbook: раздел «Способ 3: Деплой на Railway» (проект, Variables, Generate Domain, проверка, restriction) | `agents/deployment/DEPLOYMENT_RUNBOOK.md` | ✅ |
| 4 | STATUS: фаза PLAN-011, строки подсистем | `agents/STATUS.md` | ✅ |
| 5 | Верификация: `check_integrity` + `test_api_http` + `test_multi_suites` + `test_review_feature` | — | ✅ |
| 6 | Коммит + push | — | ⏳ ждать «да» |

## Не меняется
- `railway.json`, `Dockerfile` — уже валидны
- Код бэкенда / фронтенда / тестов / `tests_data/`
- `render.yaml` — запасной вариант

## Верификация
- [x] `python agents/tools/check_integrity.py` — 100%
- [x] `python agents/testing/test_api_http.py` — 13/13
- [x] `python agents/testing/test_multi_suites.py` — 4/4
- [x] `python agents/testing/test_review_feature.py` — PASSED
- [x] Docker build context: `.env` не копируется; `agents/` и `AGENTS.md` остаются в COPY
