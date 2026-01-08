const API = "http://127.0.0.1:5000";

// Normal ranges and display bounds for visualization
const NORMAL_RANGES = {
  EGT: { min: 400, max: 750, minPossible: 200, maxPossible: 900 },
  RPM: { min: 2000, max: 8500, minPossible: 0, maxPossible: 10000 },
  Vibration: { min: 0, max: 3, minPossible: 0, maxPossible: 10 },
  OilTemp: { min: 40, max: 90, minPossible: -20, maxPossible: 150 },
  OilPressure: { min: 20, max: 80, minPossible: 0, maxPossible: 200 },
  FuelFlow: { min: 200, max: 800, minPossible: 0, maxPossible: 2000 },
  Throttle: { min: 0.2, max: 0.9, minPossible: 0, maxPossible: 1 }
};

function renderRangeVisualization(paramName, value) {
  const container = document.getElementById('rangeViz');
  container.innerHTML = '';
  const cfg = NORMAL_RANGES[paramName];
  if (!cfg) {
    container.innerHTML = `<div>No normal-range data for ${paramName}</div>`;
    return;
  }

  const minP = cfg.minPossible;
  const maxP = cfg.maxPossible;
  const leftPct = Math.max(0, Math.min(100, ((cfg.min - minP) / (maxP - minP)) * 100));
  const widthPct = Math.max(0, Math.min(100, ((cfg.max - cfg.min) / (maxP - minP)) * 100));
  const valuePct = Math.max(0, Math.min(100, ((value - minP) / (maxP - minP)) * 100));

  const wrapper = document.createElement('div');
  wrapper.style.position = 'relative';
  wrapper.style.height = '36px';
  wrapper.style.border = '1px solid #e5e7eb';
  wrapper.style.borderRadius = '6px';
  wrapper.style.background = '#f9fafb';
  wrapper.style.overflow = 'hidden';
  wrapper.style.marginTop = '6px';

  const normalRange = document.createElement('div');
  normalRange.style.position = 'absolute';
  normalRange.style.left = leftPct + '%';
  normalRange.style.width = widthPct + '%';
  normalRange.style.top = '0';
  normalRange.style.bottom = '0';
  normalRange.style.background = '#10b98122';
  normalRange.style.borderLeft = '3px solid #10b98144';
  normalRange.style.borderRight = '3px solid #10b98144';

  const marker = document.createElement('div');
  marker.style.position = 'absolute';
  marker.style.left = valuePct + '%';
  marker.style.top = '-6px';
  marker.style.transform = 'translateX(-50%)';
  marker.style.width = '2px';
  marker.style.height = '48px';
  marker.style.background = '#ef4444';

  const label = document.createElement('div');
  label.style.position = 'absolute';
  label.style.left = valuePct + '%';
  label.style.top = '40px';
  label.style.transform = 'translateX(-50%)';
  label.style.fontSize = '12px';
  label.style.color = '#111827';
  label.textContent = `${paramName}: ${value}`;

  const legend = document.createElement('div');
  legend.style.marginTop = '8px';
  legend.innerHTML = `<small>Normal range: ${cfg.min} — ${cfg.max} (scale ${minP} — ${maxP})</small>`;

  wrapper.appendChild(normalRange);
  wrapper.appendChild(marker);
  container.appendChild(wrapper);
  container.appendChild(label);
  container.appendChild(legend);
}

