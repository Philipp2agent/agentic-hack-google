/**
 * DawnDispatch Mobile Call Engine
 * Simulates incoming phone call, handles Web Audio / Ray-Ban routing,
 * manages rapid quick-fire standup dialogue with dynamic cards,
 * and syncs decisions/transcript to the backend.
 */

(function () {
  'use strict';

  // State
  let audioCtx = null;
  let ringtoneInterval = null;
  let callTimerInterval = null;
  let callSeconds = 0;
  let ws = null;
  let isMuted = false;
  let isRayBanRoute = true;
  let speechSynth = window.speechSynthesis || null;
  let recognition = null;

  let agendaItems = [];
  let currentAgendaIdx = -1;
  let conversationTurns = [];
  let capturedDecisions = [];
  let audioUnlocked = false;

  // DOM Elements
  const screenIncoming = document.getElementById('screen-incoming');
  const screenActive = document.getElementById('screen-active');
  const screenEnded = document.getElementById('screen-ended');

  const btnAccept = document.getElementById('btn-accept');
  const btnDecline = document.getElementById('btn-decline');
  const btnEndCall = document.getElementById('btn-end-call');
  const btnMute = document.getElementById('btn-mute');
  const btnSpeaker = document.getElementById('btn-speaker');
  const btnRestart = document.getElementById('btn-restart-call');

  const callTimer = document.getElementById('call-timer');
  const statusClock = document.getElementById('status-clock');
  const agentSpeech = document.getElementById('agent-speech');
  const userSpeech = document.getElementById('user-speech');
  const dialogPhaseBadge = document.getElementById('dialog-phase-badge');
  const checkpointBadge = document.getElementById('checkpoint-badge');
  const qfTopic = document.getElementById('qf-topic');
  const qfRecommendation = document.getElementById('qf-recommendation');
  const qfStepper = document.getElementById('qf-stepper');
  const cardStamp = document.getElementById('card-stamp');
  const quickfireCard = document.getElementById('quickfire-card');
  const quickBudgetChips = document.getElementById('quick-budget-chips');
  const endedDurationLabel = document.getElementById('ended-duration-label');
  const summaryList = document.getElementById('summary-decision-list');
  const waveform = document.getElementById('waveform');
  const audioHint = document.getElementById('audio-hint');

  const quickfireButtons = document.querySelectorAll('.qf-btn');
  const budgetChipButtons = document.querySelectorAll('.budget-chip');

  // Clock in status bar
  function updateClock() {
    const now = new Date();
    const hrs = String(now.getHours()).padStart(2, '0');
    const mins = String(now.getMinutes()).padStart(2, '0');
    if (statusClock) statusClock.textContent = `${hrs}:${mins}`;
  }
  updateClock();
  setInterval(updateClock, 30000);

  // Initialize Web Audio Context
  function getAudioContext() {
    if (!audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        audioCtx = new AudioContextClass();
      }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume().catch(() => {});
    }
    return audioCtx;
  }

  // Audio Unlock on user tap
  function unlockAudio() {
    if (audioUnlocked) return;
    const ctx = getAudioContext();
    if (ctx) {
      audioUnlocked = true;
      if (audioHint) audioHint.style.display = 'none';
      if (ringtoneInterval) {
        playRingToneBurst();
      }
    }
  }
  window.addEventListener('click', unlockAudio, { once: true });
  window.addEventListener('touchstart', unlockAudio, { once: true });

  // Synthesize Phone Ringtone Chime using Web Audio (Dual-Tone 440Hz + 480Hz)
  function playRingToneBurst() {
    try {
      const ctx = getAudioContext();
      if (!ctx || ctx.state !== 'running') return;

      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();

      osc1.type = 'sine';
      osc2.type = 'sine';
      osc1.frequency.value = 440; // A4
      osc2.frequency.value = 480; // Standard phone chime

      const now = ctx.currentTime;
      gain.gain.setValueAtTime(0.001, now);
      gain.gain.exponentialRampToValueAtTime(0.18, now + 0.08);
      gain.gain.setValueAtTime(0.18, now + 1.25);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 1.35);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ctx.destination);

      osc1.start(now);
      osc2.start(now);
      osc1.stop(now + 1.36);
      osc2.stop(now + 1.36);

      // Trigger haptic vibration if supported
      if (navigator.vibrate) {
        navigator.vibrate([250, 100, 250]);
      }
    } catch (e) {
      // Audio autoplay policy fallback
    }
  }

  function startRingtone() {
    playRingToneBurst();
    ringtoneInterval = setInterval(playRingToneBurst, 3000);
  }

  function stopRingtone() {
    if (ringtoneInterval) {
      clearInterval(ringtoneInterval);
      ringtoneInterval = null;
    }
  }

  // Waveform state management
  function setWaveformState(state) {
    if (!waveform) return;
    waveform.classList.remove('agent-speaking', 'user-speaking', 'listening');
    if (state) {
      waveform.classList.add(state);
    } else {
      waveform.classList.add('listening');
    }
  }

  // Spoken voice synthesis helper (Gradium / Ray-Ban simulation)
  function speakAgentText(text, callback) {
    setWaveformState('agent-speaking');

    if (!speechSynth) {
      setTimeout(() => {
        setWaveformState('listening');
        if (callback) callback();
      }, 1200);
      return;
    }

    try {
      speechSynth.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.22; // High executive cadence for rapid triage
      utterance.pitch = 1.0;
      utterance.lang = 'en-US';

      const voices = speechSynth.getVoices();
      const enVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha')));
      if (enVoice) utterance.voice = enVoice;

      utterance.onend = () => {
        setWaveformState('listening');
        if (callback) callback();
      };
      utterance.onerror = () => {
        setWaveformState('listening');
        if (callback) callback();
      };

      speechSynth.speak(utterance);
    } catch (e) {
      setWaveformState('listening');
      if (callback) callback();
    }
  }

  // Load agenda items from backend
  async function loadAgendaData() {
    try {
      const res = await fetch('/api/agenda');
      if (res.ok) {
        const items = await res.json();
        if (Array.isArray(items) && items.length > 0) {
          agendaItems = items;
        }
      }
    } catch (e) {
      console.warn('Could not load agenda, using defaults', e);
    }

    if (!agendaItems || agendaItems.length === 0) {
      agendaItems = [
        {
          item_id: 'agenda-01',
          topic: 'Swarm Agent Delegation for Subsystems',
          question_for_lead: 'Should we spin up hack-bau2 and hack-bau3, or assign voice and dashboard to existing agents?',
          recommended_action: 'APPROVE - assign voice to hack-bau1 and dashboard to hack-chef',
          is_irreversible: false
        },
        {
          item_id: 'agenda-02',
          topic: 'Parallel Task Execution Pipeline Kickoff',
          question_for_lead: 'Unblock parallel worker execution following the overnight parallelstart trigger?',
          recommended_action: 'APPROVE - activate parallel agent task queues immediately',
          is_irreversible: true
        },
        {
          item_id: 'agenda-03',
          topic: 'Ray-Ban Demo and Schema Baseline',
          question_for_lead: 'Accept updated data models, Ray-Ban commute script, and web voice specs as current milestone?',
          recommended_action: 'APPROVE - lock Schritt 0 interface specs and advance to live testing',
          is_irreversible: false
        }
      ];
    }

    renderStepperDots();
  }

  // Render Stepper dots for agenda items
  function renderStepperDots() {
    if (!qfStepper) return;
    qfStepper.innerHTML = '';
    agendaItems.forEach((_, idx) => {
      const dot = document.createElement('span');
      dot.className = 'step-dot';
      dot.dataset.step = idx;
      if (idx === currentAgendaIdx) dot.classList.add('active');
      else if (idx < currentAgendaIdx) dot.classList.add('completed');
      qfStepper.appendChild(dot);
    });
  }

  function updateStepper() {
    const dots = qfStepper ? qfStepper.querySelectorAll('.step-dot') : [];
    dots.forEach((dot, idx) => {
      dot.classList.remove('active', 'completed');
      if (idx === currentAgendaIdx) {
        dot.classList.add('active');
      } else if (idx < currentAgendaIdx) {
        dot.classList.add('completed');
      }
    });
  }

  // Setup Web Speech Recognition for hands-free Ray-Ban operation
  function initSpeechRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) return;

    try {
      recognition = new SpeechRec();
      recognition.continuous = true;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onresult = (evt) => {
        const last = evt.results.length - 1;
        const spoken = evt.results[last][0].transcript.trim();
        handleUserSpokenInput(spoken);
      };

      recognition.onerror = () => {};
    } catch (e) {}
  }

  // Format Call Timer (MM:SS)
  function formatTime(sec) {
    const m = String(Math.floor(sec / 60)).padStart(2, '0');
    const s = String(sec % 60).padStart(2, '0');
    return `${m}:${s}`;
  }

  // Switch Screens
  function showScreen(screen) {
    [screenIncoming, screenActive, screenEnded].forEach(s => s.classList.remove('active'));
    screen.classList.add('active');
  }

  // Visual card animation
  function triggerCardTransition() {
    if (!quickfireCard) return;
    quickfireCard.classList.remove('card-slide-in');
    void quickfireCard.offsetWidth; // trigger reflow
    quickfireCard.classList.add('card-slide-in');
  }

  // Visual Decision Stamp
  function showDecisionStamp(decisionType, callback) {
    if (!cardStamp) {
      if (callback) callback();
      return;
    }
    cardStamp.className = 'card-stamp';
    cardStamp.textContent = decisionType;

    if (decisionType === 'HOLD') {
      cardStamp.classList.add('stamp-hold');
      cardStamp.textContent = 'HELD';
    } else if (decisionType === 'REJECT') {
      cardStamp.classList.add('stamp-reject');
      cardStamp.textContent = 'REJECTED';
    } else {
      cardStamp.textContent = 'APPROVED';
    }

    cardStamp.classList.remove('hidden');

    setTimeout(() => {
      cardStamp.classList.add('hidden');
      if (callback) callback();
    }, 450);
  }

  // Dialog progression
  function startOpeningGreeting() {
    currentAgendaIdx = -1;
    dialogPhaseBadge.textContent = 'OPENING GREETING';
    if (checkpointBadge) checkpointBadge.classList.add('hidden');
    if (qfTopic) qfTopic.textContent = 'Overnight Swarm Standup';
    if (quickBudgetChips) quickBudgetChips.classList.remove('hidden');
    if (qfRecommendation) qfRecommendation.textContent = 'Quick triage: state available commute time to begin';

    const greeting = 'Good morning Philipp. Swarm overnight triage ready. How much time do you have?';
    agentSpeech.textContent = `"${greeting}"`;
    userSpeech.textContent = 'Say your available time (e.g., "Got 60 seconds") or tap below...';

    conversationTurns.push({ speaker: 'agent', text: greeting, timestamp: '00:02' });
    speakAgentText(greeting);
    triggerCardTransition();
  }

  function advanceToNextQuestion() {
    currentAgendaIdx++;
    updateStepper();

    if (currentAgendaIdx < agendaItems.length) {
      const q = agendaItems[currentAgendaIdx];
      const qNum = currentAgendaIdx + 1;

      if (quickBudgetChips) quickBudgetChips.classList.add('hidden');

      dialogPhaseBadge.textContent = `QUICK FIRE — ${qNum} OF ${agendaItems.length}`;
      if (qfTopic) qfTopic.textContent = q.topic || `Agenda Item ${qNum}`;

      if (checkpointBadge) {
        if (q.is_irreversible) {
          checkpointBadge.classList.remove('hidden');
          checkpointBadge.textContent = '⚠️ IRREVERSIBLE CHECKPOINT';
        } else {
          checkpointBadge.classList.add('hidden');
        }
      }

      if (qfRecommendation) {
        qfRecommendation.textContent = q.recommended_action || 'APPROVE recommendation';
      }

      const promptText = `Rapid fire. ${qNum}: ${q.question_for_lead} Yes or no?`;
      agentSpeech.textContent = `"${promptText}"`;
      userSpeech.textContent = 'Listening for: Yes / Hold / No (or tap above)...';

      conversationTurns.push({ speaker: 'agent', text: promptText, timestamp: formatTime(callSeconds) });
      triggerCardTransition();
      speakAgentText(promptText);
    } else {
      finishDialogAndEndCall();
    }
  }

  function handleUserSpokenInput(text) {
    if (!text) return;
    setWaveformState('user-speaking');
    userSpeech.textContent = `You: "${text}"`;
    conversationTurns.push({ speaker: 'user', text: text, timestamp: formatTime(callSeconds) });

    // Send through WebSocket if open
    if (ws && ws.readyState === WebSocket.OPEN) {
      try {
        ws.send(JSON.stringify({
          type: 'user_response',
          text: text,
          timestamp: formatTime(callSeconds)
        }));
      } catch (e) {}
    }

    if (currentAgendaIdx === -1) {
      // Duration specified -> advance to first question
      setTimeout(() => {
        setWaveformState('listening');
        advanceToNextQuestion();
      }, 500);
    } else if (currentAgendaIdx < agendaItems.length) {
      const item = agendaItems[currentAgendaIdx];
      let decType = 'APPROVE';
      const clean = text.toLowerCase();
      if (clean.includes('no') || clean.includes('reject') || clean.includes('deny')) decType = 'REJECT';
      else if (clean.includes('hold') || clean.includes('checkpoint') || clean.includes('wait')) decType = 'HOLD';

      capturedDecisions.push({
        item_id: item.item_id,
        decision_type: decType,
        voice_notes: `Lead decided '${text}' via Ray-Ban glasses during commute triage.`
      });

      // Show Stamp animation, then advance
      showDecisionStamp(decType, () => {
        setWaveformState('listening');
        advanceToNextQuestion();
      });
    }
  }

  function finishDialogAndEndCall() {
    dialogPhaseBadge.textContent = 'WRAP-UP';
    if (checkpointBadge) checkpointBadge.classList.add('hidden');
    if (qfTopic) qfTopic.textContent = 'Knowledge Graph Updated';
    if (qfRecommendation) qfRecommendation.textContent = 'Standup sync ready for laptop dashboard';

    const wrapup = 'Captured. Knowledge graph updated. See you at your desk.';
    agentSpeech.textContent = `"${wrapup}"`;
    userSpeech.textContent = 'Triage call complete. Hanging up...';
    conversationTurns.push({ speaker: 'agent', text: wrapup, timestamp: formatTime(callSeconds) });
    triggerCardTransition();

    speakAgentText(wrapup, () => {
      setTimeout(endCallSession, 1200);
    });
  }

  // Answer Call Action
  async function answerCall() {
    stopRingtone();
    unlockAudio();

    // Request microphone for Ray-Ban Web-Audio activation
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        await navigator.mediaDevices.getUserMedia({ audio: true });
      }
    } catch (e) {
      console.log('Mic request proceeded with fallback');
    }

    showScreen(screenActive);

    // Start timer
    callSeconds = 0;
    callTimer.textContent = '00:00';
    if (callTimerInterval) clearInterval(callTimerInterval);
    callTimerInterval = setInterval(() => {
      callSeconds++;
      callTimer.textContent = formatTime(callSeconds);
    }, 1000);

    // Start speech recognition if supported
    if (recognition) {
      try { recognition.start(); } catch (e) {}
    }

    // Connect WebSocket to backend /ws/call
    try {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/call`);
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'call_ended') {
            endCallSession();
          }
        } catch (e) {}
      };
    } catch (e) {}

    // Start Dialog
    startOpeningGreeting();
  }

  // End Call Action
  async function endCallSession() {
    stopRingtone();
    if (speechSynth) speechSynth.cancel();
    if (callTimerInterval) clearInterval(callTimerInterval);
    if (recognition) {
      try { recognition.stop(); } catch (e) {}
    }
    if (ws && ws.readyState === WebSocket.OPEN) {
      try {
        ws.send(JSON.stringify({ type: 'hangup' }));
        ws.close();
      } catch (e) {}
    }

    const durationStr = formatTime(callSeconds || 58);
    endedDurationLabel.textContent = `Duration: ${durationStr}`;

    // Fill missing decisions if call ended early
    if (capturedDecisions.length < agendaItems.length) {
      for (let i = capturedDecisions.length; i < agendaItems.length; i++) {
        capturedDecisions.push({
          item_id: agendaItems[i].item_id,
          decision_type: 'APPROVE',
          voice_notes: 'Auto-approved during commute quick-fire standup.'
        });
      }
    }

    // Send transcript payload to backend
    const payload = {
      call_id: `call-${Date.now()}`,
      duration_seconds: callSeconds || 58,
      caller: 'DawnDispatch Voice Agent',
      callee: 'Philipp (Meta Ray-Ban Audio)',
      turns: conversationTurns,
      decisions_captured: capturedDecisions
    };

    try {
      await fetch('/api/end_call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch (e) {
      console.warn('Could not post transcript to backend', e);
    }

    // Populate summary card
    summaryList.innerHTML = '';
    capturedDecisions.forEach(d => {
      const li = document.createElement('li');
      const itemObj = agendaItems.find(a => a.item_id === d.item_id) || { topic: d.item_id };
      const decClass = d.decision_type.toLowerCase();
      li.innerHTML = `
        <span class="item-name">${itemObj.topic}</span>
        <span class="item-dec dec-${decClass}">${d.decision_type}</span>
      `;
      summaryList.appendChild(li);
    });

    showScreen(screenEnded);
  }

  // Event Listeners
  btnAccept.addEventListener('click', answerCall);
  btnDecline.addEventListener('click', () => {
    stopRingtone();
    showScreen(screenEnded);
    endedDurationLabel.textContent = 'Call Declined';
  });
  btnEndCall.addEventListener('click', endCallSession);

  // Mute button toggle
  btnMute.addEventListener('click', () => {
    isMuted = !isMuted;
    btnMute.classList.toggle('active', isMuted);
    btnMute.querySelector('span').textContent = isMuted ? 'Muted' : 'Mute';
  });

  // Speaker route toggle
  btnSpeaker.addEventListener('click', () => {
    isRayBanRoute = !isRayBanRoute;
    btnSpeaker.classList.toggle('active', isRayBanRoute);
    btnSpeaker.querySelector('span').textContent = isRayBanRoute ? 'Ray-Ban' : 'Speaker';
  });

  // Quick-Time Budget Chips
  budgetChipButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const timeVal = btn.getAttribute('data-time') || '60 seconds';
      handleUserSpokenInput(timeVal);
    });
  });

  // Quick-Fire Tap Buttons
  quickfireButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const answer = btn.getAttribute('data-answer');
      handleUserSpokenInput(answer);
    });
  });

  // Restart Simulation
  btnRestart.addEventListener('click', () => {
    conversationTurns = [];
    capturedDecisions = [];
    currentAgendaIdx = -1;
    showScreen(screenIncoming);
    renderStepperDots();
    startRingtone();
  });

  // Initial load
  loadAgendaData();
  initSpeechRecognition();
  startRingtone();

})();
