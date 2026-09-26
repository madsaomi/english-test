import uuid
import math
import random
import time
import logging
from typing import Dict, List, Optional, Set
from .models import Question, ClientQuestion, TestResult, SkillBreakdown, QuestionReviewItem
from .test_loader import test_repository, DEFAULT_TEST_ID

logger = logging.getLogger("cat_engine")

CEFR_LEVELS = [
    (1.0, 1.6, "A1", "A1 (Beginner)", "Начальный уровень владения языком. Понимание базовых фраз, построение простых предложений."),
    (1.6, 2.5, "A2", "A2 (Elementary)", "Элементарный уровень. Общение на простые повседневные темы, знание базовых временных форм."),
    (2.5, 3.5, "B1", "B1 (Intermediate)", "Средний уровень. Понимание сути бесед на знакомые темы, уверенное выражение мыслей в путешествиях и на работе."),
    (3.5, 4.5, "B2", "B2 (Upper-Intermediate)", "Продвинутый уровень. Свободное общение с носителями, понимание сложной грамматики и идиом."),
    (4.5, 5.5, "C1", "C1 (Advanced)", "Профессиональный уровень. Свободное беглое владение, инверсии, сослагательное наклонение, богатый словарный запас."),
    (5.5, 6.01, "C2", "C2 (Mastery / Proficiency)", "Уровень носителя языка. Абсолютное понимание нюансов, тонких идиоматических выражений и сложной стилистики."),
]

# Шкала оценки для фиксированного теста на 50 вопросов (General English Test 2026)
FIXED_50_SCORING_TABLE = [
    (0, 15, "Beginner", "Beginner", "Начальный уровень владения языком. Понимание базовых фраз, построение простых предложений."),
    (16, 24, "Elementary", "Elementary", "Элементарный уровень. Общение на простые повседневные темы, знание базовых временных форм."),
    (25, 32, "Pre-Intermediate", "Pre-Intermediate", "Уровень ниже среднего. Понимание несложных текстов, диалоги на знакомые темы, базовая грамматика."),
    (33, 39, "Intermediate", "Intermediate", "Средний уровень. Понимание сути бесед на знакомые темы, уверенное выражение мыслей в путешествиях и на работе."),
    (40, 45, "Upper-Intermediate", "Upper-Intermediate", "Продвинутый уровень. Свободное общение с носителями, понимание сложной грамматики и идиом."),
    (46, 50, "Advanced", "Advanced", "Профессиональный уровень. Свободное беглое владение языком, богатый словарный запас и точные грамматические структуры."),
]

def map_score_to_fixed_level(correct_count: int):
    correct_count = max(0, min(50, correct_count))
    for low, high, code, title, desc in FIXED_50_SCORING_TABLE:
        if low <= correct_count <= high:
            return code, title, desc
    return FIXED_50_SCORING_TABLE[-1][2], FIXED_50_SCORING_TABLE[-1][3], FIXED_50_SCORING_TABLE[-1][4]

def map_ability_to_cefr(ability: float):
    ability = max(1.0, min(6.0, ability))
    for low, high, code, title, desc in CEFR_LEVELS:
        if low <= ability < high:
            return code, title, desc
    return "C2", "C2 (Mastery / Proficiency)", CEFR_LEVELS[-1][4]

class TestSession:
    def __init__(self, session_id: str, test_id: str = DEFAULT_TEST_ID):
        self.session_id: str = session_id
        self.test_id: str = test_id
        self.test_title: str = "CEFR Adaptive Test"
        self.test_mode: str = "adaptive"  # "adaptive" or "fixed"
        self.curated_questions: List[Question] = []
        self.ability: float = 3.0  # Начинаем со среднего уровня (B1)
        self.streak: int = 0       # Положительный для серии верных, отрицательный для неверных
        self.history: List[dict] = []
        self.asked_question_ids: Set[str] = set()
        self.current_question: Optional[Question] = None
        self.min_questions: int = 10
        self.max_questions: int = 14
        self.is_finished: bool = False
        self.user_name: Optional[str] = None
        self.user_phone: Optional[str] = None
        self.tg_username: Optional[str] = None
        self.tg_user_id: Optional[int] = None
        self.result: Optional[TestResult] = None
        self.last_activity: float = time.time()

