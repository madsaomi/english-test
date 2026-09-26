from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class Question(BaseModel):
    id: str
    level: str  # A1, A2, B1, B2, C1, C2
    difficulty: float  # 1.0 (A1) to 6.0 (C2)
    category: str  # Grammar, Vocabulary, Usage
    topic: str  # e.g., Present Simple, Conditionals, Inversion
    text: str
    question_type: str = "choice"  # "choice" (4 options) or "text" (free-text input)
    options: List[str] = []
    correct_option: Optional[int] = None  # 0-indexed; None for text questions
    correct_text: Optional[str] = None  # canonical answer for text questions (case-sensitive)
    explanation: str = ""

class ClientQuestion(BaseModel):
    id: str
    question_number: int
    total_estimated: int
    category: str
    topic: str
    text: str
    question_type: str = "choice"
    options: List[str]
    current_difficulty_label: str  # e.g. "B1 (Intermediate)"

class AnswerSubmission(BaseModel):
    session_id: str
    question_id: str
    selected_option: Optional[int] = None
    selected_text: Optional[str] = None
    time_spent_seconds: float = 0.0
    is_timeout: bool = False

class UserContactSubmission(BaseModel):
    session_id: str
    name: str
    phone: Optional[str] = None
    telegram_username: Optional[str] = None
    tg_user_id: Optional[int] = None
    tg_init_data: Optional[str] = None
    branch: Optional[str] = "Главный офис"

class SkillBreakdown(BaseModel):
    category: str
    level: str
    score_percentage: int
    total_answered: int
    correct_answered: int

class QuestionReviewItem(BaseModel):
    question_number: int
    id: str
    level: str
    category: str
    topic: str
    text: str
    question_type: str = "choice"
    options: List[str]
    selected_option: Optional[int] = None
    correct_option: Optional[int] = None
    selected_text: Optional[str] = None
    correct_text: Optional[str] = None
    is_correct: bool
    explanation: str = ""
    time_spent_seconds: float

class TestResult(BaseModel):
    session_id: str
    cefr_level: str  # A1, A2, B1, B2, C1, C2
    level_title: str  # e.g. "Upper-Intermediate (Продвинутый)"
    cefr_description: str = ""  # описание уровня для экрана результатов
    score: int  # 0-100
    total_questions: int
    correct_count: int
    accuracy_percentage: int
    total_time_seconds: int
    skills: List[SkillBreakdown]
    weak_topics: List[str]
    recommendations: List[str]
    review: List[QuestionReviewItem] = []
    skipped_count: int = 0
    telegram_sent: bool = False

class TestSuiteMeta(BaseModel):
    id: str
    title: str
    description: str
    category: str
    level: str
    mode: str = "fixed"  # "adaptive" or "fixed"
    icon: str = "📝"
    estimated_time_minutes: int = 5
    total_questions: int = 0

class TestSuite(TestSuiteMeta):
    questions: List[Question] = []

class StartTestRequest(BaseModel):
    test_id: Optional[str] = None

class StartTestResponse(BaseModel):
    session_id: str
    first_question: ClientQuestion
    test_title: Optional[str] = None
    test_mode: Optional[str] = "adaptive"
