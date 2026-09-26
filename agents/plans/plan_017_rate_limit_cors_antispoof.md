# 📋 PLAN-017: Rate limiting, CORS-защита в проде, анти-спуфинг `tg_user_id`

**Статус:** ✅ COMPLETED (ожидает коммита)
**Дата:** 2026-09-26
**Утверждено:** «да» (пользователь выбрал вариант B после варианта A)

## 🔍 Аудит-основа (дыры из отчёта 2026-09-26)

| # | Дыра | Файл |
|---|---|---|
| 1 | Нет rate limiting: спам `POST /api/test/start` (рост памяти) и `POST /api/test/submit-contact` (заливка Telegram админу) | `backend/main.py` |
| 2 | CORS `*` по умолчанию — любой домен шлёт POST, если `ALLOWED_ORIGINS` не задан в Railway | `backend/config.py:24` |
| 3 | Анти-спуфинг обходится: `if payload.tg_init_data and IS_BOT_ENABLED` — клиент может просто **не передать** поле и проверка не выполнится | `backend/main.py:273` |

## 📋 Шаги

| # | Шаг | Файлы | Статус |
|---|---|---|---|
| 1 | `config.py`: `RATE_LIMIT_ENABLED`, `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`, `IS_CORS_WILDCARD` | `backend/config.py` | ✅ |
| 2 | Rate limiting: sliding-window по IP, только для мутаций (POST/PUT/PATCH/DELETE), ответ `429` + `Retry-After`; предупреждение о NAT-риске в лог | `backend/main.py` | ✅ |
| 3 | CORS: при wildcard — громкий WARNING на старте; при заданных origins — WARNING про hardcoded allow_credentials | `backend/main.py` | ✅ |
| 4 | Анти-спуфинг: если передан `tg_user_id`, но `tg_init_data` отсутствует/невалидна/бот выключен → `403` | `backend/main.py` | ✅ |
| 5 | Тесты: `test_rate_limit_blocks_burst`, `test_tg_user_id_requires_init_data`, обновление CORS-теста | `agents/testing/test_api_http.py` | ✅ |
| 6 | `.env.example`: 3 новые переменные + предупреждение про NAT | `.env.example` | ✅ |
| 7 | `check_integrity.py`: +3 чека (rate limit в main.py, анти-спуфинг 403, переменные в .env.example) | `agents/tools/check_integrity.py` | ✅ |
| 8 | Верификация: integrity, api_http, multi_suites, review, live smoke | — | ✅ |
| 9 | Документация: BUG_005, runbook (NAT-предупреждение), STATUS | `agents/` | ✅ |
| 10 | Коммит | — | ⏳ ждать «да» |

## 🔒 Инварианты

- **Никаких новых зависимостей** — лимитер на чистом Python (`collections.deque`)
- **Антипаттерн №2**: никаких `time.sleep`, только `asyncio.sleep` (лимитер вообще без sleep)
- Лимит по умолчанию **60 req/min** — выше нормального темпа теста (≈3.3 req/min), но ниже спам-порога
- GET/HEAD не лимитируются (проверка, каталог, статика)
- `ClientQuestion` по-прежнему без `correct_option`/`correct_text`
- Контракт 7 эндпоинтов не меняется, кроме новых 403/429 на злоупотребление

## ⚠️ Известный компромисс

Мобильные операторы используют CGNAT — несколько разных пользователей могут иметь
один IP. При едином лимите на IP возможен ложный 429. Поэтому:
- лимит по умолчанию высокий (60/мин);
- окно и лимит настраиваются через env;
- предупреждение о риске печатается в лог при старте;
- при фактических жалобах — поднять лимит или перейти на per-session лимиты.

## ✅ Фактическая верификация (2026-09-26)

| Проверка | Результат |
|---|---|
| `check_integrity.py` | **100%**, раздел 6 = **11 security-чеков** (было 7, стало 11) |
| `test_api_http.py` | **17/17** PASSED (было 15) |
| `test_multi_suites.py` | 4/4 PASSED |
| `test_review_feature.py` | PASSED |
| Live smoke :8765 — полный прогон | **50/50**, score 100, level Advanced — лимит **не мешает** нормальному темпу |
| Live: спуф `tg_user_id` без initData | **403** ✅ |
| Live: burst 70 POST подряд | 60 × 200 + **10 × 429** (ровно по лимиту) ✅ |
| Live: `/api/export/leads` | 503 (ключ не задан локально) ✅ |
| Новые зависимости | **нет** — лимитер на `collections.deque` |
| Временный сервер | погашен, порт 8765 свободен |

**Обнаруженный нюанс:** первый прогон тестов упал на лимите — сам тест делает 50 POST
подряд с одного IP. Это и есть риск CGNAT в миниатюре. Решение: тесты отключают
продовый лимит через `RATE_LIMIT_REQUESTS=100000` в env **до** импорта `backend`,
а `test_rate_limit_blocks_burst` временно понижает лимит до 10 и чистит бакеты.
