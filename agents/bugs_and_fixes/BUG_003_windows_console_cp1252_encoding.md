# 🐛 BUG-003: Ошибка кодировки UnicodeEncodeError charmap cp1252 в PowerShell

- **Дата обнаружения:** 2026-09-17 21:19
- **Статус:** 🟢 РЕШЕНО
- **Затронутый файл:** `backend/test_simulation.py`
- **Компонент:** Тестовые скрипты / Консольный вывод Windows

---

## 🔍 1. Симптом (Что произошло)
При запуске тестового скрипта `python -m backend.test_simulation` возникла ошибка:

```text
Traceback (most recent call last):
  File "C:\Users\~\Desktop\New folder (2)\backend\test_simulation.py", line 7, in test_cat_simulation
    print(f"Всего вопросов в банке: {len(QUESTION_BANK)}")
  File "C:\Users\~\AppData\Local\Python\pythoncore-3.14-64\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
UnicodeEncodeError: 'charmap' codec can't encode characters in position 0-4: character maps to <undefined>
```

---

## 🔬 2. Первопричина (Root Cause — ПОЧЕМУ это произошло)
- По умолчанию консоль PowerShell в англоязычной локали Windows использует кодовую страницу `cp1252` (Western European).
- Когда скрипт на Python выполняет `print(...)` с кириллическими символами («Всего вопросов...»), стандартный поток вывода Python пытается закодировать эти символы через кодек консоли (`cp1252`).
- Так как в таблице `cp1252` нет русских букв, возникает фатальное исключение `UnicodeEncodeError`.

---

## 🛠️ 3. Решение (Как исправлено)
1. В консоли PowerShell перед запуском команды Python явно задается системная переменная окружения UTF-8:
   ```powershell
   $env:PYTHONIOENCODING="utf-8"
   python -m backend.test_simulation
   ```
2. В скриптах автоматических тестов (`test_e2e.py`) строковые литералы вывода оформлены на ASCII или защищены явным кодированием в UTF-8.

---

## 🛡️ 4. Правило предотвращения (Для всех будущих агентов)
На Windows перед выполнением скриптов с не-ASCII выводом через PowerShell всегда устанавливать `$env:PYTHONIOENCODING="utf-8"`.
