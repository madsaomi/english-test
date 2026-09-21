import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID: str = os.getenv("ADMIN_CHAT_ID", "").strip()
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
WEBAPP_URL: str = os.getenv("WEBAPP_URL", f"http://localhost:{PORT}").strip()

# Режим работы бота: если токен не задан, включается демо-режим без сбоев
IS_BOT_ENABLED: bool = bool(BOT_TOKEN and BOT_TOKEN.lower() != "your_telegram_bot_token_here")

# CORS: список разрешённых origin через запятую. Если не задан — разрешаем все
# (удобно для локальной разработки), но без куки-креденшелов.
_ALLOWED_ORIGINS_RAW: str = os.getenv("ALLOWED_ORIGINS", "").strip()
ALLOWED_ORIGINS: List[str] = (
    [o.strip() for o in _ALLOWED_ORIGINS_RAW.split(",") if o.strip()]
    if _ALLOWED_ORIGINS_RAW
    else ["*"]
)
