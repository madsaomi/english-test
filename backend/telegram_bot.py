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

def format_clean_level(cefr_level: str, level_title: str) -> str:
    """Форматирует уровень без дублирования кода, например: 'B1 · Intermediate' или чистое 'Intermediate'."""
    if not cefr_level:
        return level_title or ""
    if not level_title:
        return cefr_level or ""
    if cefr_level == level_title:
        return level_title
    if "(" in level_title and ")" in level_title:
        title = level_title.replace(" (", " · ").rstrip(")")
        if not title.startswith(cefr_level):
            return f"{cefr_level} · {title}"
        return title
    if level_title.startswith(cefr_level):
        return level_title
    return f"{cefr_level} · {level_title}"

def format_compact_lead_card(name: str, level_code: str, level_title: str,
                             phone: str, received_at: str,
                             branch: Optional[str] = "Главный офис") -> str:
    """Компактная карточка заявки для сотрудника (Вариант A / обратная совместимость)."""
    branch_str = branch if branch else "Главный офис"
    return (
        "🏷 <b>НОВАЯ ЗАЯВКА С ТЕСТА</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Имя:</b> {name}\n"
        f"🏢 <b>Филиал:</b> {branch_str}\n"
        f"🏆 <b>Уровень:</b> {level_code} — {level_title}\n"
        f"📱 <b>Телефон:</b> <code>{phone}</code>\n"
        f"📅 <b>Принято:</b> {received_at}\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )

def _format_mmss(total_seconds: int) -> str:
    """Время в компактном виде MM:SS (2:30 вместо '2 мин 30 сек')."""
    seconds = max(0, int(total_seconds or 0))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _format_skills_line(skills: list) -> str:
    """Навыки в одну строку: Grammar 100% · Vocabulary 88% · Usage 75%."""
    if not skills:
        return ""
    parts = [f"<code>{s.category} {s.score_percentage}%</code>" for s in skills]
    return " · ".join(parts)


def format_unified_lead_card(name: str, phone: Optional[str], username: Optional[str],
                             result: TestResult, received_at: str,
                             branch: Optional[str] = "Главный офис") -> str:
    """Единая карточка заявки Stanford Language Center (одно сообщение).

    Компромисс между «якорем» (уровень наверху) и «реестром» (таблица):
    уровень и метрики — одной строкой-якорем, контакты — компактным блоком,
    навыки — одной строкой. Только один эмодзи и тонкие разделители.
    """
    branch_str = branch if branch else "Главный офис"
    phone_str = phone if phone else "—"
    user_link = f"@{username.lstrip('@')}" if username else "—"

    level_str = format_clean_level(result.cefr_level, result.level_title)
    time_str = _format_mmss(result.total_time_seconds)
    skills_line = _format_skills_line(result.skills)

    metrics = f"<code>{result.correct_count}</code>/<code>{result.total_questions}</code>"
    metrics += f" · <code>{result.accuracy_percentage}%</code>"
    metrics += f" · <code>{time_str}</code>"

    lines = [
        "🏛 <b>Stanford Language Center</b>",
        f"<i>General English Test 2026</i>",
        "",
        f"<b>{level_str}</b>",
        metrics,
        "",
        "───",
        f"<b>{name}</b>",
        branch_str,
        f"<code>{phone_str}</code> · {user_link}",
        received_at,
        "───",
    ]

    if skills_line:
        lines.append(f"<b>Навыки</b>  {skills_line}")

    skipped = getattr(result, "skipped_count", 0) or 0
    if skipped > 0:
        lines.append(f"<b>Пропущено по таймеру</b>  <code>{skipped}</code>")

    if result.weak_topics:
        lines.append(f"<b>Повторить</b>  " + ", ".join(result.weak_topics))
    else:
        lines.append("<b>Повторить</b>  —")

    return "\n".join(lines)

def format_result_card(name: str, phone: Optional[str], username: Optional[str], result: TestResult,
                       branch: Optional[str] = "Главный офис") -> str:
    """Карточка результата для кандидата — тот же визуальный язык, без контактов админа."""
    branch_str = branch if branch else "Главный офис"
    level_str = format_clean_level(result.cefr_level, result.level_title)
    time_str = _format_mmss(result.total_time_seconds)
    skills_line = _format_skills_line(result.skills)

    metrics = f"<code>{result.correct_count}</code>/<code>{result.total_questions}</code>"
    metrics += f" · <code>{result.accuracy_percentage}%</code>"
    metrics += f" · <code>{time_str}</code>"

    lines = [
        "🏛 <b>Stanford Language Center</b>",
        f"<i>Тест уровня английского</i>",
        "",
        f"<b>{level_str}</b>",
        metrics,
        "",
        "───",
        branch_str,
    ]

    if skills_line:
        lines.append(f"<b>Навыки</b>  {skills_line}")

    if result.weak_topics:
        lines.append(f"<b>Повторить</b>  " + ", ".join(result.weak_topics))
    else:
        lines.append("<b>Повторить</b>  —")

    return "\n".join(lines)

def get_lead_action_keyboard(phone: Optional[str], username: Optional[str]) -> Optional[InlineKeyboardMarkup]:
    """Генерирует инлайн-кнопки быстрого действия (написать в Telegram).
    Примечание: Telegram Bot API допускает в url только HTTP/HTTPS-ссылки."""
    buttons = []
    action_row = []
    if username:
        clean_user = username.lstrip("@").strip()
        if clean_user:
            action_row.append(
                InlineKeyboardButton(text="💬 Написать в Telegram", url=f"https://t.me/{clean_user}")
            )
    if action_row:
        buttons.append(action_row)
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None


async def send_admin_lead_notification(lead) -> bool:
    """Отправляет сотруднику (ADMIN_CHAT_ID) единое красивое сообщение с кнопками быстрого действия."""
    if not IS_BOT_ENABLED or not bot or not ADMIN_CHAT_ID:
        logger.info(
            f"[DEMO MODE] Уведомление сотруднику не отправлено (бот/ADMIN_CHAT_ID не настроены): "
            f"{lead.student_name} -> {lead.result.cefr_level}"
        )
        return False

    received_at = lead.received_at.strftime("%d.%m.%Y %H:%M")
    branch = getattr(lead, "branch", "Главный офис") or "Главный офис"
    text = format_unified_lead_card(
        name=lead.student_name,
        phone=lead.phone,
        username=lead.telegram_username,
        result=lead.result,
        received_at=received_at,
        branch=branch,
    )
    keyboard = get_lead_action_keyboard(lead.phone, lead.telegram_username)

    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
        logger.info(f"Единая карточка заявки отправлена сотруднику {ADMIN_CHAT_ID}")
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки единой карточки сотруднику: {e}")
        return False


async def send_student_full_result(name: str, tg_user_id: Optional[int], result: TestResult,
                                  branch: Optional[str] = "Главный офис") -> bool:
    """Отправляет полную карточку результатов самому кандидату (если известен chat_id)."""
    if not IS_BOT_ENABLED or not bot or not tg_user_id:
        return False
    try:
        user_msg = (
            f"🎉 <b>Поздравляем с прохождением теста, {name}!</b>\n\n"
            f"{format_result_card(name=name, phone=None, username=None, result=result, branch=branch)}\n\n"
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
