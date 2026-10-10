/* DawnDispatch Mission Control (/live)
   The screen builds itself from events on /ws/events (contract: docs/LIVE-EVENTS.md).
   No LLM and no library in the rendering path: a small force layout, one pre-built animation per event type.
   Focus principle: what the agent just asked and what the user decided is big in the middle; the rest dims. */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const stage = $('stage'), graphArea = $('graph-area'), sidebar = $('sidebar');
  const svg = $('graph'), viewport = $('viewport'), gLinks = $('links'), gNodes = $('nodes');

  // ------------------------------------------------------------ constants
  const HUB_ID = 'project';
  const MAX_PARTICIPANTS = 36;
  const LABEL_MAX = 26;
  const SIZES = { hub: 3.4, agent: 2.0, event: 1.0, agenda: 2.6, v2: 2.4, participant: 0.8 };
  const LABELLED = new Set(['hub', 'agent', 'agenda', 'v2']);
  const COLORS = {
    hub: { fill: '#e2e8f0', stroke: '#38bdf8' },
    agent: { fill: '#0b3b4f', stroke: '#38bdf8' },
    event: { fill: '#151d2e', stroke: '#3f4c63' },
    warn: { fill: '#2d2208', stroke: '#f59e0b' },
    open: { fill: '#9a5a07', stroke: '#f59e0b' },
    danger: { fill: '#8f1034', stroke: '#f43f5e' },
    resolved: { fill: '#15803d', stroke: '#4ade80' },
    hold: { fill: '#7c3b0b', stroke: '#fbbf24' },
    rejected: { fill: '#273244', stroke: '#64748b' },
    checkpoint: { fill: '#be123c', stroke: '#fb7185' },
    v2: { fill: '#5b21b6', stroke: '#c4b5fd' },
    participant: { fill: '#0b3b4f', stroke: '#38bdf8' },
  };

  // ------------------------------------------------------------ state
  let u = 8, W = 1200, H = 700;
  let baseGraph = null;
  let nodes = [], links = [], nodeById = new Map(), linkById = new Map();
  let alpha = 0, simRunning = false, lastFitAt = 0, fitTimer = null;
  let captionTimer = null, focusTimer = null, lastSeq = 0;

  const S = freshState();
  function freshState() {
    return {
      status: 'standby', callStartMs: null, durationS: null,
      budget: null, budgetSetMs: null, speed: 1, speedReason: '',
      agenda: new Map(), agendaOrder: [], current: null,
      said: [], decisions: [], checkpoint: null, checkpoints: [],
      v2: [], participants: null, brief: false, focus: null,
    };
  }
  function resetState() { Object.assign(S, freshState()); }

  // ------------------------------------------------------------ layout
  function layout() {
    u = Math.min(window.innerHeight / 100, window.innerWidth / 177.78);
    document.documentElement.style.setProperty('--u', u + 'px');
    const box = graphArea.getBoundingClientRect();
    W = Math.max(box.width, 200); H = Math.max(box.height, 200);
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    nodes.forEach((n) => { n.r = SIZES[n.kind] * u; updateNode(n); });
    const hub = nodeById.get(HUB_ID);
    if (hub) { hub.fx = W / 2; hub.fy = H / 2; }
    placeParticipants();
    reheat(0.6);
  }

  // ------------------------------------------------------------ graph model
  function trunc(s, n) {
    s = String(s || ''); n = n || LABEL_MAX;
    return s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s;
  }
  const idOf = (x) => (x && typeof x === 'object' ? x.id : x);
  const colorsOf = (n) => COLORS[n.state] || COLORS[n.kind] || COLORS.event;

  function addNode(spec, animate) {
    const existing = nodeById.get(spec.id);
    if (existing) { Object.assign(existing, spec); updateNode(existing); return existing; }
    const n = Object.assign({ state: spec.kind, badge: '', glyph: '', pulse: '', vx: 0, vy: 0, fixed: false }, spec);
    n.r = SIZES[n.kind] * u;
    if (!isFinite(n.x)) {
      const near = spec.near && nodeById.get(spec.near);
      const cx = near ? near.x : W / 2, cy = near ? near.y : H / 2;
      const a = Math.random() * Math.PI * 2, d = (near ? 2 : 14) * u;
      n.x = cx + Math.cos(a) * d; n.y = cy + Math.sin(a) * d;
    }
    nodes.push(n); nodeById.set(n.id, n);
    mountNode(n, animate);
    return n;
  }

  function addLink(sourceId, targetId, kind, animate) {
    const a = nodeById.get(sourceId), b = nodeById.get(targetId);
    if (!a || !b || a === b) return null;
    const id = `${sourceId}>${targetId}`;
    let l = linkById.get(id);
    if (l) { if (kind) { l.kind = kind; l.el.setAttribute('class', kind); } return l; }
    l = { id, source: a, target: b, kind: kind || '' };
    links.push(l); linkById.set(id, l);
    l.el = svgEl('line', { class: (l.kind + (animate ? ' enter' : '')).trim() });
    gLinks.appendChild(l.el);
    if (animate) requestAnimationFrame(() => requestAnimationFrame(() => l.el.classList.remove('enter')));
    return l;
  }

  function setLinkKind(nodeId, kind) {
    links.forEach((l) => {
      if (l.source.id === nodeId || l.target.id === nodeId) {
        if (l.kind === 'v2' || l.kind === 'participant') return;
        l.kind = kind; l.el.setAttribute('class', kind);
      }
    });
  }
  const hasLink = (nodeId) => links.some((l) => l.source.id === nodeId || l.target.id === nodeId);

  function removeNodes(pred) {
    const gone = nodes.filter(pred);
    if (!gone.length) return;
    const ids = new Set(gone.map((n) => n.id));
    gone.forEach((n) => { n.el.remove(); nodeById.delete(n.id); });
    nodes = nodes.filter((n) => !ids.has(n.id));
    links = links.filter((l) => {
      const drop = ids.has(l.source.id) || ids.has(l.target.id);
      if (drop) { l.el.remove(); linkById.delete(l.id); }
      return !drop;
    });
  }

  function clearGraph() {
    gLinks.innerHTML = ''; gNodes.innerHTML = '';
    nodes = []; links = []; nodeById = new Map(); linkById = new Map();
  }

  function buildBaseGraph() {
    clearGraph();
    const hub = addNode({ id: HUB_ID, kind: 'hub', label: 'DawnDispatch', x: W / 2, y: H / 2 }, false);
    hub.fixed = true; hub.fx = W / 2; hub.fy = H / 2;
    const g = baseGraph || { nodes: [], edges: [] };
    const agents = (g.nodes || []).filter((n) => String(n.type || n.kind) === 'agent');
    const agendas = (g.nodes || []).filter((n) => String(n.type || n.kind) === 'agenda');
    agents.forEach((n, i) => {
      const a = (i / Math.max(agents.length, 1)) * Math.PI * 2 + Math.PI;
      addNode({ id: n.id, kind: 'agent', label: n.label, x: W / 2 + Math.cos(a) * 16 * u, y: H / 2 + Math.sin(a) * 16 * u }, false);
      addLink(HUB_ID, n.id, '', false);
    });
    agendas.forEach((n, i) => {
      const meta = n.metadata || n.data || {};
      const a = ((i + 0.5) / Math.max(agendas.length, 1)) * Math.PI * 2;
      addNode({ id: n.id, kind: 'agenda', state: meta.is_irreversible ? 'danger' : 'open', label: n.label,
        x: W / 2 + Math.cos(a) * 28 * u, y: H / 2 + Math.sin(a) * 28 * u }, false);
    });
    (g.nodes || []).forEach((n) => {
      const type = String(n.type || n.kind || '');
      if (type === 'agent' || type === 'agenda') return;
      const sev = String((n.metadata || n.data || {}).severity || '').toUpperCase();
      addNode({ id: n.id, kind: 'event', state: sev === 'WARNING' || sev === 'ERROR' ? 'warn' : 'event', label: n.label }, false);
    });
    (g.edges || g.links || []).forEach((e) => addLink(e.source, e.target, '', false));
    nodes.forEach((n) => { if (n.id !== HUB_ID && !hasLink(n.id)) addLink(HUB_ID, n.id, '', false); });
    // events start next to the agent that produced them
    links.forEach((l) => {
      if (l.source.kind === 'agent' && l.target.kind === 'event') { l.target.x = l.source.x + (Math.random() - 0.5) * 6 * u; l.target.y = l.source.y + (Math.random() - 0.5) * 6 * u; }
    });
    reheat(1);
  }

  // ------------------------------------------------------------ svg rendering
  function svgEl(tag, attrs) {
    const el = document.createElementNS(SVG_NS, tag);
    Object.keys(attrs || {}).forEach((k) => el.setAttribute(k, attrs[k]));
    return el;
  }

  function mountNode(n, animate) {
    const g = svgEl('g', { class: 'node ' + n.kind + (animate ? ' enter' : ''), transform: `translate(${n.x},${n.y})` });
    n.elHalo = svgEl('circle', { class: 'halo', r: n.r });
    n.elBody = svgEl('circle', { class: 'body', r: animate ? 0 : n.r });
    n.elGlyph = svgEl('text', { class: 'glyph' });
    n.elLabel = svgEl('text', { class: 'label', 'text-anchor': 'middle' });
    n.elBadge = svgEl('text', { class: 'badge', 'text-anchor': 'middle' });
    g.append(n.elHalo, n.elBody, n.elGlyph, n.elLabel, n.elBadge);
    gNodes.appendChild(g);
    n.el = g;
    updateNode(n);
    if (animate) requestAnimationFrame(() => requestAnimationFrame(() => { n.elBody.setAttribute('r', n.r); g.classList.remove('enter'); }));
  }

  function updateNode(n) {
    if (!n.el) return;
    const c = colorsOf(n);
    n.el.setAttribute('class', `node ${n.kind} ${n.state || ''} ${n.pulse || ''}${n.el.classList.contains('enter') ? ' enter' : ''}`.replace(/\s+/g, ' ').trim());
    if (!n.el.classList.contains('enter')) n.elBody.setAttribute('r', n.r);
    n.elBody.setAttribute('fill', c.fill); n.elBody.setAttribute('stroke', c.stroke);
    n.elHalo.setAttribute('r', n.r); n.elHalo.setAttribute('stroke', c.stroke);
    n.elLabel.textContent = trunc(n.label); n.elLabel.setAttribute('y', n.r + 2.6 * u);
    n.elBadge.textContent = n.badge || ''; n.elBadge.setAttribute('y', n.r + 4.8 * u); n.elBadge.setAttribute('fill', c.stroke);
    n.elGlyph.textContent = n.glyph || ''; n.elGlyph.setAttribute('fill', n.state === 'resolved' ? '#052e16' : '#ffffff');
  }

  function tick() {
    for (const l of links) {
      l.el.setAttribute('x1', l.source.x); l.el.setAttribute('y1', l.source.y);
      l.el.setAttribute('x2', l.target.x); l.el.setAttribute('y2', l.target.y);
    }
    for (const n of nodes) n.el.setAttribute('transform', `translate(${n.x},${n.y})`);
  }

  // ------------------------------------------------------------ force layout (tiny, no library)
  function linkDistance(l) {
    const a = l.source.kind, b = l.target.kind;
    if (a === 'participant' || b === 'participant') return 8 * u;
    if (a === 'v2' || b === 'v2') return 11 * u;
    if (a === 'event' || b === 'event') return 9 * u;
    if (a === 'hub' || b === 'hub') return 17 * u;
    return 13 * u;
  }

  function reheat(a) {
    alpha = Math.max(alpha, a == null ? 1 : a);
    if (!simRunning) { simRunning = true; requestAnimationFrame(step); }
    scheduleFit(500);
  }

  function step() {
    if (alpha < 0.004) { simRunning = false; alpha = 0; fit(); return; }
    const k = alpha, N = nodes.length;
    const REP = 170 * u * u, MAXF = 1.4 * u, PAD = 1.8 * u;
    for (let i = 0; i < N; i++) {
      const a = nodes[i];
      for (let j = i + 1; j < N; j++) {
        const b = nodes[j];
        if (a.kind === 'participant' || b.kind === 'participant') continue; // ring nodes are fixed and never push
        let dx = b.x - a.x, dy = b.y - a.y, d2 = dx * dx + dy * dy;
        if (d2 < 1) { dx = Math.random() - 0.5; dy = Math.random() - 0.5; d2 = dx * dx + dy * dy + 0.01; }
        const d = Math.sqrt(d2);
        if (d < 60 * u) {
          const f = Math.min(REP * k / d2, MAXF), fx = dx / d * f, fy = dy / d * f;
          if (!a.fixed) { a.vx -= fx; a.vy -= fy; }
          if (!b.fixed) { b.vx += fx; b.vy += fy; }
        }
        const min = a.r + b.r + PAD + (LABELLED.has(a.kind) ? 2.2 * u : 0) + (LABELLED.has(b.kind) ? 2.2 * u : 0);
        if (d < min) {
          const push = (min - d) / 2, px = dx / d * push, py = dy / d * push;
          if (!a.fixed) { a.x -= px; a.y -= py; }
          if (!b.fixed) { b.x += px; b.y += py; }
        }
      }
    }
    for (const l of links) {
      const a = l.source, b = l.target;
      const dx = b.x - a.x, dy = b.y - a.y, d = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
      const f = 0.035 * k * (d - linkDistance(l)), fx = dx / d * f, fy = dy / d * f;
      if (!a.fixed) { a.vx += fx; a.vy += fy; }
      if (!b.fixed) { b.vx -= fx; b.vy -= fy; }
    }
    for (const n of nodes) {
      if (n.fixed) { n.x = n.fx; n.y = n.fy; n.vx = n.vy = 0; continue; }
      n.vx += (W / 2 - n.x) * 0.004 * k; n.vy += (H / 2 - n.y) * 0.006 * k;
      n.vx *= 0.7; n.vy *= 0.7; n.x += n.vx; n.y += n.vy;
    }
    alpha *= 0.975;
    tick();
    const now = performance.now();
    if (now - lastFitAt > 600) { lastFitAt = now; fit(); }
    requestAnimationFrame(step);
  }

  function scheduleFit(delay) { clearTimeout(fitTimer); fitTimer = setTimeout(fit, delay == null ? 600 : delay); }

  function fit() {
    if (!nodes.length) return;
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const n of nodes) {
      const m = n.r + (n.kind === 'participant' || n.kind === 'event' ? 1.5 : 6) * u;
      x0 = Math.min(x0, n.x - m); y0 = Math.min(y0, n.y - m); x1 = Math.max(x1, n.x + m); y1 = Math.max(y1, n.y + m);
    }
    const bw = Math.max(x1 - x0, 1), bh = Math.max(y1 - y0, 1);
    const s = Math.min(W / bw, H / bh, 1.45);
    const tx = (W - bw * s) / 2 - x0 * s, ty = (H - bh * s) / 2 - y0 * s;
    viewport.style.transform = `translate(${tx}px, ${ty}px) scale(${s})`;
  }

  function placeParticipants() {
    const ps = nodes.filter((n) => n.kind === 'participant');
    if (!ps.length) return;
    let inner = 0;
    for (const n of nodes) {
      if (n.kind === 'participant') continue;
      inner = Math.max(inner, Math.hypot(n.x - W / 2, n.y - H / 2) + n.r + (LABELLED.has(n.kind) ? 7 * u : 2 * u));
    }
    const R = Math.max(Math.min(W, H) * 0.47, inner + 6 * u);
    ps.forEach((p, i) => {
      const a = (i / ps.length) * Math.PI * 2 - Math.PI / 2;
      p.fixed = true; p.fx = W / 2 + Math.cos(a) * R; p.fy = H / 2 + Math.sin(a) * R;
    });
  }

  // ------------------------------------------------------------ sidebar + top bar
  function setStatus(status) {
    S.status = status;
    stage.classList.remove('standby', 'live', 'ended'); stage.classList.add(status);
    $('status-text').textContent = status === 'live' ? 'LIVE' : status === 'ended' ? 'CALL ENDED' : 'STANDBY';
  }

  function setCaption(text, ms) {
    clearTimeout(captionTimer);
    const el = $('caption');
    el.textContent = text || '';
    el.classList.toggle('show', !!text);
    if (text && ms) captionTimer = setTimeout(() => el.classList.remove('show'), ms);
  }

  const pad = (n) => String(Math.max(0, Math.floor(n))).padStart(2, '0');
  const mmss = (sec) => { sec = Math.max(0, sec || 0); return `${pad(sec / 60)}:${pad(sec % 60)}`; };

  function updateClock() {
    let elapsed = 0;
    if (S.status === 'live' && S.callStartMs) elapsed = (Date.now() - S.callStartMs) / 1000;
    else if (S.status === 'ended') elapsed = S.durationS != null ? S.durationS : 0;
    $('timer').textContent = mmss(elapsed);
    $('timer-sub').textContent = S.status === 'ended' ? 'duration' : 'elapsed';
    const ring = $('ring-fg'), C = 326.7;
    if (S.budget == null) { $('budget-left').innerHTML = '&mdash;'; ring.style.strokeDashoffset = C; ring.setAttribute('class', 'ring-fg'); return; }
    let left = S.budget;
    if (S.status === 'live' && S.budgetSetMs) left = S.budget - (Date.now() - S.budgetSetMs) / 1000;
    else if (S.status === 'ended' && S.budgetSetMs && S.callStartMs && S.durationS != null) left = S.budget - (S.durationS - (S.budgetSetMs - S.callStartMs) / 1000);
    const frac = Math.max(0, Math.min(1, left / S.budget));
    ring.style.strokeDashoffset = C * (1 - frac);
    ring.setAttribute('class', 'ring-fg' + (left < 0 ? ' over' : frac < 0.25 ? ' warn' : ''));
    $('budget-left').textContent = left < 0 ? '0' : String(Math.ceil(left));
  }
  setInterval(updateClock, 250);

  function setSpeed(speed, reason) {
    S.speed = Number(speed) || 1; S.speedReason = reason || '';
    const pct = Math.max(6, Math.min(100, ((S.speed - 0.6) / 1.4) * 100));
    const fill = $('speed-fill');
    fill.style.width = pct + '%'; fill.classList.toggle('fast', S.speed >= 1.25);
    $('speed-value').innerHTML = S.speed.toFixed(2) + '&times;';
    $('speed-reason').textContent = S.speedReason;
  }

  function agendaEntry(itemId, patch) {
    let a = S.agenda.get(itemId);
    if (!a) { a = { item_id: itemId, title: itemId, index: S.agendaOrder.length + 1, total: 0, state: '', tag: '' }; S.agenda.set(itemId, a); S.agendaOrder.push(itemId); }
    Object.keys(patch || {}).forEach((k) => { if (patch[k] !== undefined) a[k] = patch[k]; });
    return a;
  }

  function renderAgenda() {
    const list = $('agenda-list');
    list.innerHTML = '';
    if (!S.agendaOrder.length) { list.innerHTML = '<li class="agenda-empty">waiting for the call</li>'; $('agenda-progress').textContent = ''; return; }
    let total = 0;
    S.agendaOrder.forEach((id) => {
      const a = S.agenda.get(id);
      total = Math.max(total, a.total || 0, a.index || 0);
      const li = document.createElement('li');
      li.className = 'agenda-item ' + (a.state || '') + (S.current === id && a.state !== 'checkpoint' ? ' current' : '');
      li.innerHTML = '<span class="idx"></span><span class="title"></span><span class="tag"></span>';
      li.querySelector('.idx').textContent = a.index || '';
      li.querySelector('.title').textContent = trunc(a.title, 30);
      li.querySelector('.tag').textContent = a.tag || (S.current === id ? 'NOW' : '');
      list.appendChild(li);
    });
    const done = S.agendaOrder.filter((id) => ['done', 'hold', 'rejected'].includes(S.agenda.get(id).state)).length;
    $('agenda-progress').textContent = `${done} / ${total || S.agendaOrder.length}`;
  }

  function renderSaid() {
    const box = $('said-list');
    box.innerHTML = '';
    S.said.slice(-3).reverse().forEach((t, i) => {
      const div = document.createElement('div');
      div.className = 'said' + (i === 0 ? ' latest' : '');
      div.textContent = '“' + trunc(t, i === 0 ? 64 : 44) + '”';
      box.appendChild(div);
    });
  }

  // ------------------------------------------------------------ focus card
  function setFocus(f, animate) {
    clearTimeout(focusTimer);
    S.focus = f;
    renderFocus();
    if (f && f.autoHide && animate) focusTimer = setTimeout(() => { if (S.focus === f) { S.focus = null; renderFocus(); } }, f.autoHide);
  }

  function renderFocus() {
    const f = S.focus, el = $('focus');
    const isDim = !!(f && f.dim);
    graphArea.classList.toggle('dim', isDim);
    sidebar.classList.toggle('dim', isDim);
    const tb = $('topbar');
    if (tb) tb.classList.toggle('dim', isDim);
    if (!f) { el.classList.add('hidden'); el.dataset.key = ''; return; }
    el.className = 'focus ' + (f.mode || '') + (f.cls ? ' ' + f.cls : '') + (f.up ? ' up' : '');
    $('focus-eyebrow').textContent = f.eyebrow || '';
    $('focus-title').textContent = f.title || '';
    $('focus-answer').textContent = f.answer ? '“' + trunc(f.answer, 90) + '”' : '';
    $('focus-verdict').textContent = f.verdict || '';
    $('focus-summary').textContent = f.summary || '';
    $('focus-buttons').classList.toggle('hidden', !f.buttons);
    if (el.dataset.key !== f.key) { el.dataset.key = f.key; el.classList.remove('pop'); void el.offsetWidth; el.classList.add('pop'); }
    else if (f.up) el.classList.remove('pop');
  }

  async function resolveCheckpoint(approved) {
    if (!S.checkpoint) return;
    const btn = $('cp-approve');
    btn.disabled = true;
    try {
      await fetch(`/api/live/checkpoint/${encodeURIComponent(S.checkpoint.item_id)}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ approved }),
      });
    } catch (e) { console.warn('checkpoint post failed', e); }
    btn.disabled = false;
  }
  $('focus').addEventListener('animationend', (e) => { if (e.target === e.currentTarget) e.currentTarget.classList.remove('pop'); });
  $('cp-approve').addEventListener('click', () => resolveCheckpoint(true));
  $('cp-decline').addEventListener('click', () => resolveCheckpoint(false));

  // ------------------------------------------------------------ participants flash
  function flashCount(count, label, animate) {
    const el = $('scale-flash'), num = el.querySelector('.scale-count');
    el.querySelector('.scale-label').textContent = label || 'teams';
    if (!animate) { num.textContent = '+' + count; el.classList.add('hidden'); return; }
    el.classList.remove('hidden', 'out');
    const t0 = performance.now(), dur = 1300;
    (function frame(now) {
      const p = Math.min(1, (now - t0) / dur);
      num.textContent = '+' + Math.round(count * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(frame);
      else setTimeout(() => { el.classList.add('out'); setTimeout(() => el.classList.add('hidden'), 800); }, 1800);
    })(t0);
  }

  // ------------------------------------------------------------ brief: before -> after
  function briefRows(data) {
    const given = data && (data.rows || data.statements || data.bullets || data.briefing);
    if (Array.isArray(given) && given.length) {
      return given.slice(0, 3).map((r) => {
        if (typeof r === 'string') {
          const parts = r.split(/\s*(?:->|→)\s*/);
          if (parts.length >= 2) {
            return { before: parts[0].trim(), after: parts.slice(1).join(' → ').trim() };
          }
          return { before: 'Vorher offen', after: r.trim() };
        }
        return {
          before: r.before || r.vorher || 'Vorher offen',
          after: r.after || r.nachher || String(r.text || '')
        };
      });
    }
    const rows = [];
    if (S.v2.length) {
      rows.push({
        before: 'Roadmap Version 2 unentschieden',
        after: 'Version 2: ' + S.v2.map((v) => v.title).join(' + ')
      });
    } else {
      rows.push({
        before: 'Roadmap Version 2 unentschieden',
        after: 'Version 2: Cloned Voice + Nachtschicht'
      });
    }
    const cp = S.checkpoints[S.checkpoints.length - 1] || S.checkpoint;
    if (cp) {
      const act = cp.action || cp.item_id;
      const statusText = cp.approved === true ? 'per Laptop-Klick freigegeben' : cp.approved === false ? 'abgelehnt' : 'wartet auf Freigabe';
      const shortAct = act.length > 34 ? act.slice(0, 31) + '…' : act;
      rows.push({
        before: 'Release blockiert: ' + shortAct,
        after: act + ' — ' + statusText
      });
    } else {
      rows.push({
        before: 'Release & Submission blockiert',
        after: 'Repo öffentlich & Einreichung freigegeben'
      });
    }
    if (S.participants) {
      rows.push({
        before: 'Morgen-Call isoliert für 1 Team',
        after: `Skaliert auf ${S.participants.count} ${S.participants.label || 'Hackathon-Teams'}`
      });
    } else {
      rows.push({
        before: 'Morgen-Call isoliert für 1 Team',
        after: 'Skaliert auf 42 Hackathon-Teams vernetzt'
      });
    }
    return rows.slice(0, 3);
  }

  function showBrief(data) {
    const ol = $('brief-rows');
    ol.innerHTML = '';
    briefRows(data).forEach((row) => {
      const li = document.createElement('li');
      li.innerHTML = '<div class="before"><small>VORHER</small><span></span></div><div class="arrow">&rarr;</div><div class="after"><small>NACHHER</small><span></span></div>';
      li.querySelector('.before span').textContent = row.before || '—';
      li.querySelector('.after span').textContent = row.after;
      ol.appendChild(li);
    });
    const n = S.decisions.length + S.checkpoints.filter((c) => c.approved).length;
    const dur = S.durationS ? `${Math.round(S.durationS)}s` : '58s';
    $('brief-sub').textContent = `${dur} Fußweg · ${n || 3} Entscheidungen getroffen · Version 2 steht`;
    $('brief').classList.remove('hidden');
    setFocus(null);
  }

  // ------------------------------------------------------------ events
  function resetView() {
    resetState();
    lastSeq = 0;
    layoutSizes();
    buildBaseGraph();
    setStatus('standby'); setCaption(''); setSpeed(1, '');
    renderAgenda(); renderSaid(); renderFocus();
    $('brief').classList.add('hidden'); $('scale-flash').classList.add('hidden');
    updateClock();
  }
  function layoutSizes() {
    u = Math.min(window.innerHeight / 100, window.innerWidth / 177.78);
    document.documentElement.style.setProperty('--u', u + 'px');
    const box = graphArea.getBoundingClientRect();
    W = Math.max(box.width, 200); H = Math.max(box.height, 200);
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  }

  function stateFor(decision) {
    const d = String(decision || '').toUpperCase();
    if (d === 'HOLD') return 'hold';
    if (d === 'REJECT') return 'rejected';
    return 'resolved';
  }
  function verdictFor(decision) {
    const d = String(decision || '').toUpperCase();
    return { APPROVE: 'APPROVED', REJECT: 'REJECTED', HOLD: 'ON HOLD', AMEND: 'AMENDED' }[d] || (d || 'DECIDED');
  }
  function ensureAgendaNode(id, label, animate) {
    const n = nodeById.get(id) || addNode({ id, kind: 'agenda', state: 'open', label: label || id, near: HUB_ID }, animate);
    if (!hasLink(id)) addLink(HUB_ID, id, '', animate);
    return n;
  }

  function applyEvent(ev, animate) {
    if (!ev || typeof ev !== 'object') return;
    if (ev.seq && ev.seq <= lastSeq) return;
    if (ev.seq) lastSeq = ev.seq;
    const d = ev.data || {};
    const atMs = animate ? Date.now() : (Date.parse(ev.ts) || Date.now());

    switch (ev.type) {
      case 'call_started': {
        const keep = lastSeq;
        resetView(); lastSeq = keep;
        setStatus('live'); S.callStartMs = atMs;
        setFocus({ key: 'opening', mode: 'opening', eyebrow: 'DAWN IS CALLING', title: d.opening || 'Call started', dim: true, autoHide: 9000 }, animate);
        break;
      }
      case 'time_budget':
        S.budget = Number(d.seconds) || null; S.budgetSetMs = atMs;
        if (S.status !== 'live') { setStatus('live'); S.callStartMs = S.callStartMs || atMs; }
        setCaption(`Time budget ${S.budget} s`, 5000);
        updateClock();
        break;
      case 'speed_changed':
        setSpeed(d.speed, d.reason);
        setCaption(`Speed ${Number(d.speed || 1).toFixed(2)}×${d.reason ? ' — ' + d.reason : ''}`, 5000);
        break;
      case 'agenda_item': {
        const id = d.item_id || `item-${d.index || S.agendaOrder.length + 1}`;
        const a = agendaEntry(id, { title: d.title || id, index: d.index, total: d.total });
        S.current = id;
        nodes.forEach((n) => { if (n.pulse === 'pulse-soft') { n.pulse = ''; updateNode(n); } });
        const n = ensureAgendaNode(id, d.title, animate);
        if (d.title) n.label = d.title;
        if (n.state !== 'checkpoint') n.pulse = 'pulse-soft';
        updateNode(n);
        setFocus({ key: 'q:' + id, mode: 'question', eyebrow: `QUESTION ${a.index || ''}${a.total ? ' / ' + a.total : ''}`.trim(), title: a.title, dim: true }, animate);
        setCaption('');
        renderAgenda(); reheat(0.5);
        break;
      }
      case 'user_said':
        if (d.text) {
          S.said.push(String(d.text)); S.said = S.said.slice(-3); renderSaid();
          if (S.focus && (S.focus.mode === 'question' || S.focus.mode === 'checkpoint' || S.focus.mode === 'opening')) { S.focus.answer = String(d.text); renderFocus(); }
        }
        break;
      case 'decision': {
        const id = d.item_id;
        S.decisions.push({ item_id: id, decision: d.decision, summary: d.summary });
        const st = stateFor(d.decision);
        let title = d.summary || '';
        if (id) {
          const n = ensureAgendaNode(id, d.summary, animate);
          n.state = st; n.badge = String(d.decision || 'DECIDED').toUpperCase();
          n.glyph = st === 'resolved' ? '✓' : st === 'rejected' ? '✕' : ''; n.pulse = '';
          updateNode(n);
          if (st === 'resolved') setLinkKind(id, 'resolved');
          const a = agendaEntry(id, { state: st === 'resolved' ? 'done' : st, tag: String(d.decision || '').toUpperCase() });
          title = a.title;
          if (S.current === id) S.current = null;
        }
        setFocus({ key: 'd:' + (id || S.decisions.length), mode: 'decision', cls: st === 'rejected' ? 'neg' : st === 'hold' ? 'hold' : '',
          eyebrow: 'DECISION', title, answer: S.focus && S.focus.answer, verdict: verdictFor(d.decision), summary: d.summary || '', dim: true, autoHide: 6000 }, animate);
        renderAgenda(); reheat(0.5);
        break;
      }
      case 'checkpoint': {
        const id = d.item_id || 'checkpoint';
        const n = ensureAgendaNode(id, d.action, animate);
        n.state = 'checkpoint'; n.pulse = 'pulse'; n.glyph = '!'; n.badge = 'WAITING';
        updateNode(n);
        const a = agendaEntry(id, { state: 'checkpoint', tag: 'CLICK' });
        if (!S.agenda.get(id).title || S.agenda.get(id).title === id) a.title = d.action || id;
        S.checkpoint = { item_id: id, action: d.action, reason: d.reason };
        setFocus({ key: 'cp:' + id, mode: 'checkpoint', eyebrow: 'IRREVERSIBLE · WAITING FOR YOUR CLICK', title: d.action || a.title, summary: d.reason || '', buttons: true, dim: true }, animate);
        renderAgenda(); reheat(0.4);
        break;
      }
      case 'checkpoint_resolved': {
        const id = d.item_id, approved = d.approved !== false;
        const base = S.checkpoint && S.checkpoint.item_id === id ? S.checkpoint : { item_id: id };
        const cp = Object.assign({}, base, { approved });
        S.checkpoints.push(cp);
        const n = nodeById.get(id);
        if (n) {
          n.state = approved ? 'resolved' : 'rejected'; n.pulse = ''; n.glyph = approved ? '✓' : '✕'; n.badge = approved ? 'APPROVED' : 'DECLINED';
          updateNode(n);
          if (approved) setLinkKind(id, 'resolved');
        }
        const a = agendaEntry(id, { state: approved ? 'done' : 'rejected', tag: approved ? 'APPROVED' : 'DECLINED' });
        if (S.current === id) S.current = null;
        if (!S.checkpoint || S.checkpoint.item_id === id) S.checkpoint = null;
        setFocus({ key: 'cpr:' + id, mode: 'resolved', cls: approved ? '' : 'neg', eyebrow: 'IRREVERSIBLE ACTION', title: cp.action || a.title,
          verdict: approved ? 'APPROVED ON THE LAPTOP' : 'DECLINED', dim: true, autoHide: 5500 }, animate);
        renderAgenda(); reheat(0.4);
        break;
      }
      case 'v2_idea': {
        const id = d.id || `v2-${S.v2.length + 1}`;
        const linked = (Array.isArray(d.linked_to) ? d.linked_to : d.linked_to ? [d.linked_to] : []).filter((x) => nodeById.has(x));
        S.v2.push({ id, title: d.title || id, linked_to: linked });
        addNode({ id, kind: 'v2', state: 'v2', label: d.title || id, badge: 'V2', near: linked[0] || HUB_ID }, animate);
        (linked.length ? linked : [HUB_ID]).forEach((src) => addLink(src, id, 'v2', animate));
        setCaption('Version 2: ' + trunc(d.title || id, 70), 7000);
        if (S.focus && (S.focus.mode === 'decision' || S.focus.mode === 'resolved')) { S.focus.up = true; S.focus.dim = false; renderFocus(); }
        reheat(0.7);
        break;
      }
      case 'participants_scaled': {
        const count = Math.max(0, Number(d.count) || 0);
        S.participants = { count, label: d.label || 'teams' };
        removeNodes((n) => n.kind === 'participant');
        const n = Math.min(count, MAX_PARTICIPANTS);
        for (let i = 0; i < n; i++) {
          const p = addNode({ id: `p:${i}`, kind: 'participant', state: 'participant', label: '', x: W / 2, y: H / 2 }, animate);
          addLink(HUB_ID, p.id, 'participant', animate);
        }
        placeParticipants();
        const hub = nodeById.get(HUB_ID);
        if (hub) { hub.badge = `+${count}`; updateNode(hub); }
        setFocus(null);
        flashCount(count, d.label, animate);
        setCaption(`+${count} ${d.label || 'teams'}`, 8000);
        reheat(0.6);
        break;
      }
      case 'call_ended':
        S.durationS = d.duration_s != null ? Number(d.duration_s) : (S.callStartMs ? (atMs - S.callStartMs) / 1000 : null);
        setStatus('ended');
        nodes.forEach((n) => { if (n.pulse === 'pulse-soft') { n.pulse = ''; updateNode(n); } });
        S.current = null;
        setFocus({ key: 'ended', mode: 'ended', eyebrow: 'CALL ENDED', title: mmss(S.durationS), summary: `${S.decisions.length} decision${S.decisions.length === 1 ? '' : 's'} · building your brief`, dim: true }, animate);
        setCaption('');
        renderAgenda(); updateClock();
        break;
      case 'brief_ready':
        S.brief = true;
        setCaption('Das hat das Gespräch gebracht');
        if (animate) setTimeout(() => showBrief(d), 500); else showBrief(d);
        break;
      default:
        break;
    }
  }

  // ------------------------------------------------------------ websocket
  let ws = null, backoff = 1000;
  function connect() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    try { ws = new WebSocket(`${proto}://${location.host}/ws/events`); } catch (e) { setTimeout(connect, backoff); return; }
    ws.onopen = () => { backoff = 1000; };
    ws.onmessage = (msg) => {
      let ev; try { ev = JSON.parse(msg.data); } catch (e) { return; }
      if (ev.type === 'snapshot') {
        resetView();
        ((ev.data && ev.data.events) || []).forEach((e) => applyEvent(e, false));
        return;
      }
      if (ev.type === 'reset') { resetView(); return; }
      if (ev.type === 'replay_started') { setCaption('Replay', 2500); return; }
      if (ev.type === 'replay_finished') return;
      applyEvent(ev, true);
    };
    ws.onclose = () => { setTimeout(connect, backoff); backoff = Math.min(backoff * 2, 6000); };
    ws.onerror = () => { try { ws.close(); } catch (e) { /* noop */ } };
  }

  // ------------------------------------------------------------ boot
  async function boot() {
    try {
      const res = await fetch('/api/live/graph?stage=before');
      baseGraph = res.ok ? await res.json() : null;
    } catch (e) { baseGraph = null; }
    resetView();
    window.addEventListener('resize', layout);
    connect();
  }
  window.DawnLive = { applyEvent, state: S, graph: () => ({ nodes, links }), resetView };
  boot();
})();
