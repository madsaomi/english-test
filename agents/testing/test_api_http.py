"""HTTP-layer API tests using FastAPI TestClient.

Проверяют реальный HTTP-стек: маршрутизацию, сериализацию JSON, CORS-заголовки,
полный цикл фиксированного теста (включая text-ответы и case-sensitivity),
а также криптографию initData (Telegram WebApp).
"""

import sys
import hashlib
import hmac
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi.testclient import TestClient

from backend.main import app, verify_telegram_init_data
from backend.test_loader import test_repository
from backend.lead_store import lead_store
from backend.telegram_bot import format_compact_lead_card, format_unified_lead_card
from backend.models import TestResult


def test_health_endpoint():
    client = TestClient(app)
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["total_questions_in_bank"] >= 25
    assert data["total_questions_in_bank"] == 50
    assert "active_sessions" in data
    print("[OK] HTTP test: /api/health")


def test_catalog_endpoint():
    client = TestClient(app)
    res = client.get("/api/tests")
    assert res.status_code == 200
    metas = res.json()
    assert len(metas) == 1, f"Ожидался ровно 1 тест, получено {len(metas)}"
    assert metas[0]["id"] == "test_general_2026"
    assert metas[0]["mode"] == "fixed"
    assert metas[0]["total_questions"] == 50
    print("[OK] HTTP test: /api/tests catalog (single suite)")


def test_cors_wildcard_default():
    client = TestClient(app)
    res = client.get("/api/health", headers={"Origin": "https://example.com"})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "*"
    print("[OK] HTTP test: CORS wildcard default")


def _answer_payload(qmodel, step: int, text_value: str = None):
    if qmodel.question_type == "text":
        value = text_value if text_value is not None else (qmodel.correct_text or "").strip()
        return {"selected_text": value, "time_spent_seconds": 3.0}
    if text_value is not None:
        return {"selected_option": 0, "time_spent_seconds": 3.0}
    return {"selected_option": qmodel.correct_option, "time_spent_seconds": 3.0}


def _run_full(client, wrong_case_at_first_text: bool = False):
    """Проводит тест до конца. Возвращает (session_id, final_result, text_case_correct)."""
    start = client.post("/api/test/start", json={})
    assert start.status_code == 200
    data = start.json()
    sid = data["session_id"]
    suite = test_repository.get_test_suite("test_general_2026")

    current_q = data["first_question"]
    step = 0
    final = None
    text_case_correct = None
    used_wrong_case = False

    while current_q and step < 60:
        qmodel = next(q for q in suite.questions if q.id == current_q["id"])
        text_override = None
        if (
            wrong_case_at_first_text
            and qmodel.question_type == "text"
            and not used_wrong_case
        ):
            expected = (qmodel.correct_text or "").strip()
            text_override = expected.upper() if expected != expected.upper() else expected.lower()
            used_wrong_case = True

        payload = {
            "session_id": sid,
            "question_id": current_q["id"],
            **_answer_payload(qmodel, step, text_override),
        }
        ans = client.post("/api/test/answer", json=payload)
        assert ans.status_code == 200, ans.text
        body = ans.json()
        if text_override is not None:
            text_case_correct = body["is_correct"]
        if body["is_finished"]:
            final = body["result"]
            break
        current_q = body["next_question"]
        step += 1

    assert final is not None, "Тест должен завершиться"
    return sid, final, text_case_correct


def test_fixed_general_run_over_http():
    client = TestClient(app)
    sid, final, _ = _run_full(client)
    assert final["total_questions"] == 50
    assert final["accuracy_percentage"] == 100
    assert final["cefr_description"], "Описание CEFR должно присутствовать в результате"
    assert len(final["review"]) == 50

    res = client.get(f"/api/test/result/{sid}")
    assert res.status_code == 200
    assert res.json()["session_id"] == sid
    print("[OK] HTTP test: full fixed general run (50/50 correct)")


def test_text_answer_case_sensitive():
    client = TestClient(app)
    _, final, text_case_correct = _run_full(client, wrong_case_at_first_text=True)
    assert text_case_correct is False, "Ответ с другим регистром должен быть неверным"
    # 49 из 50 верно (первый text-ответ намеренно с неверным регистром)
    assert final["correct_count"] == 49, f"Ожидалось 49, получено {final['correct_count']}"
    assert final["accuracy_percentage"] == 98
    print("[OK] HTTP test: text answers are case-sensitive")


