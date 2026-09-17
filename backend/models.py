from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class Question(BaseModel):
    id: str
    level: str  # A1, A2, B1, B2, C1, C2
    difficulty: float  # 1.0 (A1) to 6.0 (C2)
    category: str  # Grammar, Vocabulary, Usage
    topic: str  # e.g., Present Simple, Conditionals, Inversion
    text: str
    options: List[str]
    correct_option: int  # 0-indexed
    explanation: str

class ClientQuestion(BaseModel):
    id: str
    question_number: int
    total_estimated: int
    category: str
    topic: str
    text: str
    options: List[str]
    current_difficulty_label: str  # e.g. "B1 (Intermediate)"

class AnswerSubmission(BaseModel):
    session_id: str
    question_id: str
    selected_option: int
    time_spent_seconds: float = 0.0

class UserContactSubmission(BaseModel):
    session_id: str
    name: str
    phone: Optional[str] = None
    telegram_username: Optional[str] = None
    tg_user_id: Optional[int] = None

class SkillBreakdown(BaseModel):
    category: str
    level: str
    score_percentage: int
    total_answered: int
    correct_answered: int

class TestResult(BaseModel):
    session_id: str
    cefr_level: str  # A1, A2, B1, B2, C1, C2
    level_title: str  # e.g. "Upper-Intermediate (Продвинутый)"
    score: int  # 0-100
    total_questions: int
    correct_count: int
    accuracy_percentage: int
    total_time_seconds: int
    skills: List[SkillBreakdown]
    weak_topics: List[str]
    recommendations: List[str]
    telegram_sent: bool = False

class StartTestResponse(BaseModel):
    session_id: str
    first_question: ClientQuestion
