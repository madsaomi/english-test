# 📋 План PLAN-016: Внедрение новой шкалы оценивания результатов (50 вопросов)

## 📌 Цель
Обновить логику расчета итогового уровня теста `test_general_2026` (50 вопросов) в соответствии с новыми требованиями:
- **0–15 правильных:** `Beginner`
- **16–24 правильных:** `Elementary`
- **25–32 правильных:** `Pre-Intermediate`
- **33–39 правильных:** `Intermediate`
- **40–45 правильных:** `Upper-Intermediate`
- **46–50 правильных:** `Advanced`

Отображение: чистые текстовые названия уровней без кодов CEFR.

---

## 🔍 Исследование и архитектурный анализ
1. **Текущее состояние `backend/cat_engine.py`**:
   - Для `fixed` режима сейчас используется аппроксимация по формуле `avg_diff + score_offset` и сопоставление со старыми диапазонами CEFR (A1-C2).
   - В старой таблице отсутствовал уровень `Pre-Intermediate`, а 46-50 не мапились на `Advanced` напрямую.
2. **Отображение в `telegram_bot.py`**:
   - Функция `format_clean_level(cefr_level, level_title)` форматирует строку уровня для карточки.
   - Если `cefr_level` и `level_title` совпадают (например `"Intermediate"`), отображается чистое название: `🏆 Итоговый уровень: Intermediate`.
3. **Совместимость с автотестами**:
   - `test_simulation.py` проверяет сценарии High (50/50), Mid (25/50), Low (0/50).
   - High (50 верных) получит `Advanced`.
   - Mid (25 верных) получит `Pre-Intermediate`.
   - Low (0 верных) получит `Beginner`.
   - `VALID_LEVELS` в тестах нужно расширить новыми текстовыми уровнями.

---

## 🛠️ Пошаговый план реализации

### Шаг 1. Обновление логики оценки в `backend/cat_engine.py`
- Добавить специализированную функцию/таблицу градации для фиксированного теста на 50 вопросов:
  ```python
  FIXED_50_SCORING_TABLE = [
      (0, 15, "Beginner", "Beginner", "Начальный уровень владения языком. Понимание базовых фраз, построение простых предложений."),
      (16, 24, "Elementary", "Elementary", "Элементарный уровень. Общение на простые повседневные темы, знание базовых временных форм."),
      (25, 32, "Pre-Intermediate", "Pre-Intermediate", "Уровень ниже среднего. Понимание несложных текстов, диалоги на знакомые темы, базовая грамматика."),
      (33, 39, "Intermediate", "Intermediate", "Средний уровень. Понимание сути бесед на знакомые темы, уверенное выражение мыслей в путешествиях и на работе."),
      (40, 45, "Upper-Intermediate", "Upper-Intermediate", "Продвинутый уровень. Свободное общение с носителями, понимание сложной грамматики и идиом."),
      (46, 50, "Advanced", "Advanced", "Профессиональный уровень. Свободное беглое владение языком, богатый словарный запас и точные грамматические структуры."),
  ]
  ```
- В методе `finalize_test(session)`:
  - Если режим `fixed` и `total_questions == 50` (или `session.test_id == 'test_general_2026'`), определять уровень по количеству правильных ответов `correct_count` по таблице `FIXED_50_SCORING_TABLE`.
  - Итоговый балл `score = int(round((correct_count / total_questions) * 100))`.
  - Корректно формировать блок рекомендаций для новых уровней (`Beginner`, `Elementary`, `Pre-Intermediate`, `Intermediate`, `Upper-Intermediate`, `Advanced`).

### Шаг 2. Адаптация форматирования в `backend/telegram_bot.py`
- Проверить `format_clean_level(cefr_level, level_title)`: если `cefr_level == level_title`, возвращать просто `level_title` без лишних разделителей `·`.
- Убедиться, что в карточке Telegram уровень выводится красиво: `🏆 Итоговый уровень: Intermediate` (или `Pre-Intermediate`, `Advanced` и т.д.).

### Шаг 3. Обновление автотестов
- В `backend/test_simulation.py`:
  - Добавить новые уровни в `VALID_LEVELS = {"Beginner", "Elementary", "Pre-Intermediate", "Intermediate", "Upper-Intermediate", "Advanced", "A1", "A2", "B1", "B2", "C1", "C2"}`.
  - Проверить, что `High` даёт `Advanced`, `Mid` даёт `Pre-Intermediate`, `Low` даёт `Beginner`.
- В `agents/testing/test_multi_suites.py`: убедиться в успешности прогона.

### Шаг 4. Обновление документации «Второго Мозга»
- Зафиксировать новую шкалу в `agents/architecture/CAT_ALGORITHM_SPEC.md` или создать соответствующую запись в `agents/tasks/active_task.md` и `agents/STATUS.md`.

---

## 🧪 План верификации
1. Запуск юнит-симуляции:
   ```powershell
   python -m backend.test_simulation
   ```
   *Критерий:* 0 верных -> `Beginner`, 25 верных -> `Pre-Intermediate`, 50 верных -> `Advanced`.
2. Запуск проверки всех граничных диапазонов теста (0, 15, 16, 24, 25, 32, 33, 39, 40, 45, 46, 50).
3. Запуск комплексных проверок целостности и API:
   ```powershell
   python agents/tools/check_integrity.py
   python -m agents.testing.test_multi_suites
   python -m agents.testing.test_review_feature
   python -m agents.testing.test_api_http
   ```
