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
  const qLevelBadge = document.getElementById('q-level-badge');
  const currentEvalLabel = document.getElementById('current-eval-label');
  const progressFill = document.getElementById('progress-fill');
  const timerText = document.getElementById('timer-text');
  const qCategory = document.getElementById('q-category');
  const qTopic = document.getElementById('q-topic');
  const qText = document.getElementById('q-text');
  const optionsContainer = document.getElementById('options-container');

  // DOM Elements - Result Screen
  const resultTestName = document.getElementById('result-test-name');

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
  const testMetaHint = document.getElementById('test-meta-hint');
  const btnRestartTest = document.getElementById('btn-restart-test');
  const qTestTitle = document.getElementById('q-test-title');

  let selectedTestId = 'cefr_adaptive';
  let currentTestTitle = 'CEFR General Adaptive Test';
  let currentTestMode = 'adaptive';
  let availableTests = [];

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
  loadTestSuites();

  // Event Listeners
  btnStartTest.addEventListener('click', startTest);
  btnRestartTest.addEventListener('click', resetToWelcome);
  tgSubmitForm.addEventListener('submit', handleTelegramSubmit);

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
        id: 'cefr_adaptive',
        title: 'CEFR General Adaptive Test',
        description: 'Полное адаптивное тестирование от A1 до C2 с динамической подстройкой сложности под ваши ответы.',
        category: 'General',
        level: 'A1-C2',
        mode: 'adaptive',
        icon: '🎯',
        estimated_time_minutes: 7,
        total_questions: 12
      },
      {
        id: 'test_business_english',
        title: 'Business & Formal English',
        description: 'Деловая переписка, переговоры, корпоративная лексика и профессиональный этикет.',
        category: 'Business',
        level: 'B2-C1',
        mode: 'fixed',
        icon: '💼',
        estimated_time_minutes: 6,
        total_questions: 8
      },
      {
        id: 'test_grammar_master',
        title: 'Grammar Master Intensive',
        description: 'Времена глаголов, пассивный залог, модальные глаголы и условные предложения.',
        category: 'Grammar',
        level: 'A2-B2',
        mode: 'fixed',
        icon: '⚡',
        estimated_time_minutes: 6,
        total_questions: 8
      },
      {
        id: 'test_starter_a1_a2',
        title: 'Starter & Elementary English',
        description: 'Экспресс-тест для начинающих: базовые фразы, глагол to be, Present Simple и базовая лексика.',
        category: 'Starter',
        level: 'A1-A2',
        mode: 'fixed',
        icon: '🌱',
        estimated_time_minutes: 5,
        total_questions: 8
      }
    ];
    renderTestCards(availableTests);
  }

  function renderTestCards(tests) {
    if (!testCardsGrid) return;
    testCardsGrid.innerHTML = '';

    tests.forEach((test) => {
      const isSelected = (test.id === selectedTestId);
      const card = document.createElement('div');
      card.className = `test-card ${isSelected ? 'active' : ''}`;
      card.dataset.testId = test.id;

      const modeLabel = test.mode === 'adaptive' ? 'Адаптивный' : 'Тематический';
      const modeClass = test.mode === 'adaptive' ? 'adaptive' : 'fixed';

      card.innerHTML = `
        <div class="test-card-top">
          <div class="test-card-icon-wrap">
            <span class="test-card-icon">${test.icon || '📝'}</span>
            <div class="test-card-badges">
              <span class="test-card-level">${test.level}</span>
              <span class="test-card-mode ${modeClass}">${modeLabel}</span>
            </div>
          </div>
          <div class="test-card-check">${isSelected ? '✓' : ''}</div>
        </div>
        <div class="test-card-title">${test.title}</div>
        <div class="test-card-desc">${test.description}</div>
        <div class="test-card-footer">
          <span class="test-card-meta-item">⏱ ~${test.estimated_time_minutes || 5} мин</span>
          <span class="test-card-meta-item">❓ ${test.total_questions || 8} вопр.</span>
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

    currentTestTitle = test.title;
    currentTestMode = test.mode || 'adaptive';

    if (btnStartText) {
      btnStartText.textContent = `Пройти: ${test.title}`;
    }
    if (testMetaHint) {
      testMetaHint.textContent = `⏱ Занимает ~${test.estimated_time_minutes || 5} минут • ${test.mode === 'adaptive' ? 'Динамическая сложность CAT' : (test.total_questions || 8) + ' вопросов'} • Бесплатно`;
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
    const originalBtnContent = btnStartTest.innerHTML;
    btnStartTest.innerHTML = '<span>Запуск теста...</span>';

    try {
      const response = await fetch('/api/test/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ test_id: selectedTestId })
      });

      if (!response.ok) throw new Error('Не удалось запустить тест');
      const data = await response.json();
      sessionId = data.session_id;
      currentTestTitle = data.test_title || currentTestTitle;
      currentTestMode = data.test_mode || currentTestMode;

      if (qTestTitle) qTestTitle.textContent = currentTestTitle;
      if (resultTestName) resultTestName.textContent = currentTestTitle;

      renderQuestion(data.first_question);
      showScreen(screenQuestion);
    } catch (err) {
      console.error(err);
      alert('Ошибка при запуске теста. Проверьте подключение к серверу.');
    } finally {
      btnStartTest.disabled = false;
      btnStartTest.innerHTML = originalBtnContent;
    }
  }

  // 2. RENDER QUESTION
  function renderQuestion(q) {
    currentQuestion = q;
    isAnswering = false;

    // Header info
    qCounter.textContent = `Вопрос ${q.question_number} из ~${q.total_estimated}`;
    currentEvalLabel.textContent = q.current_difficulty_label;

    // Progress bar
    const progressPct = Math.min(95, Math.round((q.question_number / q.total_estimated) * 100));
    progressFill.style.width = `${progressPct}%`;

    // Category & Topic
    qCategory.textContent = q.category;
    qTopic.textContent = q.topic;

    // Format text with highlighted gap
    let text = q.text;
    text = text.replace(/___/g, '<span style="color: var(--accent-cyan); font-weight: 700; border-bottom: 2px dashed var(--accent-cyan); padding: 0 4px;">_____</span>');
    qText.innerHTML = text;

    // Render Options
    optionsContainer.innerHTML = '';
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

    startQuestionTimer();
  }

  // 3. SELECT OPTION & SUBMIT ANSWER
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
      alert('Ошибка связи с сервером при отправке ответа.');
      isAnswering = false;
    }
  }

  // 4. RENDER RESULT
  function renderResult(res) {
    progressFill.style.width = '100%';

    if (resultTestName) {
      resultTestName.textContent = currentTestTitle;
    }

    // Результат на сайте не показывается — данные уходят администратору в Telegram.

    // Reset Telegram form state
    tgSubmitForm.style.display = 'flex';
    tgSuccessMessage.classList.add('hidden');
    btnSendTg.disabled = false;
  }

  // 6. SUBMIT TO TELEGRAM
  async function handleTelegramSubmit(e) {
    e.preventDefault();
    if (!sessionId) return;

    const name = inputUserName.value.trim();
    const phone = inputUserPhone.value.trim();
    const tgUsername = inputUserTg.value.trim().replace(/^@/, '');

    btnSendTg.disabled = true;
    btnSendTg.innerHTML = '<span>Отправка в Telegram...</span>';

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
      alert('Произошла ошибка при отправке в Telegram. Попробуйте еще раз.');
      btnSendTg.disabled = false;
      btnSendTg.innerHTML = '<span class="tg-btn-icon">✈️</span><span>Отправить результат в Telegram</span>';
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