class CATEngine:
    def __init__(self):
        self.sessions: Dict[str, TestSession] = {}

    def create_session(self, test_id: Optional[str] = None) -> TestSession:
        session_id = str(uuid.uuid4())

        suite = test_repository.get_test_suite(test_id) if test_id else None
        if not suite:
            suite = test_repository.get_test_suite(test_repository.get_default_test_id())

        resolved_id = suite.id if suite else (test_id or DEFAULT_TEST_ID)
        session = TestSession(session_id, test_id=resolved_id)

        if suite:
            session.test_title = suite.title
            session.test_mode = suite.mode
            if suite.mode == "fixed":
                session.curated_questions = list(suite.questions)
                session.min_questions = len(suite.questions)
                session.max_questions = len(suite.questions)
            else:
                session.curated_questions = list(suite.questions) if suite.questions else test_repository.get_all_questions_pool()
                session.min_questions = min(10, len(session.curated_questions))
                session.max_questions = min(14, len(session.curated_questions))
        else:
            session.curated_questions = test_repository.get_all_questions_pool()

        self.sessions[session_id] = session
        return session

    def find_question(self, session: TestSession, question_id: str) -> Optional[Question]:
        if session.current_question and session.current_question.id == question_id:
            return session.current_question
        q = next((item for item in session.curated_questions if item.id == question_id), None)
        if q:
            return q
        pool = test_repository.get_all_questions_pool()
        return next((item for item in pool if item.id == question_id), None)

    def get_session(self, session_id: str) -> Optional[TestSession]:
        return self.sessions.get(session_id)

    def cleanup_expired_sessions(self, max_age_seconds: float = 86400) -> int:
        """Удаляет неактивные более max_age_seconds сессии (состояние EXPIRED)."""
        now = time.time()
        expired_ids = [
            sid for sid, s in self.sessions.items()
            if now - (s.last_activity or now) > max_age_seconds
        ]
        for sid in expired_ids:
            self.sessions.pop(sid, None)
        if expired_ids:
            logger.info(f"🗑 GC: удалено устаревших сессий: {len(expired_ids)}")
        return len(expired_ids)

    def select_next_question(self, session: TestSession) -> Optional[Question]:
        if session.test_mode == "fixed":
            # В фиксированном тесте выдаем вопросы строго по порядку из набора
            for q in session.curated_questions:
                if q.id not in session.asked_question_ids:
                    session.current_question = q
                    session.asked_question_ids.add(q.id)
                    return q
            return None

        # В адаптивном режиме подбираем вопрос по CAT-алгоритму
        pool = session.curated_questions if session.curated_questions else test_repository.get_all_questions_pool()
        available = [q for q in pool if q.id not in session.asked_question_ids]
        if not available:
            # Fallback на полный пул вопросов если вопросы набора исчерпались
            all_pool = test_repository.get_all_questions_pool()
            available = [q for q in all_pool if q.id not in session.asked_question_ids]
            if not available:
                return None

        # Очередность категорий для баланса: Grammar -> Vocabulary -> Usage
        category_order = ["Grammar", "Vocabulary", "Usage"]
        target_category = category_order[len(session.history) % len(category_order)]

        category_candidates = [q for q in available if q.category == target_category]
        candidates = category_candidates if category_candidates else available

        # Выбираем вопрос, наиболее близкий к текущему рейтингу ability
        # С небольшим элементом рандомизации среди топ-2 подходящих
        candidates.sort(key=lambda q: abs(q.difficulty - session.ability))
        selected = random.choice(candidates[:min(2, len(candidates))])
        session.current_question = selected
        session.asked_question_ids.add(selected.id)
        return selected

    def to_client_question(self, session: TestSession, question: Question) -> ClientQuestion:
        _, label, _ = map_ability_to_cefr(session.ability)
        return ClientQuestion(
            id=question.id,
            question_number=len(session.history) + 1,
            total_estimated=session.max_questions,
            category=question.category,
            topic=question.topic,
            text=question.text,
            question_type=question.question_type,
            options=question.options,
            current_difficulty_label=label,
        )

    def submit_answer(
        self,
        session: TestSession,
        question_id: str,
        selected_option: Optional[int] = None,
        time_spent: float = 0.0,
        selected_text: Optional[str] = None,
        is_timeout: bool = False,
    ) -> bool:
        # Нормализация времени ответа: минимум 0.5 сек (защита от автокликеров, SECURITY_SPEC)
        time_spent = max(0.5, float(time_spent))
        session.last_activity = time.time()

        q = self.find_question(session, question_id)
        if not q:
            return False

        if is_timeout and (selected_option is None or selected_option < 0) and not (selected_text or "").strip():
            is_correct = False
        elif q.question_type == "text":
            given = (selected_text or "").strip()
            expected = (q.correct_text or "").strip()
            is_correct = bool(given) and given == expected
        else:
            is_correct = selected_option is not None and selected_option == q.correct_option
        
        # Динамический шаг коррекции: в начале теста шаг больше (быстрое нащупывание уровня),
        # к концу теста шаг меньше (точная калибровка)
        base_step = max(0.28, 0.75 * (0.91 ** len(session.history)))

        if is_correct:
            if session.streak > 0:
                session.streak += 1
            else:
                session.streak = 1
            multiplier = 1.0 + min(0.5, (session.streak - 1) * 0.25)
            session.ability += base_step * multiplier
        else:
            if session.streak < 0:
                session.streak -= 1
            else:
                session.streak = -1
            multiplier = 1.0 + min(0.5, (abs(session.streak) - 1) * 0.25)
            session.ability -= base_step * multiplier

        session.ability = max(1.0, min(6.0, session.ability))

        session.history.append({
            "question": q,
            "selected_option": selected_option,
            "selected_text": selected_text,
            "is_correct": is_correct,
            "is_timeout": is_timeout,
            "difficulty": q.difficulty,
            "ability_after": session.ability,
            "time_spent": time_spent,
        })
        return is_correct

    def should_finish(self, session: TestSession) -> bool:
        count = len(session.history)
        if session.test_mode == "fixed":
            # Фиксированный тест завершается строго после ответа на все вопросы
            return count >= len(session.curated_questions)

        if count >= session.max_questions:
            return True
        if count >= session.min_questions:
            # Проверяем стабилизацию за последние 4 вопроса
            recent = [h["ability_after"] for h in session.history[-4:]]
            variance = max(recent) - min(recent)
            if variance < 0.25:
                return True
        return False

    def finalize_test(self, session: TestSession) -> TestResult:
        session.is_finished = True
        correct_count = sum(1 for h in session.history if h["is_correct"])
        total_questions = len(session.history)
        accuracy_pct = int(round((correct_count / total_questions) * 100)) if total_questions > 0 else 0
        total_time = int(round(sum(h.get("time_spent", 0) for h in session.history)))

        if session.test_mode == "fixed" and total_questions > 0:
            if total_questions == 50 or session.test_id == "test_general_2026":
                cefr_code, cefr_title, cefr_desc = map_score_to_fixed_level(correct_count)
            else:
                pct = (correct_count / total_questions) * 50.0
                cefr_code, cefr_title, cefr_desc = map_score_to_fixed_level(int(round(pct)))
            normalized_score = accuracy_pct
        else:
            # В адаптивном режиме нормализуем балл по ability
            normalized_score = int(round(((session.ability - 1.0) / 5.0) * 100))
            normalized_score = max(5, min(99, normalized_score))
            cefr_code, cefr_title, cefr_desc = map_ability_to_cefr(session.ability)

        # Детализация по категориям
        categories = ["Grammar", "Vocabulary", "Usage"]
        skills_breakdown: List[SkillBreakdown] = []
        weak_topics: List[str] = []

        for cat in categories:
            cat_items = [h for h in session.history if h["question"].category == cat]
            if cat_items:
                cat_correct = sum(1 for h in cat_items if h["is_correct"])
                cat_total = len(cat_items)
                pct = int(round((cat_correct / cat_total) * 100))
                avg_diff = sum(h["difficulty"] for h in cat_items) / cat_total
                cat_code, _, _ = map_ability_to_cefr(avg_diff)
                skills_breakdown.append(SkillBreakdown(
                    category=cat,
                    level=cat_code,
                    score_percentage=pct,
                    total_answered=cat_total,
                    correct_answered=cat_correct
                ))
            else:
                skills_breakdown.append(SkillBreakdown(
                    category=cat,
                    level=cefr_code,
                    score_percentage=accuracy_pct,
                    total_answered=0,
                    correct_answered=0
                ))

        for h in session.history:
            if not h["is_correct"]:
                topic_desc = f"{h['question'].topic} ({h['question'].category})"
                if topic_desc not in weak_topics:
                    weak_topics.append(topic_desc)

        # Рекомендации
        recommendations = []
        if cefr_code in ["A1", "A2", "Beginner", "Elementary"]:
            recommendations.append("Сосредоточьтесь на базовых временах (Present/Past Simple) и правилах построения предложений.")
            recommendations.append("Увеличьте словарный запас повседневной лексики (семья, еда, работа, путешествия).")
            recommendations.append("Слушайте адаптированные подкасты и песни с разбором текста.")
        elif cefr_code in ["B1", "Pre-Intermediate", "Intermediate"]:
            recommendations.append("Повторите разницу времен Perfect и конструкции Conditionals (First, Second, Third).")
            recommendations.append("Отрабатывайте фразовые глаголы (phrasal verbs) и устойчивые словосочетания (collocations).")
            recommendations.append("Начните смотреть сериалы и видео на YouTube в оригинале с английскими субтитрами.")
        else:  # B2, C1, C2, Upper-Intermediate, Advanced
            recommendations.append("Практикуйте инверсионные структуры, сослагательное наклонение (Subjunctive) и эмфатические предложения.")
            recommendations.append("Изучайте стилистические и идиоматические нюансы академического и бизнес-английского.")
            recommendations.append("Читайте сложную литературу, статьи The Economist / Nature и участвуйте в дебатах.")

        review_items: List[QuestionReviewItem] = []
        for idx, h in enumerate(session.history, 1):
            q_obj: Question = h["question"]
            review_items.append(QuestionReviewItem(
                question_number=idx,
                id=q_obj.id,
                level=q_obj.level,
                category=q_obj.category,
                topic=q_obj.topic,
                text=q_obj.text,
                question_type=q_obj.question_type,
                options=q_obj.options,
                selected_option=h.get("selected_option"),
                correct_option=q_obj.correct_option,
                selected_text=h.get("selected_text"),
                correct_text=q_obj.correct_text,
                is_correct=h["is_correct"],
                explanation=q_obj.explanation,
                time_spent_seconds=round(float(h.get("time_spent", 0.0)), 1)
            ))

        skipped_count = sum(
            1 for h in session.history
            if h.get("is_timeout") or (h.get("selected_option") is not None and h.get("selected_option") < 0)
        )

        result = TestResult(
            session_id=session.session_id,
            cefr_level=cefr_code,
            level_title=cefr_title,
            cefr_description=cefr_desc,
            score=normalized_score,
            total_questions=total_questions,
            correct_count=correct_count,
            accuracy_percentage=accuracy_pct,
            total_time_seconds=total_time,
            skills=skills_breakdown,
            weak_topics=weak_topics[:4],  # Топ-4 слабых темы
            recommendations=recommendations,
            review=review_items,
            skipped_count=skipped_count,
            telegram_sent=False
        )
        session.result = result
        return result

cat_engine = CATEngine()
