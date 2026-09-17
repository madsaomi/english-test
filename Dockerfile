# Dockerfile for English CAT Platform & Telegram Bot
FROM python:3.11-slim

# Установка рабочей директории
WORKDIR /app

# Оптимизация Python для контейнера
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY backend/ ./backend/
COPY static/ ./static/
COPY agents/ ./agents/
COPY AGENTS.md .
COPY .env.example .

# Порт приложения
EXPOSE 8000

# Запуск единого сервера с поддержкой динамического порта Railway ($PORT)
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