// Multi-parameter Chart.js horizontal bar chart
let paramChart = null;
function renderMultiParamChart(params) {
  // params: { label: { value, cfg } }
  const labels = Object.keys(params);
  const normalData = [];
  const valueData = [];
  // normalize to 0-100 based on minPossible..maxPossible
  labels.forEach(k => {
    const { value, cfg } = params[k];
    const minP = cfg.minPossible;
    const maxP = cfg.maxPossible;
    const normMin = 0;
    const normMax = 100;
    const a = ((cfg.min - minP) / (maxP - minP)) * 100;
    const b = ((cfg.max - minP) / (maxP - minP)) * 100;
    normalData.push([a, b]);
    const v = Math.max(minP, Math.min(maxP, value));
    const vn = ((v - minP) / (maxP - minP)) * 100;
    valueData.push(vn);
  });

  const ctx = document.getElementById('paramChart').getContext('2d');
  if (paramChart) {
    try { paramChart.destroy(); } catch (e) { /* ignore */ }
  }

  paramChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Normal Range',
          data: normalData,
          backgroundColor: 'rgba(16,185,129,0.25)',
          borderColor: 'rgba(16,185,129,0.6)',
          borderWidth: 1
        },
        {
          label: 'Value',
          data: valueData,
          backgroundColor: 'rgba(59,130,246,0.85)'
        }
      ]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      scales: {
        x: {
          min: 0,
          max: 100,
          ticks: {
            callback: function(val) { return val + '%'; }
          }
        }
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: function(ctx) {
              const ds = ctx.dataset;
              if (ds.label === 'Normal Range') {
                const val = ds.data[ctx.dataIndex];
                // val is [a,b]
                const idx = ctx.dataIndex;
                const lbl = labels[idx];
                const cfg = params[lbl].cfg;
                return `Normal: ${cfg.min} — ${cfg.max}`;
              } else {
                const idx = ctx.dataIndex;
                const lbl = labels[idx];
                const v = params[lbl].value;
                return `Value: ${v}`;
              }
            }
          }
        }
      }
    }
  });
}
// Helper for POST with JSON and credentials
async function postJSON(path, data) {
  try {
    const res = await fetch(API + path, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    let j = null;
    try { j = await res.json(); } catch (e) { j = null; }
    if (!res.ok) {
      console.error('postJSON non-ok response', res.status, j);
      throw j || new Error('Request failed with status ' + res.status);
    }
    return j;
  } catch (err) {
    console.error('postJSON error', err);
    throw err;
  }
}

// small toast helper
function showToast(text, timeout = 2500) {
  const t = document.createElement('div');
  t.className = 'toast';
  t.innerText = text;
  document.body.appendChild(t);
  setTimeout(() => { t.remove(); }, timeout);
}

function markInvalid(el) {
  if (el) el.classList.add('invalid');
}

function clearInvalid(el) {
  if (el) el.classList.remove('invalid');
}

// REGISTER
const registerBtn = document.getElementById("registerBtn");
if (registerBtn) {
  registerBtn.addEventListener("click", async () => {
    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const confirm = (document.getElementById("confirm_password") && document.getElementById("confirm_password").value) || '';
    const msg = document.getElementById("msg");
    msg.textContent = "";

    // clear previous invalid state
    ["username","email","password"].forEach(id => clearInvalid(document.getElementById(id)));

    if (!username || !email || !password) {
      msg.style.color = "red";
      msg.textContent = "⚠️ All fields are required";
      if (!username) markInvalid(document.getElementById('username'));
      if (!email) markInvalid(document.getElementById('email'));
      if (!password) markInvalid(document.getElementById('password'));
      if (!confirm) markInvalid(document.getElementById('confirm_password'));
      showToast('Please fill all required fields');
      return;
    }

    // basic email validation
    const emailRe = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
    if (!emailRe.test(email)) {
      msg.style.color = "red";
      msg.textContent = "⚠️ Invalid email format";
      markInvalid(document.getElementById('email'));
      showToast('Invalid email format');
      return;
    }

    if (password.length < 6) {
      msg.style.color = "red";
      msg.textContent = "⚠️ Password must be at least 6 characters";
      markInvalid(document.getElementById('password'));
      showToast('Password too short');
      return;
    }

    if (confirm !== password) {
      msg.style.color = "red";
      msg.textContent = "⚠️ Passwords do not match";
      markInvalid(document.getElementById('password'));
      markInvalid(document.getElementById('confirm_password'));
      showToast('Passwords do not match');
      return;
    }

    try {
      const r = await postJSON('/register', { username, email, password });
      if (r && r.status === "ok") {
        msg.style.color = "green";
        msg.textContent = "✓ Registered successfully!";
        showToast('Registered successfully');
        setTimeout(() => { window.location.href = 'login.html'; }, 1200);
      } else {
        console.error('Register response', r);
        msg.style.color = "red";
        msg.textContent = "❌ " + (r && (r.error || r.message) || "Registration failed");
        showToast((r && (r.error || r.message)) || 'Registration failed');
      }
    } catch (e) {
      console.error('Register request failed', e);
      msg.style.color = "red";
      msg.textContent = "❌ Request failed: " + (e && (e.error || e.message) || JSON.stringify(e));
      showToast('Registration request failed');
    }
  });
}

// LOGIN
const loginBtn = document.getElementById("loginBtn");
if (loginBtn) {
  loginBtn.addEventListener("click", async () => {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const msg = document.getElementById("msg");
    msg.textContent = "";

    if (!username || !password) {
      msg.style.color = "red";
      msg.textContent = "⚠️ Username and password required";
      if (!username) markInvalid(document.getElementById('username'));
      if (!password) markInvalid(document.getElementById('password'));
      showToast('Please enter username and password');
      return;
    }

    try {
      const r = await postJSON('/login', { username, password });
      if (r && r.status === "ok") {
        msg.style.color = "green";
        msg.textContent = "✓ Login successful!";
        showToast('Login successful');
        setTimeout(() => { window.location.href = 'home.html'; }, 800);
      } else {
        console.error('Login response', r);
        msg.style.color = "red";
        msg.textContent = "❌ " + (r && (r.error || r.message) || "Login failed");
        showToast((r && (r.error || r.message)) || 'Login failed');
      }
    } catch (e) {
      console.error('Login request failed', e);
      msg.style.color = "red";
      msg.textContent = "❌ Request failed: " + (e && (e.error || e.message) || JSON.stringify(e));
      showToast('Login request failed');
    }
  });
}

// LOGOUT link
const logoutLink = document.getElementById("logoutLink");
if (logoutLink) {
  logoutLink.addEventListener("click", async (e) => {
    e.preventDefault();
    await postJSON('/logout', {});
    window.location.href = 'login.html';
  });
}

// DASHBOARD logic
if (document.getElementById('rpmChart')) {
  const ctxRpm = document.getElementById('rpmChart').getContext('2d');
  const ctxEgt = document.getElementById('egtChart').getContext('2d');
  const ctxFuel = document.getElementById('fuelChart').getContext('2d');
  const ctxVib = document.getElementById('vibChart').getContext('2d');
  const ctxOil = document.getElementById('oilChart').getContext('2d');
  const ctxOilP = document.getElementById('oilPChart').getContext('2d');
  const rpmData = {
    labels: [],
    datasets: [{
      label: 'RPM (rotations/min)',
      borderColor: '#1d4ed8',
      backgroundColor: 'rgba(29, 78, 216, 0.1)',
      data: [],
      tension: 0.4,
      fill: true
    }]
  };
  const egtData = {
    labels: [],
    datasets: [{
      label: 'EGT (°C)',
      borderColor: '#e67e22',
      backgroundColor: 'rgba(230, 126, 34, 0.1)',
      data: [],
      tension: 0.4,
      fill: true
    }]
  };

  const rpmChart = new Chart(ctxRpm, {
    type: 'line',
    data: rpmData,
    options: {
      responsive: true,
      animation: false,
      plugins: {
        annotation: {
          drawTime: 'beforeDatasetsDraw',
          annotations: {
            min: { type: 'line', yMin: 2000, yMax: 2000, borderColor: '#4ade80', borderWidth: 2, label: { content: ['Min: 2000'] } },
            max: { type: 'line', yMin: 8500, yMax: 8500, borderColor: '#4ade80', borderWidth: 2, label: { content: ['Max: 8500'] } }
          }
        }
      },
      scales: {
        y: { beginAtZero: false, min: 1500, max: 9500 }
      }
    }
  });

  const egtChart = new Chart(ctxEgt, {
    type: 'line',
    data: egtData,
    options: {
      responsive: true,
      animation: false,
      scales: {
        y: { beginAtZero: false }
      }
    }
  });

  const fuelData = { labels: [], datasets: [{ label: 'Fuel Flow', borderColor: '#059669', backgroundColor: 'rgba(5,150,105,0.08)', data: [], tension: 0.3, fill: true }] };
  const fuelChart = new Chart(ctxFuel, { type: 'line', data: fuelData, options: { responsive: true, animation: false } });

  const vibData = { labels: [], datasets: [{ label: 'Vibration', borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.08)', data: [], tension: 0.3, fill: true }] };
  const vibChart = new Chart(ctxVib, { type: 'line', data: vibData, options: { responsive: true, animation: false } });

  const oilData = { labels: [], datasets: [{ label: 'Oil Temp (°C)', borderColor: '#f97316', backgroundColor: 'rgba(249,115,22,0.06)', data: [], tension: 0.3, fill: true }] };
  const oilChart = new Chart(ctxOil, { type: 'line', data: oilData, options: { responsive: true, animation: false } });

  const oilPData = { labels: [], datasets: [{ label: 'Oil Pressure', borderColor: '#06b6d4', backgroundColor: 'rgba(6,182,212,0.06)', data: [], tension: 0.3, fill: true }] };
  const oilPChart = new Chart(ctxOilP, { type: 'line', data: oilPData, options: { responsive: true, animation: false } });

  const alertBox = document.getElementById('alert');

  async function poll() {
    try {
      const res = await fetch(API + '/sensor/latest', { credentials: 'include' });
      if (res.status === 401) {
        window.location.href = 'login.html';
        return;
      }
      const j = await res.json();
      if (j.error) {
        console.error("Poll error:", j.error);
        return;
      }

      const s = j.sample;
      const time = new Date(s.Timestamp).toLocaleTimeString();

      // push data
      rpmData.labels.push(time); rpmData.datasets[0].data.push(s.RPM);
      egtData.labels.push(time); egtData.datasets[0].data.push(s.EGT);
      fuelData.labels.push(time); fuelData.datasets[0].data.push(s.FuelFlow);
      vibData.labels.push(time); vibData.datasets[0].data.push(s.Vibration);
      oilData.labels.push(time); oilData.datasets[0].data.push(s.OilTemp);
      oilPData.labels.push(time); oilPData.datasets[0].data.push(s.OilPressure);

      // keep only last 40 points for smoother charts
      const MAX = 40;
      [rpmData, egtData, fuelData, vibData, oilData, oilPData].forEach(d => {
        while (d.labels.length > MAX) { d.labels.shift(); d.datasets[0].data.shift(); }
      });

      rpmChart.update(); egtChart.update(); fuelChart.update(); vibChart.update();
      oilChart.update(); oilPChart.update();

      // show alert if anomaly
      if (j.prediction && j.prediction !== 'NORMAL') {
        let probText = '';
        if (j.probabilities) {
          probText = Object.entries(j.probabilities)
            .map(([k, v]) => `${k}: ${(v * 100).toFixed(1)}%`)
            .join(' | ');
        }
        alertBox.innerHTML = `<div style="padding:12px; border-radius:6px; background:#fee2e2; border-left:4px solid #dc2626;">
          <strong style="color:#dc2626">🚨 ENGINE ALERT: ${j.prediction}</strong><br>
          ${probText}
        </div>`;
      } else {
        alertBox.innerHTML = '';
      }
    } catch (e) {
      console.error("Poll error:", e);
    }
  }

  // Poll every 60 seconds (1 minute) for data updates
  poll();
  setInterval(poll, 60000);
}

// PREDICTION page
const predictBtn = document.getElementById('predictBtn');
if (predictBtn) {
  predictBtn.addEventListener('click', async () => {
    console.log('Predict button clicked');
    const Phase = document.getElementById('Phase').value;
    const Throttle = parseFloat(document.getElementById('Throttle').value);
    const RPM = parseFloat(document.getElementById('RPM').value);
    const FuelFlow = parseFloat(document.getElementById('FuelFlow').value);
    const EGT = parseFloat(document.getElementById('EGT').value);
    const OilTemp = parseFloat(document.getElementById('OilTemp').value);
    const OilPressure = parseFloat(document.getElementById('OilPressure').value);
    const Vibration = parseFloat(document.getElementById('Vibration').value);

    const payload = { Phase, Throttle, RPM, FuelFlow, EGT, OilTemp, OilPressure, Vibration };
    let res = null;
    try {
      console.log('Sending /predict payload', payload);
      res = await postJSON('/predict', payload);
      console.log('/predict response', res);
    } catch (e) {
      console.error('Predict request failed', e);
      const out = document.getElementById('predictionResult');
      out.innerHTML = `<div style="margin-top:20px; color:#dc2626; padding:12px; background:#fee2e2; border-radius:6px;">❌ Request failed: ${e && (e.error || e.message || JSON.stringify(e))}</div>`;
      return;
    }
    const out = document.getElementById('predictionResult');

    if (res.prediction) {
      let probText = '';
      if (res.probabilities) {
        probText = Object.entries(res.probabilities)
          .map(([k, v]) => `<div>${k}: <strong>${(v * 100).toFixed(2)}%</strong></div>`)
          .join('');
      }

      const statusColor = res.prediction === 'NORMAL' ? '#10b981' : (res.prediction === 'WARNING' ? '#f59e0b' : '#dc2626');
      const statusIcon = res.prediction === 'NORMAL' ? '✓' : (res.prediction === 'WARNING' ? '⚠️' : '🚨');

      out.innerHTML = `<div id="predictionCard" style="margin-top:20px; padding:16px; border-radius:6px; background:${statusColor}20; border-left:4px solid ${statusColor};">
        <h3 style="color:${statusColor}; margin-top:0;">${statusIcon} Prediction: ${res.prediction}</h3>
        <div style="color:#333;">${probText}</div>
      </div>`;

      // determine which parameter deviates the most from its normal range
      const params = { Throttle, RPM, FuelFlow, EGT, OilTemp, OilPressure, Vibration };
      let worst = { name: null, score: 0 };
      Object.entries(params).forEach(([k, v]) => {
        const cfg = NORMAL_RANGES[k];
        if (!cfg) return;
        let score = 0;
        if (v < cfg.min) score = (cfg.min - v) / (cfg.maxPossible - cfg.minPossible);
        else if (v > cfg.max) score = (v - cfg.max) / (cfg.maxPossible - cfg.minPossible);
        if (score > worst.score) worst = { name: k, score, value: v };
      });

      // show chart for all parameters
      const paramsForChart = {};
      ['Throttle','RPM','FuelFlow','EGT','OilTemp','OilPressure','Vibration'].forEach(k => {
        const val = { Throttle, RPM, FuelFlow, EGT, OilTemp, OilPressure, Vibration }[k];
        const cfg = NORMAL_RANGES[k] || { min: 0, max: 1, minPossible: 0, maxPossible: 1 };
        paramsForChart[k] = { value: val, cfg };
      });
      document.getElementById('rangeVizContainer').style.display = 'block';
      renderMultiParamChart(paramsForChart);

      // show download button (right aligned)
      const downloadBtn = document.getElementById('downloadReportBtn');
      downloadBtn.style.display = 'inline-block';
      if (!downloadBtn._attached) {
        downloadBtn.addEventListener('click', async () => {
          const node = document.querySelector('.card.login-card');
          try {
            // hide button while capturing
            downloadBtn.style.visibility = 'hidden';
            const canvas = await html2canvas(node, { scale: 2, backgroundColor: '#ffffff', useCORS: true });
            downloadBtn.style.visibility = '';

            const imgData = canvas.toDataURL('image/png');
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF({ unit: 'mm', format: 'a4' });
            const pageWidth = doc.internal.pageSize.getWidth();
            const pageHeight = doc.internal.pageSize.getHeight();
            const margin = 10; // mm
            const pdfWidth = pageWidth - margin * 2;
            const pdfHeight = pageHeight - margin * 2;

            // canvas dimensions
            const imgWidthPx = canvas.width;
            const imgHeightPx = canvas.height;
            const ratio = pdfWidth / imgWidthPx; // scale factor from px to PDF mm units
            const renderedImgHeight = imgHeightPx * ratio;

            // single page
            if (renderedImgHeight <= pdfHeight) {
              doc.addImage(imgData, 'PNG', margin, margin, pdfWidth, renderedImgHeight);
              doc.save('prediction_report.pdf');
              return;
            }

            // multi-page: slice canvas vertically
            const pageCanvasHeightPx = Math.floor(pdfHeight / ratio);
            let remainingHeight = imgHeightPx;
            let offsetY = 0;
            while (remainingHeight > 0) {
              const sliceHeight = Math.min(pageCanvasHeightPx, remainingHeight);
              const tmpCanvas = document.createElement('canvas');
              tmpCanvas.width = imgWidthPx;
              tmpCanvas.height = sliceHeight;
              const tCtx = tmpCanvas.getContext('2d');
              tCtx.fillStyle = '#ffffff';
              tCtx.fillRect(0, 0, tmpCanvas.width, tmpCanvas.height);
              tCtx.drawImage(canvas, 0, offsetY, imgWidthPx, sliceHeight, 0, 0, imgWidthPx, sliceHeight);

              const tmpImg = tmpCanvas.toDataURL('image/png');
              const tmpImgRenderedHeight = sliceHeight * ratio;
              doc.addImage(tmpImg, 'PNG', margin, margin, pdfWidth, tmpImgRenderedHeight);

              remainingHeight -= sliceHeight;
              offsetY += sliceHeight;
              if (remainingHeight > 0) doc.addPage();
            }

            doc.save('prediction_report.pdf');
          } catch (e) {
            downloadBtn.style.visibility = '';
            showToast('Failed to generate PDF: ' + (e && e.message));
            console.error(e);
          }
        });
        downloadBtn._attached = true;
      }
    } else {
      out.innerHTML = `<div style="margin-top:20px; color:#dc2626; padding:12px; background:#fee2e2; border-radius:6px;">
        ❌ Error: ${res.error || JSON.stringify(res)}
      </div>`;
    }
  });
}
