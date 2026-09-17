# 🚑 Аварийный справочник (TROUBLESHOOTING.md)

Пошаговые инструкции по диагностике и быстрому устранению инцидентов и типичных сбоев.

---

## 🔴 Сбой 1: `TelegramConflictError: terminated by other getUpdates request`

### Симптом:
Бот падает в цикле с ошибкой `aiogram.exceptions.TelegramConflictError: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running`.

### Причина:
Запущен второй экземпляр сервера с тем же `BOT_TOKEN` (например, предыдущий процесс в фоне, или бот запущен на другом сервере/ПК).

### Устранение:
1. Завершите все фоновые процессы Python:
   ```powershell
   Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
   ```
2. Если бот запускался с вебхуком, сбросьте вебхук через команду:
   ```powershell
   python -c "import asyncio; from aiogram import Bot; b = Bot('ВАШ_ТОКЕН'); asyncio.run(b.delete_webhook(drop_pending_updates=True))"
   ```
3. Запустите сервер заново.

---

## 🔴 Сбой 2: Белый экран при открытии кнопки в Telegram WebApp

### Симптом:
При нажатии на кнопку в Telegram боте открывается окно, но экран остается белым или пишет «Не удается открыть страницу».

### Причина:
1. Адрес `WEBAPP_URL` указан через `http://` вместо `https://` (Telegram блокирует незащищенные соединения).
2. Используется самоподписанный SSL-сертификат (Telegram требует доверенный центр сертификации, например Let's Encrypt или Cloudflare).
3. Локальный сервер выключен или адрес туннеля (ngrok) изменился.

### Устранение:
1. Проверьте `WEBAPP_URL` в файле `.env`. Он должен начинаться строго с `https://`.
2. Если тестируете локально, перезапустите `ngrok http 8000` и обновите URL в `.env`.

---

## 🔴 Сбой 3: Сервер не запускается из-за `[Errno 10048] Address already in use`

### Симптом:
Uvicorn сообщает, что порт 8000 уже занят другим приложением.

### Устранение:
Выполните команду принудительного освобождения порта:
```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
# Проверка
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
```
После этого порт свободен.
