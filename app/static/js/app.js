const API_URL = "/ticket";
const HISTORY_URL = "/tickets/history";
const ALERTS_URL = "/tickets/alerts";

const CATEGORY_LABELS = {
  "donanım": "Donanım",
  "yazılım": "Yazılım",
  "ağ": "Ağ",
  "erişim": "Erişim",
};

const CATEGORY_SLUGS = {
  "donanım": "hardware",
  "yazılım": "software",
  "ağ": "network",
  "erişim": "access",
};

const PRIORITY_SLUGS = {
  "yüksek": "high",
  "orta": "medium",
  "düşük": "low",
};

const STEP_LABELS = [
  "Kategori tespiti",
  "Öncelik belirleme",
  "Benzer ticket araması (RAG)",
  "Ekip ataması",
];

// Ziyaretçi ne yazacağını düşünmesin: tek tıkla doldurulan örnekler.
const SAMPLE_TICKETS = [
  { label: "VPN kopuyor", text: "VPN bağlantısı sürekli kopuyor, uzaktan çalışamıyorum" },
  { label: "Laptop açılmıyor", text: "Laptopum açılmıyor, güç ışığı hiç yanmıyor" },
  { label: "Excel çöküyor", text: "Büyük bir Excel dosyasını açarken uygulama kapanıyor" },
  { label: "Şifre / hesap", text: "Şifremi unuttum, hesabıma giremiyorum" },
  { label: "Üretim durdu", text: "Üretim sunucusuna kimse erişemiyor, tüm ekip çalışamıyor" },
  { label: "EN örnek", text: "My VPN keeps disconnecting every few minutes while working from home" },
];

let stepTimer = null;
let categoryChart = null;
let priorityChart = null;
let currentTicketId = null;

// --- Tabs -------------------------------------------------------------

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

function switchTab(tab) {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tab);
  });
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("active", view.id === `view-${tab}`);
  });
  if (tab === "dashboard") {
    refreshDashboard();
  }
}

// --- Steps timeline -----------------------------------------------------

function startSteps() {
  const stepsEl = document.getElementById("steps");
  stepsEl.innerHTML = STEP_LABELS.map(
    (label, index) => `
      <li class="step" data-step="${index}">
        <span class="step-marker"></span>
        <span class="step-label">${label}</span>
      </li>
    `
  ).join("");

  let current = 0;
  setStepState(0, "active");

  clearInterval(stepTimer);
  stepTimer = setInterval(() => {
    setStepState(current, "done");
    current = Math.min(current + 1, STEP_LABELS.length - 1);
    setStepState(current, "active");
  }, 700);
}

function setStepState(index, state) {
  const el = document.querySelector(`.step[data-step="${index}"]`);
  if (!el) return;
  el.classList.remove("active", "done", "error");
  el.classList.add(state);
}

function finishSteps(result) {
  clearInterval(stepTimer);
  const stepEls = document.querySelectorAll(".step");
  stepEls.forEach((el) => {
    el.classList.remove("active", "error");
    el.classList.add("done");
  });

  const labels = document.querySelectorAll(".step .step-label");
  if (labels[0]) {
    labels[0].textContent = `Kategori tespiti — ${categoryLabel(result.category)}`;
  }
  if (labels[1]) {
    labels[1].textContent = `Öncelik belirleme — ${result.priority ?? "?"}`;
  }
  if (labels[2]) {
    const count = result.similar_tickets ? result.similar_tickets.length : 0;
    labels[2].textContent = `Benzer ticket araması — ${count} sonuç`;
  }
  if (labels[3]) {
    labels[3].textContent = result.assigned_team
      ? `Ekip ataması — ${result.assigned_team}`
      : "Ekip ataması — atlandı (çözüm önerildi)";
  }
}

function stopStepsWithError() {
  clearInterval(stepTimer);
  const activeEl = document.querySelector(".step.active");
  if (activeEl) {
    activeEl.classList.remove("active");
    activeEl.classList.add("error");
  }
}

