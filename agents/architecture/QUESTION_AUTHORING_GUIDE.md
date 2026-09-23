# ✍️ Руководство по добавлению вопросов (QUESTION_AUTHORING_GUIDE.md)

Этот документ регламентирует правила составления и калибровки новых вопросов для пополнения основного теста `tests_data/test_general_2026.json`.

> **Политика проекта (TASK-012):** поле `explanation` всегда `""` — ученик видит только результат, подсказок и пояснений нет.

---

## 1. Структура объекта вопроса

Каждый вопрос обязан строго соответствовать схеме Pydantic модели `Question`:

### Вопрос с выбором ответа (`question_type: "choice"`)

```json
{
  "id": "g26_46",
  "level": "B2",
  "difficulty": 4.2,
  "category": "Grammar",
  "topic": "Inversion",
  "text": "Rarely ___ such dedication.",
  "question_type": "choice",
  "options": ["I saw", "have I seen", "I had seen", "did I saw"],
  "correct_option": 1,
  "explanation": ""
}
```

### Текстовый вопрос (`question_type: "text"`)

```json
{
  "id": "g26_47",
  "level": "A2",
  "difficulty": 2.0,
  "category": "Grammar",
  "topic": "Past Continuous",
  "text": "Helena ___ when I came home. (to read)",
  "question_type": "text",
  "options": [],
  "correct_option": null,
  "correct_text": "was reading",
  "explanation": ""
}
```

⚠️ `correct_text` сравнивается **с учётом регистра** (case-sensitive): `Was reading` ≠ `was reading`. Допускается только `.strip()` внешних пробелов.

---

## 2. Калибровка дробной сложности (`difficulty`)

| Уровень CEFR | Диапазон сложности | Примеры тем |
|---|---|---|
| **A1** | `1.0 — 1.5` | To Be, Present Simple (базовый), личные местоимения, базовая еда/напитки |
| **A2** | `1.6 — 2.5` | Past Simple (неправильные глаголы), Comparatives, модальные can/must |
| **B1** | `2.6 — 3.5` | Present Perfect vs Past Simple, First Conditional, Passive Voice |
| **B2** | `3.6 — 4.5` | Second/Third Conditionals, Gerund vs Infinitive, Phrasal verbs, Collocations |
| **C1** | `4.6 — 5.5` | Negative Inversion, Subjunctive mood, Mixed Conditionals, Advanced lexis |
| **C2** | `5.6 — 6.0` | Cleft sentences, архаичные/литературные идиомы, редкие исключения |

---

## 3. Золотые правила составления вопросов:

1. **Единственный однозначный ответ**: Не должно быть вариантов, где верны два ответа в зависимости от контекста.
2. **Качественные дистракторы (неправильные варианты)**:
   - Неправильные варианты должны быть типичными ошибками изучающих язык (ложные друзья переводчика, путаница времен).
   - Избегайте абсурдных вариантов, которые легко исключить методом догадки.
3. **Обозначение пропуска**:
   - В тексте вопроса место пропуска всегда обозначается ровно тремя символами подчеркивания: `___`.
   - Фронтенд автоматически подставит красивый стилизованный бирюзовый пробел.
4. **Баланс категорий**:
   - При добавлении пачки вопросов старайтесь сохранять равную пропорцию: $33\%$ Grammar, $33\%$ Vocabulary, $33\%$ Usage.
