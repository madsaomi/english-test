# 📊 Текущий статус проекта (STATUS.md)

**Последнее обновление:** 2026-09-26 (UTC+5)  
**Ответственный агент:** opencode (space-bunny-free)  
**Текущая фаза:** PLAN-017 (Rate limiting + CORS + анти-спуфинг) — COMPLETED, ждёт коммита.  
Закрыто ранее: PLAN-016 (UI-полировка), PLAN-015 (PII + персистентность).

---

## 🚦 Состояние подсистем

| Компонент | Статус | Комментарий |
|---|---|---|
| **Экосистема «Второго Мозга» (`agents/`)** | 🟢 Готово | 13 разделов: правила, антипаттерны, шаблоны, ADR, баги, деплой, траблшутинг |
| **Git-версионирование (`.git`)** | 🟢 Готово | Последние коммиты: `0b0a03a` (UI), `d170009` (security); рабочее дерево проверяется |
| **Окружение Python & зависимости** | 🟢 Готово | `fastapi`, `aiogram`, `uvicorn`, `pydantic`; без новых зависимостей в PLAN-017 |
| **Банк вопросов & Каталог тестов (`tests_data/`)** | 🟢 Готово | Единственный набор `test_general_2026` (50 вопросов: 45 choice + 5 text) |
| **Rate limiting (PLAN-017)** | 🟢 Готово | Sliding window IP+User-Agent, только мутации `/api/*`; `429` + `Retry-After`; 60/мин по умолчанию; настраивается env |
| **Анти-спуфинг (PLAN-017)** | 🟢 Готово | `tg_user_id` без подписанной `tg_init_data` → `403`; id берётся только из подписи |
| **CORS (PLAN-017)** | 🟢 Готово | `IS_CORS_WILDCARD` + громкий WARNING на старте с примером продакшен-значения |
| **Защита PII (PLAN-015)** | 🟢 Готово | `/api/export/leads` закрыт `X-API-Key` (503 без ключа, 401 с неверным) |
| **Персистентность лидов (PLAN-015)** | 🟢 Готово | `DATA_DIR` через env; Railway volume `lead-data` → `/app/data` (создать том в UI) |
| **Веб-интерфейс (`static/`)** | 🟢 Готово | PLAN-016: прогресс-бар, кольцо-таймер, ответы без букв, переключатель темы ☀️/🌙 |
| **Тесты & CI** | 🟢 Готово | `check_integrity` (100%, 11 security-чеков), `test_api_http` (**17/17**), `test_multi_suites` (4/4), `test_review_feature` — PASSED |

---

## 🎯 Что сделано в PLAN-017:
- [x] **Rate limiting:** sliding window по IP+User-Agent (X-Forwarded-For учитывается), только `POST/PUT/PATCH/DELETE` на `/api/*`, ответ `429` + `Retry-After`, чистка протухших бакетов (нет утечки памяти).
- [x] **Переменные:** `RATE_LIMIT_ENABLED`, `RATE_LIMIT_REQUESTS` (60), `RATE_LIMIT_WINDOW_SECONDS` (60) — документированы в `.env.example` с предупреждением про **CGNAT**.
- [x] **Диагностика при старте:** WARNING при wildcard CORS, при выключенном лимите, при отсутствии `EXPORT_API_KEY`; INFO с нормой лимита.
- [x] **Анти-спуфинг исправлен:** раньше `if payload.tg_init_data and IS_BOT_ENABLED` — поле можно было просто не отправить. Теперь при переданном `tg_user_id` подпись **обязательна** (403), id берётся только из подписанных данных.
- [x] **Тесты (17/17):** `test_rate_limit_blocks_burst` (10 POST → 429, ровно 10 успешных, GET не лимитируется), `test_tg_user_id_requires_valid_init_data` (403/403/200).
- [x] `check_integrity.py`: +4 чека (rate limit, анти-спуфинг, CORS-warning, документация переменных) → **11 security-чеков**.
- [x] `BUG_005_rate_limit_cors_antispoof.md` + раздел «Диагностика по логам» в `DEPLOYMENT_RUNBOOK.md`.
- [x] Live smoke :8765 — 50/50 (лимит не мешает), спуф `tg_user_id` → 403, burst 70 → 60 OK + 10×429.

## ⚠️ Известный долг
| # | Дыра | Риск |
|---|---|---|
| 1 | CGNAT: мобильные операторы делят IP — теоретически возможен ложный 429 | 🟡 mitigated (60/мин, UA в ключе, настраивается) |
| 2 | `/api/health` отдаёт `active_sessions` в прод | 🟡 утечка метрик |
| 3 | Нет лимита на `time_spent_seconds` (мусорные значения в статистике) | 🟡 |
| 4 | Нет `og:url`, `twitter:card=summary` вместо `large_image` | 🟡 превью в соцсетях |
| 5 | Мёртвый CSS `.option-key` в `style.css` (разметка не создаётся) | ⚪ косметика |
| 6 | Сессии in-memory → рестарт Railway = потеря прогресса | ℹ️ решение принято (не персистим) |

## 📌 Требуется вручную в Railway
```ini
ALLOWED_ORIGINS=https://<service>.up.railway.app
EXPORT_API_KEY=<python -c "import secrets; print(secrets.token_urlsafe(32))">
DATA_DIR=/app/data
RATE_LIMIT_ENABLED=true
```
Volume: `lead-data` → `/app/data`. Старую копию лидов (если была) перенести в том вручную.