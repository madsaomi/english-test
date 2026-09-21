# 📐 Implementation Plan: Улучшение и ужесточение платформы (TASK-004)

- **ID плана:** PLAN-002
- **Дата создания:** 2026-09-21
- **Статус:** ✅ COMPLETED (Выполнено, все шаги прошли верификацию)
- **Цель:** Устранить 3 подтверждённых бага, закрыть 2 пробела безопасности, синхронизировать спеки и код, подключить тесты к CI, добавить HTTP-тесты и улучшить UX (CEFR-описание, хоткеи для любой раскладки).

---

## 📌 Чек-лист реализации (по пунктам аудита)

- [x] **Шаг 1 (п.1): CSS-переменные `--transition-fast` / `--transition-normal`**
  - Файл: `static/css/style.css`
  - В `:root` добавить: `--transition-fast: 0.15s ease;` и `--transition-normal: 0.25s cubic-bezier(0.16, 1, 0.3, 1);`
  - Эффект: оживёт hover-анимация карточек каталога (`style.css:1300,1377`).

- [x] **Шаг 2 (п.2): Корректный `/api/health`**
  - Файл: `backend/main.py` (`:85`)
  - Вернуть реальный размер банка: `len(test_repository.get_all_questions_pool())`.
  - Добавить поле `active_sessions: len(cat_engine.sessions)` отдельно от размера банка.

- [x] **Шаг 3 (п.3): GC сессий и нормализация времени ответа (синхронизация со спеками)**
  - Файлы: `backend/models.py`, `backend/cat_engine.py`, `backend/main.py`
  - Добавить в `TestSession` поле `last_activity: float` (timestamp), обновлять при каждом `submit_answer`.
  - В `lifespan` запускать фоновую задачу GC (раз в 10 мин): удалять сессии без активности > 24 ч (`SESSION_LIFECYCLE.md`: состояние EXPIRED).
  - Нормализовать `time_spent_seconds` в `submit_answer`: `max(0.5, time_spent)` — во исполнение `SECURITY_SPEC.md` (анти-автокликер).

- [x] **Шаг 4 (п.4): Валидация Telegram WebApp initData**
  - Файлы: `backend/config.py`, `backend/models.py`, `backend/main.py`, `static/js/app.js`
  - В `UserContactSubmission` добавить `tg_init_data: Optional[str] = None`.
  - В `main.py` при наличии `tg_init_data` и включённом боте: проверить подпись по схеме Telegram (HMAC-SHA256: `secret = HMAC_SHA256("WebAppData", BOT_TOKEN)`, затем `hash = HMAC_SHA256(init_data_without_hash, secret)`), сверить с переданным `hash`. Не прошла → `HTTPException(403)`.
  - Демо-режим (нет `BOT_TOKEN`) — валидация пропускается без падения (существующее поведение сохраняется).
  - Во `app.js`: передавать сырой `tg.initData` в `submit-contact`.

- [x] **Шаг 5 (п.5): Ужесточение CORS**
  - Файлы: `backend/config.py`, `backend/main.py`
  - Новая переменная окружения `ALLOWED_ORIGINS` (список через запятую).
  - Если не задана — сохранить `["*"]` для локальной разработки, но `allow_credentials=False`.
  - Если задана — использовать явный список с `allow_credentials=True`.

- [x] **Шаг 6 (п.7): Единый источник правды банка вопросов**
  - Файл: `agents/tools/check_integrity.py`
  - Добавить проверку синхронизации: id/уровни/кол-во вопросов в `cefr_adaptive_bank.json` должны совпадать с `QUESTION_BANK` из `questions.py`. Расхождение → FAIL. Это предотвращает дрейф двух источников.

- [x] **Шаг 7 (п.8): Реальный экспорт лидов**
  - Файлы: `backend/main.py`, `agents/tools/export_results.py`
  - Новый endpoint `GET /api/export/leads`: собирает завершённые сессии с контактами (`session.user_name`, `user_phone`, `tg_username`, `result.*`) в JSON-массив.
  - `export_results.py`: тянет реальные данные через этот endpoint; демо-запись оставляет только как fallback, если список пуст.

- [x] **Шаг 8 (п.9): Подключение новых тестов в CI**
  - Файл: `.github/workflows/ci.yml`
  - Добавить шаги: `python agents/testing/test_multi_suites.py` и `python agents/testing/test_review_feature.py`.

- [x] **Шаг 9 (п.10): HTTP-слой тестов**
  - Новый файл: `agents/testing/test_api_http.py`
  - Использовать `fastapi.testclient.TestClient` (httpx идёт в комплекте): проверить `GET /api/tests`, `POST /api/test/start`, полный цикл ответов, `/api/health`, `/api/test/result/{id}`, `/api/export/leads`.
  - Добавить запуск в CI (шаг 8).

- [x] **Шаг 10 (п.11): Описание CEFR в результатах**
  - Файлы: `backend/models.py` (`TestResult.cefr_description`), `backend/cat_engine.py` (`finalize_test` из `map_ability_to_cefr`), `static/js/app.js` (`result-summary-text` динамически).
  - Фронт перестанет показывать статичный текст — будет уровень-специфичное описание.

- [x] **Шаг 11 (п.12): Хоткеи для русской раскладки**
  - Файл: `static/js/app.js` (keydown-обработчик)
  - Перейти с `e.key` на `e.code` (`KeyA`–`KeyD`, `Digit1`–`Digit4`) — работает независимо от раскладки.

- [x] **Шаг 12: Документация**
  - `agents/tasks/active_task.md` — карточка TASK-004 с чек-листом.
  - `agents/STATUS.md` — обновление статусов.
  - `agents/history/session_2026-09-21_09_hardening_and_improvements.md` — журнал сессии (по шаблону).

---

## 🧪 План верификации
1. `python agents/tools/check_integrity.py` → 100% OK (включая новый пункт синхронизации банка).
2. `python -m backend.test_simulation` → 3 сценария сходятся.
3. `python agents/testing/test_multi_suites.py` → PASSED.
4. `python agents/testing/test_review_feature.py` → PASSED.
5. `python agents/testing/test_api_http.py` → PASSED (новый HTTP-слой).
6. Ручной smoke: старт сервера, `GET /api/health`, прогон теста в браузере (реферат уровня, хоткеи A-D в любой раскладке).

## 📁 Затрагиваемые файлы
- `static/css/style.css`
- `backend/main.py`, `backend/models.py`, `backend/cat_engine.py`, `backend/config.py`
- `static/js/app.js`
- `agents/tools/check_integrity.py`, `agents/tools/export_results.py`
- `.github/workflows/ci.yml`
- `agents/testing/test_api_http.py` (новый)
- `agents/tasks/active_task.md`, `agents/STATUS.md`, `agents/history/` (новый файл сессии)

## ⚠️ Риски и меры
- Валидация initData: неверная схема подписи сломает отправку отчётов из Telegram → покрыт тестом `test_api_http` (эндпоинт на 403 при подделанном hash).
- CORS: сужение origins может задеть локальную разработку → при незаданном `ALLOWED_ORIGINS` поведение сохраняется.
- GC сессий: не должен удалять активную сессию → порог 24 ч + обновление `last_activity` на каждый ответ.