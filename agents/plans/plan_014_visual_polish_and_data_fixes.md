# 📋 PLAN-014: Исправление данных теста и визуальный UX-апгрейд Stanford UI

**Статус:** 🟢 COMPLETED (Выполнен, ожидает коммита)  
**Дата:** 2026-09-23  
**Исполнитель:** Gemini (Antigravity)  

---

## 🎯 Цель плана
1. Исправить пунктуационные и визуальные дефекты в банке вопросов `tests_data/test_general_2026.json`.
2. Обновить парсер пропусков в `static/js/app.js` (`/_{2,}/g`).
3. Провести глубокую визуальную и эстетическую полировку веб-интерфейса в стиле Stanford Language Center.
4. Шкалу баллов и формулу CEFR не изменять (пользователь предоставит баллы отдельно).

---

## 🛠️ Затрагиваемые файлы:
- `tests_data/test_general_2026.json` — исправление 9 вопросов с опечатками пробелов/точек (g26_08, g26_09, g26_12, g26_14, g26_25, g26_34, g26_40, g26_41, g26_42, g26_50).
- `static/js/app.js` — регулярное выражение пропусков (`/_{2,}/g`), a11y фокус и role=button для опций.
- `static/css/style.css` — визуальный стиль: карточки, пропуски (`.gap-blank`), опции, таймер, прогресс, тени.
- `static/index.html` — минорные штрихи разметки, доступности и семантики.
- `agents/STATUS.md` — актуализация статуса после выполнения.

---

## 🧪 Верификация:
- [x] `python agents/tools/check_integrity.py` — 100% OK
- [x] `python -m backend.test_simulation` — 3/3 сценария PASSED
- [x] `python agents/testing/test_api_http.py` — 13/13 HTTP тестов PASSED
- [x] `python agents/testing/test_multi_suites.py` — 4/4 тестов PASSED
- [x] `python agents/testing/test_review_feature.py` — PASSED
- [x] Проверка живого сервера :8000 — health status ok, assets 200