def test_text_answer_empty_rejected():
    client = TestClient(app)
    start = client.post("/api/test/start", json={})
    data = start.json()
    sid = data["session_id"]
    suite = test_repository.get_test_suite("test_general_2026")
    text_q = next(q for q in suite.questions if q.question_type == "text")

    res = client.post("/api/test/answer", json={
        "session_id": sid,
        "question_id": text_q.id,
        "selected_text": "   ",
        "time_spent_seconds": 1.0,
    })
    assert res.status_code == 400
    assert "Введите ответ" in res.json()["detail"]
    print("[OK] HTTP test: empty text answer rejected with 400")


def test_choice_without_option_rejected():
    client = TestClient(app)
    start = client.post("/api/test/start", json={})
    data = start.json()
    sid = data["session_id"]
    choice_q_id = data["first_question"]["id"]

    res = client.post("/api/test/answer", json={
        "session_id": sid,
        "question_id": choice_q_id,
        "time_spent_seconds": 1.0,
    })
    assert res.status_code == 400
    assert "Не выбран вариант" in res.json()["detail"]
    print("[OK] HTTP test: choice without selected_option rejected with 400")


def test_leads_endpoint():
    client = TestClient(app)
    res = client.get("/api/export/leads")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    print("[OK] HTTP test: /api/export/leads")


def test_start_unknown_test_falls_back():
    client = TestClient(app)
    res = client.post("/api/test/start", json={"test_id": "not_existing_suite"})
    assert res.status_code == 200
    assert res.json()["session_id"]
    assert res.json()["test_title"] == "General English Test 2026"
    print("[OK] HTTP test: unknown suite falls back to default")


def _complete_fixed(client, test_id: str = "test_general_2026"):
    """Проводит фиксированный тест до конца, возвращает session_id."""
    start = client.post("/api/test/start", json={"test_id": test_id})
    data = start.json()
    sid = data["session_id"]
    suite = test_repository.get_test_suite(test_id)
    current_q = data["first_question"]
    step = 0
    while current_q and step < 60:
        qmodel = next(q for q in suite.questions if q.id == current_q["id"])
        ans = client.post("/api/test/answer", json={
            "session_id": sid,
            "question_id": current_q["id"],
            **_answer_payload(qmodel, step),
        })
        body = ans.json()
        if body["is_finished"]:
            return sid
        current_q = body["next_question"]
        step += 1
    raise AssertionError("Тест не завершился")


def test_contact_requires_name_and_phone():
    client = TestClient(app)
    sid = _complete_fixed(client)

    res = client.post("/api/test/submit-contact", json={"session_id": sid, "name": "Тест Тестов"})
    assert res.status_code == 400
    assert "Телефон" in res.json()["detail"]

    res = client.post("/api/test/submit-contact", json={"session_id": sid, "phone": "+998 90 123-45-67"})
    assert res.status_code == 422  # name обязателен в модели

    res = client.post("/api/test/submit-contact", json={"session_id": sid, "name": "", "phone": "+998 90 123-45-67"})
    assert res.status_code == 400
    assert "ФИО" in res.json()["detail"]

    # Проверка отклонения некорректного номера (например, мусорный или не узбекский)
    res_bad = client.post("/api/test/submit-contact", json={"session_id": sid, "name": "Тест", "phone": "+122132132132332"})
    assert res_bad.status_code == 400
    assert "Узбекистана" in res_bad.json()["detail"]

    print("[OK] HTTP test: contact requires name and phone (Uzbekistan format)")


