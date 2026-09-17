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
  const resultCefrCode = document.getElementById('result-cefr-code');
  const resultCefrBadge = document.getElementById('result-cefr-badge');
  const resultLevelTitle = document.getElementById('result-level-title');
  const resultSummaryText = document.getElementById('result-summary-text');
  const resultScore = document.getElementById('result-score');
  const resultAccuracy = document.getElementById('result-accuracy');
  const resultTime = document.getElementById('result-time');
  const skillsContainer = document.getElementById('skills-container');
  const weakTopicsBox = document.getElementById('weak-topics-box');
  const weakTagsContainer = document.getElementById('weak-tags-container');
  const recommendationsList = document.getElementById('recommendations-list');

  // Telegram Form Elements
  const tgSubmitForm = document.getElementById('tg-submit-form');
  const inputUserName = document.getElementById('input-user-name');
  const inputUserPhone = document.getElementById('input-user-phone');
  const inputUserTg = document.getElementById('input-user-tg');
  const btnSendTg = document.getElementById('btn-send-tg');
  const tgSuccessMessage = document.getElementById('tg-success-message');

  // Action Buttons
  const btnStartTest = document.getElementById('btn-start-test');
  const btnRestartTest = document.getElementById('btn-restart-test');

  // Pre-fill Telegram data if available
  if (tgUser) {
    if (inputUserName) {
      inputUserName.value = `${tgUser.first_name || ''} ${tgUser.last_name || ''}`.trim();
    }
    if (inputUserTg && tgUser.username) {
      inputUserTg.value = `@${tgUser.username}`;
    }
  }

  // Event Listeners
  btnStartTest.addEventListener('click', startTest);
  btnRestartTest.addEventListener('click', resetToWelcome);
  tgSubmitForm.addEventListener('submit', handleTelegramSubmit);

  // Keyboard navigation for options (A, B, C, D or 1, 2, 3, 4)
  window.addEventListener('keydown', (e) => {
    if (!currentQuestion || isAnswering || !screenQuestion.classList.contains('active')) return;
    const key = e.key.toUpperCase();
    const map = { '1': 0, '2': 1, '3': 2, '4': 3, 'A': 0, 'B': 1, 'C': 2, 'D': 3 };
    if (map[key] !== undefined && map[key] < currentQuestion.options.length) {
      selectOption(map[key]);
    }
  });

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
    btnStartTest.innerHTML = '<span>Запуск теста...</span>';

    try {
      const response = await fetch('/api/test/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) throw new Error('Не удалось запустить тест');
      const data = await response.json();
      sessionId = data.session_id;
      renderQuestion(data.first_question);
      showScreen(screenQuestion);
    } catch (err) {
      console.error(err);
      alert('Ошибка при запуске теста. Проверьте подключение к серверу.');
    } finally {
      btnStartTest.disabled = false;
      btnStartTest.innerHTML = '<span>Пройти адаптивный тест</span><span class="arrow-icon">→</span>';
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

    resultCefrCode.textContent = res.cefr_level;
    resultLevelTitle.textContent = `${res.cefr_level} — ${res.level_title}`;
    resultScore.textContent = res.score;
    resultAccuracy.textContent = `${res.accuracy_percentage}%`;

    const mins = Math.floor(res.total_time_seconds / 60);
    const secs = res.total_time_seconds % 60;
    resultTime.textContent = mins > 0 ? `${mins} мин ${secs} сек` : `${secs} сек`;

    // Dynamic color gradient for badge based on CEFR
    const gradients = {
      'A1': 'linear-gradient(135deg, #0ea5e9, #38bdf8)',
      'A2': 'linear-gradient(135deg, #06b6d4, #14b8a6)',
      'B1': 'linear-gradient(135deg, #10b981, #6366f1)',
      'B2': 'linear-gradient(135deg, #6366f1, #8b5cf6)',
      'C1': 'linear-gradient(135deg, #8b5cf6, #ec4899)',
      'C2': 'linear-gradient(135deg, #f59e0b, #ef4444)',
    };
    if (gradients[res.cefr_level]) {
      resultCefrBadge.style.background = gradients[res.cefr_level];
    }

    // Skills breakdown
    skillsContainer.innerHTML = '';
    res.skills.forEach(skill => {
      const card = document.createElement('div');
      card.className = 'skill-card';
      card.innerHTML = `
        <div class="skill-card-top">
          <span class="skill-name">${skill.category}</span>
          <span class="skill-level-badge">${skill.level}</span>
        </div>
        <div class="skill-meter">
          <div class="skill-meter-fill" style="width: ${skill.score_percentage}%"></div>
        </div>
        <div class="skill-score-text">${skill.correct_answered} из ${skill.total_answered} верно (${skill.score_percentage}%)</div>
      `;
      skillsContainer.appendChild(card);
    });

    // Weak topics
    if (res.weak_topics && res.weak_topics.length > 0) {
      weakTopicsBox.style.display = 'block';
      weakTagsContainer.innerHTML = '';
      res.weak_topics.forEach(topic => {
        const tag = document.createElement('span');
        tag.className = 'weak-tag';
        tag.textContent = topic;
        weakTagsContainer.appendChild(tag);
      });
    } else {
      weakTopicsBox.style.display = 'none';
    }

    // Recommendations
    recommendationsList.innerHTML = '';
    res.recommendations.forEach(rec => {
      const li = document.createElement('li');
      li.textContent = rec;
      recommendationsList.appendChild(li);
    });

    // Reset Telegram form state
    tgSubmitForm.style.display = 'flex';
    tgSuccessMessage.classList.add('hidden');
    btnSendTg.disabled = false;
  }

  // 5. SUBMIT TO TELEGRAM
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
          tg_user_id: tgUser ? tgUser.id : null
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
