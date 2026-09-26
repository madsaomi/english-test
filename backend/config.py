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

# Ключ доступа к эндпоинту экспорта лидов (GET /api/export/leads).
# Эндпоинт отдаёт персональные данные (ФИО, телефон, @username), поэтому:
#   - если ключ НЕ задан — эндпоинт отвечает 503 и отключён;
#   - если ключ задан — требуется заголовок X-API-Key с этим значением.
EXPORT_API_KEY: str = os.getenv("EXPORT_API_KEY", "").strip()

# Каталог для персистентного хранения лидов.
# В Docker/Railway переопределяется на примонтированный том, иначе данные
# теряются при каждом рестарте контейнера.
DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))

# Режим работы бота: если токен не задан, включается демо-режим без сбоев
IS_BOT_ENABLED: bool = bool(BOT_TOKEN and BOT_TOKEN.lower() != "your_telegram_bot_token_here")

# CORS: список разрешённых origin через запятую. Если не задан — разрешаем все
# (удезно для локальной разработки), но без куки-креденшелов.
_ALLOWED_ORIGINS_RAW: str = os.getenv("ALLOWED_ORIGINS", "").strip()
ALLOWED_ORIGINS: List[str] = (
    [o.strip() for o in _ALLOWED_ORIGINS_RAW.split(",") if o.strip()]
    if _ALLOWED_ORIGINS_RAW
    else ["*"]
)
IS_CORS_WILDCARD: bool = ALLOWED_ORIGINS == ["*"]

# --- Rate limiting (защита от спама и роста памяти) ---
# Применяется только к мутациям (POST/PUT/PATCH/DELETE).
# ВНИМАНИЕ: мобильные операторы используют CGNAT — несколько пользователей могут
# иметь один IP. Лимит по умолчанию задан с запасом (нормальный темп теста ≈3.3 req/min).
RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").strip().lower() not in ("0", "false", "no", "off")
RATE_LIMIT_REQUESTS: int = max(1, int(os.getenv("RATE_LIMIT_REQUESTS", "60")))
RATE_LIMIT_WINDOW_SECONDS: int = max(1, int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")))
