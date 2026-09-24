"""Simulation test for the fixed suite (test_general_2026): scoring sanity."""
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from backend.cat_engine import cat_engine

VALID_LEVELS = {
    "Beginner", "Elementary", "Pre-Intermediate", "Intermediate", "Upper-Intermediate", "Advanced",
    "A1", "A2", "B1", "B2", "C1", "C2"
}


def _answer_correctly(session, q):
    if q.question_type == "text":
        cat_engine.submit_answer(session, q.id, time_spent=3.5, selected_text=(q.correct_text or "").strip())
    else:
        cat_engine.submit_answer(session, q.id, q.correct_option, time_spent=3.5)


def _answer_wrong(session, q):
    if q.question_type == "text":
        cat_engine.submit_answer(session, q.id, time_spent=5.0, selected_text="__wrong__")
    else:
        wrong_option = (q.correct_option + 1) % len(q.options)
        cat_engine.submit_answer(session, q.id, wrong_option, time_spent=5.0)


def _run_scenario(mode: str):
    """mode: 'high' (all correct), 'low' (all wrong), 'mid' (alternating)."""
    session = cat_engine.create_session()
    assert session.test_mode == "fixed", f"Expected fixed mode, got {session.test_mode}"
    q = cat_engine.select_next_question(session)
    idx = 0
    while q:
        if mode == "high":
            _answer_correctly(session, q)
        elif mode == "low":
            _answer_wrong(session, q)
        else:
            if idx % 2 == 0:
                _answer_correctly(session, q)
            else:
                _answer_wrong(session, q)
        idx += 1
        if cat_engine.should_finish(session):
            break
        q = cat_engine.select_next_question(session)
    return cat_engine.finalize_test(session)


def test_cat_simulation():
    result_high = _run_scenario("high")
    print(f"[HIGH SCENARIO] Вопросов: {result_high.total_questions}, Уровень: {result_high.cefr_level}, Балл: {result_high.score}, Accuracy: {result_high.accuracy_percentage}%")
    assert result_high.total_questions == 50, f"Ожидалось 50 вопросов, получено {result_high.total_questions}"
    assert result_high.accuracy_percentage == 100
    assert result_high.cefr_level == "Advanced", f"Ожидался Advanced, получено {result_high.cefr_level}"
    assert len(result_high.review) == 50

    result_low = _run_scenario("low")
    print(f"[LOW SCENARIO]  Вопросов: {result_low.total_questions}, Уровень: {result_low.cefr_level}, Балл: {result_low.score}, Accuracy: {result_low.accuracy_percentage}%")
    assert result_low.total_questions == 50
    assert result_low.accuracy_percentage == 0
    assert result_low.cefr_level == "Beginner", f"Ожидался Beginner, получено {result_low.cefr_level}"

    result_mid = _run_scenario("mid")
    print(f"[MID SCENARIO]  Вопросов: {result_mid.total_questions}, Уровень: {result_mid.cefr_level}, Балл: {result_mid.score}, Accuracy: {result_mid.accuracy_percentage}%")
    assert result_mid.total_questions == 50
    assert result_mid.accuracy_percentage == 50
    assert result_mid.cefr_level == "Pre-Intermediate", f"Ожидался Pre-Intermediate, получено {result_mid.cefr_level}"

    # Монотонность балла: чем выше точность — тем выше score
    assert result_high.score > result_mid.score > result_low.score, (
        f"Score ordering broken: {result_high.score} > {result_mid.score} > {result_low.score}"
    )

    # Разбор ответов: explanation пустой (политика проекта — без подсказок)
    assert all(item.explanation == "" for item in result_high.review)

    # Текстовые вопросы присутствуют в review
    text_items = [item for item in result_high.review if item.question_type == "text"]
    assert len(text_items) == 5, f"Ожидалось 5 text-вопросов в review, получено {len(text_items)}"
    assert all(item.correct_text for item in text_items)

    print("✅ Все 3 симуляционных сценария теста test_general_2026 успешно пройдены!")


def test_score_thresholds():
    from backend.cat_engine import map_score_to_fixed_level
    checks = [
        (0, "Beginner"),
        (15, "Beginner"),
        (16, "Elementary"),
        (24, "Elementary"),
        (25, "Pre-Intermediate"),
        (32, "Pre-Intermediate"),
        (33, "Intermediate"),
        (39, "Intermediate"),
        (40, "Upper-Intermediate"),
        (45, "Upper-Intermediate"),
        (46, "Advanced"),
        (50, "Advanced"),
    ]
    for score, expected in checks:
        code, title, _ = map_score_to_fixed_level(score)
        assert code == expected and title == expected, f"Score {score} expected {expected}, got {code}"
    print("✅ Все 12 граничных значений шкалы оценивания успешно подтверждены!")


if __name__ == "__main__":
    test_score_thresholds()
    test_cat_simulation()
