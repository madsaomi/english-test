"""
Automated tests for Multi-Test Suites (CAT Platform)
Covers:
- TestRepository loading from tests_data/
- API endpoint list_available_tests()
- Fixed test run (test_business_english) from start to finish
- Review items generation for fixed test
- Adaptive test run (cefr_adaptive)
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.main import list_available_tests, start_test, answer_question, get_test_result
from backend.models import StartTestRequest, AnswerSubmission
from backend.test_loader import test_repository
from backend.cat_engine import cat_engine

def test_01_repository_loading():
    """Проверка загрузки всех наборов тестов из tests_data/"""
    metas = test_repository.get_all_tests_meta()
    suite_ids = [m.id for m in metas]
    
    assert "cefr_adaptive" in suite_ids, "cefr_adaptive должен быть в репозитории"
    assert "test_business_english" in suite_ids, "test_business_english должен быть в репозитории"
    assert "test_grammar_master" in suite_ids, "test_grammar_master должен быть в репозитории"
    assert "test_starter_a1_a2" in suite_ids, "test_starter_a1_a2 должен быть в репозитории"
    
    biz_suite = test_repository.get_test_suite("test_business_english")
    assert biz_suite is not None, "test_business_english suite should not be None"
    assert biz_suite.mode == "fixed"
    assert len(biz_suite.questions) == 8, f"Expected 8 questions, got {len(biz_suite.questions)}"
    print("[OK] Test 1: TestRepository successfully loaded all 4 test suites.")

async def test_02_api_list_tests():
    """Проверка REST API эндпоинта /api/tests"""
    data = await list_available_tests()
    assert isinstance(data, list)
    assert len(data) >= 4

    # Первый тест должен быть cefr_adaptive
    assert data[0].id == "cefr_adaptive"
    assert data[0].mode == "adaptive"

    # Находим business_english
    biz = next((t for t in data if t.id == "test_business_english"), None)
    assert biz is not None
    assert biz.level == "B2-C1"
    assert biz.mode == "fixed"
    assert biz.total_questions == 8
    print("[OK] Test 2: list_available_tests() returns valid metadata for all suites.")

async def test_03_business_english_fixed_run():
    """Полное прохождение фиксированного теста Business English"""
    start_req = StartTestRequest(test_id="test_business_english")
    start_res = await start_test(start_req)

    session_id = start_res.session_id
    assert start_res.test_title == "Business & Formal English"
    assert start_res.test_mode == "fixed"
    
    current_q = start_res.first_question
    assert current_q is not None
    assert current_q.question_number == 1

    biz_suite = test_repository.get_test_suite("test_business_english")
    
    # Отвечаем на все 8 вопросов
    step = 1
    final_result = None
    while current_q:
        q_model = next(q for q in biz_suite.questions if q.id == current_q.id)
        
        # 6 верных ответов и 2 неверных
        selected_option = q_model.correct_option if step <= 6 else (q_model.correct_option + 1) % len(q_model.options)

        ans_payload = AnswerSubmission(
            session_id=session_id,
            question_id=current_q.id,
            selected_option=selected_option,
            time_spent_seconds=14.5
        )
        ans_res = await answer_question(ans_payload)

        if ans_res.is_finished:
            final_result = ans_res.result
            break
        
        current_q = ans_res.next_question
        step += 1

    assert final_result is not None, "Тест должен завершиться и вернуть результат"
    assert final_result.total_questions == 8, f"Expected 8 questions, got {final_result.total_questions}"
    assert final_result.correct_count == 6
    assert final_result.accuracy_percentage == 75
    assert len(final_result.review) == 8

    # Проверяем, что в review есть правильные пояснения и ответы
    first_review = final_result.review[0]
    assert first_review.is_correct is True
    assert len(first_review.explanation) > 0

    # 7-й вопрос должен быть с ошибкой
    seventh_review = final_result.review[6]
    assert seventh_review.is_correct is False
    assert seventh_review.selected_option != seventh_review.correct_option

    print(f"[OK] Test 3: Fixed Business English completed. Level: {final_result.cefr_level} ({final_result.level_title}), Score: {final_result.score}, Accuracy: {final_result.accuracy_percentage}%.")

async def test_04_adaptive_cefr_run():
    """Проверка адаптивного теста (cefr_adaptive) через API"""
    start_req = StartTestRequest(test_id="cefr_adaptive")
    start_res = await start_test(start_req)

    session_id = start_res.session_id
    assert start_res.test_mode == "adaptive"
    current_q = start_res.first_question

    for i in range(14):
        if not current_q:
            break
        ans_payload = AnswerSubmission(
            session_id=session_id,
            question_id=current_q.id,
            selected_option=0,
            time_spent_seconds=10.0
        )
        ans_res = await answer_question(ans_payload)
        if ans_res.is_finished:
            break
        current_q = ans_res.next_question

    session = cat_engine.get_session(session_id)
    assert session.is_finished is True
    assert session.result is not None
    print(f"[OK] Test 4: Adaptive test finished properly with level {session.result.cefr_level}.")

async def main():
    print("====================================================")
    print("   Testing Multi-Test Suites & Test Catalog         ")
    print("====================================================")
    test_01_repository_loading()
    await test_02_api_list_tests()
    await test_03_business_english_fixed_run()
    await test_04_adaptive_cefr_run()
    print("====================================================")
    print("   ALL MULTI-SUITE TESTS PASSED SUCCESSFULLY!       ")
    print("====================================================")

if __name__ == "__main__":
    asyncio.run(main())
