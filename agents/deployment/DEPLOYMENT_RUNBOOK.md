# 🚀 Инструкция по развертыванию на Production сервере (DEPLOYMENT_RUNBOOK.md)

> [!IMPORTANT]
> **КРИТИЧЕСКОЕ ТРЕБОВАНИЕ ДЛЯ TELEGRAM WEBAPP:**  
> Telegram внутри мобильных приложений и десктопа **категорически блокирует** запуск Web Apps по протоколу `http://`.  
> Для полноценной работы кнопки Web App в боте сайт **ОБЯЗАН** работать по протоколу **`https://`** с валидным доверенным SSL-сертификатом!

---

## 🛠️ Способ 1: Быстрое локальное тестирование с HTTPS через ngrok

Если вы хотите протестировать WebApp прямо с локального компьютера на смартфоне:

1. Запустите сервер локально:
   ```powershell
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```
2. В отдельном окне запустите туннель:
   ```powershell
   npx localtunnel --port 8000
   # или ngrok
   ngrok http 8000
   ```
3. Скопируйте полученный адрес вида `https://random-name.loca.lt` или `https://xxx.ngrok-free.app`.
4. Вставьте его в `.env` в параметр:
   ```ini
   WEBAPP_URL=https://your-tunnel-address.app
   ```
5. Перезапустите сервер. Теперь кнопка в Telegram откроет реальный WebApp!

---

## 🌐 Способ 2: Развертывание на реальный Linux сервер (Ubuntu 22.04 / 24.04)

### 1. Подготовка системы и клонирование
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx git

# Переход в рабочую папку
cd /var/www
git clone <url_вашего_репозитория> english-cat
cd english-cat

# Виртуальное окружение
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Настройка файла `.env`
Создайте боевой `.env`:
```ini
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
ADMIN_CHAT_ID=123456789
HOST=127.0.0.1
PORT=8000
WEBAPP_URL=https://english-test.yourdomain.com
```

### 3. Настройка Systemd сервиса (Автозапуск 24/7)
Создайте файл `/etc/systemd/system/english-cat.service`:
```ini
[Unit]
Description=English Level CAT Platform & Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/english-cat
ExecStart=/var/www/english-cat/venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Включите и запустите сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable english-cat
sudo systemctl start english-cat
sudo systemctl status english-cat
```

### 4. Настройка Nginx (Reverse Proxy)
Создайте конфиг `/etc/nginx/sites-available/english-cat`:
```nginx
server {
    server_name english-test.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активируйте сайт и перезапустите Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/english-cat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Получение бесплатного SSL (HTTPS) от Let's Encrypt
```bash
sudo certbot --nginx -d english-test.yourdomain.com
```
Certbot автоматически сконфигурирует SSL и настроит автопродление. Теперь ваш Telegram WebApp работает на максимальной скорости и безопасности!

---

## ☁️ Способ 3: Деплой на Railway

Конфигурация уже в репозитории: `railway.json` (Dockerfile-билд, healthcheck `/api/health`, restart `ON_FAILURE` ×5) и `Dockerfile` (слушает `${PORT:-8000}`, копирует `tests_data/`).

### 1. Создание проекта
1. Откройте [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → `madsaomi/english-test`.
2. Railway сам подхватит `railway.json` и соберёт Docker-образ.

### 2. Variables (секреты — только в dashboard, не в git)
| Key | Значение |
|---|---|
| `BOT_TOKEN` | токен от @BotFather (пусто = демо-режим, сайт работает без бота) |
| `ADMIN_CHAT_ID` | ID чата для карточек лидов |
| `WEBAPP_URL` | `https://<service>.up.railway.app` (после Generate Domain) |
| `ALLOWED_ORIGINS` | тот же URL через запятую, если нужен строгий CORS |

`PORT` Railway задаёт сам — руками не указывать.

### 3. Публичный домен
**Settings → Networking → Generate Domain** → получите `https://....up.railway.app` → впишите в `WEBAPP_URL` (и при необходимости `ALLOWED_ORIGINS`) → redeploy.

### 4. Проверка
- `GET /api/health` → `status: ok`, `total_questions_in_bank: 50`
- `GET /api/tests` → один набор `test_general_2026`

### ⚠️ Если аккаунт в restriction («ToS Violation»)
Railway банит по risk-score аккаунта (регион/IP/платёжка), а не по коду этого репо. Конфиг это не обходит: напишите в support или используйте Способ 2 (VPS).
