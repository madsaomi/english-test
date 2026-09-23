# 📝 План PLAN-010: «Test for general 2026» как единственный основной тест

- **ID плана:** PLAN-010
- **Связанная задача:** TASK-012
- **Дата создания:** 2026-09-22
- **Автор:** opencode (opencode/big-pickle)
- **Статус:** ✅ COMPLETED (Выполнен)

---

## 🎯 Цель
Сделить `Test for general 2026.docx` единственным основным тестом платформы и **полностью удалить** все автоматически созданные тесты: 3 JSON-набора (`test_business_english`, `test_grammar_master`, `test_starter_a1_a2`), адаптивный `cefr_adaptive` (вместе с `backend/questions.py` → `QUESTION_BANK` и `tests_data/cefr_adaptive_bank.json`) и все проверки/симуляции, завязанные на них.

## 📌 Решения пользователя (зафиксированы)
1. **Объём удаления:** «Всё кроме нового» — вырезать 3 JSON + `cefr_adaptive` + `QUESTION_BANK` + `cefr_adaptive_bank.json` + CAT-симуляцию старого образца и связанные проверки. В каталоге остаётся **только** `test_general_2026`.
2. **5 открытых fill-in вопросов** из docx («Put the verbs in brackets…»): реализовать **поле ввода** на фронтенде; сравнение **с учётом регистра** (маленькие/большие буквы имеют значение; внешние пробелы по краям `.strip()`).
3. **Пояснения (`explanation`):** пустые строки — «ученик просто выбирает вариант, ни подсказок ничего».

## 📊 Исследование (факты)
- **docx:** 45 MCQ (A–D), ключ `Key:` = 45 букв, парсинг сходится 45/45; + 5 fill-in с текстовыми ответами (`was reading`, `will have been living`, `are playing`, `had studied`, `have been waiting`).
- **Итого в тесте: 50 вопросов** (45 choice + 5 text).
- Схема `Question` требует: `level`, `difficulty`, `category`, `topic`, `explanation` — авторизовать вручную (levels A1–C1 по содержанию, difficulty по гайду `QUESTION_AUTHORING_GUIDE`).
- Зависимости удаляемого: `test_loader.py` (fallback `cefr_adaptive` из `QUESTION_BANK`, pool из банка), `cat_engine.py` (import `QUESTION_BANK` — уже не используется), `main.py` (дефолт `"cefr_adaptive"` в `/api/test/start`), `test_simulation`, `check_integrity` (раздел 4 + синк с `cefr_adaptive_bank.json`), `test_api_http`, `test_multi_suites`, `test_review_feature`, `backend/test_e2e.py`, `app.js` (хардкод 4 карточек, `selectedTestId='cefr_adaptive'`), `CODEBASE_MAP.md`, `QUESTION_AUTHORING_GUIDE.md`.
- Фронтенд **не показывает review на сайте** (результат уходит в Telegram) — правки review UI не нужны; нужны правки Telegram-формата только если он зависит от `explanation` (проверить при верификации).

---

## 📋 Шаги реализации

### ✅ Шаг 1. Модели данных (`backend/models.py`)
- `Question`: добавить `question_type: str = "choice"` (`"choice"` | `"text"`); `options: List[str] = []`; `correct_option: Optional[int] = None`; `correct_text: Optional[str] = None`; `explanation: str = ""`.
- `ClientQuestion`: добавить `question_type: str = "choice"`.
- `AnswerSubmission`: `selected_option: Optional[int] = None` + `selected_text: Optional[str] = None`.
- `QuestionReviewItem`: `selected_option: Optional[int] = None`, `correct_option: Optional[int] = None`, + `question_type: str = "choice"`, `selected_text: Optional[str] = None`, `correct_text: Optional[str] = None`.
- `StartTestRequest.test_id: Optional[str] = None` (дефолт резолвится в единственный набор).

