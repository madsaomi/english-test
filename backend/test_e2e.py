import urllib.request
import json

def run_e2e_test():
    # 1. Start test
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/test/start',
        method='POST',
        headers={'Content-Type': 'application/json'},
        data=b'{}'
    )
    res = urllib.request.urlopen(req)
    data = json.loads(res.read().decode())
    session_id = data['session_id']
    q = data['first_question']
    print(f"==> 1. START: session_id={session_id}")

    # 2. Answer questions until completion
    question_count = 0
    final_result = None
    while q:
        question_count += 1
        if q.get('question_type') == 'text':
            payload_obj = {
                'session_id': session_id,
                'question_id': q['id'],
                'selected_text': 'answered',
                'time_spent_seconds': 4.0
            }
        else:
            payload_obj = {
                'session_id': session_id,
                'question_id': q['id'],
                'selected_option': (question_count % 3),
                'time_spent_seconds': 4.0
            }
        payload = json.dumps(payload_obj).encode('utf-8')
        r = urllib.request.urlopen(urllib.request.Request(
            'http://127.0.0.1:8000/api/test/answer',
            method='POST',
            headers={'Content-Type': 'application/json'},
            data=payload
        ))
        ans_data = json.loads(r.read().decode('utf-8'))
        print(f"   Q{question_count} answered. is_correct={ans_data['is_correct']}, next_diff={ans_data['current_difficulty_label']}")
        if ans_data['is_finished']:
            final_result = ans_data['result']
            break
        q = ans_data['next_question']

    print(f"==> 2. TEST FINISHED in {question_count} questions!")
    print(f"   Level: {final_result['cefr_level']} ({final_result['level_title']})")
    print(f"   Score: {final_result['score']}/100, Accuracy: {final_result['accuracy_percentage']}%")
    print(f"   Skills: {len(final_result['skills'])} categories, Weak: {final_result['weak_topics']}")

    # 3. Submit contact info
    contact_payload = json.dumps({
        'session_id': session_id,
        'name': 'Alexander Test',
        'phone': '+7 900 123-45-67',
        'telegram_username': 'alex_test',
        'tg_user_id': 123456789
    }).encode('utf-8')
    r_contact = urllib.request.urlopen(urllib.request.Request(
        'http://127.0.0.1:8000/api/test/submit-contact',
        method='POST',
        headers={'Content-Type': 'application/json'},
        data=contact_payload
    ))
    c_data = json.loads(r_contact.read().decode('utf-8'))
    print("==> 3. CONTACT SUBMITTED:", c_data)
    assert c_data['status'] == 'success'
    print(" ALL END-TO-END TESTS PASSED!")

if __name__ == '__main__':
    run_e2e_test()
