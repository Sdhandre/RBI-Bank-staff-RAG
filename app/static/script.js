/* ═══════════════════════════════════════════════════════════════════════════
   script.js  —  Bank Staff Assistant  (ChatGPT-style session management)
   ═══════════════════════════════════════════════════════════════════════════ */

"use strict";

// ─── API helpers ─────────────────────────────────────────────────────────────
const API = {
  sessions:        "/sessions",
  session:   (id) => `/sessions/${id}`,
  chat:            "/chat",
  health:          "/health",
};

// ─── App state ────────────────────────────────────────────────────────────────
let currentSessionId = null;   // null = no active session (welcome screen)
let isLoading        = false;
let ctxTargetId      = null;   // session id for right-click context menu

// ─── DOM refs ─────────────────────────────────────────────────────────────────
const chatWindow      = document.getElementById("chatWindow");
const queryInput      = document.getElementById("queryInput");
const sendBtn         = document.getElementById("sendBtn");
const charCounter     = document.getElementById("charCounter");
const sessionsList    = document.getElementById("sessionsList");
const sessionSearch   = document.getElementById("sessionSearch");
const newChatBtn      = document.getElementById("newChatBtn");
const currentTitle    = document.getElementById("currentSessionTitle");
const statusBadge     = document.getElementById("statusBadge");
const statusDot       = document.getElementById("statusDot");
const statusLabel     = document.getElementById("statusLabel");
const toast           = document.getElementById("toast");
const ctxMenu         = document.getElementById("ctxMenu");

// ═══════════════════════════════════════════════════════════════════════════════
// SESSION MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════════

async function loadSessions(searchQuery = "") {
  const url = searchQuery
    ? `${API.sessions}?q=${encodeURIComponent(searchQuery)}`
    : API.sessions;

  try {
    const res      = await fetch(url);
    const sessions = await res.json();
    renderSessionsList(sessions);
    return sessions;
  } catch {
    sessionsList.innerHTML = '<div class="no-sessions">Could not load sessions.</div>';
    return [];
  }
}

function renderSessionsList(sessions) {
  if (!sessions.length) {
    sessionsList.innerHTML = '<div class="no-sessions">No conversations yet</div>';
    return;
  }

  // ── Group by relative date ────────────────────────────────────────────────
  const groups = { "Today": [], "Yesterday": [], "Last 7 Days": [], "Older": [] };
  const now    = new Date();

  for (const s of sessions) {
    const d       = new Date(s.updated_at);
    const dayDiff = Math.floor((now - d) / 86_400_000);
    if      (dayDiff === 0) groups["Today"].push(s);
    else if (dayDiff === 1) groups["Yesterday"].push(s);
    else if (dayDiff <= 7)  groups["Last 7 Days"].push(s);
    else                    groups["Older"].push(s);
  }

  sessionsList.innerHTML = "";

  for (const [label, items] of Object.entries(groups)) {
    if (!items.length) continue;

    const group = document.createElement("div");
    group.className = "session-group";
    group.innerHTML = `<div class="session-group-label">${label}</div>`;

    for (const s of items) {
      group.appendChild(buildSessionItem(s));
    }
    sessionsList.appendChild(group);
  }
}

function buildSessionItem(s) {
  const item = document.createElement("div");
  item.className   = `session-item${s.id === currentSessionId ? " active" : ""}`;
  item.dataset.id  = s.id;
  item.setAttribute("role", "listitem");
  item.setAttribute("title", s.title);

  item.innerHTML = `
    <span class="session-title">${escapeHtml(s.title)}</span>
    <div class="session-actions">
      <button class="session-action-btn" data-action="rename" title="Rename" aria-label="Rename">✏️</button>
      <button class="session-action-btn delete" data-action="delete" title="Delete" aria-label="Delete">🗑️</button>
    </div>`;

  // Click: load session
  item.addEventListener("click", (e) => {
    if (e.target.closest(".session-actions")) return;
    openSession(s.id, s.title);
  });

  // Action buttons
  item.querySelector("[data-action='rename']").addEventListener("click", (e) => {
    e.stopPropagation();
    promptRename(s.id, s.title);
  });
  item.querySelector("[data-action='delete']").addEventListener("click", (e) => {
    e.stopPropagation();
    confirmDelete(s.id);
  });

  return item;
}

