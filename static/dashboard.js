/**
 * dashboard.js  v2
 * ─────────────────────────────────────────────────────────────────
 * Powers the AI Anomaly Detection real-time dashboard:
 *   • Line chart  — Live traffic (Normal vs Attack over time)
 *   • Pie chart   — Attack vs Normal distribution
 *   • Bar chart   — Model performance metrics
 *   • SSE listener — live DB updates every 2 s
 *   • Toast notifications
 *   • Simulation start / stop buttons
 */

/* ── Design tokens (mirror CSS vars) ──────────────────────────── */
const C = {
  blue:   '#60a5fa',
  green:  '#34d399',
  red:    '#f87171',
  purple: '#a78bfa',
  cyan:   '#22d3ee',
  orange: '#fb923c',
  yellow: '#fbbf24',
  bg:     '#111827',
  bg2:    '#1a2236',
  border: 'rgba(255,255,255,0.06)',
  muted:  '#64748b',
  dim:    '#94a3b8',
  text:   '#e2e8f0',
};

Chart.defaults.color = C.dim;
Chart.defaults.font.family = "'Inter', system-ui, sans-serif";

const DEFAULT_CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 500, easing: 'easeInOutQuart' },
  plugins: {
    legend: {
      labels: {
        color: C.dim,
        font: { family: "'Inter', sans-serif", size: 12, weight: '500' },
        padding: 16,
        usePointStyle: true,
        pointStyleWidth: 8,
      },
    },
    tooltip: {
      backgroundColor: C.bg,
      borderColor: 'rgba(96,165,250,0.2)',
      borderWidth: 1,
      titleColor: C.text,
      bodyColor: C.dim,
      padding: 12,
      cornerRadius: 8,
      displayColors: true,
    },
  },
};

/* ── Shared axis styles ───────────────────────────────────────── */
const AXIS_STYLE = {
  ticks:    { color: C.muted, font: { size: 11 } },
  grid:     { color: 'rgba(255,255,255,0.04)' },
  border:   { color: 'transparent' },
};


/* ════════════════════════════════════════════════════════════════
   1. LINE CHART — Live Traffic Monitor
   ════════════════════════════════════════════════════════════════ */
const MAX_POINTS   = 20;
const trafficCtx   = document.getElementById('trafficChart');
let   trafficChart = null;

if (trafficCtx) {
  trafficChart = new Chart(trafficCtx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Normal',
          data: [],
          borderColor: C.green,
          backgroundColor: 'rgba(52,211,153,0.08)',
          fill: true,
          tension: 0.45,
          pointRadius: 3,
          pointBackgroundColor: C.green,
          pointHoverRadius: 6,
          borderWidth: 2,
        },
        {
          label: 'Attack',
          data: [],
          borderColor: C.red,
          backgroundColor: 'rgba(248,113,113,0.08)',
          fill: true,
          tension: 0.45,
          pointRadius: 3,
          pointBackgroundColor: C.red,
          pointHoverRadius: 6,
          borderWidth: 2,
        },
      ],
    },
    options: {
      ...DEFAULT_CHART_OPTIONS,
      scales: { x: AXIS_STYLE, y: { ...AXIS_STYLE, beginAtZero: true } },
      plugins: {
        ...DEFAULT_CHART_OPTIONS.plugins,
        legend: { ...DEFAULT_CHART_OPTIONS.plugins.legend, position: 'top' },
      },
    },
  });
}


/* ════════════════════════════════════════════════════════════════
   2. PIE CHART — Attack vs Normal Distribution
   ════════════════════════════════════════════════════════════════ */
const pieCtx   = document.getElementById('pieChart');
let   pieChart = null;

if (pieCtx) {
  pieChart = new Chart(pieCtx, {
    type: 'doughnut',
    data: {
      labels: ['Normal Traffic', 'Attack Traffic'],
      datasets: [{
        data: [0, 0],
        backgroundColor: [
          'rgba(52,211,153,0.75)',
          'rgba(248,113,113,0.75)',
        ],
        borderColor: [C.green, C.red],
        borderWidth: 2,
        hoverBackgroundColor: [C.green, C.red],
        hoverOffset: 6,
      }],
    },
    options: {
      ...DEFAULT_CHART_OPTIONS,
      cutout: '60%',
      plugins: {
        ...DEFAULT_CHART_OPTIONS.plugins,
        legend: { ...DEFAULT_CHART_OPTIONS.plugins.legend, position: 'bottom' },
        tooltip: {
          ...DEFAULT_CHART_OPTIONS.plugins.tooltip,
          callbacks: {
            label: (ctx) => {
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
              const pct   = total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
              return ` ${ctx.label}: ${ctx.parsed.toLocaleString()} (${pct}%)`;
            },
          },
        },
      },
    },
  });
}


