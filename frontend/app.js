const WS_BASE = "ws://localhost:8000/ws";

// ── DOM refs ──────────────────────────────────────────────────────────────────
const loginScreen   = document.getElementById("login-screen");
const chatScreen    = document.getElementById("chat-screen");
const usernameInput = document.getElementById("username-input");
const joinBtn       = document.getElementById("join-btn");
const leaveBtn      = document.getElementById("leave-btn");
const messagesEl    = document.getElementById("messages");
const messageInput  = document.getElementById("message-input");
const sendBtn       = document.getElementById("send-btn");
const onlineCount   = document.getElementById("online-count");
const myNameEl      = document.getElementById("my-name");

let ws = null;
let myUsername = "";

// ── Helpers ───────────────────────────────────────────────────────────────────
function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function getInitial(name) {
  return name.charAt(0).toUpperCase();
}

function avatarColor(name) {
  const colors = ["#6c63ff","#22c55e","#f59e0b","#ef4444","#3b82f6","#ec4899","#14b8a6"];
  let hash = 0;
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) & 0xffffffff;
  return colors[Math.abs(hash) % colors.length];
}

// ── Render functions ──────────────────────────────────────────────────────────
function appendSystem(text) {
  const div = document.createElement("div");
  div.className = "msg-system";
  div.textContent = text;
  messagesEl.appendChild(div);
  scrollToBottom();
}

function appendMessage({ username, text, time }, animate = true) {
  const isMe = username === myUsername;

  const row = document.createElement("div");
  row.className = `msg-row ${isMe ? "me" : "other"}`;
  if (!animate) row.style.animation = "none";

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = getInitial(username);
  avatar.style.background = avatarColor(username);

  const wrap = document.createElement("div");
  wrap.className = "bubble-wrap";

  if (!isMe) {
    const nameEl = document.createElement("div");
    nameEl.className = "bubble-name";
    nameEl.textContent = username;
    wrap.appendChild(nameEl);
  }

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  const timeEl = document.createElement("div");
  timeEl.className = "bubble-time";
  timeEl.textContent = time;

  wrap.appendChild(bubble);
  wrap.appendChild(timeEl);

  row.appendChild(avatar);
  row.appendChild(wrap);
  messagesEl.appendChild(row);
  scrollToBottom();
}

function loadHistory(messages) {
  messagesEl.innerHTML = "";
  if (messages.length === 0) {
    appendSystem("아직 메시지가 없습니다. 첫 번째 메시지를 보내보세요!");
    return;
  }
  for (const msg of messages) {
    appendMessage(msg, false);
  }
  scrollToBottom();
}

function updateOnlineCount(count) {
  onlineCount.textContent = `● ${count}명 접속중`;
}

// ── WebSocket ─────────────────────────────────────────────────────────────────
function connect(username) {
  ws = new WebSocket(`${WS_BASE}/${encodeURIComponent(username)}`);

  ws.addEventListener("open", () => {
    console.log("WebSocket connected");
  });

  ws.addEventListener("message", (event) => {
    let data;
    try {
      data = JSON.parse(event.data);
    } catch {
      return;
    }

    switch (data.type) {
      case "history":
        loadHistory(data.messages);
        break;
      case "message":
        appendMessage(data);
        break;
      case "system":
        appendSystem(data.text);
        if (data.count !== undefined) {
          updateOnlineCount(data.count);
        }
        break;
    }
  });

  ws.addEventListener("close", () => {
    console.log("WebSocket disconnected");
  });

  ws.addEventListener("error", (err) => {
    console.error("WebSocket error:", err);
    appendSystem("서버 연결에 문제가 발생했습니다.");
  });
}

function disconnect() {
  if (ws) {
    ws.close();
    ws = null;
  }
}

function sendMessage() {
  const text = messageInput.value.trim();
  if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({ type: "message", text }));
  messageInput.value = "";
  messageInput.focus();
}

// ── UI transitions ────────────────────────────────────────────────────────────
function showChat(username) {
  myUsername = username;
  myNameEl.textContent = username;
  loginScreen.classList.add("hidden");
  chatScreen.classList.remove("hidden");
  messageInput.focus();
  connect(username);
}

function showLogin() {
  chatScreen.classList.add("hidden");
  loginScreen.classList.remove("hidden");
  messagesEl.innerHTML = "";
  onlineCount.textContent = "● 0명 접속중";
  usernameInput.value = "";
  usernameInput.focus();
}

// ── Event listeners ───────────────────────────────────────────────────────────
joinBtn.addEventListener("click", () => {
  const username = usernameInput.value.trim();
  if (!username) {
    usernameInput.focus();
    return;
  }
  showChat(username);
});

usernameInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") joinBtn.click();
});

leaveBtn.addEventListener("click", () => {
  disconnect();
  showLogin();
});

sendBtn.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    sendMessage();
  }
});
