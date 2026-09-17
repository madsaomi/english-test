# 📏 Стандарты и соглашения о коде (CODING_STANDARDS.md)

Этот документ регламентирует правила написания кода для Python (Backend) и JavaScript/CSS (Frontend).

---

## 🐍 1. Python (FastAPI & aiogram)

### Архитектура и слои:
- **`backend/models.py`** — только описание структур данных (Pydantic). Никакой бизнес-логики.
- **`backend/cat_engine.py`** — вся логика расчета адаптивности, стрейков, CEFR и сессий.
- **`backend/telegram_bot.py`** — логика бота, генерация сообщений, отправка уведомлений.
- **`backend/main.py`** — только маршрутизация REST API, монтирование статики и `lifespan`.

### Стиль и типизация:
- **Type Hinting**: все функции обязаны содержать аннотации типов входных параметров и возвращаемого значения (например: `def get_session(self, session_id: str) -> Optional[TestSession]:`).
- **Pydantic v2**: поля с дефолтным `None` обязательно декларируются как `Optional[T] = None`.
- **Логирование**: вместо `print()` в коде бэкенда используется стандартный модуль `logging` с именованными логгерами (`logger = logging.getLogger("...")`).
- **Обработка ошибок**: эндпоинты возвращают стандартные HTTP исключения FastAPI (`raise HTTPException(status_code=404, detail="...")`).

---

## 🌐 2. Frontend (HTML, CSS, JS)

### Архитектура стилей (`style.css`):
- **CSS переменные**: все цвета, радиусы, тени и шрифты определяются в `:root` (`--bg-color`, `--primary`, `--radius-md`). Прямые hex-коды в селекторах не используются.
- **Glassmorphism**: полупрозрачные фоны с `backdrop-filter: blur(...)` и тонкими рамками `rgba(255, 255, 255, 0.08)`.
- **Мобильная адаптивность**: верстка строится по принципу Mobile-First или Fluid с обязательным брейкпоинтом `@media (max-width: 768px)` для корректного отображения внутри Telegram WebApp.

### JavaScript (`app.js`):
- **Чистый Vanilla JS**: без внешних тяжелых библиотек (React, Vue, jQuery).
- **Стейт приложения**: централизованные переменные `sessionId`, `currentQuestion`, `isAnswering`.
- **Telegram SDK**: безопасная проверка `window.Telegram?.WebApp` перед вызовом API мессенджера.
- **Защита от двойного клика**: при выборе ответа флаг `isAnswering = true` блокирует повторные нажатия до получения ответа от сервера.