function markActive(sid) {
  document.querySelectorAll(".session-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.id === sid);
  });
}

// ─── Open / load a session ────────────────────────────────────────────────────
async function openSession(sid, title = "") {
  currentSessionId = sid;
  if (title) currentTitle.textContent = title;
  markActive(sid);

  chatWindow.innerHTML = "";

  try {
    const res  = await fetch(API.session(sid));
    const data = await res.json();

    currentTitle.textContent = data.session.title;

    if (!data.messages.length) {
      showWelcomeScreen();
      return;
    }

    for (const msg of data.messages) {
      if (msg.role === "user") {
        appendUserMessage(msg.content, msg.created_at);
      } else {
        appendBotMessage(msg.content, msg.sources, msg.created_at);
      }
    }
    scrollToBottom();

  } catch {
    showToast("Failed to load session.", "error");
  }
}

// ─── New Chat ─────────────────────────────────────────────────────────────────
function newChat() {
  currentSessionId = null;
  currentTitle.textContent = "Bank Staff Assistant";
  markActive(null);
  showWelcomeScreen();
  queryInput.focus();
}

// ─── Rename ───────────────────────────────────────────────────────────────────
async function promptRename(sid, currentName) {
  const name = window.prompt("Rename conversation:", currentName);
  if (!name || name.trim() === currentName) return;

  try {
    await fetch(API.session(sid), {
      method:  "PATCH",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ title: name.trim() }),
    });
    if (currentSessionId === sid) currentTitle.textContent = name.trim();
    await loadSessions(sessionSearch.value);
    markActive(currentSessionId);
    showToast("Renamed successfully.", "success");
  } catch {
    showToast("Failed to rename.", "error");
  }
}

// ─── Delete ───────────────────────────────────────────────────────────────────
async function confirmDelete(sid) {
  if (!window.confirm("Delete this conversation? This cannot be undone.")) return;

  try {
    await fetch(API.session(sid), { method: "DELETE" });
    if (currentSessionId === sid) {
      currentSessionId = null;
      currentTitle.textContent = "Bank Staff Assistant";
      showWelcomeScreen();
    }
    await loadSessions(sessionSearch.value);
    markActive(currentSessionId);
    showToast("Conversation deleted.", "success");
  } catch {
    showToast("Failed to delete.", "error");
  }
}


// ═══════════════════════════════════════════════════════════════════════════════
// CHAT
// ═══════════════════════════════════════════════════════════════════════════════

async function sendQuery() {
  if (isLoading) return;

  const query = queryInput.value.trim();
  if (!query) { queryInput.focus(); return; }

  // ── Create session on first message if none open ──────────────────────────
  if (!currentSessionId) {
    try {
      const res  = await fetch(API.sessions, { method: "POST" });
      const data = await res.json();
      currentSessionId = data.id;
    } catch {
      showToast("Could not create session.", "error");
      return;
    }
  }

  // Clear welcome screen
  const ws = chatWindow.querySelector(".welcome-screen");
  if (ws) ws.remove();

  // Render user bubble immediately
  appendUserMessage(query);

  queryInput.value = "";
  charCounter.textContent = "0 / 1000";
  autoResize(queryInput);
  setLoading(true);

  try {
    const provider = document.getElementById("modelSelect").value;
    const res  = await fetch(API.chat, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ query, session_id: currentSessionId, provider }),
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);

    appendBotMessage(data.answer, data.sources || []);

    // Refresh sessions list (auto-title may have updated)
    await loadSessions(sessionSearch.value);
    markActive(currentSessionId);

    // Update top-bar title
    const active = sessionsList.querySelector(".session-item.active .session-title");
    if (active) currentTitle.textContent = active.textContent;

  } catch (err) {
    appendErrorBubble(err.message || "Something went wrong.");
    showToast("Failed to get answer.", "error");
    setOffline();
  } finally {
    setLoading(false);
    queryInput.focus();
  }
}


// ═══════════════════════════════════════════════════════════════════════════════
// DOM BUILDERS
// ═══════════════════════════════════════════════════════════════════════════════

