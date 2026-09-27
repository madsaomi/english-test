# 🔧 PLAN-035: M1 (rate limit XFF) + M3 (свежесть initData) + L1/L2 (зависимости) + L6 (console.log)

**Статус:** ✅ COMPLETED
**Дата:** 2026-09-27
**Основание:** аудит 2026-09-27 (`agents/audits/audit_2026-09-27_full_security.md`).
Одобрено владельцем: «да».

## 1. M1 — rate limit обходится подделкой X-Forwarded-For
В `backend/main.py:181-187` ключ бакета брался из первой записи `X-Forwarded-For` — клиент
сам подставляет заголовок → новый бакет на каждый запрос → лимит бесполезен.

| # | Шаг | Статус |
|---|---|---|
| 1 | `_client_key`: ключ = `request.client.host` (реальный peer) + хеш User-Agent. XFF от клиента не доверяем | ✅ |
| 2 | За прокси (Railway) тот же `request.client` раскрывает **uvicorn с `--proxy-headers`** (он сам превращает XFF прокси в client) — документировано докстрингом + комментарием | ✅ |
| 3 | Жёсткий потолок `_MAX_RATE_BUCKETS = 50000` в `_cleanup_rate_buckets` (prune старейших) — страховка от роста словаря | ✅ |

## 2. M3 — initData можно «переигрывать» (нет свежести auth_date)
`verify_telegram_init_data` проверяла подпись, но не возраст данных → перехваченный
initData работает бесконечно долго.

| # | Шаг | Статус |
|---|---|---|
| 4 | `INIT_DATA_MAX_AGE_SECONDS = 24*3600`; `auth_date` обязателен и не старше суток (`time.time() - auth_ts`) | ✅ |
| 5 | Тесты обновлены: валидная initData строится со свежим `time.time()`; добавлены кейсы «просрочка» и «нет auth_date» | ✅ |

## 3. L1/L2 — supply-chain / гигиена
| # | Шаг | Статус |
|---|---|---|
| 6 | `requirements.txt`: зависимости запинены `==` (были `>=`) по версиям из `pip freeze` | ✅ |
| 7 | Удалены неиспользуемые `httpx2` и `pydantic-settings` (проверено grep: не импортируются нигде) | ✅ |

## 4. L6 — лишний console.log
| # | Шаг | Статус |
|---|---|---|
| 8 | `static/js/app.js:97` удалён `console.log('Telegram WebApp user detected:', tgUser)` | ✅ |

## 5. Не трогаем
- Логика лимита/окна, все остальные пункты аудита (L3/L4/L5/L9, M2-продолжение) — следующue планы.

## 6. Верификация
- `test_api_http` — 21/21 (обновлён initData-тест)
- `test_multi_suites` 4/4 · `test_review_feature` · `test_simulation` · `test_e2e` · `check_integrity` 100%