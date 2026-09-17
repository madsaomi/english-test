# 🐛 BUG-001: Ошибка валидации Pydantic v2 при значении None для модели

- **Дата обнаружения:** 2026-09-17 21:20
- **Статус:** 🟢 РЕШЕНО
- **Затронутый файл:** `backend/main.py`
- **Компонент:** FastAPI REST API (`AnswerResponse`)

---

## 🔍 1. Симптом (Что произошло)
При отправке ответа на вопрос через `POST /api/test/answer` сервер возвращал HTTP 500 Internal Server Error:

```text
Traceback (most recent call last):
  File "C:\Users\~\Desktop\New folder (2)\backend\main.py", line 139, in answer_question
    return AnswerResponse(
        is_finished=False,
        result=None
    )
  ...
pydantic_core._pydantic_core.ValidationError: 1 validation error for AnswerResponse
result
  Input should be a valid dictionary or instance of TestResult [type=model_type, input_value=None, input_type=NoneType]
    For further information visit https://errors.pydantic.dev/2.13/v/model_type
```

---

## 🔬 2. Первопричина (Root Cause — ПОЧЕМУ это произошло)
В коде модель была объявлена следующим образом:
```python
class AnswerResponse(BaseModel):
    is_finished: bool
    is_correct: bool
    current_difficulty_label: str
    next_question: ClientQuestion = None
    result: TestResult = None
```
- **Специфика Pydantic v2:** В первой версии Pydantic конструкция `field: MyModel = None` автоматически считала поле опциональным (`Optional`). 
- Однако в **Pydantic v2 (версии 2.6+)** это поведение было ужесточено: если тип указан как `TestResult`, валидатор требует экземпляр именно этого класса. Передача `None` вызывает фатальную ошибку валидации схемы.

---

## 🛠️ 3. Решение (Как исправлено)
В файле `backend/main.py` был добавлен импорт `from typing import Optional`, и поля явно помечены как `Optional`:

```python
from typing import Optional

class AnswerResponse(BaseModel):
    is_finished: bool
    is_correct: bool
    current_difficulty_label: str
    next_question: Optional[ClientQuestion] = None
    result: Optional[TestResult] = None
```

---

## 🛡️ 4. Правило предотвращения (Для всех будущих агентов)
Любое поле модели Pydantic v2, которое может принимать значение `None`, **ОБЯЗАНО** быть явно типизировано через `Optional[T]` или `T | None`.
