/**
 * FINAL DASHBOARD.JS (ANIMATION + WORKING FIX)
 */

let prevNormals = 0;
let prevAttacks = 0;

/* ---------------- TIME ---------------- */
function nowTime() {
  return new Date().toLocaleTimeString();
}

/* ---------------- ANIMATION ---------------- */
function animateValue(el, newVal, suffix = "") {
  if (!el) return;

  const oldVal = parseInt(el.textContent) || 0;
  const newNum = parseInt(newVal) || 0;

  if (oldVal === newNum) return;

  el.style.animation = "none";
  el.textContent = newNum + suffix;
  void el.offsetWidth;
  el.style.animation = "countUp 0.4s ease";
}

/* ---------------- UPDATE CARDS ---------------- */
function updateCards(stats) {
  animateValue(document.getElementById("statTotal"), stats.total);
  animateValue(document.getElementById("statAttacks"), stats.attacks);
  animateValue(document.getElementById("statNormals"), stats.normals);

  const rateEl = document.getElementById("statRate");
  if (rateEl) rateEl.textContent = stats.attack_rate + "%";
}

/* ---------------- STATUS ---------------- */
function updateSimStatus(running) {
  const status = document.getElementById("simStatusText");
  const startBtn = document.getElementById("btnStart");
  const stopBtn = document.getElementById("btnStop");

  if (running) {
    status.innerText = "RUNNING";
    status.style.color = "#22c55e";
    startBtn.style.display = "none";
    stopBtn.style.display = "inline-block";
  } else {
    status.innerText = "STOPPED";
    status.style.color = "#94a3b8";
    startBtn.style.display = "inline-block";
    stopBtn.style.display = "none";
  }
}

/* ---------------- LINE CHART ---------------- */
function pushLinePoint(normals, attacks) {
  if (!window.trafficChart) return;

  trafficChart.data.labels.push(nowTime());
  trafficChart.data.datasets[0].data.push(normals);
  trafficChart.data.datasets[1].data.push(attacks);

  if (trafficChart.data.labels.length > 20) {
    trafficChart.data.labels.shift();
    trafficChart.data.datasets[0].data.shift();
    trafficChart.data.datasets[1].data.shift();
  }

  trafficChart.update("none");
}

/* ---------------- PIE CHART ---------------- */
function updatePieChart(normals, attacks) {
  if (!window.pieChart) return;

  pieChart.data.datasets[0].data = [normals, attacks];
  pieChart.update();
}

/* ---------------- TABLE ---------------- */
function updateTable(recent) {
  const tbody = document.getElementById("tbodyRecent");
  if (!tbody) return;

  tbody.innerHTML = (recent || []).map(log => {
    const conf = (log.confidence_score * 100).toFixed(2);
    return `
      <tr>
        <td>${log.id}</td>
        <td>${log.timestamp}</td>
        <td>${log.source_ip}</td>
        <td>${log.prediction}</td>
        <td>${conf}%</td>
      </tr>`;
  }).join("");
}

/* ---------------- TOAST ---------------- */
function showToast(msg) {
  console.log(msg);
}

/* ---------------- MAIN POLLING ---------------- */
setInterval(async () => {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();

    const stats = data.stats || {};
    const recent = data.recent || [];

    const processed = stats.processed || 0;
    const attacks = stats.attacks || 0;
    const normals = stats.normals || 0;

    const attackRate = processed > 0
      ? ((attacks / processed) * 100).toFixed(1)
      : 0;

    updateCards({
      total: processed,
      attacks: attacks,
      normals: normals,
      attack_rate: attackRate
    });

    updateTable(recent);

    updateSimStatus(data.sim?.running);

    if (normals !== prevNormals || attacks !== prevAttacks) {
      pushLinePoint(normals, attacks);
      updatePieChart(normals, attacks);

      prevNormals = normals;
      prevAttacks = attacks;
    }

  } catch (err) {
    console.log("Polling error:", err);
  }
}, 1000);

/* ---------------- START ---------------- */
function startSim() {
  fetch("/api/start_simulation", { method: "POST" })
    .then(res => res.json())
    .then(d => {
      if (d.ok) {
        showToast("▶ Simulation Started");
        updateSimStatus(true);
      }
    });
}

/* ---------------- STOP ---------------- */
function stopSim() {
  fetch("/api/stop_simulation", { method: "POST" })
    .then(res => res.json())
    .then(d => {
      if (d.ok) {
        showToast("⏹ Simulation Stopped");
        updateSimStatus(false);
      }
    });
}
