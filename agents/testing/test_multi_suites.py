"""
Automated tests for the single main suite (test_general_2026).
Covers:
- TestRepository loading: exactly one suite
- API endpoint list_available_tests()
- Full fixed run (45 choice + 5 text) start to finish
- Case-sensitivity of text answers
- Review items generation (choice + text)
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.main import list_available_tests, start_test, answer_question
from backend.models import StartTestRequest, AnswerSubmission
from backend.test_loader import test_repository
from backend.cat_engine import cat_engine


def test_01_repository_loading():
    """Проверка загрузки единственного набора тестов из tests_data/"""
    metas = test_repository.get_all_tests_meta()
    suite_ids = [m.id for m in metas]

    assert suite_ids == ["test_general_2026"], f"Ожидался один набор, получено: {suite_ids}"

    suite = test_repository.get_test_suite("test_general_2026")
    assert suite is not None, "test_general_2026 suite should not be None"
    assert suite.mode == "fixed"
    assert len(suite.questions) == 50, f"Expected 50 questions, got {len(suite.questions)}"

    choice = [q for q in suite.questions if q.question_type == "choice"]
    text = [q for q in suite.questions if q.question_type == "text"]
    assert len(choice) == 45, f"Expected 45 choice questions, got {len(choice)}"
    assert len(text) == 5, f"Expected 5 text questions, got {len(text)}"
    for q in choice:
        assert len(q.options) == 4, q.id
        assert q.correct_option is not None and 0 <= q.correct_option < 4, q.id
        assert q.explanation == "", f"{q.id}: explanation must be empty"
    for q in text:
        assert q.correct_text, q.id
        assert q.correct_option is None, q.id
    print("[OK] Test 1: single suite test_general_2026 loaded (45 choice + 5 text).")


async def test_02_api_list_tests():
    """Проверка REST API эндпоинта /api/tests"""
    data = await list_available_tests()
    assert isinstance(data, list)
    assert len(data) == 1, f"Expected exactly 1 suite, got {len(data)}"
    assert data[0].id == "test_general_2026"
    assert data[0].mode == "fixed"
    assert data[0].total_questions == 50
    print("[OK] Test 2: list_available_tests() returns exactly the main suite.")


async def test_03_full_fixed_run():
    """Полное прохождение фиксированного теста General English Test 2026"""
    start_req = StartTestRequest(test_id="test_general_2026")
    start_res = await start_test(start_req)

    session_id = start_res.session_id
    assert start_res.test_title == "General English Test 2026"
    assert start_res.test_mode == "fixed"

    current_q = start_res.first_question
    assert current_q is not None
    assert current_q.question_number == 1

    suite = test_repository.get_test_suite("test_general_2026")

    final_result = None
    step = 0
    while current_q and step < 60:
        q_model = next(q for q in suite.questions if q.id == current_q.id)
        payload_kwargs = {"session_id": session_id, "question_id": current_q.id, "time_spent_seconds": 9.5}
        if q_model.question_type == "text":
            payload_kwargs["selected_text"] = (q_model.correct_text or "").strip()
        else:
            payload_kwargs["selected_option"] = q_model.correct_option

        ans_res = await answer_question(AnswerSubmission(**payload_kwargs))
        if ans_res.is_finished:
            final_result = ans_res.result
            break
        current_q = ans_res.next_question
        step += 1

    assert final_result is not None, "Тест должен завершиться и вернуть результат"
    assert final_result.total_questions == 50, f"Expected 50 questions, got {final_result.total_questions}"
    assert final_result.correct_count == 50
    assert final_result.accuracy_percentage == 100
    assert len(final_result.review) == 50

    text_items = [i for i in final_result.review if i.question_type == "text"]
    assert len(text_items) == 5
    assert all(i.explanation == "" for i in final_result.review)
    print(f"[OK] Test 3: Full fixed run completed. Level: {final_result.cefr_level}, Score: {final_result.score}, Accuracy: {final_result.accuracy_percentage}%.")


async def test_04_text_case_sensitivity():
    """Текстовые ответы чувствительны к регистру"""
    suite = test_repository.get_test_suite("test_general_2026")
    text_q = next(q for q in suite.questions if q.question_type == "text")

    # Сессия A: ответ с неверным регистром
    start_res = await start_test(StartTestRequest(test_id="test_general_2026"))
    session_a = start_res.session_id
    expected = (text_q.correct_text or "").strip()
    wrong_case = expected.upper() if expected != expected.upper() else expected.lower()
    res_a = await answer_question(AnswerSubmission(
        session_id=session_a,
        question_id=text_q.id,
        selected_text=wrong_case,
        time_spent_seconds=2.0,
    ))
    assert res_a.is_correct is False, "Другой регистр должен давать неверный ответ"

    # Сессия B: точное совпадение
    start_res_b = await start_test(StartTestRequest(test_id="test_general_2026"))
    session_b = start_res_b.session_id
    res_b = await answer_question(AnswerSubmission(
        session_id=session_b,
        question_id=text_q.id,
        selected_text=expected,
        time_spent_seconds=2.0,
    ))
    assert res_b.is_correct is True, "Точное совпадение должно быть верным"
    print(f"[OK] Test 4: text answers are case-sensitive ({text_q.correct_text!r}).")


async def main():
    print("====================================================")
    print("   Testing Single Main Suite (test_general_2026)    ")
    print("====================================================")
    test_01_repository_loading()
    await test_02_api_list_tests()
    await test_03_full_fixed_run()
    await test_04_text_case_sensitivity()
    print("====================================================")
    print("   ALL MAIN-SUITE TESTS PASSED SUCCESSFULLY!        ")
    print("====================================================")


if __name__ == "__main__":
    asyncio.run(main())
