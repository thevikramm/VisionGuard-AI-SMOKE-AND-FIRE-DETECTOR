const RING_CIRCUMFERENCE = 326.7;
const DUR_FIRE = parseFloat(document.body.dataset.durFire) || 2;
const DUR_SMOKE = parseFloat(document.body.dataset.durSmoke) || 3;

function setRing(el, ratio) {
  const clamped = Math.max(0, Math.min(1, ratio));
  el.style.strokeDashoffset = RING_CIRCUMFERENCE * (1 - clamped);
}

function updateClock() {
  const now = new Date();
  document.getElementById('clock').textContent = now.toLocaleTimeString('en-GB');
}

function stateLabel(active, ratio) {
  if (ratio >= 1) return { text: 'ALARM', cls: 'alarm' };
  if (active) return { text: 'WATCH', cls: 'watch' };
  return { text: 'CLEAR', cls: '' };
}

async function pollStatus() {
  try {
    const res = await fetch('/api/status');
    const s = await res.json();

    const camDot = document.getElementById('camDot');
    const camText = document.getElementById('camText');
    if (s.camera_connected) {
      camDot.className = 'dot on';
      camText.textContent = 'Camera online';
    } else {
      camDot.className = 'dot off';
      camText.textContent = 'Camera offline';
    }

    const fireRatio = s.fire_duration / DUR_FIRE;
    const smokeRatio = s.smoke_duration / DUR_SMOKE;

    setRing(document.getElementById('fireRing'), fireRatio);
    setRing(document.getElementById('smokeRing'), smokeRatio);

    document.getElementById('fireTime').textContent = s.fire_duration.toFixed(1) + 's';
    document.getElementById('smokeTime').textContent = s.smoke_duration.toFixed(1) + 's';
    document.getElementById('fireConf').textContent = s.fire_confidence.toFixed(2);
    document.getElementById('smokeConf').textContent = s.smoke_confidence.toFixed(2);

    const fs = stateLabel(s.fire_detected, fireRatio);
    const ss = stateLabel(s.smoke_detected, smokeRatio);
    const fireStateEl = document.getElementById('fireState');
    const smokeStateEl = document.getElementById('smokeState');
    fireStateEl.textContent = fs.text;
    fireStateEl.className = 'gauge-state ' + fs.cls;
    smokeStateEl.textContent = ss.text;
    smokeStateEl.className = 'gauge-state ' + ss.cls;
  } catch (e) {
    console.error('status poll failed', e);
  }
}

let lastAlertCount = 0;
async function pollAlerts() {
  try {
    const res = await fetch('/api/alerts');
    const alertsList = await res.json();

    document.getElementById('logCount').textContent = alertsList.length + ' events';

    if (alertsList.length === lastAlertCount) return;
    lastAlertCount = alertsList.length;

    const container = document.getElementById('logList');
    if (alertsList.length === 0) {
      container.innerHTML = '<div class="log-empty">No confirmed events yet. An entry appears here once fire or smoke clears its persistence fuse.</div>';
      return;
    }

    container.innerHTML = alertsList.map(a => `
      <div class="log-row">
        <img class="log-thumb" src="${a.image}" alt="${a.type} detection">
        <div class="log-info">
          <div class="log-type ${a.type}">${a.type.toUpperCase()} CONFIRMED</div>
          <div class="log-ts">${a.timestamp}</div>
        </div>
        <div class="log-conf">conf ${a.confidence}</div>
      </div>
    `).join('');
  } catch (e) {
    console.error('alerts poll failed', e);
  }
}

updateClock();
setInterval(updateClock, 1000);
pollStatus();
pollAlerts();
setInterval(pollStatus, 400);
setInterval(pollAlerts, 2000);
