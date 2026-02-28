import { ChatSocket } from "./socket.js";
import { appendMessage, appendSystem, loadHistory, clearMessages } from "./renderer.js";

// ── DOM refs ──────────────────────────────────────────────────────────────────
const loginScreen   = document.getElementById("login-screen");
const chatScreen    = document.getElementById("chat-screen");
const usernameInput = document.getElementById("username-input");
const joinBtn       = document.getElementById("join-btn");
const leaveBtn      = document.getElementById("leave-btn");
const messageInput  = document.getElementById("message-input");
const sendBtn       = document.getElementById("send-btn");
const onlineCount   = document.getElementById("online-count");
const myNameEl      = document.getElementById("my-name");

let myUsername = "";

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

// ── UI transitions ────────────────────────────────────────────────────────────
function showChat(username) {
  myUsername = username;
  myNameEl.textContent = username;
  loginScreen.classList.add("hidden");
  chatScreen.classList.remove("hidden");
  messageInput.focus();
  socket.connect(username);
}

function showLogin() {
  socket.disconnect();
  chatScreen.classList.add("hidden");
  loginScreen.classList.remove("hidden");
  clearMessages();
  onlineCount.textContent = "● 0명 접속중";
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
  if (e.key === "Enter") joinBtn.click();
});

leaveBtn.addEventListener("click", showLogin);

sendBtn.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    sendMessage();
  }
});