/* ════════════════════════════════════════════════════════════════
   3. BAR CHART — Model Performance Metrics
   ════════════════════════════════════════════════════════════════ */
const barCtx   = document.getElementById('barChart');
let   barChart = null;

const METRIC_COLORS = [C.blue, C.green, C.purple, C.cyan];
const METRIC_LABELS = ['Accuracy', 'Precision', 'Recall', 'F1 Score'];

if (barCtx) {
  barChart = new Chart(barCtx, {
    type: 'bar',
    data: {
      labels: METRIC_LABELS,
      datasets: [{
        label: 'Score (%)',
        data: [99.3, 98.7, 98.4, 98.5],
        backgroundColor: METRIC_COLORS.map(c => c + '33'),
        borderColor: METRIC_COLORS,
        borderWidth: 2,
        borderRadius: 6,
        hoverBackgroundColor: METRIC_COLORS.map(c => c + '66'),
      }],
    },
    options: {
      ...DEFAULT_CHART_OPTIONS,
      indexAxis: 'x',
      scales: {
        x: AXIS_STYLE,
        y: {
          ...AXIS_STYLE,
          min: 90,
          max: 100,
          ticks: {
            ...AXIS_STYLE.ticks,
            callback: (v) => v + '%',
          },
        },
      },
      plugins: {
        ...DEFAULT_CHART_OPTIONS.plugins,
        legend: { display: false },
        tooltip: {
          ...DEFAULT_CHART_OPTIONS.plugins.tooltip,
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y}%`,
          },
        },
      },
    },
  });

  // Render metric progress bars
  renderMetricBars({ Accuracy: 99.3, Precision: 98.7, Recall: 98.4, 'F1 Score': 98.5 });

  // Fetch live metrics from backend
  fetch('/api/model_metrics')
    .then(r => r.json())
    .then(d => {
      if (!d.ok) return;
      const vals = Object.values(d.metrics);
      if (barChart) {
        barChart.data.datasets[0].data = vals;
        barChart.update();
      }
      renderMetricBars(d.metrics);
    })
    .catch(err => console.warn('[barChart] fetch metrics error:', err));
}

function renderMetricBars(metrics) {
  const container = document.getElementById('metricBars');
  if (!container) return;
  const metricColors = { Accuracy: C.blue, Precision: C.green, Recall: C.purple, 'F1 Score': C.cyan };
  container.innerHTML = Object.entries(metrics).map(([key, val]) => `
    <div class="metric-row">
      <div class="metric-label">${key}</div>
      <div class="metric-bar-wrap">
        <div class="metric-fill" style="width:0%; background:${metricColors[key] || C.blue};"
             data-target="${val}" id="mbar-${key.replace(' ','')}"></div>
      </div>
      <div class="metric-value">${val}%</div>
    </div>
  `).join('');

  // Animate bars
  requestAnimationFrame(() => {
    Object.keys(metrics).forEach(key => {
      const bar = document.getElementById(`mbar-${key.replace(' ','')}`);
      if (bar) bar.style.width = ((metrics[key] - 90) / 10 * 100) + '%';
    });
  });
}


/* ════════════════════════════════════════════════════════════════
   HELPERS
   ════════════════════════════════════════════════════════════════ */
function nowTime() {
  return new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function animateValue(el, newVal, suffix = '') {
  if (!el) return;
  const oldVal   = parseInt(el.textContent) || 0;
  const parsed   = parseInt(newVal) || 0;
  if (oldVal === parsed) return;
  el.style.animation = 'none';
  el.textContent = (isNaN(newVal) ? newVal : parsed) + suffix;
  void el.offsetWidth; // trigger reflow
  el.style.animation = 'countUp 0.4s ease';
}

function updateCards(stats) {
  animateValue(document.getElementById('statTotal'),   stats.total   ?? 0);
  animateValue(document.getElementById('statAttacks'), stats.attacks ?? 0);
  animateValue(document.getElementById('statNormals'), stats.normals ?? 0);
  const rate = stats.attack_rate ?? 0;
  const rateEl = document.getElementById('statRate');
  if (rateEl) rateEl.textContent = rate + '%';
}

function updateSimStatus(running) {
  const dot       = document.getElementById('simDot');
  const statusTxt = document.getElementById('simStatusText');
  const btnStart  = document.getElementById('btnStart');
  const btnStop   = document.getElementById('btnStop');

  if (dot) {
    dot.className = 'status-dot ' + (running ? 'running' : 'stopped');
  }
  if (statusTxt) {
    statusTxt.textContent = running ? 'RUNNING' : 'STOPPED';
    statusTxt.style.color = running ? 'var(--green)' : 'var(--text-muted)';
  }
  if (btnStart) btnStart.style.display = running ? 'none' : 'inline-flex';
  if (btnStop)  btnStop.style.display  = running ? 'inline-flex' : 'none';
}

let prevNormals = 0, prevAttacks = 0;

function pushLinePoint(normals, attacks) {
  if (!trafficChart) return;
  trafficChart.data.labels.push(nowTime());
  trafficChart.data.datasets[0].data.push(normals);
  trafficChart.data.datasets[1].data.push(attacks);
  if (trafficChart.data.labels.length > MAX_POINTS) {
    trafficChart.data.labels.shift();
    trafficChart.data.datasets[0].data.shift();
    trafficChart.data.datasets[1].data.shift();
  }
  trafficChart.update('none');
}

function updatePieChart(normals, attacks) {
  if (!pieChart) return;
  pieChart.data.datasets[0].data = [normals, attacks];
  pieChart.update();
}

function updateTable(recent) {
  const tbody = document.getElementById('tbodyRecent');
  if (!tbody || !recent || recent.length === 0) return;
  tbody.innerHTML = recent.map(log => {
    const isAttack   = log.prediction === 'Attack';
    const rowClass   = isAttack ? 'row-attack' : 'row-normal';
    const badgeClass = isAttack ? 'badge-attack' : 'badge-normal';
    const icon       = isAttack ? '⚠' : '✔';
    const conf       = (log.confidence_score * 100).toFixed(2);
    const fillClass  = isAttack ? 'attack' : 'normal';
    return `
      <tr class="${rowClass}">
        <td class="id-cell">${log.id}</td>
        <td class="ts-cell">${log.timestamp}</td>
        <td class="ip-cell">${log.source_ip}</td>
        <td><span class="badge ${badgeClass}">${icon} ${log.prediction}</span></td>
        <td>
          <div class="conf-bar-wrap">
            <div class="conf-bar">
              <div class="conf-fill ${fillClass}" style="width:${conf}%"></div>
            </div>
            <span class="conf-text">${conf}%</span>
          </div>
        </td>
      </tr>`;
  }).join('');
}

/* ── Toast helper ────────────────────────────────────────────── */
function showToast(msg, type = 'success') {
  const toast = document.getElementById('toast');
  const icon  = document.getElementById('toastIcon');
  const text  = document.getElementById('toastMsg');
  if (!toast) return;
  icon.textContent  = type === 'success' ? '✅' : '❌';
  text.textContent  = msg;
  toast.className   = `toast show toast-${type}`;
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => { toast.className = 'toast'; }, 3000);
}


/* ════════════════════════════════════════════════════════════════
   SSE — Server-Sent Events
   ════════════════════════════════════════════════════════════════ */
function connectSSE() {
  const evtSrc = new EventSource('/api/stream');

  evtSrc.onmessage = (e) => {
    try {
      const data   = JSON.parse(e.data);
      if (data.error) { console.warn('[SSE] error:', data.error); return; }

      const stats  = data.stats    || {};
      const recent = data.recent   || [];
      const simSt  = data.sim_stats || {};

      updateCards(stats);
      updateTable(recent);
      updateSimStatus(!!simSt.running);

      const newN = stats.normals ?? 0;
      const newA = stats.attacks ?? 0;

      // Push to line chart only when data changes
      if (newN !== prevNormals || newA !== prevAttacks) {
        pushLinePoint(newN, newA);
        updatePieChart(newN, newA);
        prevNormals = newN;
        prevAttacks = newA;
      }
    } catch (err) {
      console.error('[SSE] parse error:', err);
    }
  };

  evtSrc.onerror = () => {
    console.warn('[SSE] Connection lost. Retrying in 5 s…');
    evtSrc.close();
    setTimeout(connectSSE, 5000);
  };
}

connectSSE();


/* ════════════════════════════════════════════════════════════════
   Simulation Controls
   ════════════════════════════════════════════════════════════════ */
function startSim() {
  fetch('/api/start_simulation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chunk_size: 50, delay_seconds: 1.5 }),
  })
    .then(r => r.json())
    .then(d => {
      if (d.ok) {
        showToast('▶ Simulation started successfully', 'success');
      } else {
        showToast('⚠ ' + (d.message || d.error || 'Failed'), 'error');
      }
    })
    .catch(err => {
      console.error('[startSim]', err);
      showToast('Network error — could not start simulation', 'error');
    });
}

function stopSim() {
  fetch('/api/stop_simulation', { method: 'POST' })
    .then(r => r.json())
    .then(d => {
      if (d.ok) {
        showToast('⏹ Simulation stopped', 'success');
      } else {
        showToast('⚠ ' + (d.message || d.error || 'Failed'), 'error');
      }
    })
    .catch(err => {
      console.error('[stopSim]', err);
      showToast('Network error — could not stop simulation', 'error');
    });
}