### ✅ Шаг 2. Данные нового теста (`tests_data/test_general_2026.json`)
- Сгенерировать скриптом из docx (парсинг paragraphs + `Key:`), затем дополнить авторскими метаданными:
  - id: `test_general_2026`, title: «General English Test 2026», description (RU), category `General`, level `A1-C1`, mode `fixed`, icon `📝`, `estimated_time_minutes: 15`.
  - 45 choice: `id g26_01..g26_45`, ровно 4 options из docx, `correct_option` = индекс буквы ключа (A=0…D=3), `level`/`difficulty` (1.0–4.5 по гайду)/`category` (Grammar|Vocabulary|Usage по содержанию)/`topic` (конкретная тема), `explanation: ""`, пропуск `______…` нормализовать в `___`.
  - 5 text: `id g26_46..g26_50`, `question_type: "text"`, `options: []`, `correct_option: null`, `correct_text` из Key (кириллица/регистр эталона — как в docx), `___` вместо длинных подчёркиваний, свои level/difficulty/topic, `explanation: ""`.
- Валидация генерации: ровно 50 вопросов, 45 с `correct_option ∈ [0..3]`, 5 с непустым `correct_text`, id уникальны.

### ✅ Шаг 3. Удаление старых тестов
- `tests_data/test_business_english.json`
- `tests_data/test_grammar_master.json`
- `tests_data/test_starter_a1_a2.json`
- `tests_data/cefr_adaptive_bank.json`
- `backend/questions.py` (`QUESTION_BANK`)
- `tests_data/template_*.json` **не трогаем** (лоадер их пропускает, это шаблоны).

### ✅ Шаг 4. Загрузчик (`backend/test_loader.py`)
- Убрать import `QUESTION_BANK`, fallback-сборку `cefr_adaptive`, подмешивание банка в `get_all_questions_pool()`.
- `get_all_tests_meta()`: убрать спецпорядок с `cefr_adaptive` — обычный список наборов.
- Ввести `DEFAULT_TEST_ID = "test_general_2026"` (или «единственный набор в репозитории») для фолбэков.

### ✅ Шаг 5. Движок (`backend/cat_engine.py`)
- Удалить неиспользуемый import `QUESTION_BANK`; дефолты `test_id` → `DEFAULT_TEST_ID`.
- `submit_answer(..., selected_text: Optional[str] = None)`:
  - `question_type == "text"`: верность `(selected_text or "").strip() == (correct_text or "").strip()` — **без** приведения регистра (case-sensitive);
  - иначе прежняя логика по `selected_option` (требовать `selected_option is not None`, иначе False/400).
- Хранить в `history` также `selected_text`; в `finalize_test` наполнять `QuestionReviewItem` новыми полями (для text: `selected_option`/`correct_option` = None).
- Адаптивная ветка `select_next_question` остаётся технически (наборов с mode=adaptive больше нет) — не выпиливаем, чтобы не переписывать весь движок; все живые наборы `fixed`.

### ✅ Шаг 6. API (`backend/main.py`)
- `/api/test/start`: `test_id = payload.test_id or DEFAULT_TEST_ID`; неизвестный id → фолбэк на DEFAULT (существующий контракт «unknown suite fallback» сохраняется).
- `/api/test/answer`: пробрасывать `selected_text`; для choice без `selected_option` → 400 «Не выбран вариант», для text без непустого `selected_text` → 400 «Введите ответ».
- `/api/health`: `total_questions_in_bank` уже берёт pool (=50) — без изменений.

### ✅ Шаг 7. Фронтенд (`static/js/app.js` + `static/css/style.css`)
- `selectedTestId = 'test_general_2026'`, `currentTestMode = 'fixed'`.
- `renderDefaultTestCards()`: одна карточка `test_general_2026` (icon `ICONS.target`, 50 вопросов, ~15 мин).
- `renderQuestion(q)`:
  - `q.question_type === 'text'` → вместо option-карточек поле `<input class="text-answer-input">` (автофокус, Enter отправляет) + кнопка «Ответить»;
  - иначе текущий рендер 4 вариантов.
- Новый `submitTextAnswer()`: пустой ввод → тост «Введите ответ»; POST `{session_id, question_id, selected_text, time_spent_seconds}` (без `selected_option`); та же пауза 350 мс и переход.
- Выбор варианта (choice) — без изменений.
- CSS: `.text-answer-input` в стиле бланка (бумажный фон, нижняя граница как пропуск, focus-ring `--primary`), кнопка — существующие `.btn-primary`.

### ✅ Шаг 8. Переписать тесты инфраструктуры
- `agents/testing/test_api_http.py`:
  - catalog: `len(metas) == 1`, `metas[0].id == "test_general_2026"`, `mode == "fixed"`, `total_questions == 50`;
  - полный прогон динамическим циклом (`while not finished`, лимит 60): для choice отвечать `correct_option`, для text — `correct_text` (плюс один негативный кейс: text с другим регистром → `is_correct == false`);
  - `_complete_*` обобщить; health `>= 25` остаётся (50 ≥ 25).
