import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.cat_engine import cat_engine
from backend.models import TestResult, QuestionReviewItem

def test_cat_engine_review():
    print("Testing CAT Engine Review generation...")
    session = cat_engine.create_session()
    assert session.test_mode == "fixed"

    # 1. Первый вопрос (choice) — ответ верно
    q1 = cat_engine.select_next_question(session)
    assert q1 is not None, "First question should exist"
    assert q1.question_type == "choice"
    cat_engine.submit_answer(session, q1.id, q1.correct_option, 12.5)

    # 2. Второй вопрос (choice) — ответ неверно
    q2 = cat_engine.select_next_question(session)
    assert q2 is not None, "Second question should exist"
    wrong_opt = (q2.correct_option + 1) % len(q2.options)
    cat_engine.submit_answer(session, q2.id, wrong_opt, 8.2)

    # 3. Текстовый вопрос — верный ответ (case-sensitive эталон)
    text_q = next(q for q in session.curated_questions if q.question_type == "text")
    cat_engine.submit_answer(session, text_q.id, time_spent=2.0, selected_text=(text_q.correct_text or "").strip())

    # Finalize test
    res = cat_engine.finalize_test(session)
    assert isinstance(res, TestResult), "Result should be instance of TestResult"
    assert len(res.review) == 3, f"Review should contain 3 items, got {len(res.review)}"

    rev1 = res.review[0]
    assert rev1.is_correct is True
    assert rev1.question_type == "choice"
    assert rev1.selected_option == q1.correct_option
    assert rev1.explanation == "" and q1.explanation == ""
    assert rev1.time_spent_seconds == 12.5

    rev2 = res.review[1]
    assert rev2.is_correct is False
    assert rev2.selected_option == wrong_opt
    assert rev2.correct_option == q2.correct_option
    assert rev2.explanation == ""
    assert rev2.time_spent_seconds == 8.2

    rev3 = res.review[2]
    assert rev3.question_type == "text"
    assert rev3.is_correct is True
    assert rev3.selected_text == text_q.correct_text
    assert rev3.correct_text == text_q.correct_text
    assert rev3.selected_option is None
    assert rev3.correct_option is None

    # Неверный регистр в текстовом ответе
    session2 = cat_engine.create_session()
    text_q2 = next(q for q in session2.curated_questions if q.question_type == "text")
    expected = (text_q2.correct_text or "").strip()
    wrong_case = expected.upper() if expected != expected.upper() else expected.lower()
    ok = cat_engine.submit_answer(session2, text_q2.id, time_spent=2.0, selected_text=wrong_case)
    assert ok is False, "Другой регистр должен давать неверный ответ"

    print("[OK] CAT Engine Review feature tests PASSED successfully!")

def test_api_review():
    print("Testing API Review endpoint serialization...")
    import asyncio
    from backend.main import start_test, answer_question, get_test_result
    from backend.models import AnswerSubmission

    async def run_flow():
        start_res = await start_test()
        assert start_res.session_id is not None
        assert start_res.first_question is not None
        assert start_res.test_mode == "fixed"

        # Первый вопрос — choice
        first = start_res.first_question
        assert first.question_type == "choice"
        ans_payload = AnswerSubmission(
            session_id=start_res.session_id,
            question_id=first.id,
            selected_option=first.options and 0 or 0,
            time_spent_seconds=4.5
        )
        ans_res = await answer_question(ans_payload)
        assert ans_res is not None

        # Finalize and get result
        sess = cat_engine.get_session(start_res.session_id)
        cat_engine.finalize_test(sess)

        result = await get_test_result(start_res.session_id)
        assert result is not None
        assert len(result.review) >= 1
        item = result.review[0]
        assert item.explanation is not None
        assert item.explanation == ""
        assert item.text is not None
        assert item.is_correct in (True, False)
        assert item.time_spent_seconds == 4.5
        print("[OK] API Review serialization tests PASSED successfully!")

    asyncio.run(run_flow())

if __name__ == "__main__":
    test_cat_engine_review()
    test_api_review()
