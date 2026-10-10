/**
 * DawnDispatch Desktop Web Dashboard
 * Interactive Knowledge Graph, Audio Transcript & Human Checkpoint Engine
 */

(function () {
  'use strict';
  window.DawnDispatchLoaded = true;

  // State
  let graphBeforeData = null;
  let graphAfterData = null;
  let transcriptData = null;
  let actionsData = [];
  let selectedNode = null;
  let viewMode = 'split'; // 'split', 'before', 'after'
  let zoomLevel = 1.0;
  let panX = 0;
  let panY = 0;

  let audioPlaying = false;
  let audioTimerInterval = null;
  let currentTurnIndex = 0;
  let playbackSeconds = 0;

  // DOM Elements
  const btnViewSplit = document.getElementById('btn-view-split');
  const btnViewBefore = document.getElementById('btn-view-before');
  const btnViewAfter = document.getElementById('btn-view-after');
  const btnZoomIn = document.getElementById('btn-zoom-in');
  const btnZoomOut = document.getElementById('btn-zoom-out');
  const btnZoomReset = document.getElementById('btn-zoom-reset');
  const btnRefresh = document.getElementById('btn-refresh');

  const graphsWorkspace = document.getElementById('graphs-workspace');
  const svgBefore = document.getElementById('svg-before');
  const svgAfter = document.getElementById('svg-after');

  const nodeInspector = document.getElementById('node-inspector');
  const btnCloseInspector = document.getElementById('btn-close-inspector');
  const inspId = document.getElementById('insp-id');
  const inspStatus = document.getElementById('insp-status');
  const inspType = document.getElementById('insp-type');
  const inspTitle = document.getElementById('insp-title');
  const inspDetails = document.getElementById('insp-details');
  const inspJson = document.getElementById('insp-json');
  const inspTypeBadge = document.getElementById('insp-type-badge');

  const transcriptScroll = document.getElementById('transcript-scroll');
  const btnAudioPlay = document.getElementById('btn-audio-play');
  const playIcon = document.getElementById('play-icon');
  const playText = document.getElementById('play-text');
  const soundWave = document.getElementById('sound-wave');
  const audioTimer = document.getElementById('audio-timer');

  const checkpointsList = document.getElementById('checkpoints-list');
  const metricCheckpointsCount = document.getElementById('metric-checkpoints-count');
  const checkpointTagText = document.getElementById('checkpoint-tag-text');
  const toastContainer = document.getElementById('toast-container');

  // Initialization
  async function init() {
    setupEventListeners();
    setupClock();
    checkUrlTargetCheckpoint();
    await loadAllData();
  }

  function setupEventListeners() {
    if (btnViewSplit) btnViewSplit.addEventListener('click', () => setViewMode('split'));
    if (btnViewBefore) btnViewBefore.addEventListener('click', () => setViewMode('before'));
    if (btnViewAfter) btnViewAfter.addEventListener('click', () => setViewMode('after'));

    if (btnZoomIn) btnZoomIn.addEventListener('click', () => adjustZoom(0.15));
    if (btnZoomOut) btnZoomOut.addEventListener('click', () => adjustZoom(-0.15));
    if (btnZoomReset) btnZoomReset.addEventListener('click', () => resetZoom());
    if (btnRefresh) btnRefresh.addEventListener('click', () => loadAllData());

    if (btnCloseInspector) btnCloseInspector.addEventListener('click', () => closeInspector());

    if (btnAudioPlay) btnAudioPlay.addEventListener('click', toggleAudioPlayback);

    window.addEventListener('resize', () => {
      if (graphBeforeData) renderGraph(svgBefore, graphBeforeData, 'BEFORE');
      if (graphAfterData) renderGraph(svgAfter, graphAfterData, 'AFTER');
    });
  }

  function setupClock() {
    const clockEl = document.getElementById('clock-display');
    if (!clockEl) return;
    const updateTime = () => {
      const now = new Date();
      clockEl.textContent = now.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) + ' CEST';
    };
    updateTime();
    setInterval(updateTime, 30000);
  }

  function checkUrlTargetCheckpoint() {
    const path = window.location.pathname;
    const match = path.match(/\/dashboard\/checkpoint\/([^\/]+)/);
    if (match) {
      window.targetCheckpointId = match[1];
    }
  }

  // Load API Data (supporting /api/state as well as dedicated endpoints)
  async function loadAllData() {
    try {
      let stateData = null;
      try {
        const stateRes = await fetch('/api/state');
        if (stateRes.ok) {
          stateData = await stateRes.json();
        }
      } catch (e) {
        // Optional /api/state
      }

      if (stateData) {
        if (stateData.actions && stateData.actions.length > 0) {
          actionsData = stateData.actions;
        }
        if (stateData.call && stateData.call.transcript && stateData.call.transcript.length > 0) {
          transcriptData = { turns: stateData.call.transcript };
        }
      }

      // Fetch Before Graph
      try {
        const beforeRes = await fetch('/api/graph?phase=before').then(r => r.ok ? r : fetch('/api/graph/before'));
        if (beforeRes && beforeRes.ok) graphBeforeData = await beforeRes.json();
      } catch (e) {}

      // Fetch After Graph
      try {
        const afterRes = await fetch('/api/graph?phase=after').then(r => r.ok ? r : fetch('/api/graph/after'));
        if (afterRes && afterRes.ok) graphAfterData = await afterRes.json();
      } catch (e) {}

      // Fallback transcript
      if (!transcriptData) {
        try {
          const transRes = await fetch('/api/transcript');
          if (transRes.ok) transcriptData = await transRes.json();
        } catch (e) {}
      }

      // Fallback actions
      if (!actionsData || actionsData.length === 0) {
        try {
          const actsRes = await fetch('/api/actions');
          if (actsRes.ok) actionsData = await actsRes.json();
        } catch (e) {}
      }

      // If graph is still missing, synthesize from stateData
      if (!graphBeforeData && stateData && stateData.events) {
        graphBeforeData = synthesizeGraphBefore(stateData.events, stateData.agenda || []);
      }
      if (!graphAfterData && graphBeforeData && stateData) {
        graphAfterData = synthesizeGraphAfter(graphBeforeData, stateData.decisions || [], actionsData);
      }

      updateMetrics();
      if (svgBefore && graphBeforeData) renderGraph(svgBefore, graphBeforeData, 'BEFORE');
      if (svgAfter && graphAfterData) renderGraph(svgAfter, graphAfterData, 'AFTER');
      renderTranscript();
      renderCheckpoints();
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      showToast('Fehler beim Laden der Daten', 'error');
    }
  }

  function synthesizeGraphBefore(events, agenda) {
    const nodes = [];
    const edges = [];
    const seenAgents = new Set();

    events.forEach(evt => {
      const agentId = evt.agent_id || 'hack-agent';
      if (!seenAgents.has(agentId)) {
        seenAgents.add(agentId);
        nodes.push({ id: `agent-${agentId}`, label: agentId, type: 'agent', status: 'ACTIVE', details: `Agent ${agentId}` });
      }
      nodes.push({ id: evt.id || `evt-${Math.random()}`, label: evt.title || 'Event', type: 'event', status: 'UNRESOLVED', details: evt.details || '' });
      edges.push({ source: `agent-${agentId}`, target: evt.id, relation: 'PRODUCED', status: 'PENDING' });
    });

    agenda.forEach((ag, idx) => {
      nodes.push({ id: ag.item_id || `agenda-${idx}`, label: ag.topic || 'Agenda Item', type: 'agenda', status: 'PENDING_TRIAGE', details: ag.question_for_lead || '' });
      if (events[idx]) {
        edges.push({ source: events[idx].id, target: ag.item_id, relation: 'TRIGGERS', status: 'PENDING' });
      }
    });

    return { stage: 'BEFORE', nodes, edges };
  }

  function synthesizeGraphAfter(before, decisions, actions) {
    const nodes = JSON.parse(JSON.stringify(before.nodes));
    const edges = JSON.parse(JSON.stringify(before.edges));

    nodes.forEach(n => {
      if (n.type === 'event') n.status = 'RESOLVED';
    });

    decisions.forEach(d => {
      const decId = `dec-${d.item_id}`;
      nodes.push({ id: decId, label: `Decision: ${d.decision_type}`, type: 'decision', status: 'RECORDED', details: d.voice_notes || '' });
      edges.push({ source: d.item_id, target: decId, relation: 'DECIDED_BY', status: 'RESOLVED' });
    });

    actions.forEach(a => {
      nodes.push({ id: a.action_id, label: a.action_type, type: 'action', status: a.status, details: a.artifacts?.reason || '' });
      edges.push({ source: `dec-${a.item_id}`, target: a.action_id, relation: 'DISPATCHES', status: a.status === 'COMPLETED' ? 'RESOLVED' : 'BLOCKED' });
    });

    return { stage: 'AFTER', nodes, edges };
  }

  function setViewMode(mode) {
    viewMode = mode;
    if (btnViewSplit) btnViewSplit.classList.toggle('active', mode === 'split');
    if (btnViewBefore) btnViewBefore.classList.toggle('active', mode === 'before');
    if (btnViewAfter) btnViewAfter.classList.toggle('active', mode === 'after');

    if (graphsWorkspace) graphsWorkspace.className = 'graphs-workspace layout-' + mode;

    setTimeout(() => {
      if (graphBeforeData && svgBefore) renderGraph(svgBefore, graphBeforeData, 'BEFORE');
      if (graphAfterData && svgAfter) renderGraph(svgAfter, graphAfterData, 'AFTER');
    }, 150);
  }

  function adjustZoom(delta) {
    zoomLevel = Math.max(0.4, Math.min(2.5, zoomLevel + delta));
    if (svgBefore) applyTransform(svgBefore);
    if (svgAfter) applyTransform(svgAfter);
  }

  function resetZoom() {
    zoomLevel = 1.0;
    panX = 0;
    panY = 0;
    if (svgBefore) applyTransform(svgBefore);
    if (svgAfter) applyTransform(svgAfter);
  }

  function applyTransform(svg) {
    const g = svg.querySelector('.viewport-group');
    if (g) {
      g.setAttribute('transform', `translate(${panX}, ${panY}) scale(${zoomLevel})`);
    }
  }

  function updateMetrics() {
    if (graphBeforeData && graphBeforeData.nodes) {
      const eventNodes = graphBeforeData.nodes.filter(n => n.type === 'event');
      const unresolved = graphBeforeData.nodes.filter(n => n.status === 'UNRESOLVED' || n.status === 'BLOCKED');
      const elCount = document.getElementById('metric-events-count');
      const elUnres = document.getElementById('before-unresolved-count');
      if (elCount) elCount.textContent = `${eventNodes.length} Events`;
      if (elUnres) elUnres.textContent = `${unresolved.length} Ungeloest`;
    }

    if (actionsData) {
      const blocked = actionsData.filter(a => a.status === 'BLOCKED_ON_CHECKPOINT');
      if (metricCheckpointsCount) {
        metricCheckpointsCount.textContent = `${blocked.length} Ausstehend`;
        if (blocked.length === 0) {
          metricCheckpointsCount.className = 'metric-val text-emerald';
          metricCheckpointsCount.textContent = '0 Ausstehend';
        }
      }
      if (checkpointTagText) {
        checkpointTagText.textContent = blocked.length === 0 ? 'Alle Freigegeben' : `${blocked.length} Blockiert`;
      }
    }
  }

  // ==========================================
  // Knowledge Graph Rendering Engine (SVG)
  // ==========================================
  function renderGraph(svg, data, stage) {
    if (!svg || !data || !data.nodes) return;

    svg.innerHTML = '';
    const width = svg.clientWidth || 600;
    const height = svg.clientHeight || 420;

    // Defs: Arrow heads & glowing filters
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    defs.innerHTML = `
      <marker id="arrow-pending-${stage}" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 10 5 L 0 9 z" fill="#f59e0b" />
      </marker>
      <marker id="arrow-resolved-${stage}" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981" />
      </marker>
      <marker id="arrow-blocked-${stage}" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 10 5 L 0 9 z" fill="#f43f5e" />
      </marker>
      <filter id="glow-${stage}" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="3" result="blur" />
        <feComposite in="SourceGraphic" in2="blur" operator="over" />
      </filter>
    `;
    svg.appendChild(defs);

    const viewport = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    viewport.setAttribute('class', 'viewport-group');
    viewport.setAttribute('transform', `translate(${panX}, ${panY}) scale(${zoomLevel})`);
    svg.appendChild(viewport);

    // Compute Node Layout by category / layer
    const nodes = data.nodes;
    const edges = data.edges || [];

    const layerMap = {
      agent: 0,
      event: 1,
      agenda: 2,
      decision: 3,
      action: 4,
    };

    const layers = [[], [], [], [], []];
    nodes.forEach(n => {
      const idx = layerMap[n.type] !== undefined ? layerMap[n.type] : 1;
      layers[idx].push(n);
    });

    const activeLayers = layers.filter(l => l.length > 0).length;
    const colWidth = Math.max(140, (width - 80) / Math.max(1, activeLayers));
    const nodeCoords = {};

    let currentLayerCol = 0;
    layers.forEach((layerNodes, lIdx) => {
      if (layerNodes.length === 0) return;
      const x = 50 + currentLayerCol * colWidth + colWidth * 0.4;
      const count = layerNodes.length;
      const rowHeight = (height - 60) / (count + 1);

      layerNodes.forEach((node, rIdx) => {
        const y = 35 + (rIdx + 1) * rowHeight;
        nodeCoords[node.id] = { x, y, node };
      });
      currentLayerCol++;
    });

    // Render Edges
    const edgesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    edgesGroup.setAttribute('class', 'edges-layer');
    viewport.appendChild(edgesGroup);

    edges.forEach(edge => {
      const src = nodeCoords[edge.source];
      const tgt = nodeCoords[edge.target];
      if (!src || !tgt) return;

      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      const dx = tgt.x - src.x;
      const dy = tgt.y - src.y;
      const cx1 = src.x + dx * 0.45;
      const cy1 = src.y;
      const cx2 = src.x + dx * 0.55;
      const cy2 = tgt.y;

      const d = `M ${src.x} ${src.y} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${tgt.x} ${tgt.y}`;
      path.setAttribute('d', d);

      const statusClass = edge.status === 'RESOLVED' ? 'edge-resolved' : (edge.status === 'BLOCKED' ? 'edge-blocked' : 'edge-pending');
      path.setAttribute('class', `graph-edge ${statusClass}`);
      const markerType = edge.status === 'RESOLVED' ? 'resolved' : (edge.status === 'BLOCKED' ? 'blocked' : 'pending');
      path.setAttribute('marker-end', `url(#arrow-${markerType}-${stage})`);
      edgesGroup.appendChild(path);

      if (edge.relation) {
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', (src.x + tgt.x) / 2);
        text.setAttribute('y', (src.y + tgt.y) / 2 - 4);
        text.setAttribute('class', 'graph-edge-text');
        text.textContent = edge.relation;
        edgesGroup.appendChild(text);
      }
    });

    // Render Nodes
    const nodesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    nodesGroup.setAttribute('class', 'nodes-layer');
    viewport.appendChild(nodesGroup);

    nodes.forEach(node => {
      const coord = nodeCoords[node.id];
      if (!coord) return;

      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('class', 'graph-node');
      g.setAttribute('transform', `translate(${coord.x}, ${coord.y})`);
      g.setAttribute('data-id', node.id);

      const style = getNodeVisuals(node, stage);

      if (node.type === 'agent') {
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('r', '22');
        circle.setAttribute('fill', style.fill);
        circle.setAttribute('stroke', style.stroke);
        circle.setAttribute('stroke-width', '2.5');
        circle.setAttribute('class', 'node-shape');
        g.appendChild(circle);

        const icon = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        icon.setAttribute('text-anchor', 'middle');
        icon.setAttribute('dy', '5');
        icon.setAttribute('font-size', '16');
        icon.textContent = '🤖';
        g.appendChild(icon);
      } else if (node.type === 'decision') {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', '-50');
        rect.setAttribute('y', '-16');
        rect.setAttribute('width', '100');
        rect.setAttribute('height', '32');
        rect.setAttribute('rx', '16');
        rect.setAttribute('fill', style.fill);
        rect.setAttribute('stroke', style.stroke);
        rect.setAttribute('stroke-width', '2');
        rect.setAttribute('class', 'node-shape');
        g.appendChild(rect);

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('class', 'node-label');
        text.setAttribute('y', '4');
        text.textContent = '✓ ' + (node.label.replace('Decision: ', ''));
        g.appendChild(text);
      } else {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', '-60');
        rect.setAttribute('y', '-18');
        rect.setAttribute('width', '120');
        rect.setAttribute('height', '36');
        rect.setAttribute('rx', '8');
        rect.setAttribute('fill', style.fill);
        rect.setAttribute('stroke', style.stroke);
        rect.setAttribute('stroke-width', '2');
        rect.setAttribute('class', 'node-shape');
        g.appendChild(rect);

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('class', 'node-label');
        text.setAttribute('y', '-2');
        const truncatedLabel = node.label.length > 18 ? node.label.substring(0, 16) + '…' : node.label;
        text.textContent = truncatedLabel;
        g.appendChild(text);

        const badge = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        badge.setAttribute('class', 'node-badge-text');
        badge.setAttribute('y', '11');
        badge.setAttribute('fill', style.badgeColor);
        badge.textContent = node.status;
        g.appendChild(badge);
      }

      g.addEventListener('click', (e) => {
        e.stopPropagation();
        openInspector(node);
      });

      nodesGroup.appendChild(g);
    });
  }

  function getNodeVisuals(node, stage) {
    if (node.type === 'agent') {
      return { fill: '#1e1b4b', stroke: '#818cf8', badgeColor: '#c7d2fe' };
    }

    if (node.type === 'decision') {
      return { fill: '#312e81', stroke: '#a855f7', badgeColor: '#f3e8ff' };
    }

    if (node.type === 'action') {
      if (node.status === 'COMPLETED') {
        return { fill: '#064e3b', stroke: '#10b981', badgeColor: '#6ee7b7' };
      }
      return { fill: '#4c0519', stroke: '#f43f5e', badgeColor: '#fca5a5' };
    }

    if (node.type === 'agenda') {
      if (node.status.startsWith('DECIDED_')) {
        return { fill: '#042f2e', stroke: '#14b8a6', badgeColor: '#5eead4' };
      }
      return { fill: '#083344', stroke: '#06b6d4', badgeColor: '#67e8f9' };
    }

    if (stage === 'AFTER' || node.status === 'RESOLVED') {
      return { fill: '#022c22', stroke: '#059669', badgeColor: '#34d399' };
    }

    if (node.status === 'BLOCKED') {
      return { fill: '#450a0a', stroke: '#ef4444', badgeColor: '#f87171' };
    }
    if (node.status === 'UNRESOLVED') {
      return { fill: '#451a03', stroke: '#f59e0b', badgeColor: '#fbbf24' };
    }

    return { fill: '#0f172a', stroke: '#38bdf8', badgeColor: '#7dd3fc' };
  }

  // ==========================================
  // Node Inspector Drawer
  // ==========================================
  function openInspector(node) {
    selectedNode = node;
    if (inspId) inspId.textContent = node.id;
    if (inspStatus) inspStatus.textContent = node.status;
    if (inspType) inspType.textContent = node.type;
    if (inspTitle) inspTitle.textContent = node.label;
    if (inspDetails) inspDetails.textContent = node.details || 'Keine zusaetzlichen Details.';
    if (inspTypeBadge) inspTypeBadge.textContent = node.type.toUpperCase();
    if (inspJson) inspJson.textContent = JSON.stringify(node, null, 2);

    if (nodeInspector) nodeInspector.classList.add('open');
  }

  function closeInspector() {
    if (nodeInspector) nodeInspector.classList.remove('open');
    selectedNode = null;
  }

  // ==========================================
  // 60-Second Call Transcript & Audio Player
  // ==========================================
  function renderTranscript() {
    if (!transcriptScroll) return;
    if (!transcriptData || !transcriptData.turns) {
      transcriptScroll.innerHTML = '<div class="transcript-loading">Kein Transcript vorhanden</div>';
      return;
    }

    transcriptScroll.innerHTML = '';
    transcriptData.turns.forEach((turn, idx) => {
      const isAgent = turn.speaker.toLowerCase().includes('agent') || turn.speaker.toLowerCase().includes('dawndispatch');
      const turnDiv = document.createElement('div');
      turnDiv.className = `transcript-turn ${isAgent ? 'speaker-agent' : 'speaker-philipp'}`;
      turnDiv.id = `turn-${idx}`;

      const tagClass = turn.tag && turn.tag.includes('Decision') ? 'tag-decision' : (turn.tag && turn.tag.includes('Rapid') ? 'tag-checkpoint' : '');

      turnDiv.innerHTML = `
        <div class="turn-header">
          <span class="turn-speaker ${isAgent ? 'speaker-tag-agent' : 'speaker-tag-lead'}">
            ${isAgent ? '🤖 DawnDispatch' : '👓 Philipp (Ray-Ban)'}
          </span>
          <div style="display:flex; gap:6px; align-items:center;">
            ${turn.tag ? `<span class="turn-tag ${tagClass}">${turn.tag}</span>` : ''}
            <span class="turn-time">${turn.time || ''}</span>
          </div>
        </div>
        <p class="turn-text">${turn.text}</p>
      `;

      turnDiv.addEventListener('click', () => {
        highlightTurn(idx);
      });

      transcriptScroll.appendChild(turnDiv);
    });
  }

  function toggleAudioPlayback() {
    if (audioPlaying) {
      pauseAudioPlayback();
    } else {
      startAudioPlayback();
    }
  }

  function startAudioPlayback() {
    audioPlaying = true;
    if (btnAudioPlay) btnAudioPlay.classList.add('playing');
    if (playIcon) playIcon.textContent = '⏸';
    if (playText) playText.textContent = 'Pause';
    if (soundWave) soundWave.classList.add('active');

    if (currentTurnIndex >= (transcriptData?.turns?.length || 0)) {
      currentTurnIndex = 0;
      playbackSeconds = 0;
    }

    audioTimerInterval = setInterval(() => {
      playbackSeconds += 1;
      const mins = String(Math.floor(playbackSeconds / 60)).padStart(2, '0');
      const secs = String(playbackSeconds % 60).padStart(2, '0');
      if (audioTimer) audioTimer.textContent = `${mins}:${secs} / 01:00`;

      const turns = transcriptData?.turns || [];
      const targetTurnIndex = Math.min(turns.length - 1, Math.floor(playbackSeconds / 6.5));
      if (targetTurnIndex !== currentTurnIndex) {
        currentTurnIndex = targetTurnIndex;
        highlightTurn(currentTurnIndex);
      }

      if (playbackSeconds >= 60 || currentTurnIndex >= turns.length - 1) {
        pauseAudioPlayback();
      }
    }, 1000);

    highlightTurn(currentTurnIndex);
  }

  function pauseAudioPlayback() {
    audioPlaying = false;
    if (btnAudioPlay) btnAudioPlay.classList.remove('playing');
    if (playIcon) playIcon.textContent = '▶';
    if (playText) playText.textContent = 'Transcript abspielen';
    if (soundWave) soundWave.classList.remove('active');
    clearInterval(audioTimerInterval);
  }

  function highlightTurn(idx) {
    document.querySelectorAll('.transcript-turn').forEach(el => el.classList.remove('active-turn'));
    const target = document.getElementById(`turn-${idx}`);
    if (target) {
      target.classList.add('active-turn');
      target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  // ==========================================
  // Human Checkpoint Action Cards Engine
  // ==========================================
  function renderCheckpoints() {
    if (!checkpointsList) return;
    if (!actionsData || actionsData.length === 0) {
      checkpointsList.innerHTML = '<div class="checkpoints-loading">Keine Checkpoints registriert</div>';
      return;
    }

    checkpointsList.innerHTML = '';
    actionsData.forEach(action => {
      const isBlocked = action.status === 'BLOCKED_ON_CHECKPOINT' || action.status === 'BLOCKED';
      const isTarget = window.targetCheckpointId && (action.item_id === window.targetCheckpointId || action.action_id === window.targetCheckpointId);

      const card = document.createElement('div');
      card.className = `action-card ${isBlocked ? 'status-blocked' : 'status-completed'} ${isTarget ? 'highlight-focus' : ''}`;
      card.id = `action-card-${action.action_id}`;

      const reason = action.artifacts?.reason || action.artifacts?.dispatch_status || 'Keine Begruendung hinterlegt.';
      const port = action.artifacts?.port ? `Port: ${action.artifacts.port}` : '';
      const commit = action.artifacts?.commit ? `Commit: ${action.artifacts.commit}` : '';

      card.innerHTML = `
        <div class="card-top">
          <div class="action-code-wrap">
            <span class="action-type">${action.action_type}</span>
            <span class="action-id">${action.action_id} • Ref: ${action.item_id}</span>
          </div>
          <span class="action-status-badge ${isBlocked ? 'badge-blocked' : 'badge-completed'}">
            ${isBlocked ? '⚠️ Checkpoint Blocked' : '✓ Completed'}
          </span>
        </div>
        <p class="action-reason">${reason}</p>
        <div class="action-artifacts-box">
          ${port ? `<div class="artifact-row"><span class="artifact-key">Endpoint:</span><span class="artifact-val">${port}</span></div>` : ''}
          ${commit ? `<div class="artifact-row"><span class="artifact-key">Git Commit:</span><span class="artifact-val">${commit}</span></div>` : ''}
          ${action.artifacts?.scope ? `<div class="artifact-row"><span class="artifact-key">Scope:</span><span class="artifact-val">${action.artifacts.scope}</span></div>` : ''}
          ${action.artifacts?.confirmed_by ? `<div class="artifact-row"><span class="artifact-key">Verified:</span><span class="artifact-val">${action.artifacts.confirmed_by}</span></div>` : ''}
        </div>
        <div class="action-actions-bar">
          ${
            isBlocked
              ? `<button class="btn-confirm-cp" data-id="${action.action_id}">
                  <span>⚡</span> Freigeben & Ausfuehren (1-Klick)
                </button>`
              : `<span class="btn-confirmed-ok">✓ Human-Verified & Executed</span>`
          }
        </div>
      `;

      if (isBlocked) {
        const btn = card.querySelector('.btn-confirm-cp');
        btn.addEventListener('click', () => confirmCheckpoint(action.action_id));
      }

      checkpointsList.appendChild(card);
    });

    if (window.targetCheckpointId) {
      const targetCard = document.querySelector('.highlight-focus');
      if (targetCard) {
        targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }

  async function confirmCheckpoint(actionId) {
    const card = document.getElementById(`action-card-${actionId}`);
    const btn = card?.querySelector('.btn-confirm-cp');
    if (btn) {
      btn.innerHTML = '⏳ Wird bestaetigt...';
      btn.disabled = true;
    }

    try {
      let res = await fetch(`/api/actions/${encodeURIComponent(actionId)}/confirm`, { method: 'POST' });
      if (!res.ok) {
        res = await fetch(`/api/checkpoint/${encodeURIComponent(actionId)}/confirm`, { method: 'POST' });
      }
      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      showToast(`Checkpoint ${actionId} freigegeben und ausgefuehrt!`, 'success');
      await loadAllData();
    } catch (err) {
      console.error('Failed to confirm checkpoint:', err);
      showToast(`Fehler bei Freigabe von ${actionId}: ${err.message}`, 'error');
      if (btn) {
        btn.innerHTML = '⚡ Erneut versuchen';
        btn.disabled = false;
      }
    }
  }

  // ==========================================
  // Toasts
  // ==========================================
  function showToast(message, type = 'info') {
    if (!toastContainer) return;
    const toast = document.createElement('div');
    toast.className = 'toast';
    if (type === 'error') toast.style.borderColor = '#f43f5e';
    toast.innerHTML = `
      <span>${type === 'success' ? '✅' : (type === 'error' ? '❌' : 'ℹ️')}</span>
      <span>${message}</span>
    `;

    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(20px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
