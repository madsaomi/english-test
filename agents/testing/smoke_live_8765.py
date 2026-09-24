import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8765"


def post(path, obj):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(obj).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def get(path):
    with urllib.request.urlopen(BASE + path) as r:
        return r.status, json.loads(r.read().decode())


def main():
    print("health", get("/api/health")[1])
    print("catalog", get("/api/tests")[1][0]["id"])
    with open("tests_data/test_general_2026.json", encoding="utf-8") as f:
        bank = json.load(f)
    ans = {q["id"]: q for q in bank["questions"]}
    st, start = post("/api/test/start", {})
    assert st == 200, st
    sid, qid = start["session_id"], start["first_question"]["id"]
    n = 0
    while True:
        n += 1
        q = ans[qid]
        payload = {"session_id": sid, "question_id": qid, "time_spent_seconds": 1}
        if q["question_type"] == "text":
            payload["selected_text"] = q["correct_text"]
        else:
            payload["selected_option"] = q["correct_option"]
        st, r = post("/api/test/answer", payload)
        assert st == 200, (n, st, r)
        if qid == "g26_29":
            print(f"reached Q29 at n={n}")
        if r["is_finished"]:
            res = r["result"]
            print(
                "FULL RUN n=%s score=%s acc=%s%% total=%s level=%s"
                % (
                    n,
                    res["score"],
                    res["accuracy_percentage"],
                    res["total_questions"],
                    res["cefr_level"],
                )
            )
            break
        qid = r["next_question"]["id"]
    st, body = post(
        "/api/test/answer",
        {"session_id": "stale-uuid", "question_id": "g26_01", "selected_option": 0, "time_spent_seconds": 1},
    )
    print("stale", st, body)
    assert st == 404 and "Сессия" in body["detail"]
    print("ALL LIVE SMOKE PASSED")


if __name__ == "__main__":
    main()
