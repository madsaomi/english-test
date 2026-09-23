# 📋 Активная задача: TASK-012 — «Test for general 2026» как единственный основной тест

**Статус:** 🟢 COMPLETED (Завершена)  
**Дата создания:** 2026-09-22  
**Дата завершения:** 2026-09-22  
**Исполнитель:** opencode (opencode/mimo-v2.6-flash-free)  
**План:** PLAN-010 `agents/plans/plan_010_main_test_general_2026.md`

---

## 🎯 Цель задачи
Сделать `Test for general 2026.docx` единственным основным тестом платформы, полностью удалить все автоматически созданные тесты и реализовать поле ввода для 5 текстовых вопросов (case-sensitive).

## 📌 Решения пользователя
1. Объём удаления: «Всё кроме нового» — 3 JSON + `cefr_adaptive` + `QUESTION_BANK` + `cefr_adaptive_bank.json` + CAT-проверки старого образца.
2. 5 fill-in вопросов → поле ввода; сравнение **с учётом регистра** (только `.strip()` внешних пробелов).
3. `explanation: ""` для всех вопросов — без подсказок и пояснений.

---

## 📌 Чек-лист выполнения:

- [x] **Шаг 1:** `backend/models.py` — `question_type`, `selected_text`, Optional `correct_option`/`correct_text`, расширенный `QuestionReviewItem`, `StartTestRequest.test_id = None`.
- [x] **Шаг 2:** `tests_data/test_general_2026.json` — 50 вопросов (45 choice + 5 text), id `g26_01..g26_50`, ключ docx 45/45, `explanation: ""`.
- [x] **Шаг 3:** Удалены `test_business_english.json`, `test_grammar_master.json`, `test_starter_a1_a2.json`, `cefr_adaptive_bank.json`, `backend/questions.py`; `template_*.json` не тронуты.
- [x] **Шаг 4:** `test_loader.py` — без `QUESTION_BANK`, `DEFAULT_TEST_ID = "test_general_2026"`, `get_default_test_id()`.
- [x] **Шаг 5:** `cat_engine.py` — без `QUESTION_BANK`, `find_question()`, `submit_answer(..., selected_text=None)` case-sensitive, history/review с новыми полями.
- [x] **Шаг 6:** `main.py` — дефолтный `test_id = None`, 400-валидация (choice без `selected_option`, text без непустого `selected_text`).
- [x] **Шаг 7:** Фронтенд — `selectedTestId = 'test_general_2026'`, `renderDefaultTestCards` (1 карточка), text-ветка `#text-answer-input`/`#text-answer-btn`, `submitTextAnswer()`, CSS `.text-answer-*`.
- [x] **Шаг 8:** Переписаны `test_simulation.py` (accuracy 100/0/50), `test_api_http.py` (catalog==1, 50Q, case, 400), `test_multi_suites.py`, `test_review_feature.py`, `test_e2e.py`, `export_results.py`.
- [x] **Шаг 9:** `check_integrity.py` раздел 4 — ≥50 вопросов, 45 choice + 5 text, единственность набора; синк с `cefr_adaptive_bank` удалён.
- [x] **Шаг 10:** Документация — `CODEBASE_MAP.md`, `QUESTION_AUTHORING_GUIDE.md`, `SECURITY_SPEC.md`, `README.md`, `QA_CHECKLIST.md`; user-facing текст (`index.html` meta/title/hero, `telegram_bot.py` welcome/help) приведён к 50-вопросному тесту.
- [x] **Шаг 11:** Верификация — integrity 100%; `test_api_http` 13/13; `test_simulation` 3/3; `test_multi_suites` 4/4; `test_review_feature` OK; `test_e2e` PASSED; live smoke :8764 OK (catalog, health=50, wrong choice, empty 400, case-sensitivity, full 50/50, fallback).
- [x] **Шаг 12:** Документация — `active_task.md` (TASK-012), `STATUS.md`, журнал сессии 17, план PLAN-010 → COMPLETED.

---

## 🏁 Результаты:
Единственный тест `test_general_2026` (50 вопросов, ~15 мин) в каталоге; все автотесты удалены; 5 текстовых вопросов вводятся в поле с case-sensitive сравнением; empty text и пустой выбор — 400; неизвестный `test_id` фолбэкается на основной тест. Тесты: 100% / 13/13 / 3/3 / 4/4 / review OK / e2e OK / live smoke OK. Изменения НЕ закоммичены — ждать явного «да» пользователя.
