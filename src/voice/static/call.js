/**
 * DawnDispatch Mobile Call Engine
 * Simulates incoming phone call, handles Web Audio / Ray-Ban routing,
 * manages rapid quick-fire standup dialogue, and syncs transcript to backend.
 */

(function () {
  // State
  let audioCtx = null;
  let ringtoneInterval = null;
  let callTimerInterval = null;
  let callSeconds = 0;
  let ws = null;
  let isMuted = false;
  let speechSynth = window.speechSynthesis || null;
  let recognition = null;

  let agendaItems = [];
  let currentAgendaIdx = -1;
  let conversationTurns = [];
  let capturedDecisions = [];

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
  const endedDurationLabel = document.getElementById('ended-duration-label');
  const summaryList = document.getElementById('summary-decision-list');
  const waveform = document.getElementById('waveform');

  const quickfireButtons = document.querySelectorAll('.qf-btn');

  // Update top clock
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
      audioCtx = new AudioContextClass();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    return audioCtx;
  }

  // Synthesize Phone Ringtone Chime using Web Audio
  function playRingToneBurst() {
    try {
      const ctx = getAudioContext();
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();

      osc1.type = 'sine';
      osc2.type = 'sine';
      osc1.frequency.value = 440; // A4
      osc2.frequency.value = 480; // Standard US ringtone pair

      gain.gain.setValueAtTime(0, ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.15, ctx.currentTime + 0.05);
      gain.gain.setValueAtTime(0.15, ctx.currentTime + 1.2);
      gain.gain.linearRampToValueAtTime(0, ctx.currentTime + 1.3);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ctx.destination);

      osc1.start(ctx.currentTime);
      osc2.start(ctx.currentTime);
      osc1.stop(ctx.currentTime + 1.3);
      osc2.stop(ctx.currentTime + 1.3);
    } catch (e) {
      // Audio autoplay policy fallback
    }
  }

  function startRingtone() {
    playRingToneBurst();
    ringtoneInterval = setInterval(playRingToneBurst, 3200);
  }

  function stopRingtone() {
    if (ringtoneInterval) {
      clearInterval(ringtoneInterval);
      ringtoneInterval = null;
    }
  }

  // Spoken voice synthesis helper (Gradium/Ray-Ban simulation)
  function speakAgentText(text, callback) {
    if (!speechSynth) {
      if (callback) setTimeout(callback, 800);
      return;
    }
    speechSynth.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.22; // High executive cadence for rapid triage
    utterance.pitch = 1.0;
    utterance.lang = 'en-US';

    // Try finding good English voice
    const voices = speechSynth.getVoices();
    const enVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha')));
    if (enVoice) utterance.voice = enVoice;

    utterance.onend = () => {
      if (callback) callback();
    };
    utterance.onerror = () => {
      if (callback) callback();
    };

    speechSynth.speak(utterance);
  }

  // Load agenda items from backend
  async function loadAgendaData() {
    try {
      const res = await fetch('/api/agenda');
      if (res.ok) {
        agendaItems = await res.json();
      }
    } catch (e) {
      console.warn('Could not load agenda, using defaults', e);
    }

    if (!agendaItems || agendaItems.length === 0) {
      agendaItems = [
        {
          item_id: 'agenda-01',
          topic: 'Voice WebSocket Deployment',
          question_for_lead: 'Deploy gradbot voice streaming backend to port 8090 for smartphone Ray-Ban connection?',
          recommended_action: 'APPROVE',
          is_irreversible: false
        },
        {
          item_id: 'agenda-02',
          topic: 'Database & State Reset',
          question_for_lead: 'Purge overnight ephemeral logs and apply schema migration before live commute demo?',
          recommended_action: 'APPROVE',
          is_irreversible: true
        },
        {
          item_id: 'agenda-03',
          topic: 'Visual Brand Release',
          question_for_lead: 'Publish DawnDispatch hero banner and logo to public repo README?',
          recommended_action: 'APPROVE',
          is_irreversible: false
        }
      ];
    }
  }

  // Setup Web Speech Recognition
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

  // Format Call Timer
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

  // Dialog progression
  function startOpeningGreeting() {
    dialogPhaseBadge.textContent = 'OPENING GREETING';
    const greeting = 'Good morning Philipp. Swarm overnight triage ready. How much time do you have?';
    agentSpeech.textContent = `"${greeting}"`;
    userSpeech.textContent = 'Say your available time (e.g., "Got 60 seconds") or tap below...';

    conversationTurns.push({ speaker: 'agent', text: greeting, timestamp: '00:02' });
    speakAgentText(greeting);
  }

  function advanceToNextQuestion() {
    currentAgendaIdx++;
    if (currentAgendaIdx < agendaItems.length) {
      const q = agendaItems[currentAgendaIdx];
      const qNum = currentAgendaIdx + 1;
      const irrevTag = q.is_irreversible ? ' [IRREVERSIBLE CHECKPOINT]' : '';
      dialogPhaseBadge.textContent = `QUICK FIRE — ${qNum} OF ${agendaItems.length}${irrevTag}`;

      const promptText = `Rapid fire. ${qNum}: ${q.question_for_lead} Yes or no?`;
      agentSpeech.textContent = `"${promptText}"`;
      userSpeech.textContent = 'Listening for: Yes / No / Hold...';

      conversationTurns.push({ speaker: 'agent', text: promptText, timestamp: formatTime(callSeconds) });
      speakAgentText(promptText);
    } else {
      // Conclude dialogue
      finishDialogAndEndCall();
    }
  }

  function handleUserSpokenInput(text) {
    if (!text) return;
    userSpeech.textContent = `You: "${text}"`;
    conversationTurns.push({ speaker: 'user', text: text, timestamp: formatTime(callSeconds) });

    if (currentAgendaIdx === -1) {
      // Duration answered -> start quick fire
      setTimeout(advanceToNextQuestion, 400);
    } else if (currentAgendaIdx < agendaItems.length) {
      // Decision answered
      const item = agendaItems[currentAgendaIdx];
      let decType = 'APPROVE';
      const clean = text.toLowerCase();
      if (clean.includes('no') || clean.includes('reject')) decType = 'REJECT';
      else if (clean.includes('hold') || clean.includes('checkpoint') || clean.includes('wait')) decType = 'HOLD';

      capturedDecisions.push({
        item_id: item.item_id,
        decision_type: decType,
        voice_notes: `Lead decided '${text}' via Ray-Ban glasses during commute triage.`
      });

      // Quick acknowledge & advance
      setTimeout(advanceToNextQuestion, 300);
    }
  }

  function finishDialogAndEndCall() {
    dialogPhaseBadge.textContent = 'WRAP-UP';
    const wrapup = 'Captured. Knowledge graph updated. See you at your desk.';
    agentSpeech.textContent = `"${wrapup}"`;
    userSpeech.textContent = 'Triage call complete. Hanging up...';
    conversationTurns.push({ speaker: 'agent', text: wrapup, timestamp: formatTime(callSeconds) });

    speakAgentText(wrapup, () => {
      setTimeout(endCallSession, 1200);
    });
  }

  // Answer Call Action
  async function answerCall() {
    stopRingtone();
    getAudioContext();

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
    callTimerInterval = setInterval(() => {
      callSeconds++;
      callTimer.textContent = formatTime(callSeconds);
    }, 1000);

    // Start speech recognition if supported
    if (recognition) {
      try { recognition.start(); } catch (e) {}
    }

    // Connect WebSocket
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
      try { ws.close(); } catch (e) {}
    }

    const durationStr = formatTime(callSeconds);
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
    startRingtone();
  });

  // Init
  loadAgendaData();
  initSpeechRecognition();
  startRingtone();

})();