function showWelcomeScreen() {
  chatWindow.innerHTML = `
    <div class="welcome-screen" id="welcomeScreen">
      <div class="welcome-hero">
        <div class="welcome-icon" aria-hidden="true">🏦</div>
        <h1 class="welcome-title">Bank Staff Assistant</h1>
        <p class="welcome-sub">Powered by RBI Document Intelligence</p>
      </div>
      <div class="topic-grid" role="list">

        <div class="topic-card" role="listitem">
          <div class="topic-header"><span class="topic-emoji">📌</span><span class="topic-name">General Policy</span></div>
          <button class="topic-sample" onclick="injectSample(this)">What are the eligibility criteria for joining RBI staff?</button>
          <button class="topic-sample" onclick="injectSample(this)">What are the rules for probation and confirmation of service?</button>
          <button class="topic-sample" onclick="injectSample(this)">What is the retirement age for RBI employees?</button>
        </div>

        <div class="topic-card" role="listitem">
          <div class="topic-header"><span class="topic-emoji">💰</span><span class="topic-name">Salary &amp; Benefits</span></div>
          <button class="topic-sample" onclick="injectSample(this)">How is the pay structure defined for RBI staff?</button>
          <button class="topic-sample" onclick="injectSample(this)">What allowances are provided (housing, travel, medical)?</button>
          <button class="topic-sample" onclick="injectSample(this)">What are the rules for pension and gratuity?</button>
        </div>

        <div class="topic-card" role="listitem">
          <div class="topic-header"><span class="topic-emoji">🕒</span><span class="topic-name">Leave &amp; Working Hours</span></div>
          <button class="topic-sample" onclick="injectSample(this)">How many types of leave are available to RBI staff?</button>
          <button class="topic-sample" onclick="injectSample(this)">What is the maximum duration of earned leave?</button>
          <button class="topic-sample" onclick="injectSample(this)">Are there special provisions for maternity/paternity leave?</button>
        </div>

        <div class="topic-card" role="listitem">
          <div class="topic-header"><span class="topic-emoji">📈</span><span class="topic-name">Promotions &amp; Transfers</span></div>
          <button class="topic-sample" onclick="injectSample(this)">What is the process for staff promotions?</button>
          <button class="topic-sample" onclick="injectSample(this)">How are transfers between branches regulated?</button>
          <button class="topic-sample" onclick="injectSample(this)">What are the criteria for career progression?</button>
        </div>

        <div class="topic-card" role="listitem">
          <div class="topic-header"><span class="topic-emoji">⚖️</span><span class="topic-name">Conduct &amp; Discipline</span></div>
          <button class="topic-sample" onclick="injectSample(this)">What are the rules regarding staff conduct and ethics?</button>
          <button class="topic-sample" onclick="injectSample(this)">What disciplinary actions can be taken for misconduct?</button>
          <button class="topic-sample" onclick="injectSample(this)">How are grievances or appeals handled?</button>
        </div>

        <div class="topic-card" role="listitem">
          <div class="topic-header"><span class="topic-emoji">🏥</span><span class="topic-name">Welfare &amp; Miscellaneous</span></div>
          <button class="topic-sample" onclick="injectSample(this)">schemes available for employees</button>
          <button class="topic-sample" onclick="injectSample(this)">Are there provisions for staff housing or loans?</button>
          <button class="topic-sample" onclick="injectSample(this)">What are the rules for medical reimbursement?</button>
        </div>

      </div>
    </div>`;
}

function appendUserMessage(text, timestamp = null) {
  const ts  = timestamp ? fmtTime(timestamp) : nowTime();
  const div = document.createElement("div");
  div.className = "message user-message";
  div.setAttribute("aria-label", "Your message");
  div.innerHTML = `
    <div class="avatar user-avatar" aria-hidden="true">👤</div>
    <div class="message-body">
      <div class="bubble">${escapeHtml(text)}</div>
      <time class="message-time">${ts}</time>
    </div>`;
  chatWindow.appendChild(div);
  scrollToBottom();
}

