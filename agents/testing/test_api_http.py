"""HTTP-layer API tests using FastAPI TestClient.

Проверяют реальный HTTP-стек: маршрутизацию, сериализацию JSON, CORS-заголовки,
полный цикл фиксированного теста, а также криптографию initData (Telegram WebApp).
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
from backend.telegram_bot import format_compact_lead_card


def test_health_endpoint():
    client = TestClient(app)
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["total_questions_in_bank"] >= 25
    assert "active_sessions" in data
    print("[OK] HTTP test: /api/health")


def test_catalog_endpoint():
    client = TestClient(app)
    res = client.get("/api/tests")
    assert res.status_code == 200
    metas = res.json()
    assert len(metas) >= 4
    assert metas[0]["id"] == "cefr_adaptive"
    assert metas[0]["mode"] == "adaptive"
    print("[OK] HTTP test: /api/tests catalog")


def test_cors_wildcard_default():
    client = TestClient(app)
    res = client.get("/api/health", headers={"Origin": "https://example.com"})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "*"
    print("[OK] HTTP test: CORS wildcard default")


def test_fixed_business_run_over_http():
    client = TestClient(app)
    start = client.post("/api/test/start", json={"test_id": "test_business_english"})
    assert start.status_code == 200
    data = start.json()
    sid = data["session_id"]
    suite = test_repository.get_test_suite("test_business_english")

    current_q = data["first_question"]
    step = 0
    final = None
    while current_q and step < 8:
        qmodel = next(q for q in suite.questions if q.id == current_q["id"])
        ans = client.post("/api/test/answer", json={
            "session_id": sid,
            "question_id": current_q["id"],
            "selected_option": qmodel.correct_option,
            "time_spent_seconds": 3.0
        })
        assert ans.status_code == 200
        body = ans.json()
        if body["is_finished"]:
            final = body["result"]
            break
        current_q = body["next_question"]
        step += 1

    assert final is not None, "Фиксированный тест должен завершиться"
    assert final["total_questions"] == 8
    assert final["cefr_description"], "Описание CEFR должно присутствовать в результате"

    res = client.get(f"/api/test/result/{sid}")
    assert res.status_code == 200
    assert res.json()["session_id"] == sid
    print("[OK] HTTP test: full fixed business run")


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
    print("[OK] HTTP test: unknown suite fallback")


def _complete_fixed_business(client, test_id: str = "test_business_english"):
    """Проводит фиксированный тест до конца, возвращает session_id."""
    start = client.post("/api/test/start", json={"test_id": test_id})
    data = start.json()
    sid = data["session_id"]
    suite = test_repository.get_test_suite(test_id)
    current_q = data["first_question"]
    step = 0
    while current_q and step < 8:
        qmodel = next(q for q in suite.questions if q.id == current_q["id"])
        ans = client.post("/api/test/answer", json={
            "session_id": sid,
            "question_id": current_q["id"],
            "selected_option": qmodel.correct_option,
            "time_spent_seconds": 3.0
        })
        body = ans.json()
        if body["is_finished"]:
            return sid
        current_q = body["next_question"]
        step += 1
    raise AssertionError("Тест не завершился")


def test_contact_requires_name_and_phone():
    client = TestClient(app)
    sid = _complete_fixed_business(client)

    res = client.post("/api/test/submit-contact", json={"session_id": sid, "name": "Тест Тестов"})
    assert res.status_code == 400
    assert "Телефон" in res.json()["detail"]

    res = client.post("/api/test/submit-contact", json={"session_id": sid, "phone": "+7 999 000-00-00"})
    assert res.status_code == 422  # name обязателен в модели

    res = client.post("/api/test/submit-contact", json={"session_id": sid, "name": "", "phone": "+7 999 000-00-00"})
    assert res.status_code == 400
    assert "ФИО" in res.json()["detail"]
    print("[OK] HTTP test: contact requires name and phone")


def test_contact_persist_and_export():
    client = TestClient(app)
    sid = _complete_fixed_business(client)

    resp = client.post("/api/test/submit-contact", json={
        "session_id": sid,
        "name": "Иван Петров",
        "phone": "+7 999 123-45-67",
        "telegram_username": "ivan_petrov",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    lead = lead_store.get_lead(sid)
    assert lead is not None
    assert lead.student_name == "Иван Петров"
    assert lead.phone == "+7 999 123-45-67"
    assert lead.result.cefr_level

    export = client.get("/api/export/leads").json()
    assert any(item["session_id"] == sid for item in export)
    print("[OK] HTTP test: lead persisted and exported")


def test_compact_lead_card_format():
    card = format_compact_lead_card(
        name="Иван Петров",
        level_code="B2",
        level_title="Upper-Intermediate",
        phone="+7 999 123-45-67",
        received_at="21.09.2026 14:30",
    )
    assert "НОВАЯ ЗАЯВКА С ТЕСТА" in card
    assert "Иван Петров" in card
    assert "B2 — Upper-Intermediate" in card
    assert "<code>+7 999 123-45-67</code>" in card
    assert "21.09.2026 14:30" in card
    print("[OK] HTTP test: compact lead card format")


def test_init_data_validation():
    token = "123456:TESTTOKEN"

    assert verify_telegram_init_data("auth_date=1700000000&user=%7B%22id%22%3A1%7D&hash=deadbeef", token) is False
    assert verify_telegram_init_data("foo=bar&hash=deadbeef", token) is False
    assert verify_telegram_init_data("", token) is False

    pairs = [
        ("auth_date", "1700000000"),
        ("query_id", "AAHdF6IQAAAAAN0XohDhrOrc"),
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


if __name__ == "__main__":
    test_health_endpoint()
    test_catalog_endpoint()
    test_cors_wildcard_default()
    test_fixed_business_run_over_http()
    test_leads_endpoint()
    test_start_unknown_test_falls_back()
    test_contact_requires_name_and_phone()
    test_contact_persist_and_export()
    test_compact_lead_card_format()
    test_init_data_validation()
    print("[OK] ALL HTTP-LAYER TESTS PASSED!")