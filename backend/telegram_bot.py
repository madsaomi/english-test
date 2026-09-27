import html
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
    """Время в компактном виде: 02:30 вместо '2 мин 30 сек'."""
    seconds = max(0, int(total_seconds or 0))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _esc(value) -> str:
    """Экранирование HTML.

    Обязательно: Telegram отклоняет сообщение при неэкранированном виде,
    а в имя/филиал/тему попадают данные пользователя.
    """
    return html.escape(str(value if value is not None else ""), quote=False)


# Максимум тем в блоке «Темы для повторения» — карточка не должна растягиваться
WEAK_TOPICS_LIMIT = 5


def _format_weak_topics(topics: list) -> str:
    if not topics:
        return "—"
    shown = list(topics)[:WEAK_TOPICS_LIMIT]
    rest = len(topics) - len(shown)
    text = ", ".join(_esc(t) for t in shown)
    if rest > 0:
        text += f" <i>и ещё {rest}</i>"
    return text


def _format_skills_block(skills: list) -> list:
    """Блок «Навыки». Уровень по навыку (A2/B1) убран: он дублировал итоговый."""
    return [f"• {_esc(skill.category)} {skill.score_percentage}%" for skill in skills]


def _format_metrics_block(result: TestResult) -> list:
    """Метрики. Строка про пропуски печатается только когда пропуски есть."""
    lines = [
        f"📊 {result.score}/100",
        f"🎯 {result.correct_count} из {result.total_questions} · {result.accuracy_percentage}%",
    ]
    skipped = getattr(result, "skipped_count", 0) or 0
    if skipped > 0:
        lines.append(f"⏳ Пропущено по таймеру: {skipped}")
    lines.append(f"⏱ {_format_mmss(result.total_time_seconds)}")
    return lines


def _format_header(subtitle: str) -> list:
    """Шапка карточки. Блок разделяется пустой строкой, а не линейкой."""
    return [
        "🏛 <b>Stanford Language Center</b>",
        f"<i>{_esc(subtitle)}</i>",
        "",
    ]


def _format_tg_link(username: Optional[str]) -> str:
    if not username:
        return "—"
    return "@" + _esc(username.lstrip("@"))


def format_unified_lead_card(name: str, phone: Optional[str], username: Optional[str],
                             result: TestResult, received_at: str,
                             branch: Optional[str] = "Главный офис") -> str:
    """Карточка заявки для сотрудника: одно сообщение, исходная структура, минимум шума."""
    level_str = format_clean_level(result.cefr_level, result.level_title)

    lines = _format_header("Результат тестирования английского")
    lines += [
        f"👤 <b>{_esc(name)}</b>",
        f"🏢 {_esc(branch) if branch else 'Главный офис'}",
        f"📱 <code>{_esc(phone) if phone else '—'}</code>",
        f"💬 {_format_tg_link(username)}",
        f"📅 {_esc(received_at)}",
        "",
        f"🏆 <b>{_esc(level_str)}</b>",
    ]
    lines += _format_metrics_block(result)
    lines.append("")
    lines.append("📚 <b>Навыки</b>")
    lines += _format_skills_block(result.skills)
    lines.append("")
    lines.append("⚠️ <b>Темы для повторения</b>")
    lines.append(_format_weak_topics(result.weak_topics))
    return "\n".join(lines)


def format_result_card(name: str, phone: Optional[str], username: Optional[str], result: TestResult,
                       branch: Optional[str] = "Главный офис") -> str:
    """Карточка результата для кандидата: тот же язык, без блока контактов администратора."""
    level_str = format_clean_level(result.cefr_level, result.level_title)

    lines = _format_header("Тест уровня английского")
    lines += [
        f"👤 <b>{_esc(name)}</b>",
        f"🏢 {_esc(branch) if branch else 'Главный офис'}",
        "",
        f"🏆 <b>{_esc(level_str)}</b>",
    ]
    lines += _format_metrics_block(result)
    lines.append("")
    lines.append("📚 <b>Навыки</b>")
    lines += _format_skills_block(result.skills)
    lines.append("")
    lines.append("⚠️ <b>Темы для повторения</b>")
    lines.append(_format_weak_topics(result.weak_topics))
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
