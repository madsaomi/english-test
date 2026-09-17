import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import HOST, PORT, IS_BOT_ENABLED, BOT_TOKEN, ADMIN_CHAT_ID, WEBAPP_URL
from .models import (
    StartTestResponse,
    AnswerSubmission,
    UserContactSubmission,
    TestResult,
    ClientQuestion
)
from .cat_engine import cat_engine
from .telegram_bot import bot, dp, send_result_notifications

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main_server")

bot_task: asyncio.Task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_task
    logger.info("🚀 Запуск единого сервера English CAT Platform...")
    
    if IS_BOT_ENABLED and dp and bot:
        logger.info(f"🤖 Запуск Telegram-бота (aiogram polling). URL: {WEBAPP_URL}")
        # Удаляем старые вебхуки перед запуском polling
        await bot.delete_webhook(drop_pending_updates=True)
        bot_task = asyncio.create_task(dp.start_polling(bot))
    else:
        logger.warning(
            "⚠️ ВНИМАНИЕ: Telegram-бот запущен в ДЕМО-режиме (без BOT_TOKEN). "
            "Сайт и тест полностью функционируют! Чтобы активировать бота, добавьте BOT_TOKEN в файл .env"
        )

    yield

    logger.info("🛑 Остановка сервисов...")
    if bot_task and not bot_task.done():
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
    if bot:
        await bot.session.close()
    logger.info("Сервер успешно остановлен.")

app = FastAPI(
    title="English Level CAT Platform",
    description="Adaptive Computerized English Testing System with Telegram Bot Integration",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- REST API Endpoints -----------------

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "bot_enabled": IS_BOT_ENABLED,
        "admin_chat_configured": bool(ADMIN_CHAT_ID),
        "total_questions_in_bank": len(cat_engine.sessions)
    }

@app.post("/api/test/start", response_model=StartTestResponse)
async def start_test():
    session = cat_engine.create_session()
    first_q = cat_engine.select_next_question(session)
    if not first_q:
        raise HTTPException(status_code=500, detail="Ошибка банка вопросов")
    
    client_q = cat_engine.to_client_question(session, first_q)
    return StartTestResponse(session_id=session.session_id, first_question=client_q)

from typing import Optional

class AnswerResponse(BaseModel):
    is_finished: bool
    is_correct: bool
    current_difficulty_label: str
    next_question: Optional[ClientQuestion] = None
    result: Optional[TestResult] = None

@app.post("/api/test/answer", response_model=AnswerResponse)
async def answer_question(payload: AnswerSubmission):
    session = cat_engine.get_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия тестирования не найдена")
    if session.is_finished:
        raise HTTPException(status_code=400, detail="Тест уже завершен")

    is_correct = cat_engine.submit_answer(
        session=session,
        question_id=payload.question_id,
        selected_option=payload.selected_option,
        time_spent=payload.time_spent_seconds
    )

    should_end = cat_engine.should_finish(session)
    if should_end:
        result = cat_engine.finalize_test(session)
        return AnswerResponse(
            is_finished=True,
            is_correct=is_correct,
            current_difficulty_label=result.level_title,
            next_question=None,
            result=result
        )

    next_q = cat_engine.select_next_question(session)
    if not next_q:
        result = cat_engine.finalize_test(session)
        return AnswerResponse(
            is_finished=True,
            is_correct=is_correct,
            current_difficulty_label=result.level_title,
            next_question=None,
            result=result
        )

    client_q = cat_engine.to_client_question(session, next_q)
    return AnswerResponse(
        is_finished=False,
        is_correct=is_correct,
        current_difficulty_label=client_q.current_difficulty_label,
        next_question=client_q,
        result=None
    )

@app.get("/api/test/result/{session_id}", response_model=TestResult)
async def get_test_result(session_id: str):
    session = cat_engine.get_session(session_id)
    if not session or not session.result:
        raise HTTPException(status_code=404, detail="Результат теста не найден")
    return session.result

@app.post("/api/test/submit-contact")
async def submit_user_contact(payload: UserContactSubmission):
    session = cat_engine.get_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия тестирования не найдена")

    if not session.result:
        cat_engine.finalize_test(session)

    session.user_name = payload.name
    session.user_phone = payload.phone
    session.tg_username = payload.telegram_username
    session.tg_user_id = payload.tg_user_id

    sent = await send_result_notifications(
        name=payload.name,
        phone=payload.phone,
        username=payload.telegram_username,
        tg_user_id=payload.tg_user_id,
        result=session.result
    )
    session.result.telegram_sent = sent

    return {
        "status": "success",
        "telegram_sent": sent,
        "is_bot_enabled": IS_BOT_ENABLED
    }

# ----------------- Статические файлы фронтенда -----------------
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)
