# 🔧 PLAN-034: баг анти-копи (B1) + идемпотентность уведомления (M4/B2) + лимиты длин (M5)

**Статус:** ✅ COMPLETED
**Дата:** 2026-09-27
**Основание:** аудит 2026-09-27 (`agents/audits/audit_2026-09-27_full_security.md`).
Одобрено владельцем: «да».

## 1. B1 — сломанный анти-копи обработчик (undefined activeScreen)
`static/js/app.js:1050` использует `activeScreen`, который нигде не объявлен →
`ReferenceError` в keydown-обработчике → `Ctrl+C/X/U/S/P` **не блокируются** во время теста.

| # | Шаг | Статус |
|---|---|---|
| 1 | Объявить `let activeScreen = null;` в состоянии | ✅ |
| 2 | В `showScreen(screen)` устанавливать `activeScreen = screen` | ✅ |
| 3 | Строка `if (activeScreen === screenResult) return;` начинает работать: на экране результата копию разрешаем (поля формы), во время теста — блокируем | ✅ |

## 2. M4/B2 — дубли уведомления админу при повторном submit-contact
Повторный POST на `/api/test/submit-contact` с тем же `session_id` снова звал
`send_admin_lead_notification` → N сообщений в Telegram админу.

| # | Шаг | Статус |
|---|---|---|
| 4 | В `submit_user_contact`: если `session.result.telegram_sent` уже True — пропустить отправку, вернуть `telegram_sent: True` | ✅ |
| 5 | Семантика сохранена: доставлено = True; сбой при первой отправке (sent=False) позволяет повторную попытку | ✅ |
| 6 | Тест-идемпотентность: monkey-patch `send_admin_lead_notification` (счётчик вызовов), два submit → ровно 1 вызов | ✅ |

## 3. M5 — отсутствие лимитов длины у контактов
`name`/`branch`/`telegram_username`/`phone` без `max_length` → мегастроки ломают
Telegram-сообщение и мусорят JSON/логи. Пустые значения по-прежнему дают 400
(проверка `strip()` в эндпоинте сохранена, поэтому min_length не добавляем).

| # | Шаг | Статус |
|---|---|---|
| 7 | `models.py`: `name ≤ 100`, `phone ≤ 30`, `telegram_username ≤ 64`, `branch ≤ 60` через `Field(max_length=…)` | ✅ |
| 8 | Тест: слишком длинный `name`/`branch` → 422 | ✅ |

## 4. Не трогаем
- Логика формы и эндпоинта (400 для пустых) — прежняя.
- Прочее из аудита (M1/M3/L*, M2-продолжение) — следующие планы.

## 5. Верификация
- `test_api_http` — 20/20 (добавлены 2 теста: идемпотентность, лимиты длин)
- `test_multi_suites` 4/4 · `test_review_feature` · `test_simulation` · `test_e2e` · `check_integrity` 100%