- `agents/testing/test_multi_suites.py`: ровно 1 набор; полный fixed-прогон; case-sensitivity кейс; **удалить** adaptive-тест `test_04`.
- `agents/testing/test_review_feature.py`: сессия на новом наборе; `explanation == ""`; поддержать text-вопрос в review.
- `backend/test_simulation.py`: переписать под fixed-набор (3 сценария: все верно / все неверно / 50-на-50); ассерт **accuracy 100/0/50 + монотонность score(high > mid > low) + уровень из валидного CEFR-набора** (не захардкоженные полосы C1/A1 — формула fixed зависит от авторской difficulty).
- `backend/test_e2e.py`: учитывать `question_type` (для text слать `selected_text`).

### ✅ Шаг 9. Integrity (`agents/tools/check_integrity.py`)
- Раздел 4 переписать: наличие `tests_data/test_general_2026.json`; ≥50 вопросов; уникальные id; у choice: `len(options) == 4` и `0 <= correct_option < 4`; у text: непустой `correct_text` и `question_type == "text"`; все `level` из `{A1..C2}`; **удалить** проверку синка с `cefr_adaptive_bank.json` и требование полного охвата A1–C2 (контент не покрывает C2 — вместо этого: ≥4 разных уровней).
- `explanation == ""` — не проверяем (по решению пользователя пустые).

### ✅ Шаг 10. Документация Второго Мозга
- Обновить `agents/architecture/CODEBASE_MAP.md` (строка `backend/questions.py` → `tests_data/test_general_2026.json`).
- Обновить `agents/architecture/QUESTION_AUTHORING_GUIDE.md` (источник новых вопросов — JSON в `tests_data/`, без `questions.py`; убрать требование explanation-текста → пусто по политике проекта).
- Историю (`agents/history/*`, старые планы, BUG_003) **не переписывать**.

### ✅ Шаг 11. Верификация
1. `python agents/tools/check_integrity.py` → 100%.
2. `python agents/testing/test_api_http.py` → все [OK].
3. `python agents/testing/test_multi_suites.py` → все [OK].
4. `python agents/testing/test_review_feature.py` → [OK].
5. `python -m backend.test_simulation` → 3/3.
6. Live smoke (uvicorn :8764, PowerShell `[ordered]@{}`/.Contains()):
   - `/api/tests` → ровно 1 запись `test_general_2026`;
   - `/api/test/start` `{}` → 50 вопросов (первый choice);
   - ответ choice верный/неверный; text: точное совпадение → верно, другой регистр (`Was reading`) → **неверно**, пустой ввод → 400;
   - полный прогон до результата; `/api/health.total_questions_in_bank == 50`;
   - фолбэк неизвестного `test_id` → 200.
7. Ручной прогон в браузере: каталог — 1 карточка, у вопроса 46 поле ввода, подсказок/пояснений нет.

### ✅ Шаг 12. Документация после верификации
- `agents/tasks/active_task.md` → TASK-012 COMPLETED.
- `agents/STATUS.md` — фаза + строка веб/контента.
- `agents/history/session_2026-09-22_17_main_test_general.md` (н�овый файл, не перезапись).
- `plan_010_main_test_general_2026.md` → COMPLETED + ✅ к каждому шагу.
- **Commit + push — только после отдельного явного «да» пользователя.**

---

## ⚠️ Риски и митигация
- **Регистр в текстовых ответах:** эталоны из docx копируются байт-в-байт; тест case-sensitivity покрывает.
- **Формула уровня fixed** зависит от авторской difficulty → симуляция ассертит accuracy/монотонность, а не жёсткие CEFR-полосы.
- **`selected_option: Optional`** — совместимо с текущими payload (все старые тесты его передают).
- **Адаптивный код в `cat_engine` остаётся мёртвым** (наборов adaptive нет) — осознанно: выпиливание = переписывание движка, вне объёма.
- Telegram-карточка результата: при пустых `explanation` лишнего текста не появится — проверить при smoke.

## 📎 Вне объёма
- Изменение CAT-алгоритма, тем, стилей (кроме поля ввода), PDF (отменён навсегда), `og:image`, истории лидов.
