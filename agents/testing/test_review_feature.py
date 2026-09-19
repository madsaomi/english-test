import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.cat_engine import cat_engine
from backend.models import TestResult, QuestionReviewItem

def test_cat_engine_review():
    print("Testing CAT Engine Review generation...")
    session = cat_engine.create_session()
    q1 = cat_engine.select_next_question(session)
    assert q1 is not None, "First question should exist"
    
    # 1. Answer correctly
    cat_engine.submit_answer(session, q1.id, q1.correct_option, 12.5)
    
    # 2. Answer incorrectly
    q2 = cat_engine.select_next_question(session)
    assert q2 is not None, "Second question should exist"
    wrong_opt = (q2.correct_option + 1) % len(q2.options)
    cat_engine.submit_answer(session, q2.id, wrong_opt, 8.2)
    
    # Finalize test
    res = cat_engine.finalize_test(session)
    assert isinstance(res, TestResult), "Result should be instance of TestResult"
    assert len(res.review) == 2, f"Review should contain 2 items, got {len(res.review)}"
    
    rev1 = res.review[0]
    assert rev1.is_correct is True
    assert rev1.selected_option == q1.correct_option
    assert rev1.explanation == q1.explanation
    assert rev1.time_spent_seconds == 12.5
    
    rev2 = res.review[1]
    assert rev2.is_correct is False
    assert rev2.selected_option == wrong_opt
    assert rev2.correct_option == q2.correct_option
    assert rev2.explanation == q2.explanation
    assert rev2.time_spent_seconds == 8.2
    
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

        # Answer question
        ans_payload = AnswerSubmission(
            session_id=start_res.session_id,
            question_id=start_res.first_question.id,
            selected_option=0,
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
        assert item.text is not None
        assert item.is_correct in (True, False)
        assert item.time_spent_seconds == 4.5
        print("[OK] API Review serialization tests PASSED successfully!")

    asyncio.run(run_flow())

if __name__ == "__main__":
    test_cat_engine_review()
    test_api_review()
