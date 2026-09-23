/**
 * English Level CAT Platform — Client Application
 */

document.addEventListener('DOMContentLoaded', () => {
  // State
  let sessionId = null;
  let currentQuestion = null;
  let questionStartTime = null;
  let timerInterval = null;
  let secondsElapsed = 0;
  let isAnswering = false;
  let toastTimer = null;

  // Telegram WebApp detection
  const tg = window.Telegram?.WebApp;
  let tgUser = null;

  if (tg) {
    try {
      tg.ready();
      tg.expand();
      if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        tgUser = tg.initDataUnsafe.user;
        console.log('Telegram WebApp user detected:', tgUser);
      }
    } catch (e) {
      console.warn('Telegram WebApp initialization error:', e);
    }
  }

  // DOM Elements - Screens
  const screenWelcome = document.getElementById('screen-welcome');
  const screenQuestion = document.getElementById('screen-question');
  const screenResult = document.getElementById('screen-result');

  // DOM Elements - Question Screen
  const qCounter = document.getElementById('q-counter');
  const progressFill = document.getElementById('progress-fill');
  const timerText = document.getElementById('timer-text');
  const qText = document.getElementById('q-text');
  const optionsContainer = document.getElementById('options-container');
  const questionCard = document.getElementById('question-card');
  const progressDots = document.getElementById('progress-dots');

  // Telegram Form Elements
  const tgSubmitForm = document.getElementById('tg-submit-form');
  const inputUserName = document.getElementById('input-user-name');
  const inputUserPhone = document.getElementById('input-user-phone');
  const inputUserTg = document.getElementById('input-user-tg');
  const btnSendTg = document.getElementById('btn-send-tg');
  const tgSuccessMessage = document.getElementById('tg-success-message');

  // Test Catalog & Suite Selection Elements
  const testCardsGrid = document.getElementById('test-cards-grid');
  const btnStartTest = document.getElementById('btn-start-test');
  const btnStartText = document.getElementById('btn-start-text');
  const btnRestartTest = document.getElementById('btn-restart-test');

  let selectedTestId = 'test_general_2026';
  let currentTestMode = 'fixed';
  let availableTests = [];

  const TG_BTN_DEFAULT_HTML = btnSendTg.innerHTML;

  const svgIcon = (inner, size = 18, fill = false) =>
    `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="${fill ? 'currentColor' : 'none'}" stroke="${fill ? 'none' : 'currentColor'}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${inner}</svg>`;

  const ICONS = {
    clock: svgIcon('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', 13),
    target: svgIcon('<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none"/>', 20),
    briefcase: svgIcon('<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>', 20),
    zap: svgIcon('<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z"/>', 20, true),
    sprout: svgIcon('<path d="M12 21v-8"/><path d="M12 13C12 9 9 6 5 6c0 4 3 7 7 7z"/><path d="M12 13c0-3 2.5-6 6-6 0 3.5-2.5 6-6 6z"/>', 20),
    doc: svgIcon('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/>', 20),
  };

  // Pre-fill Telegram data if available
  if (tgUser) {
    if (inputUserName) {
      inputUserName.value = `${tgUser.first_name || ''} ${tgUser.last_name || ''}`.trim();
    }
    if (inputUserTg && tgUser.username) {
      inputUserTg.value = `@${tgUser.username}`;
    }
  }

  // Initial load of test suites
  renderSkeletons();
  loadTestSuites();

  // Event Listeners
  btnStartTest.addEventListener('click', startTest);
  btnRestartTest.addEventListener('click', resetToWelcome);
  tgSubmitForm.addEventListener('submit', handleTelegramSubmit);

  [inputUserName, inputUserPhone].forEach((input) => {
    input.addEventListener('input', () => {
      const group = input.closest('.form-group');
      if (group) {
        group.classList.remove('has-error');
        const err = group.querySelector('.field-error');
        if (err) err.remove();
      }
    });
  });

  // Phone mask: +7 (999) 000-00-00
  function maskPhone(raw) {
    let d = raw.replace(/\D/g, '');
    if (d.startsWith('8')) d = '7' + d.slice(1);
    else if (d.length > 0 && !d.startsWith('7')) d = '7' + d;
    d = d.slice(0, 11);
    if (!d) return '';
    let out = '+7';
    if (d.length > 1) out += ' (' + d.slice(1, 4);
    if (d.length >= 4) out += ')';
    if (d.length > 4) out += ' ' + d.slice(4, 7);
    if (d.length > 7) out += '-' + d.slice(7, 9);
    if (d.length > 9) out += '-' + d.slice(9, 11);
    return out;
  }

  function countDigits(str, idx) {
    return (str.slice(0, idx).match(/\d/g) || []).length;
  }

  function caretAtDigit(formatted, n) {
    if (n <= 0) return 0;
    let seen = 0;
    for (let i = 0; i < formatted.length; i++) {
      if (formatted[i] >= '0' && formatted[i] <= '9') {
        seen++;
        if (seen === n) return i + 1;
      }
    }
    return formatted.length;
  }

  inputUserPhone.addEventListener('input', () => {
    const el = inputUserPhone;
    const digitsBefore = countDigits(el.value, el.selectionStart);
    const formatted = maskPhone(el.value);
    el.value = formatted;
    const pos = caretAtDigit(formatted, digitsBefore);
    el.setSelectionRange(pos, pos);
  });

  inputUserPhone.addEventListener('keydown', (e) => {
    if (e.key !== 'Backspace') return;
    const el = inputUserPhone;
    if (el.selectionStart !== el.selectionEnd) return;
    const pos = el.selectionStart;
    const v = el.value;
    if (pos > 0 && pos === v.length && /\D/.test(v[pos - 1])) {
      e.preventDefault();
      let i = pos - 1;
      while (i >= 0 && /\D/.test(v[i])) i--;
      if (i >= 0 && /\d/.test(v[i])) {
        const n = countDigits(v, i);
        if (n === 0) {
          el.value = '';
          return;
        }
        const nv = v.slice(0, i) + v.slice(i + 1);
        const formatted = maskPhone(nv);
        el.value = formatted;
        const p = caretAtDigit(formatted, n);
        el.setSelectionRange(p, p);
      } else {
        el.value = '';
      }
    }
  });

  function showToast(message) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('visible');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.classList.remove('visible');
    }, 4000);
  }

  // Keyboard navigation for options (A, B, C, D or 1, 2, 3, 4).
  // Используем e.code (физические клавиши), чтобы работало и на русской раскладке.
  window.addEventListener('keydown', (e) => {
    if (!currentQuestion || isAnswering || !screenQuestion.classList.contains('active')) return;
    const codeMap = {
      'Digit1': 0, 'Digit2': 1, 'Digit3': 2, 'Digit4': 3,
      'KeyA': 0, 'KeyB': 1, 'KeyC': 2, 'KeyD': 3
    };
    const idx = codeMap[e.code];
    if (idx !== undefined && idx < currentQuestion.options.length) {
      selectOption(idx);
    }
  });

  // Test Suite Catalog Loader
  function renderSkeletons() {
    if (!testCardsGrid) return;
    const sk = `
      <div class="test-card skeleton" aria-hidden="true">
        <div class="skeleton-line sk-icon"></div>
        <div class="skeleton-line sk-title"></div>
        <div class="skeleton-line sk-desc"></div>
        <div class="skeleton-line sk-desc2"></div>
        <div class="skeleton-line sk-meta"></div>
      </div>`;
    testCardsGrid.innerHTML = sk.repeat(4);
  }

  async function loadTestSuites() {
    try {
      const res = await fetch('/api/tests');
      if (res.ok) {
        availableTests = await res.json();
        renderTestCards(availableTests);
      } else {
        renderDefaultTestCards();
      }
    } catch (e) {
      console.warn('Fallback to default tests:', e);
      renderDefaultTestCards();
    }
  }

  function renderDefaultTestCards() {
    availableTests = [
      {
        id: 'test_general_2026',
        title: 'General English Test 2026',
        description: 'Основной общий тест 2026: грамматика, лексика и употребление английского. 45 вопросов с выбором и 5 с вводом ответа.',
        category: 'General',
        level: 'A1-C1',
        mode: 'fixed',
        icon: ICONS.target,
        estimated_time_minutes: 15,
        total_questions: 50
      }
    ];
    renderTestCards(availableTests);
  }

  function renderTestCards(tests) {
    if (!testCardsGrid) return;
    testCardsGrid.innerHTML = '';

    if (!tests || tests.length === 0) {
      testCardsGrid.innerHTML = '<div class="catalog-empty">Тесты временно недоступны. Попробуйте обновить страницу.</div>';
      return;
    }

    tests.forEach((test) => {
      const isSelected = (test.id === selectedTestId);
      const card = document.createElement('div');
      card.className = `test-card ${isSelected ? 'active' : ''}`;
      card.dataset.testId = test.id;

      card.innerHTML = `
        <div class="test-card-top">
          <span class="test-card-icon">${test.icon || ICONS.doc}</span>
          <div class="test-card-check">${isSelected ? '✓' : ''}</div>
        </div>
        <div class="test-card-title">${test.title}</div>
        <div class="test-card-desc">${test.description}</div>
        <div class="test-card-footer">
          <span class="test-card-meta-item">${ICONS.clock} ~${test.estimated_time_minutes || 5} мин</span>
          <span class="test-card-meta-item">${test.total_questions || 8} вопросов</span>
        </div>
      `;

      card.addEventListener('click', () => {
        selectTest(test.id);
      });

      testCardsGrid.appendChild(card);
    });

    updateStartButtonForTest(selectedTestId);
  }

  function selectTest(testId) {
    selectedTestId = testId;
    document.querySelectorAll('.test-card').forEach(card => {
      const check = card.querySelector('.test-card-check');
      if (card.dataset.testId === testId) {
        card.classList.add('active');
        if (check) check.textContent = '✓';
      } else {
        card.classList.remove('active');
        if (check) check.textContent = '';
      }
    });
    updateStartButtonForTest(testId);
  }

  function updateStartButtonForTest(testId) {
    const test = availableTests.find(t => t.id === testId);
    if (!test) return;

    currentTestMode = test.mode || 'fixed';

    if (btnStartText) {
      btnStartText.textContent = 'Начать тест';
    }
  }

  // Switch Screen
  function showScreen(screen) {
    [screenWelcome, screenQuestion, screenResult].forEach(s => {
      s.classList.remove('active');
    });
    screen.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Timer helper
  function startQuestionTimer() {
    stopQuestionTimer();
    secondsElapsed = 0;
    questionStartTime = Date.now();
    updateTimerDisplay();
    timerInterval = setInterval(() => {
      secondsElapsed++;
      updateTimerDisplay();
    }, 1000);
  }

  function stopQuestionTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  function updateTimerDisplay() {
    const mins = Math.floor(secondsElapsed / 60);
    const secs = secondsElapsed % 60;
    timerText.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }

  // 1. START TEST
  async function startTest() {
    btnStartTest.disabled = true;
    btnStartTest.classList.add('is-loading');
    const originalBtnContent = btnStartTest.innerHTML;
    btnStartTest.innerHTML = '<span class="btn-spinner"></span><span>Запуск теста...</span>';

    try {
      const response = await fetch('/api/test/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ test_id: selectedTestId })
      });

      if (!response.ok) throw new Error('Не удалось запустить тест');
      const data = await response.json();
      sessionId = data.session_id;
      currentTestMode = data.test_mode || currentTestMode;

      renderQuestion(data.first_question);
      showScreen(screenQuestion);
    } catch (err) {
      console.error(err);
      showToast('Ошибка при запуске теста. Проверьте подключение к серверу.');
    } finally {
      btnStartTest.disabled = false;
      btnStartTest.classList.remove('is-loading');
      btnStartTest.innerHTML = originalBtnContent;
    }
  }

  // 2. RENDER QUESTION
  function renderProgressDots(current, total) {
    if (!progressDots) return;
    const n = Math.max(total || 12, current);
    let html = '';
    for (let i = 1; i <= n; i++) {
      const cls = i < current ? 'done' : (i === current ? 'current' : '');
      html += `<span class="progress-dot ${cls}"></span>`;
    }
    progressDots.innerHTML = html;
  }

  function renderQuestion(q) {
    currentQuestion = q;
    isAnswering = false;

    if (questionCard) {
      questionCard.classList.remove('q-enter');
      void questionCard.offsetWidth;
      questionCard.classList.add('q-enter');
    }

    qCounter.textContent = `Вопрос ${q.question_number} из ~${q.total_estimated}`;

    renderProgressDots(q.question_number, q.total_estimated);

    // Progress bar
    const progressPct = Math.min(95, Math.round((q.question_number / q.total_estimated) * 100));
    progressFill.style.width = `${progressPct}%`;

    // Format text with highlighted gap
    let text = q.text;
    text = text.replace(/___/g, '<span style="color: var(--accent-cyan); font-weight: 700; border-bottom: 2px dashed var(--accent-cyan); padding: 0 4px;">_____</span>');
    qText.innerHTML = text;

    // Render Options
    optionsContainer.innerHTML = '';

    if (q.question_type === 'text') {
      const wrap = document.createElement('div');
      wrap.className = 'text-answer-block';
      wrap.innerHTML = `
        <input type="text" class="text-answer-input" id="text-answer-input"
               autocomplete="off" autocapitalize="off" spellcheck="false"
               placeholder="Введите ответ..." aria-label="Введите ответ">
        <button type="button" class="btn-primary text-answer-btn" id="text-answer-btn">Ответить</button>
      `;
      optionsContainer.appendChild(wrap);
      const textInput = document.getElementById('text-answer-input');
      const textBtn = document.getElementById('text-answer-btn');
      textBtn.addEventListener('click', () => submitTextAnswer());
      textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          submitTextAnswer();
        }
      });
      setTimeout(() => textInput.focus(), 50);
    } else {
      const keys = ['A', 'B', 'C', 'D'];

      q.options.forEach((optText, index) => {
        const card = document.createElement('div');
        card.className = 'option-card';
        card.id = `option-${index}`;
        card.innerHTML = `
          <div class="option-key">${keys[index]}</div>
          <div class="option-text">${optText}</div>
        `;
        card.addEventListener('click', () => selectOption(index));
        optionsContainer.appendChild(card);
      });
    }

    startQuestionTimer();
  }

  // 3. SELECT OPTION & SUBMIT ANSWER
  async function submitTextAnswer() {
    if (isAnswering || !currentQuestion) return;

    const input = document.getElementById('text-answer-input');
    const btn = document.getElementById('text-answer-btn');
    const value = input ? input.value.trim() : '';
    if (!value) {
      showToast('Введите ответ');
      return;
    }

    isAnswering = true;
    stopQuestionTimer();
    const timeSpent = Math.max(1, (Date.now() - questionStartTime) / 1000);

    if (input) input.disabled = true;
    if (btn) btn.disabled = true;

    try {
      const response = await fetch('/api/test/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question_id: currentQuestion.id,
          selected_text: value,
          time_spent_seconds: timeSpent
        })
      });

      if (!response.ok) throw new Error('Ошибка отправки ответа');
      const data = await response.json();

      setTimeout(() => {
        if (data.is_finished && data.result) {
          renderResult(data.result);
          showScreen(screenResult);
        } else if (data.next_question) {
          renderQuestion(data.next_question);
        }
      }, 350);

    } catch (err) {
      console.error(err);
      showToast('Ошибка связи с сервером при отправке ответа.');
      isAnswering = false;
      if (input) input.disabled = false;
      if (btn) btn.disabled = false;
    }
  }

  async function selectOption(index) {
    if (isAnswering || !currentQuestion) return;
    isAnswering = true;
    stopQuestionTimer();

    const timeSpent = Math.max(1, (Date.now() - questionStartTime) / 1000);

    // Visual selection
    const selectedCard = document.getElementById(`option-${index}`);
    if (selectedCard) {
      selectedCard.classList.add('selected');
    }

    // Disable all options
    document.querySelectorAll('.option-card').forEach(c => {
      c.style.pointerEvents = 'none';
    });

    try {
      const response = await fetch('/api/test/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question_id: currentQuestion.id,
          selected_option: index,
          time_spent_seconds: timeSpent
        })
      });

      if (!response.ok) throw new Error('Ошибка отправки ответа');
      const data = await response.json();

      // Small pause for smooth UX transition
      setTimeout(() => {
        if (data.is_finished && data.result) {
          renderResult(data.result);
          showScreen(screenResult);
        } else if (data.next_question) {
          renderQuestion(data.next_question);
        }
      }, 350);

    } catch (err) {
      console.error(err);
      showToast('Ошибка связи с сервером при отправке ответа.');
      isAnswering = false;
      document.querySelectorAll('.option-card').forEach(c => {
        c.style.pointerEvents = '';
      });
      const sel = document.getElementById(`option-${index}`);
      if (sel) sel.classList.remove('selected');
    }
  }

  // 4. RENDER RESULT
  function renderResult(res) {
    progressFill.style.width = '100%';

    // Результат на сайте не показывается — данные уходят администратору в Telegram.

    // Reset Telegram form state
    tgSubmitForm.style.display = 'flex';
    tgSuccessMessage.classList.add('hidden');
    btnSendTg.disabled = false;
    btnSendTg.classList.remove('is-loading');
    btnSendTg.innerHTML = TG_BTN_DEFAULT_HTML;
  }

  // 5. FORM VALIDATION
  function setFieldError(input, message) {
    const group = input.closest('.form-group');
    if (!group) return;
    group.classList.add('has-error');
    let err = group.querySelector('.field-error');
    if (!err) {
      err = document.createElement('span');
      err.className = 'field-error';
      err.setAttribute('role', 'alert');
      group.appendChild(err);
    }
    err.textContent = message;
  }

  function clearFieldErrors() {
    document.querySelectorAll('.form-group.has-error').forEach((group) => {
      group.classList.remove('has-error');
      const err = group.querySelector('.field-error');
      if (err) err.remove();
    });
  }

  // 6. SUBMIT TO TELEGRAM
  async function handleTelegramSubmit(e) {
    e.preventDefault();
    if (!sessionId) return;

    const name = inputUserName.value.trim();
    const phone = inputUserPhone.value.trim();
    const tgUsername = inputUserTg.value.trim().replace(/^@/, '');

    clearFieldErrors();
    let firstInvalid = null;
    if (!name) {
      setFieldError(inputUserName, 'Укажите имя');
      firstInvalid = firstInvalid || inputUserName;
    }
    const phoneDigits = phone.replace(/\D/g, '');
    if (phoneDigits.length !== 11 || !phoneDigits.startsWith('7')) {
      setFieldError(inputUserPhone, 'Введите корректный телефон');
      firstInvalid = firstInvalid || inputUserPhone;
    }
    if (firstInvalid) {
      firstInvalid.focus();
      return;
    }

    btnSendTg.disabled = true;
    btnSendTg.classList.add('is-loading');
    btnSendTg.innerHTML = '<span class="btn-spinner"></span><span>Отправка в Telegram...</span>';

    try {
      const response = await fetch('/api/test/submit-contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          name: name,
          phone: phone || null,
          telegram_username: tgUsername || null,
          tg_user_id: tgUser ? tgUser.id : null,
          tg_init_data: tg ? tg.initData : null
        })
      });

      if (!response.ok) throw new Error('Ошибка отправки контактов');
      const data = await response.json();

      tgSubmitForm.style.display = 'none';
      tgSuccessMessage.classList.remove('hidden');

      // If in Telegram WebApp, notify user or haptic feedback
      if (tg?.HapticFeedback) {
        tg.HapticFeedback.notificationOccurred('success');
      }
    } catch (err) {
      console.error(err);
      showToast('Произошла ошибка при отправке в Telegram. Попробуйте еще раз.');
      btnSendTg.disabled = false;
      btnSendTg.classList.remove('is-loading');
      btnSendTg.innerHTML = TG_BTN_DEFAULT_HTML;
    }
  }

  // 6. RESET TO WELCOME
  function resetToWelcome() {
    stopQuestionTimer();
    sessionId = null;
    currentQuestion = null;
    isAnswering = false;
    showScreen(screenWelcome);
  }
});
