import uuid
import math
import random
from typing import Dict, List, Optional, Set
from .models import Question, ClientQuestion, TestResult, SkillBreakdown
from .questions import QUESTION_BANK

CEFR_LEVELS = [
    (1.0, 1.6, "A1", "A1 (Beginner)", "Начальный уровень владения языком. Понимание базовых фраз, построение простых предложений."),
    (1.6, 2.5, "A2", "A2 (Elementary)", "Элементарный уровень. Общение на простые повседневные темы, знание базовых временных форм."),
    (2.5, 3.5, "B1", "B1 (Intermediate)", "Средний уровень. Понимание сути бесед на знакомые темы, уверенное выражение мыслей в путешествиях и на работе."),
    (3.5, 4.5, "B2", "B2 (Upper-Intermediate)", "Продвинутый уровень. Свободное общение с носителями, понимание сложной грамматики и идиом."),
    (4.5, 5.5, "C1", "C1 (Advanced)", "Профессиональный уровень. Свободное беглое владение, инверсии, сослагательное наклонение, богатый словарный запас."),
    (5.5, 6.01, "C2", "C2 (Mastery / Proficiency)", "Уровень носителя языка. Абсолютное понимание нюансов, тонких идиоматических выражений и сложной стилистики."),
]

def map_ability_to_cefr(ability: float):
    ability = max(1.0, min(6.0, ability))
    for low, high, code, title, desc in CEFR_LEVELS:
        if low <= ability < high:
            return code, title, desc
    return "C2", "C2 (Mastery / Proficiency)", CEFR_LEVELS[-1][4]

class TestSession:
    def __init__(self, session_id: str):
        self.session_id: str = session_id
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

class CATEngine:
    def __init__(self):
        self.sessions: Dict[str, TestSession] = {}

    def create_session(self) -> TestSession:
        session_id = str(uuid.uuid4())
        session = TestSession(session_id)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[TestSession]:
        return self.sessions.get(session_id)

    def select_next_question(self, session: TestSession) -> Optional[Question]:
        available = [q for q in QUESTION_BANK if q.id not in session.asked_question_ids]
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
            options=question.options,
            current_difficulty_label=label,
        )

    def submit_answer(self, session: TestSession, question_id: str, selected_option: int, time_spent: float) -> bool:
        if not session.current_question or session.current_question.id != question_id:
            # На случай перезагрузки/синхронизации ищем по id
            q = next((q for q in QUESTION_BANK if q.id == question_id), None)
            if not q:
                return False
        else:
            q = session.current_question

        is_correct = (selected_option == q.correct_option)
        
        # Динамический шаг коррекции: в начале теста шаг больше (быстрое нащупывание уровня),
        # к концу теста шаг меньше (точная калибровка)
        base_step = max(0.28, 0.75 * (0.91 ** len(session.history)))

        if is_correct:
            if session.streak > 0:
                session.streak += 1
            else:
                session.streak = 1
            
            # Если серия верных ответов, делаем шаг крупнее
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
            "is_correct": is_correct,
            "difficulty": q.difficulty,
            "ability_after": session.ability,
            "time_spent": time_spent,
        })
        return is_correct

    def should_finish(self, session: TestSession) -> bool:
        count = len(session.history)
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
        cefr_code, cefr_title, cefr_desc = map_ability_to_cefr(session.ability)

        # Вычисление баллов по шкале 0..100
        normalized_score = int(round(((session.ability - 1.0) / 5.0) * 100))
        normalized_score = max(5, min(99, normalized_score))

        correct_count = sum(1 for h in session.history if h["is_correct"])
        total_questions = len(session.history)
        accuracy_pct = int(round((correct_count / total_questions) * 100)) if total_questions > 0 else 0
        total_time = int(round(sum(h.get("time_spent", 0) for h in session.history)))

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
                # Вычисляем среднюю сложность успешных вопросов категории
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
        if cefr_code in ["A1", "A2"]:
            recommendations.append("Сосредоточьтесь на базовых временах (Present/Past Simple) и правилах построения предложений.")
            recommendations.append("Увеличьте словарный запас повседневной лексики (семья, еда, работа, путешествия).")
            recommendations.append("Слушайте адаптированные подкасты и песни с разбором текста.")
        elif cefr_code in ["B1", "B2"]:
            recommendations.append("Повторите разницу времен Perfect и конструкции Conditionals (First, Second, Third).")
            recommendations.append("Отрабатывайте фразовые глаголы (phrasal verbs) и устойчивые словосочетания (collocations).")
            recommendations.append("Начните смотреть сериалы и видео на YouTube в оригинале с английскими субтитрами.")
        else:  # C1, C2
            recommendations.append("Практикуйте инверсионные структуры, сослагательное наклонение (Subjunctive) и эмфатические предложения.")
            recommendations.append("Изучайте стилистические и идиоматические нюансы академического и бизнес-английского.")
            recommendations.append("Читайте сложную литературу, статьи The Economist / Nature и участвуйте в дебатах.")

        result = TestResult(
            session_id=session.session_id,
            cefr_level=cefr_code,
            level_title=cefr_title,
            score=normalized_score,
            total_questions=total_questions,
            correct_count=correct_count,
            accuracy_percentage=accuracy_pct,
            total_time_seconds=total_time,
            skills=skills_breakdown,
            weak_topics=weak_topics[:4],  # Топ-4 слабых темы
            recommendations=recommendations,
            telegram_sent=False
        )
        session.result = result
        return result

cat_engine = CATEngine()
