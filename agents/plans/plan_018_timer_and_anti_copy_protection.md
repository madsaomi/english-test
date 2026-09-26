# 📋 План PLAN-018: Таймер (30/35 сек), фиксация пропущенных вопросов в Telegram и защита от копирования/скриншотов

**Статус:** 🟢 COMPLETED (Успешно выполнен)  
**Дата:** 2026-09-25  
**Исполнитель:** Gemini 3.8 Flash (Antigravity)  

## 📌 Цель
1. **Дифференцированный таймер с автопереходом:**
   - **Q1–Q45 (выбор варианта):** 30 секунд.
   - **Q46–Q50 (ввод текста):** 35 секунд (больше времени на набор слова с клавиатуры).
   - Обратный отсчет по системному времени `Date.now()` (защита от читерства со сворачиванием вкладки).
   - Предупреждающая пульсация при остатке ≤ 5 секунд.
   - При истечении времени — автоматическая фиксация текущего ответа (если набран в инпуте — отправляется он; если пусто — пропуск) и мгновенный переход к следующему вопросу.
2. **Фиксация пропущенных (по таймауту) вопросов в Telegram:**
   - Подсчет количества вопросов, пропущенных из-за таймаута: `skipped_count`.
   - Вывод в единую карточку результатов в Telegram:
     - Например: `🎯 Точность: 38 из 50 (76%) · ⏳ Пропущено по времени: 4` (или `✨ Все вопросы отвечены вовремя`).
3. **Защита от копирования вопросов (Anti-Copy):**
   - Запрет выделения текста (`user-select: none; -webkit-touch-callout: none`).
   - Блокировка контекстного меню (`contextmenu`).
   - Блокировка горячих клавиш копирования и отладки (`Ctrl+C`, `Ctrl+X`, `Ctrl+U`, `Ctrl+S`, `F12`, DevTools).
   - Блокировка событий буфера обмена (`copy`, `cut`, `dragstart`).
   - Запрет вставки (`paste`) в текстовое поле ввода Q46–Q50 (слово нужно вводить руками, а не вставлять из шпаргалки).
4. **Защита от скриншотов (Anti-Screenshot):**
   - Перехват клавиши `PrintScreen` с очисткой буфера обмена (`navigator.clipboard.writeText('')`).
   - Скрытие/размытие карточки при уходе с вкладки / сворачивании приложения (`visibilitychange` / `window.blur` с проверкой активного элемента).
   - Предотвращение случайного закрытия в Telegram WebApp (`tg.enableClosingConfirmation()`).
   - `@media print { body { display: none !important; } }`.

---

## 🔍 Архитектурный анализ и затрагиваемые файлы

1. **`backend/models.py`:**
   - Добавить поле `skipped_count: int = 0` в модель `TestResult`.
2. **`backend/cat_engine.py`:**
   - В методе `submit_answer`: учитывать флаг таймаута или пропущенный ответ (`selected_option == -1` или пустой ввод с пометкой `is_timeout=True`).
   - В методе `finalize_test`: подсчитывать `skipped_count = sum(1 for h in session.history if h.get('is_timeout') or (h.get('selected_option') == -1 and not h.get('selected_text')))` и передавать в `TestResult`.
3. **`backend/main.py`:**
   - В `@app.post("/api/test/answer")`: разрешить `selected_option = -1` и пустой `selected_text = ""` при таймауте (чтобы бэкенд не возвращал ошибку 400).
4. **`backend/telegram_bot.py`:**
   - В `format_unified_lead_card` и `format_result_card`: добавить строку с информацией о пропущенных по таймеру вопросах:
     `🎯 Точность: {result.correct_count} из {result.total_questions} ({result.accuracy_percentage}%)\n⏳ Пропущено по таймеру: {result.skipped_count}`.
5. **`static/js/app.js`:**
   - Таймер: 30 секунд для `choice` (Q1–Q45) и 35 секунд для `text` (Q46–Q50).
   - Расчет через разницу реального времени `Date.now() - questionStartTime`.
   - Автоотправка при нуле секунд: `is_timeout = true`.
   - Защита: `contextmenu`, `copy`, `cut`, `dragstart`, `keydown`, `paste` на инпуте, `visibilitychange` блюр.
   - Вызов `tg.enableClosingConfirmation()` при наличии Telegram WebApp.
6. **`static/css/style.css`:**
   - `user-select: none;` на вопросе, стили пульсации таймера ≤ 5 сек, стили блюра при скрытии страницы, `@media print`.

---

## 🧪 План верификации

1. `python agents/tools/check_integrity.py` — проверка целостности структуры.
2. `python agents/testing/test_api_http.py` — проверка REST API (включая таймаут и проверку поля `skipped_count`).
3. `python -m backend.test_simulation` — прогон симуляции тестов.
4. Проверка в браузере: таймер 30 сек на Q1–Q45, 35 сек на Q46–Q50, автопереход при истечении, запрет копирования, размытие при уходе со вкладки.
