# 📱 Спецификация интеграции с Telegram (Bot & WebApp)

Этот документ описывает устройство и механизм взаимодействия бэкенда с Telegram Bot API и Telegram Mini Apps.

---

## 1. Единый процесс запуска (FastAPI Lifespan)

Telegram-бот построен на базе фреймворка **`aiogram 3.x`** и работает в **том же самом процессе**, что и веб-сервер FastAPI:

```python
# backend/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    if IS_BOT_ENABLED and dp and bot:
        # Очистка старых вебхуков и запуск фонового polling
        await bot.delete_webhook(drop_pending_updates=True)
        bot_task = asyncio.create_task(dp.start_polling(bot))
    yield
    # Корректное закрытие сессий при остановке
    if bot_task:
        bot_task.cancel()
    if bot:
        await bot.session.close()
```

---

## 2. Безопасный демо-режим (Fault-Tolerant Demo Mode)

В `backend/config.py`:
```python
IS_BOT_ENABLED: bool = bool(BOT_TOKEN and BOT_TOKEN.lower() != "your_telegram_bot_token_here")
```
- Если пользователь запустил проект без настройки `.env`, сервер **НЕ ПАДАЕТ**, а продолжает полноценно обслуживать веб-сайт.
- При вызове функций отправки уведомлений в консоль пишется информационный лог `[DEMO MODE]`.

---

## 3. Поддержка Telegram WebApp (Mini App)

1. В `static/index.html` подключен официальный скрипт SDK:
   ```html
   <script src="https://telegram.org/js/telegram-web-app.js"></script>
   ```
2. В `static/js/app.js`:
   - Автоматически вызывается `tg.ready()` и `tg.expand()`.
   - Если приложение открыто внутри Telegram, из объекта `tg.initDataUnsafe.user` извлекаются:
     - `first_name` и `last_name`
     - `username`
     - `id` (числовой chat_id пользователя)
   - Поля формы контактов на экране результатов заполняются автоматически!
   - При успешной отправке срабатывает тактильный отклик `tg.HapticFeedback.notificationOccurred('success')`.

---

## 4. Формат уведомления в Telegram

Когда пользователь нажимает «Отправить результат в Telegram», бэкенд формирует HTML-карточку:

- **Администратору (`ADMIN_CHAT_ID`)**:
  - Имя, телефон, ссылка на Telegram пользователя.
  - Точный уровень CEFR (A1–C2) и расшифровка.
  - Графическая шкала прогресса `[🟩🟩🟩🟩🟩🟩🟩⬜⬜⬜]`.
  - Время прохождения, точность в процентах.
  - Детализация по категориям (*Grammar*, *Vocabulary*, *Usage*).
  - Список тем, где были допущены ошибки.
- **Ученику лично** (если известен `tg_user_id`):
  - Поздравление и карточка уровня.
  - Список персональных рекомендаций от преподавателя.
