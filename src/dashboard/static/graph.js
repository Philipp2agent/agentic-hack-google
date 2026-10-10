/**
 * DawnDispatch Desktop Web Dashboard
 * Interactive Knowledge Graph, Audio Transcript & Human Checkpoint Engine
 * Enhanced with v1 vs v2 Evolution Contrast & "Show me, don't tell me" Checkpoint Gates
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
  let currentFilter = 'all'; // 'all', 'v1', 'v2', 'checkpoints'
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

  const btnFilterAll = document.getElementById('btn-filter-all');
  const btnFilterV1 = document.getElementById('btn-filter-v1');
  const btnFilterV2 = document.getElementById('btn-filter-v2');
  const btnFilterCheckpoints = document.getElementById('btn-filter-checkpoints');

  const graphsWorkspace = document.getElementById('graphs-workspace');
  const svgBefore = document.getElementById('svg-before');
  const svgAfter = document.getElementById('svg-after');

  const nodeInspector = document.getElementById('node-inspector');
  const btnCloseInspector = document.getElementById('btn-close-inspector');
  const inspId = document.getElementById('insp-id');
  const inspStatus = document.getElementById('insp-status');
  const inspType = document.getElementById('insp-type');
  const inspEvolution = document.getElementById('insp-evolution');
  const inspCheckpointRow = document.getElementById('insp-checkpoint-row');
  const inspCheckpointAlert = document.getElementById('insp-checkpoint-alert');
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

    if (btnFilterAll) btnFilterAll.addEventListener('click', () => setFilter('all'));
    if (btnFilterV1) btnFilterV1.addEventListener('click', () => setFilter('v1'));
    if (btnFilterV2) btnFilterV2.addEventListener('click', () => setFilter('v2'));
    if (btnFilterCheckpoints) btnFilterCheckpoints.addEventListener('click', () => setFilter('checkpoints'));

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

  // Load API Data
  async function loadAllData() {
    try {
      let stateData = null;
      try {
        const stateRes = await fetch('/api/state');
        if (stateRes.ok) {
          stateData = await stateRes.json();
        }
      } catch (e) {
        // Optional endpoint
      }

      const [resBefore, resAfter, resTrans, resActions] = await Promise.all([
        fetch('/api/graph/before').catch(() => null),
        fetch('/api/graph/after').catch(() => null),
        fetch('/api/transcript').catch(() => null),
        fetch('/api/actions').catch(() => null),
      ]);

      if (resBefore && resBefore.ok) {
        graphBeforeData = await resBefore.json();
      } else if (stateData?.graph_before) {
        graphBeforeData = stateData.graph_before;
      }

      if (resAfter && resAfter.ok) {
        graphAfterData = await resAfter.json();
      } else if (stateData?.graph_after) {
        graphAfterData = stateData.graph_after;
      }

      if (resTrans && resTrans.ok) {
        transcriptData = await resTrans.json();
      } else if (stateData?.transcript) {
        transcriptData = stateData.transcript;
      }

      if (resActions && resActions.ok) {
        actionsData = await resActions.json();
      } else if (stateData?.actions) {
        actionsData = stateData.actions;
      }

      updateMetrics();
      renderAll();
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      showToast('Fehler beim Laden der Dashboard-Daten: ' + err.message, 'error');
    }
  }

  function renderAll() {
    if (graphBeforeData) renderGraph(svgBefore, graphBeforeData, 'BEFORE');
    if (graphAfterData) renderGraph(svgAfter, graphAfterData, 'AFTER');
    renderTranscript();
    renderCheckpoints();
    applyFilterToGraphs();
  }

  // View Mode Controls
  function setViewMode(mode) {
    viewMode = mode;
    [btnViewSplit, btnViewBefore, btnViewAfter].forEach(b => b?.classList.remove('active'));

    if (mode === 'split') {
      btnViewSplit?.classList.add('active');
      graphsWorkspace.className = 'graphs-workspace';
    } else if (mode === 'before') {
      btnViewBefore?.classList.add('active');
      graphsWorkspace.className = 'graphs-workspace mode-before';
    } else if (mode === 'after') {
      btnViewAfter?.classList.add('active');
      graphsWorkspace.className = 'graphs-workspace mode-after';
    }

    setTimeout(() => {
      if (graphBeforeData) renderGraph(svgBefore, graphBeforeData, 'BEFORE');
      if (graphAfterData) renderGraph(svgAfter, graphAfterData, 'AFTER');
      applyFilterToGraphs();
    }, 50);
  }

  // Evolution & Checkpoint Filter
  function setFilter(filter) {
    currentFilter = filter;
    [btnFilterAll, btnFilterV1, btnFilterV2, btnFilterCheckpoints].forEach(b => b?.classList.remove('active'));
    if (filter === 'all') btnFilterAll?.classList.add('active');
    else if (filter === 'v1') btnFilterV1?.classList.add('active');
    else if (filter === 'v2') btnFilterV2?.classList.add('active');
    else if (filter === 'checkpoints') btnFilterCheckpoints?.classList.add('active');

    applyFilterToGraphs();
    const filterNames = {
      all: 'Alle Knoten',
      v1: 'v1 MVP Baseline (Heute gebaut)',
      v2: 'v2 Next-Gen Evolution (Roadmap)',
      checkpoints: 'Human Checkpoints („Show me, don't tell me“)',
    };
    showToast(`Filter aktiv: ${filterNames[filter] || filter}`, 'info');
  }

  function applyFilterToGraphs() {
    const nodes = document.querySelectorAll('.graph-node');
    const edges = document.querySelectorAll('.graph-edge');

    nodes.forEach(el => {
      const v = el.getAttribute('data-version');
      const isCp = el.getAttribute('data-checkpoint') === 'true';

      let match = true;
      if (currentFilter === 'v1') match = (v === 'v1');
      else if (currentFilter === 'v2') match = (v === 'v2');
      else if (currentFilter === 'checkpoints') match = isCp;

      if (match) {
        el.classList.remove('dimmed');
        if (currentFilter !== 'all') el.classList.add('highlighted');
        else el.classList.remove('highlighted');
      } else {
        el.classList.add('dimmed');
        el.classList.remove('highlighted');
      }
    });

    edges.forEach(el => {
      const v = el.getAttribute('data-version');
      const isCp = el.getAttribute('data-checkpoint') === 'true';

      let match = true;
      if (currentFilter === 'v1') match = (v === 'v1');
      else if (currentFilter === 'v2') match = (v === 'v2');
      else if (currentFilter === 'checkpoints') match = isCp;

      if (match) {
        el.classList.remove('dimmed');
      } else {
        el.classList.add('dimmed');
      }
    });
  }

  // Zoom Controls
  function adjustZoom(delta) {
    zoomLevel = Math.max(0.5, Math.min(2.5, zoomLevel + delta));
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

  // Metrics Update
  function updateMetrics() {
    if (graphBeforeData && graphBeforeData.nodes) {
      const eventNodes = graphBeforeData.nodes.filter(n => n.type === 'event');
      const unresolved = graphBeforeData.nodes.filter(n => n.status === 'UNRESOLVED' || n.status === 'BLOCKED');
      const elCount = document.getElementById('metric-events-count');
      const elUnresFoot = document.getElementById('metric-unresolved-foot');
      const elUnres = document.getElementById('before-unresolved-count');
      if (elCount) elCount.textContent = `${eventNodes.length} Events`;
      if (elUnresFoot) elUnresFoot.textContent = `${unresolved.length} ungeloeste Blocker`;
      if (elUnres) elUnres.textContent = `${unresolved.length} Ungeloest`;
    }

    if (graphAfterData && graphAfterData.nodes) {
      let v1Count = 0;
      let v2Count = 0;
      graphAfterData.nodes.forEach(n => {
        const meta = getNodeClassification(n, 'AFTER');
        if (meta.version === 'v2') v2Count++;
        else v1Count++;
      });
      const elEvo = document.getElementById('metric-evolution-count');
      const elEvoFoot = document.getElementById('metric-evolution-foot');
      if (elEvo) elEvo.textContent = `${v1Count} v1 ➔ ${v2Count} v2`;
      if (elEvoFoot) elEvoFoot.textContent = `${v2Count} Next-Gen Weichen freigegeben`;
    }

    if (actionsData) {
      const blocked = actionsData.filter(a => a.status === 'BLOCKED_ON_CHECKPOINT' || a.status === 'BLOCKED');
      if (metricCheckpointsCount) {
        if (blocked.length === 0) {
          metricCheckpointsCount.className = 'metric-val text-emerald';
          metricCheckpointsCount.textContent = '0 Ausstehend';
        } else {
          metricCheckpointsCount.className = 'metric-val text-rose';
          metricCheckpointsCount.textContent = `${blocked.length} Ausstehend`;
        }
      }
      if (checkpointTagText) {
        checkpointTagText.textContent = blocked.length === 0 ? 'Alle Freigegeben' : `${blocked.length} Blockiert`;
      }
    }
  }

  // ==========================================
  // Classification Engine: v1 vs v2 & Checkpoints
  // ==========================================
  function getNodeClassification(node, stage) {
    const isAgent = node.type === 'agent';
    const isDecision = node.type === 'decision';
    const isAction = node.type === 'action';
    const isAgenda = node.type === 'agenda';
    const isEvent = node.type === 'event';

    const fullText = `${node.id} ${node.label || ''} ${node.details || ''} ${JSON.stringify(node.metadata || {})}`.toLowerCase();

    // Human Checkpoint Gate ("Show me, don't tell me")
    const isCheckpoint = !!(
      node.metadata?.is_irreversible === true ||
      node.metadata?.requires_checkpoint === true ||
      node.status === 'BLOCKED_ON_CHECKPOINT' ||
      (node.status === 'BLOCKED' && (isAction || isAgenda)) ||
      fullText.includes('checkpoint') ||
      fullText.includes('irreversible') ||
      fullText.includes('desk sign-off') ||
      fullText.includes('schreibtisch') ||
      fullText.includes('public release')
    );

    // Version Classification: v1 (MVP Built Today) vs v2 (Next-Gen Autonomous Evolution)
    let version = 'v1';
    if (
      node.version === 'v2' ||
      node.metadata?.version === 'v2' ||
      fullText.includes('version 2') ||
      fullText.includes('v2') ||
      fullText.includes('whatsapp') ||
      fullText.includes('night shift') ||
      fullText.includes('voice clone') ||
      fullText.includes('cloned voice') ||
      fullText.includes('build queue') ||
      fullText.includes('autonomous write')
    ) {
      version = 'v2';
    }

    return { isAgent, isDecision, isAction, isAgenda, isEvent, isCheckpoint, version };
  }

  function getNodeVisuals(node, stage, classification) {
    const { isCheckpoint, version } = classification;

    if (isCheckpoint) {
      return {
        fill: '#380c1a',
        stroke: '#f43f5e',
        badgeColor: '#fca5a5',
        versionBadge: version.toUpperCase(),
        versionColor: '#fca5a5',
        auraColor: '#f43f5e',
      };
    }

    if (node.type === 'agent') {
      return {
        fill: '#0f172a',
        stroke: '#38bdf8',
        badgeColor: '#7dd3fc',
        versionBadge: version.toUpperCase(),
        versionColor: '#38bdf8',
      };
    }

    if (node.type === 'decision') {
      if (version === 'v2') {
        return {
          fill: '#2e1065',
          stroke: '#c084fc',
          badgeColor: '#f3e8ff',
          versionBadge: 'v2 EVO',
          versionColor: '#c084fc',
        };
      }
      return {
        fill: '#022c22',
        stroke: '#10b981',
        badgeColor: '#6ee7b7',
        versionBadge: 'v1 DEC',
        versionColor: '#10b981',
      };
    }

    if (node.type === 'action') {
      if (node.status === 'COMPLETED') {
        return {
          fill: '#064e3b',
          stroke: '#10b981',
          badgeColor: '#6ee7b7',
          versionBadge: version.toUpperCase(),
          versionColor: '#6ee7b7',
        };
      }
      return {
        fill: '#4c0519',
        stroke: '#f43f5e',
        badgeColor: '#fca5a5',
        versionBadge: version.toUpperCase(),
        versionColor: '#fca5a5',
      };
    }

    if (version === 'v2') {
      return {
        fill: '#1e0d36',
        stroke: '#c084fc',
        badgeColor: '#e9d5ff',
        versionBadge: 'v2 EVO',
        versionColor: '#c084fc',
      };
    }

    if (node.type === 'agenda') {
      if (node.status && node.status.startsWith('DECIDED_')) {
        return {
          fill: '#042f2e',
          stroke: '#14b8a6',
          badgeColor: '#5eead4',
          versionBadge: 'v1 MVP',
          versionColor: '#14b8a6',
        };
      }
      return {
        fill: '#083344',
        stroke: '#06b6d4',
        badgeColor: '#67e8f9',
        versionBadge: 'v1 MVP',
        versionColor: '#06b6d4',
      };
    }

    if (stage === 'AFTER' || node.status === 'RESOLVED') {
      return {
        fill: '#022c22',
        stroke: '#059669',
        badgeColor: '#34d399',
        versionBadge: 'v1 MVP',
        versionColor: '#34d399',
      };
    }

    if (node.status === 'BLOCKED') {
      return {
        fill: '#450a0a',
        stroke: '#ef4444',
        badgeColor: '#f87171',
        versionBadge: 'v1 MVP',
        versionColor: '#f87171',
      };
    }
    if (node.status === 'UNRESOLVED') {
      return {
        fill: '#451a03',
        stroke: '#f59e0b',
        badgeColor: '#fbbf24',
        versionBadge: 'v1 MVP',
        versionColor: '#fbbf24',
      };
    }

    return {
      fill: '#091e36',
      stroke: '#38bdf8',
      badgeColor: '#7dd3fc',
      versionBadge: 'v1 MVP',
      versionColor: '#38bdf8',
    };
  }

  // ==========================================
  // Knowledge Graph Rendering Engine (SVG)
  // ==========================================
  function renderGraph(svg, data, stage) {
    if (!svg || !data || !data.nodes) return;

    svg.innerHTML = '';
    const width = svg.clientWidth || 600;
    const height = svg.clientHeight || 420;

    // SVG Defs: Glowing filters and arrowheads
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    defs.innerHTML = `
      <marker id="arrow-pending-${stage}" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 10 5 L 0 9 z" fill="#f59e0b" />
      </marker>
      <marker id="arrow-resolved-${stage}" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981" />
      </marker>
      <marker id="arrow-v2-${stage}" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 10 5 L 0 9 z" fill="#c084fc" />
      </marker>
      <marker id="arrow-checkpoint-${stage}" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1 L 10 5 L 0 9 z" fill="#f43f5e" />
      </marker>
      <filter id="glow-checkpoint-${stage}" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur stdDeviation="4" result="blur" />
        <feComposite in="SourceGraphic" in2="blur" operator="over" />
      </filter>
      <filter id="glow-v2-${stage}" x="-20%" y="-20%" width="140%" height="140%">
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
    const colWidth = Math.max(150, (width - 80) / Math.max(1, activeLayers));
    const nodeCoords = {};

    let currentLayerCol = 0;
    layers.forEach((layerNodes) => {
      if (layerNodes.length === 0) return;
      const x = 50 + currentLayerCol * colWidth + colWidth * 0.45;
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

      const srcClass = getNodeClassification(src.node, stage);
      const tgtClass = getNodeClassification(tgt.node, stage);
      const isV2Edge = (srcClass.version === 'v2' || tgtClass.version === 'v2');
      const isCpEdge = (srcClass.isCheckpoint || tgtClass.isCheckpoint);

      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      const dx = tgt.x - src.x;
      const dy = tgt.y - src.y;
      const cx1 = src.x + dx * 0.45;
      const cy1 = src.y;
      const cx2 = src.x + dx * 0.55;
      const cy2 = tgt.y;

      const d = `M ${src.x} ${src.y} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${tgt.x} ${tgt.y}`;
      path.setAttribute('d', d);

      let edgeClass = 'graph-edge';
      let markerType = 'pending';

      if (isCpEdge) {
        edgeClass += ' edge-checkpoint';
        markerType = 'checkpoint';
      } else if (isV2Edge) {
        edgeClass += ' edge-v2';
        markerType = 'v2';
      } else if (edge.status === 'RESOLVED') {
        edgeClass += ' edge-resolved';
        markerType = 'resolved';
      } else if (edge.status === 'BLOCKED') {
        edgeClass += ' edge-blocked';
        markerType = 'checkpoint';
      } else {
        edgeClass += ' edge-pending';
        markerType = 'pending';
      }

      path.setAttribute('class', edgeClass);
      path.setAttribute('data-version', isV2Edge ? 'v2' : 'v1');
      path.setAttribute('data-checkpoint', isCpEdge ? 'true' : 'false');
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

      const classification = getNodeClassification(node, stage);
      const visuals = getNodeVisuals(node, stage, classification);

      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      let nodeClassList = `graph-node node-${classification.version}`;
      if (classification.isCheckpoint) nodeClassList += ' node-checkpoint';

      g.setAttribute('class', nodeClassList);
      g.setAttribute('transform', `translate(${coord.x}, ${coord.y})`);
      g.setAttribute('data-id', node.id);
      g.setAttribute('data-version', classification.version);
      g.setAttribute('data-checkpoint', classification.isCheckpoint ? 'true' : 'false');

      // Checkpoint Animated Aura Ring / Rect
      if (classification.isCheckpoint) {
        const aura = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        aura.setAttribute('x', '-76');
        aura.setAttribute('y', '-26');
        aura.setAttribute('width', '152');
        aura.setAttribute('height', '52');
        aura.setAttribute('rx', '10');
        aura.setAttribute('class', 'checkpoint-aura');
        g.appendChild(aura);
      }

      if (node.type === 'agent') {
        // Agent Circular Node
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('r', '22');
        circle.setAttribute('fill', visuals.fill);
        circle.setAttribute('stroke', visuals.stroke);
        circle.setAttribute('stroke-width', '2.5');
        circle.setAttribute('class', 'node-shape');
        g.appendChild(circle);

        const icon = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        icon.setAttribute('text-anchor', 'middle');
        icon.setAttribute('dy', '5');
        icon.setAttribute('font-size', '16');
        icon.textContent = '🤖';
        g.appendChild(icon);

        // Small Version Pill Badge
        const vPill = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        vPill.setAttribute('class', 'node-version-badge-text');
        vPill.setAttribute('x', '0');
        vPill.setAttribute('y', '32');
        vPill.setAttribute('fill', visuals.versionColor);
        vPill.textContent = visuals.versionBadge;
        g.appendChild(vPill);

      } else if (node.type === 'decision') {
        // Decision Pill Shape
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', '-55');
        rect.setAttribute('y', '-16');
        rect.setAttribute('width', '110');
        rect.setAttribute('height', '32');
        rect.setAttribute('rx', '16');
        rect.setAttribute('fill', visuals.fill);
        rect.setAttribute('stroke', visuals.stroke);
        rect.setAttribute('stroke-width', '2');
        rect.setAttribute('class', 'node-shape');
        g.appendChild(rect);

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('class', 'node-label');
        text.setAttribute('y', '3');
        const decLabel = node.label.replace('Decision: ', '');
        text.textContent = '✓ ' + decLabel;
        g.appendChild(text);

        // Version badge above
        const vPill = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        vPill.setAttribute('class', 'node-version-badge-text');
        vPill.setAttribute('y', '-20');
        vPill.setAttribute('fill', visuals.versionColor);
        vPill.textContent = visuals.versionBadge;
        g.appendChild(vPill);

      } else {
        // Standard Card Node (Event / Agenda / Action)
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', '-70');
        rect.setAttribute('y', '-20');
        rect.setAttribute('width', '140');
        rect.setAttribute('height', '40');
        rect.setAttribute('rx', '8');
        rect.setAttribute('fill', visuals.fill);
        rect.setAttribute('stroke', visuals.stroke);
        rect.setAttribute('stroke-width', '2');
        rect.setAttribute('class', 'node-shape');
        g.appendChild(rect);

        // Title Label
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('class', 'node-label');
        text.setAttribute('y', '-4');
        const truncatedLabel = node.label.length > 20 ? node.label.substring(0, 18) + '…' : node.label;
        text.textContent = truncatedLabel;
        g.appendChild(text);

        // Subtitle / Status / Checkpoint Banner
        const badge = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        badge.setAttribute('class', 'node-badge-text');
        badge.setAttribute('y', '11');
        badge.setAttribute('fill', visuals.badgeColor);

        if (classification.isCheckpoint) {
          badge.textContent = '🛡️ SHOW ME GATE';
        } else {
          badge.textContent = `${visuals.versionBadge} • ${node.status}`;
        }
        g.appendChild(badge);
      }

      // Interaction
      g.addEventListener('click', (e) => {
        e.stopPropagation();
        openInspector(node, classification);
        if (classification.isCheckpoint) {
          focusActionCard(node.id);
          showToast(`Human Checkpoint gewählt: „Show me, don't tell me“`, 'info');
        }
      });

      nodesGroup.appendChild(g);
    });
  }

  // ==========================================
  // Node Inspector Drawer
  // ==========================================
  function openInspector(node, classification) {
    selectedNode = node;
    const meta = classification || getNodeClassification(node, 'INSPECTOR');

    if (inspId) inspId.textContent = node.id;
    if (inspStatus) inspStatus.textContent = node.status;
    if (inspType) inspType.textContent = node.type;
    if (inspTitle) inspTitle.textContent = node.label;
    if (inspDetails) inspDetails.textContent = node.details || 'Keine zusätzlichen Details hinterlegt.';
    if (inspTypeBadge) inspTypeBadge.textContent = node.type.toUpperCase();

    if (inspEvolution) {
      if (meta.version === 'v2') {
        inspEvolution.innerHTML = '<span class="text-violet">v2 Next-Gen (Autonomous Evolution)</span>';
      } else {
        inspEvolution.innerHTML = '<span class="text-cyan">v1 MVP (Heute gebaut • Web & Ray-Ban)</span>';
      }
    }

    if (inspCheckpointRow) {
      inspCheckpointRow.style.display = meta.isCheckpoint ? 'flex' : 'none';
    }
    if (inspCheckpointAlert) {
      inspCheckpointAlert.style.display = meta.isCheckpoint ? 'flex' : 'none';
    }

    if (inspJson) inspJson.textContent = JSON.stringify(node, null, 2);
    if (nodeInspector) nodeInspector.classList.add('open');
  }

  function closeInspector() {
    if (nodeInspector) nodeInspector.classList.remove('open');
    selectedNode = null;
  }

  function focusActionCard(nodeId) {
    const card = document.querySelector(`[data-item-id="${nodeId}"], #action-card-${nodeId}`);
    if (card) {
      document.querySelectorAll('.action-card').forEach(c => c.classList.remove('highlight-focus'));
      card.classList.add('highlight-focus');
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
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
      card.setAttribute('data-item-id', action.item_id || action.action_id);

      const reason = action.artifacts?.reason || action.artifacts?.dispatch_status || 'Keine Begründung hinterlegt.';
      const port = action.artifacts?.port ? `Port: ${action.artifacts.port}` : '';
      const commit = action.artifacts?.commit ? `Commit: ${action.artifacts.commit}` : '';

      card.innerHTML = `
        <div class="card-top">
          <div class="action-code-wrap">
            <div style="display:flex; align-items:center; gap:8px;">
              <span class="action-type">${action.action_type}</span>
              <span class="card-checkpoint-stamp">🛡️ SHOW ME, DON'T TELL ME</span>
            </div>
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
                  <span>⚡</span> Freigeben & Ausführen (1-Klick)
                </button>`
              : `<span class="btn-confirmed-ok">✓ Human-Verified & Executed</span>`
          }
        </div>
      `;

      if (isBlocked) {
        const btn = card.querySelector('.btn-confirm-cp');
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          confirmCheckpoint(action.action_id);
        });
      }

      card.addEventListener('click', () => {
        // Highlight corresponding node in SVG
        const matchingNode = document.querySelector(`[data-id="${action.item_id}"], [data-id="${action.action_id}"]`);
        if (matchingNode) {
          matchingNode.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        }
      });

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
      btn.innerHTML = '⏳ Wird bestätigt...';
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

      showToast(`Checkpoint ${actionId} erfolgreich freigegeben und ausgeführt!`, 'success');
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
    if (type === 'info') toast.style.borderColor = '#38bdf8';
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
