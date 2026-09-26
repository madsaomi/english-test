/**
 * Stanford Language Center — English Test
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
      // Detect Telegram dark theme
      if (tg.colorScheme === 'dark') document.body.classList.add('theme-dark');
      tg.onEvent('themeChanged', () => {
        document.body.classList.toggle('theme-dark', tg.colorScheme === 'dark');
      });
      if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        tgUser = tg.initDataUnsafe.user;
        console.log('Telegram WebApp user detected:', tgUser);
      }
    } catch (e) {
      console.warn('Telegram WebApp initialization error:', e);
    }
  }

  // System dark mode for non-Telegram browsers
  if (!tg && window.matchMedia?.('(prefers-color-scheme: dark)').matches) {
    document.body.classList.add('theme-dark');
  }

  // DOM Elements - Screens
  const screenWelcome = document.getElementById('screen-welcome');
  const screenQuestion = document.getElementById('screen-question');
  const screenResult = document.getElementById('screen-result');

  // DOM Elements - Question Screen
  const qCounter = document.getElementById('q-counter');
  const progressFill = document.getElementById('progress-fill');
  const timerBadge = document.getElementById('timer-badge');
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
  const inputUserBranch = document.getElementById('input-user-branch');
  const branchButtons = document.querySelectorAll('.branch-btn');
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
  let isTestActive = false;

  const TG_BTN_DEFAULT_HTML = btnSendTg.innerHTML;

  function triggerHaptic(type = 'light') {
    try {
      if (tg?.HapticFeedback) {
        if (type === 'light' || type === 'medium' || type === 'heavy') {
          tg.HapticFeedback.impactOccurred(type);
        } else if (type === 'success' || type === 'error' || type === 'warning') {
          tg.HapticFeedback.notificationOccurred(type);
        }
      }
    } catch (_) {}
  }

  // Prevent accidental back-swipe or tab close during an active test session
  window.addEventListener('beforeunload', (e) => {
    if (isTestActive) {
      e.preventDefault();
      e.returnValue = '';
    }
  });

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

  if (branchButtons && branchButtons.length > 0) {
    branchButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        branchButtons.forEach(b => {
          b.classList.remove('is-active');
          b.setAttribute('aria-checked', 'false');
        });
        btn.classList.add('is-active');
        btn.setAttribute('aria-checked', 'true');
        const branchVal = btn.dataset.branch || 'Главный офис';
        if (inputUserBranch) {
          inputUserBranch.value = branchVal;
        }
        triggerHaptic('light');
      });
    });
  }

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

  // Uzbekistan Phone mask (+998 (XX) XXX-XX-XX) — fixed non-erasable prefix, strictly 9 digits
  const UZ_PREFIX = '+998 ';

  function maskUzPhone(raw) {
    let digits = String(raw || '').replace(/\D/g, '');
    if (digits.startsWith('998')) {
      digits = digits.slice(3);
    }
    // Limit to exactly 9 digits of the subscriber number
    digits = digits.slice(0, 9);

    if (digits.length === 0) {
      return UZ_PREFIX;
    }
    let out = '+998 (';
    out += digits.slice(0, 2);
    if (digits.length >= 2) out += ') ';
    if (digits.length > 2) out += digits.slice(2, 5);
    if (digits.length >= 5) out += '-';
    if (digits.length > 5) out += digits.slice(5, 7);
    if (digits.length >= 7) out += '-';
    if (digits.length > 7) out += digits.slice(7, 9);
    return out;
  }

  function countDigits(str, idx) {
    return (str.slice(0, idx).match(/\d/g) || []).length;
  }

  function caretAtDigit(formatted, n) {
    if (n <= 0) return UZ_PREFIX.length;
    let seen = 0;
    for (let i = 0; i < formatted.length; i++) {
      if (formatted[i] >= '0' && formatted[i] <= '9') {
        seen++;
        if (seen === n) return i + 1;
      }
    }
    return formatted.length;
  }

  inputUserPhone.addEventListener('focus', () => {
    if (!inputUserPhone.value || inputUserPhone.value.trim() === '' || inputUserPhone.value.trim() === '+998') {
      inputUserPhone.value = UZ_PREFIX;
      setTimeout(() => {
        inputUserPhone.setSelectionRange(UZ_PREFIX.length, UZ_PREFIX.length);
      }, 0);
    }
  });

  inputUserPhone.addEventListener('click', () => {
    if (inputUserPhone.selectionStart < UZ_PREFIX.length) {
      inputUserPhone.setSelectionRange(UZ_PREFIX.length, UZ_PREFIX.length);
    }
  });

  inputUserPhone.addEventListener('input', () => {
    const el = inputUserPhone;
    const digitsBefore = countDigits(el.value, el.selectionStart);
    const formatted = maskUzPhone(el.value);
    el.value = formatted;
    const pos = Math.max(UZ_PREFIX.length, caretAtDigit(formatted, digitsBefore));
    el.setSelectionRange(pos, pos);
  });

  inputUserPhone.addEventListener('keydown', (e) => {
    const el = inputUserPhone;
    if (e.key === 'Backspace') {
      if (el.selectionStart <= UZ_PREFIX.length && el.selectionEnd <= UZ_PREFIX.length) {
        e.preventDefault();
        el.setSelectionRange(UZ_PREFIX.length, UZ_PREFIX.length);
        return;
      }
      if (el.selectionStart !== el.selectionEnd) return;
      const pos = el.selectionStart;
      const v = el.value;
      if (pos > UZ_PREFIX.length && /\D/.test(v[pos - 1])) {
        e.preventDefault();
        let i = pos - 1;
        while (i >= UZ_PREFIX.length && /\D/.test(v[i])) i--;
        if (i >= UZ_PREFIX.length && /\d/.test(v[i])) {
          const n = countDigits(v, i);
          const nv = v.slice(0, i) + v.slice(i + 1);
          const formatted = maskUzPhone(nv);
          el.value = formatted;
          const p = Math.max(UZ_PREFIX.length, caretAtDigit(formatted, n));
          el.setSelectionRange(p, p);
        }
      }
    } else if (e.key === 'ArrowLeft' || e.key === 'Home') {
      if (el.selectionStart <= UZ_PREFIX.length) {
        setTimeout(() => el.setSelectionRange(UZ_PREFIX.length, UZ_PREFIX.length), 0);
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

  // POST /api/test/answer with clear error classification + one retry on blip.
  // Returns parsed JSON body; throws { status, detail, sessionLost }.
  async function postAnswer(payload, { retries = 1 } = {}) {
    let lastErr = null;
    for (let attempt = 0; attempt <= retries; attempt++) {
      let response;
      try {
        response = await fetch('/api/test/answer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      } catch (networkErr) {
        lastErr = { status: 0, detail: 'network', sessionLost: false, cause: networkErr };
        if (attempt < retries) {
          await new Promise((r) => setTimeout(r, 600));
          continue;
        }
        break;
      }

      if (response.ok) {
        return response.json();
      }

      let detail = '';
      try {
        const body = await response.json();
        detail = body.detail || '';
      } catch (_) { /* non-JSON error body */ }

      const status = response.status;
      const sessionLost = status === 404 && String(detail).includes('Сессия');
      lastErr = { status, detail, sessionLost };

      // Retry only transient gateway/network failures — never 4xx.
      const retryable = status === 0 || status === 502 || status === 503;
      if (retryable && attempt < retries) {
        await new Promise((r) => setTimeout(r, 600));
        continue;
      }
      break;
    }
    throw lastErr || { status: 0, detail: 'unknown', sessionLost: false };
  }

  function describeAnswerError(err) {
    if (!err) return 'Ошибка связи с сервером при отправке ответа.';
    if (err.sessionLost || (err.status === 404 && String(err.detail || '').includes('Сессия'))) {
      return 'Сессия истекла (сервер перезапустился). Начните тест заново.';
    }
    if (err.status === 404) return err.detail || 'Вопрос не найден. Обновите страницу.';
    if (err.status === 400) return err.detail || 'Некорректный ответ. Попробуйте ещё раз.';
    if (err.status >= 500) return 'Сервер временно недоступен. Повторите попытку.';
    if (err.status === 0) return 'Нет связи с сервером. Проверьте интернет и повторите.';
    return err.detail || 'Ошибка связи с сервером при отправке ответа.';
  }

  function handleAnswerError(err) {
    console.error('answer error', err);
    showToast(describeAnswerError(err));
    isAnswering = false;
    if (err && err.sessionLost) {
      resetToWelcome();
    }
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
    testCardsGrid.classList.toggle('is-single', Array.isArray(tests) && tests.length === 1);

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

    // Move focus for keyboard / screen readers (one task per screen).
    requestAnimationFrame(() => {
      if (screen === screenQuestion && questionCard) {
        questionCard.focus({ preventScroll: true });
      } else if (screen === screenWelcome && btnStartTest) {
        btnStartTest.focus({ preventScroll: true });
      } else if (screen === screenResult && inputUserName) {
        inputUserName.focus({ preventScroll: true });
      }
    });
  }

  // Timer helper
  let questionTimeLimit = 30; // 30s for choice, 35s for text

  function startQuestionTimer() {
    stopQuestionTimer();
    questionTimeLimit = currentQuestion?.question_type === 'text' ? 35 : 30;
    questionStartTime = Date.now();
    updateTimerDisplay(questionTimeLimit);

    if (timerBadge) {
      timerBadge.classList.remove('timer-warning');
    }

    timerInterval = setInterval(() => {
      const elapsedSeconds = Math.floor((Date.now() - questionStartTime) / 1000);
      const remaining = Math.max(0, questionTimeLimit - elapsedSeconds);
      updateTimerDisplay(remaining);

      if (remaining <= 5 && timerBadge) {
        timerBadge.classList.add('timer-warning');
      }

      if (remaining <= 0) {
        stopQuestionTimer();
        handleQuestionTimeout();
      }
    }, 250);
  }

  function stopQuestionTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
    if (timerBadge) {
      timerBadge.classList.remove('timer-warning');
    }
  }

  function updateTimerDisplay(remaining) {
    const mins = Math.floor(remaining / 60);
    const secs = remaining % 60;
    timerText.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }

  async function handleQuestionTimeout() {
    if (isAnswering || !currentQuestion) return;
    isAnswering = true;
    triggerHaptic('error');

    showToast('Время вышло! Переход к следующему вопросу');

    const isText = currentQuestion.question_type === 'text';
    const textInput = document.getElementById('text-answer-input');
    const typedValue = textInput ? textInput.value.trim() : '';

    if (textInput) textInput.disabled = true;
    const textBtn = document.getElementById('text-answer-btn');
    if (textBtn) textBtn.disabled = true;

    document.querySelectorAll('.option-card').forEach(c => {
      c.style.pointerEvents = 'none';
    });

    try {
      const payload = {
        session_id: sessionId,
        question_id: currentQuestion.id,
        time_spent_seconds: questionTimeLimit,
        is_timeout: true
      };

      if (isText) {
        payload.selected_text = typedValue;
      } else {
        payload.selected_option = -1;
      }

      const data = await postAnswer(payload);

      setTimeout(() => {
        if (data.is_finished && data.result) {
          renderResult(data.result);
          showScreen(screenResult);
        } else if (data.next_question) {
          renderQuestion(data.next_question);
        }
      }, 400);
    } catch (err) {
      handleAnswerError(err);
    }
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
      isTestActive = true;

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

    // Progress bar (+ a11y aria-valuenow)
    const progressPct = Math.min(95, Math.round((q.question_number / q.total_estimated) * 100));
    progressFill.style.width = `${progressPct}%`;
    const progressShell = progressFill.parentElement;
    if (progressShell && progressShell.hasAttribute('role')) {
      progressShell.setAttribute('aria-valuenow', String(progressPct));
      progressShell.setAttribute('aria-label', `Прогресс: вопрос ${q.question_number} из ~${q.total_estimated}`);
    }

    // Format text with highlighted gap (supports 2 or more underscores)
    let text = q.text;
    text = text.replace(/_{2,}/g, '<span class="gap-blank">_____</span>');
    qText.innerHTML = text;

    // Render Options
    optionsContainer.innerHTML = '';

    if (questionCard) {
      questionCard.classList.remove('question-enter');
      void questionCard.offsetWidth; // trigger reflow for smooth animation
      questionCard.classList.add('question-enter');
    }

    if (q.question_type === 'text') {
      const wrap = document.createElement('div');
      wrap.className = 'text-answer-block';
      wrap.innerHTML = `
        <input type="text" class="text-answer-input" id="text-answer-input"
               autocomplete="off" autocapitalize="none" autocorrect="off" spellcheck="false"
               enterkeyhint="done" placeholder="Введите ответ..." aria-label="Введите ответ">
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
      textInput.addEventListener('paste', (e) => {
        e.preventDefault();
        showToast('Вставка текста запрещена. Введите ответ вручную.');
      });
      setTimeout(() => textInput.focus(), 50);
    } else {
      const keys = ['A', 'B', 'C', 'D'];

      q.options.forEach((optText, index) => {
        const card = document.createElement('div');
        card.className = 'option-card';
        card.id = `option-${index}`;
        card.setAttribute('role', 'button');
        card.setAttribute('tabindex', '0');
        card.setAttribute('aria-label', `${keys[index]}. ${optText}`);
        card.innerHTML = `
          <div class="option-key">${keys[index]}</div>
          <div class="option-text">${optText}</div>
        `;
        card.addEventListener('click', () => selectOption(index));
        card.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            selectOption(index);
          }
        });
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
    triggerHaptic('medium');
    stopQuestionTimer();
    const timeSpent = Math.max(1, (Date.now() - questionStartTime) / 1000);

    if (input) input.disabled = true;
    if (btn) btn.disabled = true;

    try {
      const data = await postAnswer({
        session_id: sessionId,
        question_id: currentQuestion.id,
        selected_text: value,
        time_spent_seconds: timeSpent
      });

      setTimeout(() => {
        if (data.is_finished && data.result) {
          renderResult(data.result);
          showScreen(screenResult);
        } else if (data.next_question) {
          renderQuestion(data.next_question);
        }
      }, 350);

    } catch (err) {
      handleAnswerError(err);
      if (input && !err?.sessionLost) input.disabled = false;
      if (btn && !err?.sessionLost) btn.disabled = false;
    }
  }

  async function selectOption(index) {
    if (isAnswering || !currentQuestion) return;
    isAnswering = true;
    triggerHaptic('light');
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
      const data = await postAnswer({
        session_id: sessionId,
        question_id: currentQuestion.id,
        selected_option: index,
        time_spent_seconds: timeSpent
      });

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
      handleAnswerError(err);
      if (err && !err.sessionLost) {
        document.querySelectorAll('.option-card').forEach(c => {
          c.style.pointerEvents = '';
        });
        const sel = document.getElementById(`option-${index}`);
        if (sel) sel.classList.remove('selected');
      }
    }
  }

  // 4. RENDER RESULT
  function renderResult(res) {
    isTestActive = false;
    progressFill.style.width = '100%';
    const progressShell = progressFill.parentElement;
    if (progressShell && progressShell.hasAttribute('role')) {
      progressShell.setAttribute('aria-valuenow', '100');
    }

    // Результат на сайте не показывается — данные уходят администратору в Telegram.

    // Reset Telegram form state
    tgSubmitForm.style.display = 'flex';
    tgSuccessMessage.classList.add('hidden');
    btnSendTg.disabled = false;
    btnSendTg.classList.remove('is-loading');
    btnSendTg.innerHTML = TG_BTN_DEFAULT_HTML;

    // Reset phone to Uzbekistan prefix
    if (inputUserPhone) inputUserPhone.value = UZ_PREFIX;

    // Reset branch selection to default
    if (inputUserBranch) inputUserBranch.value = 'Главный офис';
    if (branchButtons && branchButtons.length > 0) {
      branchButtons.forEach(btn => {
        const isDefault = (btn.dataset.branch === 'Главный офис');
        btn.classList.toggle('is-active', isDefault);
        btn.setAttribute('aria-checked', isDefault ? 'true' : 'false');
      });
    }
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
    const branch = inputUserBranch ? (inputUserBranch.value || 'Главный офис') : 'Главный офис';

    clearFieldErrors();
    let firstInvalid = null;
    if (!name) {
      setFieldError(inputUserName, 'Укажите имя');
      firstInvalid = firstInvalid || inputUserName;
    }
    const uzDigits = phone.replace(/\D/g, '').replace(/^998/, '');
    if (uzDigits.length !== 9) {
      setFieldError(inputUserPhone, 'Введите номер полностью: +998 (XX) XXX-XX-XX (9 цифр)');
      firstInvalid = firstInvalid || inputUserPhone;
    }
    if (firstInvalid) {
      triggerHaptic('error');
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
          tg_init_data: tg ? tg.initData : null,
          branch: branch
        })
      });

      if (!response.ok) throw new Error('Ошибка отправки контактов');
      const data = await response.json();

      tgSubmitForm.style.display = 'none';
      tgSuccessMessage.classList.remove('hidden');
      triggerHaptic('success');
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
    isTestActive = false;
    stopQuestionTimer();
    sessionId = null;
    currentQuestion = null;
    isAnswering = false;
    showScreen(screenWelcome);
  }

  // ----------------- 7. ANTI-COPY & ANTI-SCREENSHOT PROTECTION -----------------
  // Enable Telegram WebApp closing confirmation
  if (tg && typeof tg.enableClosingConfirmation === 'function') {
    try {
      tg.enableClosingConfirmation();
    } catch (e) {
      console.warn('enableClosingConfirmation not supported:', e);
    }
  }

  // A. Block context menu (right click & mobile long press)
  document.addEventListener('contextmenu', (e) => {
    if (isTestActive) {
      e.preventDefault();
      showToast('Контекстное меню отключено на время теста');
    }
  });

  // B. Block copy, cut, and dragstart on test screen
  document.addEventListener('copy', (e) => {
    if (isTestActive) {
      e.preventDefault();
      showToast('Копирование вопросов запрещено');
    }
  });

  document.addEventListener('cut', (e) => {
    if (isTestActive) {
      e.preventDefault();
    }
  });

  document.addEventListener('dragstart', (e) => {
    if (isTestActive) {
      e.preventDefault();
    }
  });

  // C. Block devtools, print, save, and copy hotkeys
  document.addEventListener('keydown', (e) => {
    // PrintScreen detection & clipboard wiping
    if (e.key === 'PrintScreen' || e.keyCode === 44) {
      if (isTestActive) {
        try {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText('');
          }
        } catch (err) {}
        showToast('Создание снимков экрана запрещено');
      }
      return;
    }

    if (!isTestActive) return;

    const isCtrl = e.ctrlKey || e.metaKey;
    const key = e.key ? e.key.toLowerCase() : '';

    // Ctrl+C, Ctrl+X, Ctrl+U (view source), Ctrl+S (save), Ctrl+P (print)
    if (isCtrl && (key === 'c' || key === 'x' || key === 'u' || key === 's' || key === 'p')) {
      // Allow copy in form input only on result screen
      if (activeScreen === screenResult) return;
      e.preventDefault();
      showToast('Горячие клавиши копирования/сохранения отключены');
      return;
    }

    // F12 or Ctrl+Shift+I / Ctrl+Shift+J / Ctrl+Shift+C (DevTools)
    if (e.key === 'F12' || (isCtrl && e.shiftKey && (key === 'i' || key === 'j' || key === 'c'))) {
      e.preventDefault();
      showToast('Инструменты разработчика отключены');
    }
  });

  // D. Blur shield on tab switch / window blur during active test
  let focusOverlay = null;

  function showFocusWarning() {
    if (!isTestActive || focusOverlay) return;
    if (screenQuestion) screenQuestion.classList.add('test-blur-shield');

    focusOverlay = document.createElement('div');
    focusOverlay.className = 'focus-warning-overlay';
    focusOverlay.innerHTML = `
      <div class="focus-warning-box">
        <div class="focus-warning-icon">🛡️</div>
        <div class="focus-warning-title">Тестирование приостановлено</div>
        <div class="focus-warning-desc">
          Переключение окон и создание скриншотов во время прохождения теста запрещено. Вернитесь к тесту для продолжения.
        </div>
        <button type="button" class="focus-warning-btn" id="btn-return-focus">Вернуться к тесту</button>
      </div>
    `;
    document.body.appendChild(focusOverlay);

    const btnReturn = document.getElementById('btn-return-focus');
    if (btnReturn) {
      btnReturn.addEventListener('click', hideFocusWarning);
    }
  }

  function hideFocusWarning() {
    if (focusOverlay) {
      focusOverlay.remove();
      focusOverlay = null;
    }
    if (screenQuestion) screenQuestion.classList.remove('test-blur-shield');
  }

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      if (isTestActive) showFocusWarning();
    }
  });

  window.addEventListener('blur', () => {
    // Only show if active element is not an input inside our form
    if (isTestActive && document.activeElement !== document.getElementById('text-answer-input')) {
      showFocusWarning();
    }
  });

  window.addEventListener('focus', () => {
    // Keep overlay until user explicitly clicks "Return" button or dismisses
  });
});
