"""Simulation test for CATEngine to verify convergence and edge cases."""
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from backend.cat_engine import cat_engine, map_ability_to_cefr
from backend.questions import QUESTION_BANK

def test_cat_simulation():
    print(f"Всего вопросов в банке: {len(QUESTION_BANK)}")
    assert len(QUESTION_BANK) >= 25, "Банк вопросов должен содержать минимум 25 вопросов"

    # Сценарий 1: Пользователь уровня Advanced/Proficiency (всегда отвечает верно)
    session_high = cat_engine.create_session()
    q = cat_engine.select_next_question(session_high)
    while q:
        is_correct = cat_engine.submit_answer(session_high, q.id, q.correct_option, time_spent=3.5)
        if cat_engine.should_finish(session_high):
            break
        q = cat_engine.select_next_question(session_high)
    result_high = cat_engine.finalize_test(session_high)
    print(f"[HIGH SCENARIO] Вопросов: {result_high.total_questions}, Уровень: {result_high.cefr_level}, Балл: {result_high.score}")
    assert result_high.cefr_level in ["C1", "C2"], f"Ожидался C1/C2, получен {result_high.cefr_level}"

    # Сценарий 2: Начинающий пользователь (всегда отвечает неверно)
    session_low = cat_engine.create_session()
    q = cat_engine.select_next_question(session_low)
    while q:
        wrong_option = (q.correct_option + 1) % len(q.options)
        cat_engine.submit_answer(session_low, q.id, wrong_option, time_spent=5.0)
        if cat_engine.should_finish(session_low):
            break
        q = cat_engine.select_next_question(session_low)
    result_low = cat_engine.finalize_test(session_low)
    print(f"[LOW SCENARIO]  Вопросов: {result_low.total_questions}, Уровень: {result_low.cefr_level}, Балл: {result_low.score}")
    assert result_low.cefr_level in ["A1", "A2"], f"Ожидался A1/A2, получен {result_low.cefr_level}"

    # Сценарий 3: Средний пользователь B1/B2 (отвечает 50/50)
    session_mid = cat_engine.create_session()
    q = cat_engine.select_next_question(session_mid)
    idx = 0
    while q:
        chosen = q.correct_option if (idx % 2 == 0) else (q.correct_option + 1) % len(q.options)
        cat_engine.submit_answer(session_mid, q.id, chosen, time_spent=4.0)
        idx += 1
        if cat_engine.should_finish(session_mid):
            break
        q = cat_engine.select_next_question(session_mid)
    result_mid = cat_engine.finalize_test(session_mid)
    print(f"[MID SCENARIO]  Вопросов: {result_mid.total_questions}, Уровень: {result_mid.cefr_level}, Балл: {result_mid.score}")
    assert result_mid.cefr_level in ["A2", "B1", "B2"], f"Ожидался A2/B1/B2, получен {result_mid.cefr_level}"

    print("✅ Все 3 симуляционных сценария CAT успешно пройдены!")

if __name__ == "__main__":
    test_cat_simulation()