function appendBotMessage(answer, sources = [], timestamp = null) {
  const ts  = timestamp ? fmtTime(timestamp) : nowTime();
  const div = document.createElement("div");
  div.className = "message bot-message";
  div.setAttribute("aria-label", "Assistant answer");

  let sourcesHtml = "";
  if (sources.length) {
    const pills = sources.map((s) => {
      const name = (s.source || "Document").split(/[/\\]/).pop();
      const page = s.page ?? "?";
      return `<span class="source-pill" title="${escapeHtml(s.source || "")}">${escapeHtml(name)} — Page ${escapeHtml(String(page))}</span>`;
    }).join("");
    sourcesHtml = `
      <div class="sources-block" aria-label="Source documents">
        <div class="sources-label">📚 Sources</div>
        ${pills}
      </div>`;
  }

  div.innerHTML = `
    <div class="avatar bot-avatar" aria-hidden="true">🤖</div>
    <div class="message-body">
      <div class="bubble">${marked.parse(answer)}</div>
      ${sourcesHtml}
      <time class="message-time">${ts}</time>
    </div>`;
  chatWindow.appendChild(div);
  scrollToBottom();
}

function appendTypingIndicator() {
  const div = document.createElement("div");
  div.className = "message bot-message";
  div.id = "typingIndicator";
  div.setAttribute("aria-label", "Assistant is typing");
  div.innerHTML = `
    <div class="avatar bot-avatar" aria-hidden="true">🤖</div>
    <div class="message-body">
      <div class="bubble typing-bubble">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    </div>`;
  chatWindow.appendChild(div);
  scrollToBottom();
}

function removeTypingIndicator() {
  document.getElementById("typingIndicator")?.remove();
}

function appendErrorBubble(msg) {
  const div = document.createElement("div");
  div.className = "message bot-message";
  div.innerHTML = `
    <div class="avatar bot-avatar" aria-hidden="true">⚠️</div>
    <div class="message-body">
      <div class="bubble" style="border-color:rgba(239,68,68,.4);background:rgba(239,68,68,.07);">
        <p style="color:#fca5a5;">${escapeHtml(msg)}</p>
      </div>
      <time class="message-time">${nowTime()}</time>
    </div>`;
  chatWindow.appendChild(div);
  scrollToBottom();
}

// ─── Inject sample question from welcome screen ───────────────────────────────
function injectSample(btn) {
  queryInput.value = btn.textContent.trim();
  charCounter.textContent = `${queryInput.value.length} / 1000`;
  autoResize(queryInput);
  queryInput.focus();
}


// ═══════════════════════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════════════════════

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
}

function nowTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function fmtTime(ts) {
  try { return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); }
  catch { return nowTime(); }
}

function scrollToBottom() {
  chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });
}

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 140) + "px";
}

function setLoading(loading) {
  isLoading          = loading;
  sendBtn.disabled   = loading;
  queryInput.disabled = loading;
  loading ? appendTypingIndicator() : removeTypingIndicator();
}

function setOffline() {
  statusBadge.classList.add("offline");
  statusLabel.textContent = "Reconnecting…";
}

function setOnline() {
  statusBadge.classList.remove("offline");
  statusLabel.textContent = "Online";
}

let _toastTimer = null;
function showToast(msg, type = "") {
  toast.textContent = msg;
  toast.className   = `toast show ${type}`;
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => { toast.className = "toast"; }, 3500);
}

async function checkHealth() {
  try {
    const res = await fetch(API.health);
    res.ok ? setOnline() : setOffline();
  } catch { setOffline(); }
}

function debounce(fn, delay) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}


// ═══════════════════════════════════════════════════════════════════════════════
// EVENT LISTENERS
// ═══════════════════════════════════════════════════════════════════════════════

newChatBtn.addEventListener("click", newChat);

sendBtn.addEventListener("click", sendQuery);

queryInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendQuery(); }
});

queryInput.addEventListener("input", () => {
  const len = queryInput.value.length;
  charCounter.textContent = `${len} / 1000`;
  charCounter.style.color = len > 900 ? "var(--amber)" : "var(--txt-3)";
  autoResize(queryInput);
});

sessionSearch.addEventListener("input", debounce(async (e) => {
  await loadSessions(e.target.value.trim());
  markActive(currentSessionId);
}, 280));

// Close context menu on outside click
document.addEventListener("click", (e) => {
  if (!ctxMenu.contains(e.target)) ctxMenu.classList.remove("open");
});


// ═══════════════════════════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════════════════════════

(async function init() {
  showWelcomeScreen();            // show welcome immediately
  queryInput.focus();

  const sessions = await loadSessions();

  if (sessions.length > 0) {
    // Load the most recent session automatically
    await openSession(sessions[0].id, sessions[0].title);
  }

  checkHealth();
  setInterval(checkHealth, 30_000);
})();
