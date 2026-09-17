# 🤖 AGENTS.md — Системный Протокол для AI-Агентов

> [!IMPORTANT]
> **ПРАВИЛО №0 (КАТЕГОРИЧЕСКИ ОБЯЗАТЕЛЬНОЕ):**  
> Прежде чем писать или изменять хоть один файл кода в этом репозитории, ты **ОБЯЗАН** полностью изучить «Второй Мозг» проекта, расположенный в папке `agents/`.

---

## 🧭 Стартовый протокол агента:

1. **Изучи Главный Навигатор:**  
   👉 [agents/AGENT_GUIDE.md](file:///c:/Users/~/Desktop/New%20folder%20(2)/agents/AGENT_GUIDE.md)

2. **Проверь Правила и Запреты:**  
   👉 [agents/rules/AGENT_RULES.md](file:///c:/Users/~/Desktop/New%20folder%20(2)/agents/rules/AGENT_RULES.md)  
   👉 [agents/rules/ANTI_PATTERNS.md](file:///c:/Users/~/Desktop/New%20folder%20(2)/agents/rules/ANTI_PATTERNS.md)

3. **Проверь Базу Знаний по Ошибкам (чтобы не наступать на прошлые грабли):**  
   👉 [agents/bugs_and_fixes/](file:///c:/Users/~/Desktop/New%20folder%20(2)/agents/bugs_and_fixes)

4. **Узнай Текущую Задачу и Статус:**  
   👉 [agents/STATUS.md](file:///c:/Users/~/Desktop/New%20folder%20(2)/agents/STATUS.md)  
   👉 [agents/tasks/active_task.md](file:///c:/Users/~/Desktop/New%20folder%20(2)/agents/tasks/active_task.md)

5. **Используй Только Шаблоны из `agents/templates/`:**  
   - Для журналов сессий: `agents/templates/template_session_log.md`
   - Для отчетов об ошибках: `agents/templates/template_bug_report.md`
   - Для новых задач: `agents/templates/template_task.md`
   - Для архитектурных решений: `agents/templates/template_adr.md`

6. **Проверь Целостность Проекта Командой:**  
   ```powershell
   python agents/tools/check_integrity.py
   ```

---

## 🚫 Строгие Запреты:
- **НЕ** передавать правильные ответы `correct_option` во фронтенд.
- **НЕ** использовать синхронный `time.sleep` в async коде (только `asyncio.sleep`).
- **НЕ** перезаписывать файлы в `agents/history/` (только инкрементальные новые файлы).
- **НЕ** коммитить секретные токены в код (только `.env`).
