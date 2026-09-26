# 📋 PLAN-014: OG-превью, countdown с авто-ответом, история попыток

**Статус:** ❌ CANCELLED (неактуален после аудита 2026-09-26)
**Дата:** 2026-09-26
**Предыдущий:** PLAN-013 (Stanford UI) — код готов, ждёт коммита

> [!CAUTION]
> **ОТМЕНЁН.** Повторная проверка кода показала, что пункт 2 и 3 этого плана
> **уже реализованы** в коммитах `7d4c500` / `46bfa80`: обратный отсчёт таймера
> (`static/js/app.js:494-501`) и авто-ответ с `is_timeout: true` (`app.js:548`),
> а также `<meta property="og:image">` (`static/index.html:14`).
> Остался только `og:url` и история попыток — они вынесены в отдельные задачи.
> Актуальные планы: **PLAN-015** (безопасность/персистентность).

## 🔍 Результаты исследования (почему план именно такой)

| Находка | Файл | Следствие |
|---|---|---|
| `AnswerRequest.is_timeout: bool = False` уже есть | `backend/models.py:34` | Backend **уже** принимает таймаут — менять не нужно |
| `cat_engine` при `is_timeout` + пустой выбор → `is_correct: False` | `cat_engine.py:189` | Авто-ответ без выбора засчитается как неверный, сессия идёт дальше |
| `main.py:192,208` прокидывает `is_timeout` | `backend/main.py` | Эндпоинт готов |
| `<meta property="og:image" content="/logo.png">` **уже есть** | `static/index.html:14` | Нужно только добавить `og:url` и улучшить `twitter:card` |
| Эндпоинтов истории нет; `localStorage` не используется | — | Реализуем на клиенте (без БД и миграций) |
| Критичные 22 id сохраняем; `.progress-bar-container` скрыт | `static/css/style.css` | Прогресс-бар можно переиспользовать под countdown |

## 📋 Шаги

| # | Шаг | Файлы | Статус |
|---|---|---|---|
| 1 | `og:url` + `twitter:card=summary_large_image` + абсолютный `og:image` через `${location.origin}` (app.js) | `static/index.html`, `static/js/app.js` | ⏳ |
| 2 | **Countdown на вопросе:** заменить счётчик времени на обратный (по умолчанию **120 сек**), визуал: badge краснеет на последних 20 сек | `static/index.html`, `static/css/style.css`, `static/js/app.js` | ⏳ |
| 3 | **Авто-ответ:** при 0 → `postAnswer({..., is_timeout: true, selected_option: -1})`, карточка гаснет ~600 мс, идёт следующий вопрос; для text-вопросов — авто-отправка пустой строки | `static/js/app.js` | ⏳ |
| 4 | Отмена таймера при ручном ответе (уже есть `stopQuestionTimer`, проверить вызовы) | `static/js/app.js` | ⏳ |
| 5 | **История попыток:** `localStorage` (`slc_history_v1`): дата, уровень, точность, балл; на welcome — блок «Ваш прошлый результат» (скрыт, если истории нет); кнопка очистки | `static/index.html`, `static/css/style.css`, `static/js/app.js` | ⏳ |
| 6 | Убрать `smoke_live_8765.py` из репозитория (устарел, порт 8765) или обновить на :8000 — **решить при коммите** | — | ⏳ |
| 7 | Тесты: обновить `test_api_http.py` (кейс таймаут-ответа) + `check_integrity.py` (проверка новых id) | `agents/testing/`, `agents/tools/` | ⏳ |
| 8 | Верификация: integrity, api_http, multi_suites, review, live smoke :8000 (50/50 + таймаут-кейс) | — | ⏳ |
| 9 | Обновить `STATUS.md`, `plan_013` (закрыть), журнал сессии в `agents/history/` | `agents/` | ⏳ |
| 10 | Коммит + push | — | ⏳ ждать «да» |

## 🔒 Инварианты (не нарушать)

- **22 критичных id** в HTML сохраняются без изменений
- `ClientQuestion` **не получает** `correct_option`/`correct_text` (антипаттерн №1)
- Никаких `time.sleep`; только `asyncio.sleep` (антипаттерн №2)
- Vanilla CSS, без новых зависимостей (ADR-002)
- `BOT_TOKEN`/`ADMIN_CHAT_ID` — только в `.env` (антипаттерн №4)
- Новый id для блока истории: `attempt-history` (не конфликтует)

## ✅ План верификации

1. `python agents/tools/check_integrity.py` → 100%
2. `python agents/testing/test_api_http.py` → 13+1 PASSED (добавлен таймаут-кейс)
3. `python agents/testing/test_multi_suites.py` → 4/4
4. `python agents/testing/test_review_feature.py` → PASSED
5. Live smoke :8000 — 50/50, статические файлы 200, 22 id на месте
6. Ручная проверка countdown: ждём 0 на коротком лимите → авто-переход
7. Ручная проверка истории: пройти тест → блок появляется на welcome → очистка

## ❓ Открытые вопросы к пользователю

1. **Лимит на вопрос:** 60 сек (строго, как EF SET) или 120 сек (спокойно)? — предлагаю **120**
2. **`smoke_live_8765.py`:** удалить из проекта или обновить под :8000?
3. **История:** хранить в `localStorage` (только у пользователя, без БД) — ок?