// --- Ticket form ----------------------------------------------------------

const form = document.getElementById("ticket-form");
const submitBtn = document.getElementById("submit-btn");
const errorBox = document.getElementById("error");
const resultPanel = document.getElementById("result-panel");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const text = document.getElementById("ticket-text").value.trim();
  if (!text) return;

  errorBox.hidden = true;
  submitBtn.disabled = true;
  startSteps();

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? response.statusText);
      throw new Error(detail);
    }

    const data = await response.json();
    finishSteps(data);
    renderResult(data);
    refreshHistoryTable();
  } catch (err) {
    stopStepsWithError();
    showError(err.message || "Bilinmeyen bir hata oluştu.");
  } finally {
    submitBtn.disabled = false;
  }
});

function showError(message) {
  errorBox.hidden = false;
  errorBox.textContent = `Bir hata oluştu: ${message}`;
}

// --- Rendering result -------------------------------------------------

function categoryLabel(category) {
  return CATEGORY_LABELS[category] ?? category ?? "bilinmiyor";
}

function categorySlug(category) {
  return CATEGORY_SLUGS[category] ?? "unknown";
}

function prioritySlug(priority) {
  return PRIORITY_SLUGS[priority] ?? "unknown";
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

// L2 mesafesini (skor küçük = daha benzer) görsel bir yüzdeye çevirir.
// Kalibre edilmiş bir olasılık değildir, sadece görselleştirme amaçlıdır.
function similarityPercent(score) {
  return Math.round((1 / (1 + Math.max(score, 0))) * 100);
}

function renderResult(data) {
  document.getElementById("badge-category").textContent = categoryLabel(data.category);

  const priorityBadge = document.getElementById("badge-priority");
  priorityBadge.textContent = data.priority ?? "—";
  priorityBadge.className = `badge badge-priority priority-${prioritySlug(data.priority)}`;

  const confidenceChip = document.getElementById("confidence-chip");
  if (data.confidence != null) {
    confidenceChip.hidden = false;
    confidenceChip.textContent = `Güven: %${data.confidence}`;
  } else {
    confidenceChip.hidden = true;
  }

  document.getElementById("solution-text").textContent =
    data.solution || "Belirli bir çözüm metni üretilmedi.";

  const assignedTeamEl = document.getElementById("assigned-team");
  assignedTeamEl.textContent = data.assigned_team ? `Yönlendirilen ekip: ${data.assigned_team}` : "";

  currentTicketId = data.ticket_id ?? null;
  const correctionBox = document.getElementById("correction-box");
  correctionBox.hidden = currentTicketId == null;
  document.getElementById("correction-select").value = "";
  document.getElementById("correction-status").textContent = "";

  const list = document.getElementById("similar-list");
  const tickets = data.similar_tickets || [];

  if (tickets.length === 0) {
    list.innerHTML = `<p class="muted">Benzer geçmiş ticket bulunamadı.</p>`;
  } else {
    list.innerHTML = tickets
      .map((ticket) => {
        const pct = similarityPercent(ticket.score);
        return `
          <div class="similar-card cat-${categorySlug(ticket.category)}">
            <div class="similar-head">
              <span class="similar-title">${escapeHtml(ticket.title)}</span>
              <span class="badge priority-${prioritySlug(ticket.priority)}">${escapeHtml(ticket.priority)}</span>
            </div>
            <p class="similar-solution">${escapeHtml(ticket.solution)}</p>
            <div class="similar-meta">
              <span>${categoryLabel(ticket.category)}</span>
              <span>${escapeHtml(ticket.team)}</span>
            </div>
            <div class="similarity-bar"><div class="similarity-fill" style="width:${pct}%"></div></div>
            <span class="similarity-pct">${pct}% benzer <small>(skor: ${Number(ticket.score).toFixed(3)})</small></span>
          </div>
        `;
      })
      .join("");
  }

  resultPanel.classList.remove("flash");
  void resultPanel.offsetWidth; // reflow'u zorla, animasyonu yeniden başlat
  resultPanel.classList.add("flash");
}

// --- History + dashboard ------------------------------------------------

async function fetchHistory() {
  const response = await fetch(HISTORY_URL);
  if (!response.ok) throw new Error("Ticket geçmişi alınamadı");
  return response.json();
}

async function fetchAlerts() {
  const response = await fetch(ALERTS_URL);
  if (!response.ok) throw new Error("Uyarılar alınamadı");
  return response.json();
}

function renderAlerts(alerts) {
  const container = document.getElementById("alerts-container");

  if (!alerts || alerts.length === 0) {
    container.hidden = true;
    container.innerHTML = "";
    return;
  }

  container.hidden = false;
  container.innerHTML = alerts
    .map(
      (alert) => `
        <div class="alert-banner">
          ⚠ Son ${alert.days} günde ${alert.count} '${categoryLabel(alert.category)}' sorunu — tekrarlayan bir örüntü olabilir.
        </div>
      `
    )
    .join("");
}

function truncate(text, maxLen) {
  if (!text) return "";
  return text.length > maxLen ? `${text.slice(0, maxLen)}…` : text;
}

function formatDate(sqliteUtcTimestamp) {
  // Backend "YYYY-MM-DD HH:MM:SS" (UTC) formatında dönüyor.
  const date = new Date(`${sqliteUtcTimestamp.replace(" ", "T")}Z`);
  if (Number.isNaN(date.getTime())) return sqliteUtcTimestamp;
  return date.toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "short" });
}