def test_contact_persist_and_export():
    client = TestClient(app)
    sid = _complete_fixed(client)

    # 1. Отправка с явным выбором филиала "Университет"
    resp = client.post("/api/test/submit-contact", json={
        "session_id": sid,
        "name": "Иван Петров",
        "phone": "+998 90 123-45-67",
        "telegram_username": "ivan_petrov",
        "branch": "Университет",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    lead = lead_store.get_lead(sid)
    assert lead is not None
    assert lead.student_name == "Иван Петров"
    assert lead.phone == "+998 (90) 123-45-67"
    assert lead.branch == "Университет"
    assert lead.result.cefr_level

    export = client.get("/api/export/leads").json()
    saved = next((item for item in export if item["session_id"] == sid), None)
    assert saved is not None
    assert saved.get("branch") == "Университет"

    # 2. Проверка дефолтного филиала "Главный офис"
    sid2 = _complete_fixed(client)
    resp2 = client.post("/api/test/submit-contact", json={
        "session_id": sid2,
        "name": "Анна Сидорова",
        "phone": "+998 99 765-43-21",
    })
    assert resp2.status_code == 200
    lead2 = lead_store.get_lead(sid2)
    assert lead2 is not None
    assert lead2.phone == "+998 (99) 765-43-21"
    assert lead2.branch == "Главный офис"
    print("[OK] HTTP test: lead persisted and exported with branch")


def test_lead_card_format():
    # Проверка компактной карточки
    card = format_compact_lead_card(
        name="Иван Петров",
        level_code="B2",
        level_title="Upper-Intermediate",
        phone="+998 (90) 123-45-67",
        received_at="21.09.2026 14:30",
        branch="Университет",
    )
    assert "НОВАЯ ЗАЯВКА С ТЕСТА" in card
    assert "Иван Петров" in card
    assert "Университет" in card
    assert "B2 — Upper-Intermediate" in card
    assert "<code>+998 (90) 123-45-67</code>" in card
    assert "21.09.2026 14:30" in card

    # Проверка единой брендированной карточки
    client = TestClient(app)
    sid = _complete_fixed(client)
    res_resp = client.get(f"/api/test/result/{sid}")
    result_data = TestResult(**res_resp.json())
    unified = format_unified_lead_card(
        name="Иван Петров",
        phone="+998 (90) 123-45-67",
        username="ivan_petrov",
        result=result_data,
        received_at="25.09.2026 21:30",
        branch="Главный офис",
    )
    assert "STANFORD LANGUAGE CENTER" in unified
    assert "🏢 <b>Филиал:</b> Главный офис" in unified
    assert "👤 <b>Кандидат:</b> Иван Петров" in unified
    print("[OK] HTTP test: lead card format with branch")


def test_init_data_validation():
    token = "123456:TESTTOKEN"

    assert verify_telegram_init_data("auth_date=1700000000&user=%7B%22id%22%3A1%7D&hash=deadbeef", token) is False
    assert verify_telegram_init_data("foo=bar&hash=deadbeef", token) is False
    assert verify_telegram_init_data("", token) is False

    pairs = [
        ("auth_date", "1700000000"),
        ("query_id", "AAHdF6IQAAAAAN0XohDhr3Qrc"),
        ("user", '{"id":42,"first_name":"Test"}'),
    ]
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs))
    secret = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
    good_hash = hmac.new(secret, check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    init_data = "&".join(f"{k}={v}" for k, v in sorted(pairs)) + f"&hash={good_hash}"
    init_data_urlencoded = urlencode(sorted(pairs)) + f"&hash={good_hash}"

    assert verify_telegram_init_data(init_data, token) is True
    assert verify_telegram_init_data(init_data_urlencoded, token) is True
    assert verify_telegram_init_data(f"{init_data}hash={good_hash[:-3]}", token) is False
    print("[OK] HTTP test: initData HMAC validation")


def test_timeout_answers_allowed():
    client = TestClient(app)
    start_res = client.post("/api/test/start").json()
    sid = start_res["session_id"]
    first_q = start_res["first_question"]

    # Отправляем ответ по таймауту (is_timeout=True, selected_option=-1)
    ans_res = client.post("/api/test/answer", json={
        "session_id": sid,
        "question_id": first_q["id"],
        "selected_option": -1,
        "time_spent_seconds": 30.0,
        "is_timeout": True
    })
    assert ans_res.status_code == 200
    data = ans_res.json()
    assert data["is_correct"] is False
    assert data["next_question"] is not None
    print("[OK] HTTP test: timeout answers allowed and counted as incorrect")


if __name__ == "__main__":
    test_health_endpoint()
    test_catalog_endpoint()
    test_cors_wildcard_default()
    test_fixed_general_run_over_http()
    test_text_answer_case_sensitive()
    test_text_answer_empty_rejected()
    test_choice_without_option_rejected()
    test_timeout_answers_allowed()
    test_leads_endpoint()
    test_start_unknown_test_falls_back()
    test_contact_requires_name_and_phone()
    test_contact_persist_and_export()
    test_lead_card_format()
    test_init_data_validation()
    print("[OK] ALL HTTP-LAYER TESTS PASSED!")
