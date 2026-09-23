import logging
from typing import Optional
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from .config import BOT_TOKEN, ADMIN_CHAT_ID, WEBAPP_URL, IS_BOT_ENABLED
from .models import TestResult

logger = logging.getLogger("telegram_bot")

bot: Optional[Bot] = None
dp: Optional[Dispatcher] = None

if IS_BOT_ENABLED:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

def get_webapp_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    if WEBAPP_URL.startswith("https://"):
        buttons.append([
            InlineKeyboardButton(
                text="🚀 Пройти тест на уровень (Web App)",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="🌐 Открыть сайт теста",
                url=WEBAPP_URL
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

if dp:
    @dp.message(CommandStart())
    async def command_start_handler(message: types.Message):
        user_name = message.from_user.first_name if message.from_user else "Студент"
        welcome_text = (
            f"👋 Привет, <b>{user_name}</b>!\n\n"
            "🎯 Я бот платформы тестирования английского языка (шкала CEFR: A1–C2).\n\n"
            "✨ <b>Как устроен тест:</b>\n"
            "• General English Test 2026: 50 вопросов — грамматика, лексика и употребление.\n"
            "• 45 вопросов с выбором варианта и 5 с вводом ответа.\n"
            "• Результат (уровень, точность, навыки) придёт вам прямо сюда.\n\n"
            "Нажмите кнопку ниже, чтобы начать:"
        )
        await message.answer(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_webapp_keyboard()
        )

    @dp.message(Command("help"))
    async def command_help_handler(message: types.Message):
        help_text = (
            "ℹ️ <b>Справка:</b>\n\n"
            "Этот бот интегрирован с веб-платформой тестирования английского языка.\n"
            "Пройдите тест по ссылке, и ваши результаты (уровень, грамматика, словарный запас и слабые темы) "
            "будут сохранены и отправлены вам прямо сюда!"
        )
        await message.answer(help_text, parse_mode=ParseMode.HTML)

def format_result_card(name: str, phone: Optional[str], username: Optional[str], result: TestResult) -> str:
    # Графический индикатор
    progress_blocks = "🟩" * (result.score // 10) + "⬜" * (10 - (result.score // 10))
    
    minutes = result.total_time_seconds // 60
    seconds = result.total_time_seconds % 60
    time_str = f"{minutes} мин {seconds} сек" if minutes > 0 else f"{seconds} сек"

    user_link = f"@{username}" if username else "Не указан"
    phone_str = phone if phone else "Не указан"

    skills_lines = []
    for skill in result.skills:
        skills_lines.append(f"• <b>{skill.category}:</b> {skill.level} ({skill.score_percentage}%)")
    skills_text = "\n".join(skills_lines)

    weak_text = "\n".join([f"• <i>{topic}</i>" for topic in result.weak_topics]) if result.weak_topics else "Ошибок почти нет!"

    card = (
        "🎓 <b>РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ АНГЛИЙСКОГО (CAT)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Кандидат:</b> {name}\n"
        f"📱 <b>Телефон:</b> <code>{phone_str}</code>\n"
        f"💬 <b>Telegram:</b> {user_link}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 <b>Итоговый уровень:</b> <b>{result.cefr_level}</b> — {result.level_title}\n"
        f"📊 <b>Общий балл:</b> <b>{result.score}/100</b>\n"
        f"📈 <b>Шкала:</b> [{progress_blocks}]\n"
        f"🎯 <b>Точность:</b> {result.correct_count} из {result.total_questions} вопросов ({result.accuracy_percentage}%)\n"
        f"⏱ <b>Время теста:</b> {time_str}\n\n"
        f"📚 <b>Детализация по навыкам:</b>\n{skills_text}\n\n"
        f"⚠️ <b>Темы для повторения:</b>\n{weak_text}\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )
    return card

def format_compact_lead_card(name: str, level_code: str, level_title: str,
                             phone: str, received_at: str) -> str:
    """Компактная карточка заявки для сотрудника (Вариант A)."""
    return (
        "🏷 <b>НОВАЯ ЗАЯВКА С ТЕСТА</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Имя:</b> {name}\n"
        f"🏆 <b>Уровень:</b> {level_code} — {level_title}\n"
        f"📱 <b>Телефон:</b> <code>{phone}</code>\n"
        f"📅 <b>Принято:</b> {received_at}\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )


async def send_admin_lead_notification(lead) -> bool:
    """Отправляет сотруднику (ADMIN_CHAT_ID) ДВА сообщения подряд:
    1) компактная карточка, 2) детальный результат кандидата."""
    if not IS_BOT_ENABLED or not bot or not ADMIN_CHAT_ID:
        logger.info(
            f"[DEMO MODE] Уведомление сотруднику не отправлено (бот/ADMIN_CHAT_ID не настроены): "
            f"{lead.student_name} -> {lead.result.cefr_level}"
        )
        return False

    received_at = lead.received_at.strftime("%d.%m.%Y %H:%M")
    compact = format_compact_lead_card(
        name=lead.student_name,
        level_code=lead.result.cefr_level,
        level_title=lead.result.level_title,
        phone=lead.phone,
        received_at=received_at,
    )
    detailed = format_result_card(
        name=lead.student_name,
        phone=lead.phone,
        username=lead.telegram_username,
        result=lead.result,
    )

    sent = True
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=compact, parse_mode=ParseMode.HTML)
    except Exception as e:
        sent = False
        logger.error(f"Ошибка отправки карточки сотруднику: {e}")

    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"📊 <b>Детальный результат кандидата «{lead.student_name}»:</b>\n\n{detailed}",
            parse_mode=ParseMode.HTML
        )
        sent = sent and True
        logger.info(f"Карточка и детали отправлены сотруднику {ADMIN_CHAT_ID}")
    except Exception as e:
        sent = False
        logger.error(f"Ошибка отправки детального результата сотруднику: {e}")

    return sent


async def send_student_full_result(name: str, tg_user_id: Optional[int], result: TestResult) -> bool:
    """Отправляет полную карточку результатов самому кандидату (если известен chat_id)."""
    if not IS_BOT_ENABLED or not bot or not tg_user_id:
        return False
    try:
        user_msg = (
            f"🎉 <b>Поздравляем с прохождением теста, {name}!</b>\n\n"
            f"{format_result_card(name=name, phone=None, username=None, result=result)}\n\n"
            "💡 <b>Рекомендации преподавателя:</b>\n" +
            "\n".join([f"✨ {r}" for r in result.recommendations])
        )
        await bot.send_message(chat_id=tg_user_id, text=user_msg, parse_mode=ParseMode.HTML)
        logger.info(f"Отчет успешно отправлен ученику {tg_user_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки ученику {tg_user_id}: {e}")
        return False


async def send_result_notifications(
    name: str,
    phone: Optional[str],
    username: Optional[str],
    tg_user_id: Optional[int],
    result: TestResult
) -> bool:
    """Совместимая обёртка: отправляет уведомление сотруднику и кандидату."""
    if not IS_BOT_ENABLED or not bot:
        logger.info(f"[DEMO MODE] Telegram уведомление не отправлено (бот не настроен в .env): {name} -> {result.cefr_level}")
        return False

    sent_admin = False
    if ADMIN_CHAT_ID:
        try:
            card = format_result_card(name, phone, username, result)
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"🔔 <b>НОВАЯ ЗАЯВКА С ТЕСТА!</b>\n\n{card}",
                parse_mode=ParseMode.HTML
            )
            sent_admin = True
        except Exception as e:
            logger.error(f"Ошибка отправки администратору: {e}")

    sent_student = await send_student_full_result(name, tg_user_id, result)
    return sent_admin or sent_student