function renderHistoryTable(history) {
  const tbody = document.getElementById("history-tbody");

  if (!history || history.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="muted">Henüz ticket gönderilmedi.</td></tr>`;
    return;
  }

  tbody.innerHTML = history
    .map((item) => {
      const correctionText = item.is_corrected
        ? `${categoryLabel(item.corrected_category)} olarak düzeltildi`
        : "—";
      return `
        <tr>
          <td>${formatDate(item.created_at)}</td>
          <td class="history-text" title="${escapeHtml(item.ticket_text)}">${escapeHtml(truncate(item.ticket_text, 60))}</td>
          <td>${categoryLabel(item.category)}</td>
          <td>${item.priority ? `<span class="badge priority-${prioritySlug(item.priority)}">${escapeHtml(item.priority)}</span>` : "—"}</td>
          <td>${escapeHtml(item.assigned_team ?? "—")}</td>
          <td class="${item.is_corrected ? "corrected" : "muted"}">${correctionText}</td>
        </tr>
      `;
    })
    .join("");
}

async function refreshHistoryTable() {
  try {
    renderHistoryTable(await fetchHistory());
  } catch (err) {
    console.error(err);
  }
}

function chartBaseOptions(title) {
  return {
    responsive: true,
    plugins: {
      legend: { labels: { color: "#c9ccd6" } },
      title: { display: true, text: title, color: "#e7e9ee", font: { size: 14, weight: "600" } },
    },
  };
}

async function refreshDashboard() {
  try {
    const [history, alerts] = await Promise.all([fetchHistory(), fetchAlerts()]);
    renderDashboardCharts(history);
    renderAlerts(alerts);
  } catch (err) {
    console.error(err);
  }
}

function renderDashboardCharts(history) {
  const emptyState = document.getElementById("dashboard-empty");
  const chartsWrap = document.getElementById("dashboard-charts");
  const historyCount = document.getElementById("history-count");

  if (!history || history.length === 0) {
    emptyState.hidden = false;
    chartsWrap.hidden = true;
    historyCount.textContent = "";
    return;
  }

  emptyState.hidden = true;
  chartsWrap.hidden = false;
  historyCount.textContent = `${history.length} ticket kaydedildi (backend'deki ticket geçmişi)`;

  const categories = ["donanım", "yazılım", "ağ", "erişim"];
  const categoryCounts = categories.map((c) => history.filter((h) => h.category === c).length);
  const categoryColors = ["#fb923c", "#a78bfa", "#38bdf8", "#34d399"];

  const priorities = ["düşük", "orta", "yüksek"];
  const priorityCounts = priorities.map((p) => history.filter((h) => h.priority === p).length);
  const priorityColors = ["#34d399", "#fbbf24", "#fb7185"];

  if (categoryChart) categoryChart.destroy();
  categoryChart = new Chart(document.getElementById("category-chart"), {
    type: "pie",
    data: {
      labels: categories.map(categoryLabel),
      datasets: [{ data: categoryCounts, backgroundColor: categoryColors, borderColor: "#1d212c", borderWidth: 2 }],
    },
    options: chartBaseOptions("Kategori Dağılımı"),
  });

  if (priorityChart) priorityChart.destroy();
  priorityChart = new Chart(document.getElementById("priority-chart"), {
    type: "bar",
    data: {
      labels: priorities,
      datasets: [{ label: "Ticket sayısı", data: priorityCounts, backgroundColor: priorityColors, borderRadius: 6 }],
    },
    options: {
      ...chartBaseOptions("Öncelik Dağılımı"),
      scales: {
        x: { ticks: { color: "#c9ccd6" }, grid: { color: "rgba(255,255,255,0.06)" } },
        y: { beginAtZero: true, ticks: { color: "#c9ccd6", precision: 0 }, grid: { color: "rgba(255,255,255,0.06)" } },
      },
    },
  });
}

// --- Manual correction ---------------------------------------------------

function populateCorrectionSelect() {
  const select = document.getElementById("correction-select");
  const options = Object.entries(CATEGORY_LABELS)
    .map(([value, label]) => `<option value="${value}">${label}</option>`)
    .join("");
  select.innerHTML = `<option value="" disabled selected>Doğru kategoriyi seç</option>${options}`;
}

document.getElementById("correction-save-btn").addEventListener("click", async () => {
  const select = document.getElementById("correction-select");
  const statusEl = document.getElementById("correction-status");
  const correctedCategory = select.value;

  if (!correctedCategory || currentTicketId == null) return;

  statusEl.textContent = "Kaydediliyor...";
  try {
    const response = await fetch(`/tickets/history/${currentTicketId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ corrected_category: correctedCategory }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(typeof body.detail === "string" ? body.detail : `HTTP ${response.status}`);
    }

    statusEl.textContent = "Düzeltme kaydedildi ✓";
    refreshHistoryTable();
  } catch (err) {
    statusEl.textContent = `Hata: ${err.message}`;
  }
});

// --- Demo helpers ---------------------------------------------------------

function renderSampleChips() {
  const container = document.getElementById("sample-chips");
  const textarea = document.getElementById("ticket-text");

  container.innerHTML = SAMPLE_TICKETS.map(
    (sample, index) =>
      `<button type="button" class="sample-chip" data-index="${index}">${escapeHtml(sample.label)}</button>`
  ).join("");

  container.querySelectorAll(".sample-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      textarea.value = SAMPLE_TICKETS[Number(chip.dataset.index)].text;
      textarea.focus();
    });
  });
}

async function loadModelInfo() {
  const footerEl = document.getElementById("model-info");
  const howtoEl = document.getElementById("howto-model");
  try {
    const response = await fetch("/health");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const info = await response.json();
    const text = `Canlı model: ${info.llm_model} (${info.llm_provider}) · embedding: ${info.embedding_model.split("/").pop()} (${info.embedding_provider})`;
    footerEl.textContent = text;
    howtoEl.textContent = text;
  } catch (err) {
    footerEl.textContent = "canlı model bilgisi alınamadı";
  }
}

// --- Init ---------------------------------------------------------------

populateCorrectionSelect();
renderSampleChips();
loadModelInfo();
refreshHistoryTable();
