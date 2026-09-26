# 📊 Текущий статус проекта (STATUS.md)

**Последнее обновление:** 2026-09-26 (UTC+5)  
**Ответственный агент:** opencode (space-bunny-free)  
**Текущая фаза:** PLAN-015 (Безопасность экспорта лидов + персистентность) — COMPLETED, ждёт коммита.

---

## 🚦 Состояние подсистем

| Компонент | Статус | Комментарий |
|---|---|---|
| **Экосистема «Второго Мозга» (`agents/`)** | 🟢 Готово | 13 разделов: правила, антипаттерны, шаблоны, ADR, баги, деплой, траблшутинг |
| **Git-версионирование (`.git`)** | 🟢 Готово | Инициализирован Git, настроен `.gitignore`, создан первый коммит |
| **Окружение Python & зависимости** | 🟢 Готово | `fastapi`, `aiogram`, `uvicorn`, `pydantic`; добавлен `httpx2` для TestClient |
| **Банк вопросов & Каталог тестов (`tests_data/`)** | 🟢 Готово | Единственный набор `test_general_2026` (50 вопросов: 45 choice + 5 text) |
| **Безопасность & Защита (Anti-Cheat / Anti-Copy)** | 🟢 Готово | Таймер 30/35с по `Date.now()`, запрет выделения, блокировка копирования, PrintScreen, блюр при потере фокуса |
| **Защита PII (PLAN-015)** | 🟢 Готово | `/api/export/leads` закрыт `X-API-Key` (503 без ключа, 401 с неверным); `EXPORT_API_KEY` + `DATA_DIR` в env |
| **Персистентность лидов (PLAN-015)** | 🟢 Готово | `DATA_DIR` настраивается через env; Railway volume `lead-data` → `/app/data` (создать том в UI) |
| **Жизненный цикл сессий (GC)** | 🟢 Готово | `last_activity`, фоновый GC (24ч), нормализация `time_spent >= 0.5` |
| **CAT & Fixed движок (`cat_engine.py`)** | 🟢 Готово | Новая шкала 50 вопросов (Beginner–Advanced); поддержка таймаутов, фиксация `skipped_count` |
| **Единый сервер (`main.py` + FastAPI)** | 🟢 Готово | REST API; `/api/health`; валидация телефонов Узбекистана; отправка лидов с филиалом; `/api/export/leads` |
| **Telegram-бот (`telegram_bot.py`)** | 🟢 Готово | Единая карточка с филиалом (`Главный офис`/`Университет`), кнопкой Telegram, уровнем и стандартизированным телефоном |
| **Веб-интерфейс (`static/`)** | 🟢 Готово | Ультра-минималистичный welcome-экран, нестираемый `+998`, строгая маска `+998 (XX) XXX-XX-XX`, 9 цифр лимит |
| **Тесты & CI** | 🟢 Готово | `check_integrity` (100%, включая раздел 6 «Безопасность»), `test_api_http` (15/15), `test_multi_suites` (4/4), `test_review_feature` — PASSED |

---

## 🎯 Что сделано в PLAN-015 (аудит 2026-09-26):
- [x] **Найдена дыра №1 (🔴):** `GET /api/export/leads` отдавал ФИО/телефоны/`@username` **любому** без авторизации.
- [x] **Исправлено:** обязательный заголовок `X-API-Key`; без ключа в конфиге — `503` (fail-closed); сравнение через `hmac.compare_digest`.
- [x] **Найдена дыра №2 (🔴):** `data/` в `.dockerignore` без volume → **все лиды терялись при каждом деплое/рестарте Railway**.
- [x] **Исправлено:** `DATA_DIR` вынесен в `config.py` (env), `lead_store.py` импортирует его; в `railway.json` добавлен volume `lead-data` → `/app/data`.
- [x] `agents/tools/export_results.py` шлёт `X-API-Key` (из env/`.env`).
- [x] `.env.example` дополнен `EXPORT_API_KEY` и `DATA_DIR`.
- [x] Новый тест `test_export_leads_requires_api_key` (401/401/200) → `test_api_http` 15/15.
- [x] Новый **раздел 6** в `check_integrity.py`: 7 security-чеков (включая проверку, что токены не зашиты в код).
- [x] `BUG_004_leads_pii_leak_and_data_loss.md` + раздел про Volume/ключи в `DEPLOYMENT_RUNBOOK.md`.

## ⚠️ Известный долг (не в этом плане)
| # | Дыра | Риск |
|---|---|---|
| 1 | Нет rate limiting на 7 эндпоинтах | 🟠 спам `start` (память) и `submit-contact` (Telegram) |
| 2 | CORS `*` по умолчанию | 🟠 любой домен шлёт POST, если `ALLOWED_ORIGINS` не задан в проде |
| 3 | Анти-спуфинг обходится: `if payload.tg_init_data` (клиент может не передать) | 🟠 подделка `tg_user_id` |
| 4 | Нет лимита на `time_spent_seconds` | 🟡 мусор в статистике |
| 5 | `/api/health` отдаёт `active_sessions` | 🟡 утечка метрик |
| 6 | Нет `og:url`, `twitter:card=summary` вместо `large_image` | 🟡 превью в соцсетях |

## 📌 Требуется вручную в Railway (посе деплоя PLAN-015)
1. Variables: `EXPORT_API_KEY=<secrets.token_urlsafe(32)>`, `DATA_DIR=/app/data`
2. Volume: `lead-data`, mount path `/app/data` (том создаётся в UI, в репо только `railway.json`)
3. Старую копию лидов (если была) перенести в том вручную
4. Перезапустить локальный uvicorn — на :8000 сейчас старый код (экспорт отдаёт 200 без ключа)