# 📊 Текущий статус проекта (STATUS.md)

**Последнее обновление:** 2026-09-22 (UTC+5)  
**Ответственный агент:** opencode (opencode/mimo-v2.6-flash-free)  
**Текущая фаза:** Настройка деплоя на Railway (PLAN-011) — `railway.json` + runbook; основной тест `test_general_2026` (50 вопросов) остаётся единственным

---

## 🚦 Состояние подсистем

| Компонент | Статус | Комментарий |
|---|---|---|
| **Экосистема «Второго Мозга» (`agents/`)** | 🟢 Готово | 13 разделов: правила, антипаттерны, шаблоны, ADR, баги, деплой, траблшутинг |
| **Git-версионирование (`.git`)** | 🟢 Готово | Инициализирован Git, настроен `.gitignore`, создан первый коммит |
| **Окружение Python & зависимости** | 🟢 Готово | `fastapi`, `aiogram`, `uvicorn`, `pydantic`; добавлен `httpx2` для TestClient |
| **Банк вопросов & Каталог тестов (`tests_data/`)** | 🟢 Готово | Единственный набор `test_general_2026` (50 вопросов: 45 choice + 5 text); автотесты удалены; `template_*.json` — шаблоны |
| **Безопасность (CORS + Telegram initData)** | 🟢 Готово | `ALLOWED_ORIGINS` из env; HMAC-валидация WebApp initData в прод-режиме |
| **Жизненный цикл сессий (GC)** | 🟢 Готово | `last_activity`, фоновый GC (24ч), нормализация `time_spent >= 0.5` |
| **CAT & Fixed движок (`cat_engine.py`)** | 🟢 Готово | Adaptive CAT и fixed режимы, anti-cheat, review, CEFR-описание уровня |
| **Единый сервер (`main.py` + FastAPI)** | 🟢 Готово | REST API; `/api/health` реальный; `GET /api/export/leads`; Lifespan aiogram |
| **Telegram-бот (`telegram_bot.py`)** | 🟢 Готово | aiogram 3.x бот, TMA кнопка, форматированные карточки |
| **Веб-интерфейс (`static/`)** | 🟢 Готово | Бумажный стиль + Lora; скелетоны/спиннеры/SVG-иконки/маска/тосты/favicon; детали: штамп «ПРОЙДЕНО», скрепка, линовка, watermark, точки прогресса, shimmer, reduced-motion; мёртвый CSS вычищен |
| **Экспорт лидов** | 🟢 Готово | `/api/export/leads` + скрипт `export_results.py`; лиды персистентны (lead store) |
| **Заявки в приёмную** | 🟢 Готово | Телефон обязателен; сотруднику — карточка (имя/уровень/телефон/дата) + второе сообщение с детальным результатом |
| **Тесты & CI** | 🟢 Готово | `check_integrity`, `test_simulation`, `test_multi_suites`, `test_review_feature`, `test_api_http`, `test_e2e` — все PASSED, включены в GitHub Actions |

---

## 🎯 Что делается прямо сейчас:
- PLAN-011 (настройка Railway): `.dockerignore` (исключены `.env`/`data`/`exports`/`.github`/docx), `.env.example` + `ALLOWED_ORIGINS`, раздел «Способ 3: Railway» в `DEPLOYMENT_RUNBOOK.md`. Код не менялся. Коммит — после явного «да».
- PLAN-010 закоммичен (`8395761`, `6c8dc8b`, `2fae992`): `test_general_2026` — единственный тест, 50 вопросов, case-sensitive text.
- Напомню: результат на сайте не показывается — сотрудник получает карточку + детальный результат в Telegram. Для реальной отправки нужны `BOT_TOKEN` и `ADMIN_CHAT_ID` в Variables Railway (или `.env` локально).
- Осталось (малое): таймер-countdown с авто-ответом (нужен бэкенд), `og:image`/`og:url` (нужен домен+ассет), история попыток по `tg_user_id`. **PDF-сертификат — отменён навсегда (решение пользователя), не предлагать.**
- ⚠️ Railway previously: «ToS Violation» на аккаунт — risk-score, не код; если restriction висит — support или VPS (Способ 2).