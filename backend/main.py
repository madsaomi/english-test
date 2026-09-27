import asyncio
import hashlib
import hmac
import json
import logging
import re
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from typing import List, Optional
from .config import (
    HOST,
    PORT,
    IS_BOT_ENABLED,
    BOT_TOKEN,
    ADMIN_CHAT_ID,
    WEBAPP_URL,
    ALLOWED_ORIGINS,
    EXPORT_API_KEY,
    IS_CORS_WILDCARD,
    RATE_LIMIT_ENABLED,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    SHOW_INTERNAL_METRICS,
)
from .models import (
    StartTestRequest,
    StartTestResponse,
    AnswerSubmission,
    UserContactSubmission,
    TestResult,
    ClientQuestion,
    TestSuiteMeta
)
from .cat_engine import cat_engine
from .test_loader import test_repository, DEFAULT_TEST_ID
from .telegram_bot import bot, dp, send_admin_lead_notification
from .lead_store import lead_store, LeadRecord

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main_server")

bot_task: asyncio.Task = None
gc_task: asyncio.Task = None

GC_INTERVAL_SECONDS = 600
GC_MAX_AGE_SECONDS = 24 * 3600


def verify_telegram_init_data(init_data: str, bot_token: str) -> bool:
    """Проверка подписи WebApp initData по официальной схеме Telegram.

    secret_key = HMAC_SHA256(key='WebAppData', data=BOT_TOKEN)
    calc_hash  = HMAC_SHA256(key=secret_key, data=data_check_string)
    data_check_string = отсортированные по ключу пары 'k=v' без поля 'hash', разделённые \n.
    """
    try:
        parsed = dict(parse_qsl(init_data))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return False
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )
        secret_key = hmac.new(
            b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256
        ).digest()
        calc_hash = hmac.new(
            secret_key, data_check_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(calc_hash, received_hash)
    except Exception:
        return False


async def _garbage_collector() -> None:
    """Периодическая очистка устаревших сессий (состояние EXPIRED)."""
    while True:
        await asyncio.sleep(GC_INTERVAL_SECONDS)
        try:
            cat_engine.cleanup_expired_sessions(max_age_seconds=GC_MAX_AGE_SECONDS)
        except Exception as e:
            logger.error(f"GC ошибка: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_task, gc_task
    logger.info("🚀 Запуск единого сервера English CAT Platform...")
    
    # Фоновая очистка устаревших сессий (всегда активна)
    gc_task = asyncio.create_task(_garbage_collector())

    # --- Предупреждения безопасности на старте ---
    if IS_CORS_WILDCARD:
        logger.warning(
            "⚠️ CORS: ALLOWED_ORIGINS не задан → разрешён любой origin ('*'). "
            "В проде обязательно укажите домен сайта, например "
            "ALLOWED_ORIGINS=https://<service>.up.railway.app"
        )
    else:
        logger.warning(
            "⚠️ CORS: задан список origins и одновременно allow_credentials=True. "
            "Если cookies не используются — это лишнее, лучше оставить '*' без credentials."
        )

    if RATE_LIMIT_ENABLED:
        logger.info(
            f"🛡️ Rate limit: {RATE_LIMIT_REQUESTS} мутационных запросов за "
            f"{RATE_LIMIT_WINDOW_SECONDS}с на IP+User-Agent. "
            "Учтите CGNAT: мобильные операторы делят IP между пользователями."
        )
    else:
        logger.warning("⚠️ Rate limit ВЫКЛЮЧЁН (RATE_LIMIT_ENABLED=false) — эндпоинты не защищены от спама.")

    if not EXPORT_API_KEY:
        logger.warning("⚠️ EXPORT_API_KEY не задан → /api/export/leads отвечает 503 (отключён).")

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
    if gc_task and not gc_task.done():
        gc_task.cancel()
        try:
            await gc_task
        except asyncio.CancelledError:
            pass
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
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=(ALLOWED_ORIGINS != ["*"]),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Rate limiting (sliding window per client) -----------------

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_rate_buckets: dict = defaultdict(deque)


def _client_key(request: Request) -> str:
    """Ключ бакета: IP (с X-Forwarded-For при наличии) + хеш User-Agent."""
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    ua = request.headers.get("user-agent", "")
    ua_hash = hashlib.sha256(ua.encode("utf-8")).hexdigest()[:8]
    return f"{ip}|{ua_hash}"


def _cleanup_rate_buckets(now: float) -> None:
    """Периодическая чистка протухших бакетов, чтобы не течь по памяти."""
    for key in [k for k, hits in _rate_buckets.items() if not hits or hits[-1] < now - RATE_LIMIT_WINDOW_SECONDS]:
        _rate_buckets.pop(key, None)


if RATE_LIMIT_ENABLED:
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        if request.method not in MUTATING_METHODS or not request.url.path.startswith("/api/"):
            return await call_next(request)

        now = time.monotonic()
        _cleanup_rate_buckets(now)

        key = _client_key(request)
        hits = _rate_buckets[key]
        if len(hits) >= RATE_LIMIT_REQUESTS:
            retry_after = max(1, int(RATE_LIMIT_WINDOW_SECONDS - (now - hits[0])))
            logger.warning(
                f"Rate limit: {key} превысил {RATE_LIMIT_REQUESTS} запросов за "
                f"{RATE_LIMIT_WINDOW_SECONDS}с на {request.url.path}"
            )
            return JSONResponse(
                status_code=429,
                content={"detail": f"Слишком много запросов. Повторите через {retry_after} сек."},
                headers={"Retry-After": str(retry_after)},
            )

        hits.append(now)
        return await call_next(request)

# ----------------- REST API Endpoints -----------------

@app.get("/api/health")
async def health_check():
    payload = {
        "status": "ok",
        "bot_enabled": IS_BOT_ENABLED,
        "admin_chat_configured": bool(ADMIN_CHAT_ID),
        "total_questions_in_bank": len(test_repository.get_all_questions_pool()),
    }
    # Технические метрики (например, число активных сессий) не отдаются наружу
    # по умолчанию — включаются флагом SHOW_INTERNAL_METRICS.
    if SHOW_INTERNAL_METRICS:
        payload["active_sessions"] = len(cat_engine.sessions)
    return payload

@app.get("/api/tests", response_model=List[TestSuiteMeta])
async def list_available_tests():
    return test_repository.get_all_tests_meta()

@app.post("/api/test/start", response_model=StartTestResponse)
async def start_test(payload: Optional[StartTestRequest] = None):
    test_id = payload.test_id if payload and payload.test_id else None
    session = cat_engine.create_session(test_id=test_id)
    first_q = cat_engine.select_next_question(session)
    if not first_q:
        raise HTTPException(status_code=500, detail="Ошибка банка вопросов")
    
    client_q = cat_engine.to_client_question(session, first_q)
    return StartTestResponse(
        session_id=session.session_id,
        first_question=client_q,
        test_title=session.test_title,
        test_mode=session.test_mode
    )

class AnswerResponse(BaseModel):
    is_finished: bool
    current_difficulty_label: str
    next_question: Optional[ClientQuestion] = None
    result: Optional[TestResult] = None

@app.post("/api/test/answer", response_model=AnswerResponse)
async def answer_question(payload: AnswerSubmission):
    session = cat_engine.get_session(payload.session_id)
    if not session:
        logger.warning(
            "404 answer: session not found sid=%s qid=%s (restart or expired?)",
            payload.session_id, payload.question_id,
        )
        raise HTTPException(status_code=404, detail="Сессия тестирования не найдена")
    if session.is_finished:
        raise HTTPException(status_code=400, detail="Тест уже завершен")

    question = cat_engine.find_question(session, payload.question_id)
    if not question:
        logger.warning(
            "404 answer: question not found sid=%s qid=%s",
            payload.session_id, payload.question_id,
        )
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    if payload.is_timeout:
        # Автоматический таймаут (30/35 сек истекли)
        pass
    elif question.question_type == "text":
        if payload.selected_text is None or not payload.selected_text.strip():
            raise HTTPException(status_code=400, detail="Введите ответ")
    else:
        if payload.selected_option is None or payload.selected_option < 0:
            raise HTTPException(status_code=400, detail="Не выбран вариант ответа")

    # H1 (audit 2026-09-27): правильность ответа клиенту НЕ отдаём — фронтенд
    # её не использует, а публикация позволяет скриптом вытянуть весь ключ ответов.
    cat_engine.submit_answer(
        session=session,
        question_id=payload.question_id,
        selected_option=payload.selected_option,
        time_spent=payload.time_spent_seconds,
        selected_text=payload.selected_text,
        is_timeout=payload.is_timeout,
    )

    should_end = cat_engine.should_finish(session)
    if should_end:
        result = cat_engine.finalize_test(session)
        return AnswerResponse(
            is_finished=True,
            current_difficulty_label=result.level_title,
            next_question=None,
            result=result
        )

    next_q = cat_engine.select_next_question(session)
    if not next_q:
        result = cat_engine.finalize_test(session)
        return AnswerResponse(
            is_finished=True,
            current_difficulty_label=result.level_title,
            next_question=None,
            result=result
        )

    client_q = cat_engine.to_client_question(session, next_q)
    return AnswerResponse(
        is_finished=False,
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
    if not payload.name or not payload.name.strip():
        raise HTTPException(status_code=400, detail="ФИО обязательно")
    if not payload.phone or not payload.phone.strip():
        raise HTTPException(status_code=400, detail="Телефон обязателен")

    phone_clean = re.sub(r"\D", "", payload.phone)
    if not (len(phone_clean) == 12 and phone_clean.startswith("998")):
        raise HTTPException(
            status_code=400,
            detail="Номер телефона должен быть в формате Узбекистана: +998 (XX) XXX-XX-XX"
        )
    formatted_phone = f"+998 ({phone_clean[3:5]}) {phone_clean[5:8]}-{phone_clean[8:10]}-{phone_clean[10:12]}"

    session = cat_engine.get_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия тестирования не найдена")

    if not session.result:
        cat_engine.finalize_test(session)

    # Валидация Telegram WebApp initData (анти-спуфинг tg_user_id).
    # Если клиент прислал tg_user_id, он обязан подтвердить его подписью initData.
    # Иначе проверку можно обойти, просто не отправив поле (антипаттерн).
    if payload.tg_user_id is not None:
        if not IS_BOT_ENABLED:
            raise HTTPException(
                status_code=403,
                detail="Проверка Telegram недоступна: сервер работает без BOT_TOKEN"
            )
        if not payload.tg_init_data:
            raise HTTPException(
                status_code=403,
                detail="Невалидные данные Telegram WebApp: initData обязательна вместе с tg_user_id"
            )
        if not verify_telegram_init_data(payload.tg_init_data, BOT_TOKEN):
            raise HTTPException(status_code=403, detail="Невалидные данные Telegram WebApp")
        try:
            query = dict(parse_qsl(payload.tg_init_data))
            user_json = json.loads(query.get("user", "{}"))
            if isinstance(user_json, dict) and user_json.get("id") is not None:
                # id берём только из подписанных данных, поле клиента игнорируем
                session.tg_user_id = user_json["id"]
        except (ValueError, TypeError):
            pass
    elif payload.tg_init_data and IS_BOT_ENABLED:
        if not verify_telegram_init_data(payload.tg_init_data, BOT_TOKEN):
            raise HTTPException(status_code=403, detail="Невалидные данные Telegram WebApp")
        try:
            query = dict(parse_qsl(payload.tg_init_data))
            user_json = json.loads(query.get("user", "{}"))
            if isinstance(user_json, dict) and user_json.get("id") is not None:
                payload.tg_user_id = user_json["id"]
        except (ValueError, TypeError):
            pass

    session.user_name = payload.name.strip()
    session.user_phone = formatted_phone
    session.tg_username = payload.telegram_username
    if payload.tg_user_id is not None:
        session.tg_user_id = payload.tg_user_id
    branch_val = (payload.branch or "Главный офис").strip()
    session.branch = branch_val

    lead = LeadRecord(
        session_id=payload.session_id,
        student_name=session.user_name,
        phone=session.user_phone,
        telegram_username=session.tg_username,
        tg_user_id=session.tg_user_id,
        test_id=session.test_id,
        received_at=datetime.now(),
        result=session.result,
        branch=branch_val,
    )
    lead_store.add_lead(lead)

    # Результат уходит ТОЛЬКО сотруднику. Кандидату ничего не отправляем:
    # раскрытие уровня убирает смысл звонка (решение владельца, PLAN-032).
    sent = await send_admin_lead_notification(lead)
    session.result.telegram_sent = sent

    return {
        "status": "success",
        "telegram_sent": sent,
        "is_bot_enabled": IS_BOT_ENABLED
    }

# ----------------- Экспорт лидов для CRM / преподавателей -----------------

class LeadExportItem(BaseModel):
    session_id: str
    student_name: Optional[str] = None
    phone: Optional[str] = None
    telegram_username: Optional[str] = None
    branch: Optional[str] = "Главный офис"
    test_id: Optional[str] = None
    cefr_level: Optional[str] = None
    level_title: Optional[str] = None
    score: Optional[int] = None
    accuracy_pct: Optional[int] = None
    time_seconds: Optional[int] = None
    weak_topics: List[str] = []

@app.get("/api/export/leads")
async def export_leads(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    # Эндпоинт отдаёт персональные данные (ФИО, телефон, Telegram) — защищён ключом.
    if not EXPORT_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Экспорт лидов отключён: не задан EXPORT_API_KEY на сервере"
        )
    if not x_api_key or not hmac.compare_digest(x_api_key, EXPORT_API_KEY):
        raise HTTPException(
            status_code=401,
            detail="Требуется корректный заголовок X-API-Key"
        )

    leads: List[LeadExportItem] = []
    for lead in lead_store.list_leads():
        leads.append(LeadExportItem(
            session_id=lead.session_id,
            student_name=lead.student_name,
            phone=lead.phone,
            telegram_username=lead.telegram_username,
            branch=getattr(lead, "branch", "Главный офис") or "Главный офис",
            test_id=lead.test_id,
            cefr_level=lead.result.cefr_level,
            level_title=lead.result.level_title,
            score=lead.result.score,
            accuracy_pct=lead.result.accuracy_percentage,
            time_seconds=lead.result.total_time_seconds,
            weak_topics=lead.result.weak_topics
        ))
    return leads

# ----------------- Статические файлы фронтенда -----------------
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)
