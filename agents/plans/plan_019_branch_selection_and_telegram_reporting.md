# 📋 План PLAN-019: Выбор филиала при отправке контактов и вывод в Telegram

**Статус:** 🟢 COMPLETED (Успешно выполнен)  
**Дата:** 2026-09-25  
**Исполнитель:** Gemini 3.8 Flash (Antigravity)  

---

## 🎯 1. Цель
Добавить в финальную форму отправки контактов выбор филиала с помощью 2 удобных кнопок:
1. **Главный офис** (по умолчанию активна)
2. **Университет** (филиал «Универ»)

После отправки формы выбранный филиал должен:
- Сохраняться в сессии и базе лидов (`LeadRecord`).
- Отображаться в Telegram в единой карточке заявки для администратора:
  `🏢 Филиал: Главный офис` или `🏢 Филиал: Университет`.
- Отображаться в сообщении для студента (если бот активен).
- Экспортироваться в `/api/export/leads` для CRM.

---

## 🔍 2. Затрагиваемые файлы и архитектурные изменения

1. **`backend/models.py`:**
   - В `UserContactSubmission` добавить поле `branch: Optional[str] = "Главный офис"`.

2. **`backend/lead_store.py`:**
   - Добавить `"branch"` в `__slots__` класса `LeadRecord`.
   - В конструктор `LeadRecord.__init__` добавить параметр `branch: Optional[str] = "Главный офис"`.
   - В `LeadRecord.to_dict()` включить `"branch": self.branch`.
   - В `_load_from_disk()` безопасно считывать `branch=item.get("branch", "Главный офис")`.

3. **`backend/main.py`:**
   - В эндпоинте `/api/test/submit-contact`:
     - Сохранять `branch = (payload.branch or "Главный офис").strip()` в сессию.
     - Передавать `branch` в конструктор `LeadRecord`.
     - Передавать `branch` в `send_student_full_result`.

4. **`backend/telegram_bot.py`:**
   - В функцию `format_unified_lead_card`: добавить параметр `branch: Optional[str] = "Главный офис"` и строку:
     `🏢 <b>Филиал:</b> {branch}`.
   - В функцию `format_result_card`: добавить параметр `branch: Optional[str] = "Главный офис"` и аналогичную строку.
   - В функцию `format_compact_lead_card`: добавить отображение филиала.
   - В `send_admin_lead_notification(lead)`: извлекать `branch` из `lead` и передавать в `format_unified_lead_card`.
   - В `send_student_full_result`: передавать `branch` в `format_result_card`.

5. **`static/index.html`:**
   - Внутри формы `#tg-submit-form` (над полем имени или между именем и телефоном) разместить блок выбора филиала:
     - Две стильные кнопки-переключатели:
       - `🏛️ Главный офис` (active)
       - `🎓 Университет`
     - Скрытый input `<input type="hidden" id="input-branch" value="Главный офис">`.

6. **`static/css/style.css`:**
   - Стили для контейнера `.branch-selector` и кнопок `.branch-btn`:
     - Сетка из 2 равных колонок (`grid-template-columns: 1fr 1fr`).
     - Элегантная рамка, тактильные микро-анимации нажатия, янтарная подсветка активного филиала.
     - Полная поддержка светлой и темной темы.

7. **`static/js/app.js`:**
   - Обработка кликов по кнопкам филиалов с переключением класса `is-active`, обновлением значения `#input-branch` и легким виброоткликом `triggerHaptic('light')`.
   - В функции `submitUserContact(e)`: передавать `branch` в теле запроса `/api/test/submit-contact`.

8. **`agents/testing/test_api_http.py`:**
   - Добавить тест отправки контакта с выбором филиала (`branch="Университет"`), проверку сохранения в `lead_store` и наличия филиала в тексте карточки Telegram.

---

## 🧪 3. План верификации

1. **Автоматические тесты:**
   - `python agents/testing/test_api_http.py` — проверка REST API с новым полем `branch`.
   - `python agents/tools/check_integrity.py` — проверка целостности структуры.
   - `python -m backend.test_simulation` — проверка движка тестирования.
   - `python agents/testing/test_multi_suites.py` — общие тесты.
2. **Ручная проверка в браузере:**
   - Открытие формы контактов на экране результатов.
   - Переключение между кнопками «Главный офис» и «Университет».
   - Отправка и проверка формирования лида с выбранным филиалом.
