import { ChatSocket } from "./socket.js";
import { appendMessage, appendSystem, loadHistory, clearMessages, renderChannelList } from "./renderer.js";
import { API_BASE } from "./config.js";

// ── DOM refs ──────────────────────────────────────────────────────────────────
const loginScreen        = document.getElementById("login-screen");
const channelScreen      = document.getElementById("channel-screen");
const chatScreen         = document.getElementById("chat-screen");
const usernameInput      = document.getElementById("username-input");
const joinBtn            = document.getElementById("join-btn");
const leaveBtn           = document.getElementById("leave-btn");
const messageInput       = document.getElementById("message-input");
const sendBtn            = document.getElementById("send-btn");
const onlineCount        = document.getElementById("online-count");
const myNameEl           = document.getElementById("my-name");
const createChannelName  = document.getElementById("create-channel-name");
const createChannelBtn   = document.getElementById("create-channel-btn");
const refreshChannelsBtn = document.getElementById("refresh-channels-btn");
const backToLoginBtn     = document.getElementById("back-to-login-btn");
const currentChannelName = document.getElementById("current-channel-name");

let myUsername    = "";
let currentChannel = "";

// ── Socket ────────────────────────────────────────────────────────────────────
const socket = new ChatSocket({
  onMessage(data) {
    switch (data.type) {
      case "history":
        loadHistory(data.messages, myUsername);
        break;
      case "message":
        appendMessage(data, myUsername);
        break;
      case "system":
        appendSystem(data.text);
        if (data.count !== undefined) {
          onlineCount.textContent = `● ${data.count}명 접속중`;
        }
        break;
    }
  },
  onError() {
    appendSystem("서버 연결에 문제가 발생했습니다.");
  },
});

// ── Channel API ───────────────────────────────────────────────────────────────
async function loadChannels() {
  try {
    const res = await fetch(`${API_BASE}/channels`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const channels = await res.json();
    renderChannelList(channels, joinChannel, deleteChannel, myUsername);
  } catch (err) {
    console.error("Failed to load channels:", err);
  }
}

async function createChannel(name) {
  try {
    const res = await fetch(`${API_BASE}/channels`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, created_by: myUsername }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    await loadChannels();
  } catch (err) {
    console.error("Failed to create channel:", err);
  }
}

async function deleteChannel(name) {
  try {
    const res = await fetch(`${API_BASE}/channels/${encodeURIComponent(name)}?username=${encodeURIComponent(myUsername)}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    await loadChannels();
  } catch (err) {
    console.error("Failed to delete channel:", err);
  }
}

// ── UI transitions ────────────────────────────────────────────────────────────
function showChat(username) {
  myUsername = username;
  myNameEl.textContent = username;
  loginScreen.classList.add("hidden");
  channelScreen.classList.remove("hidden");
  loadChannels();
}

function joinChannel(channelName) {
  currentChannel = channelName;
  if (currentChannelName) {
    currentChannelName.textContent = `#${channelName}`;
  }
  channelScreen.classList.add("hidden");
  chatScreen.classList.remove("hidden");
  messageInput.focus();
  socket.connect(myUsername, channelName);
}

function showChannels() {
  socket.disconnect();
  chatScreen.classList.add("hidden");
  channelScreen.classList.remove("hidden");
  clearMessages();
  onlineCount.textContent = "● 0명 접속중";
  currentChannel = "";
  if (currentChannelName) currentChannelName.textContent = "";
  loadChannels();
}

function showLogin() {
  socket.disconnect();
  channelScreen.classList.add("hidden");
  chatScreen.classList.add("hidden");
  loginScreen.classList.remove("hidden");
  clearMessages();
  onlineCount.textContent = "● 0명 접속중";
  myUsername = "";
  currentChannel = "";
  if (currentChannelName) currentChannelName.textContent = "";
  usernameInput.value = "";
  usernameInput.focus();
}

function sendMessage() {
  const text = messageInput.value.trim();
  if (!text || !socket.isOpen) return;
  socket.send({ type: "message", text });
  messageInput.value = "";
  messageInput.focus();
}

// ── Event listeners ───────────────────────────────────────────────────────────
joinBtn.addEventListener("click", () => {
  const username = usernameInput.value.trim();
  if (!username) { usernameInput.focus(); return; }
  showChat(username);
});

usernameInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.isComposing) joinBtn.click();
});

leaveBtn.addEventListener("click", showChannels);

backToLoginBtn.addEventListener("click", showLogin);

createChannelBtn.addEventListener("click", () => {
  const name = createChannelName.value.trim();
  if (!name) { createChannelName.focus(); return; }
  createChannel(name);
  createChannelName.value = "";
});

createChannelName.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.isComposing) createChannelBtn.click();
});

refreshChannelsBtn.addEventListener("click", loadChannels);

sendBtn.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    sendMessage();
  }
});
