import { API_BASE } from "./config.js";
import { auth } from "./auth.js";
import { ChatSocket } from "./socket.js";
import {
  appendMessage,
  appendSystem,
  clearMessages,
  loadHistory,
  renderChannelList,
} from "./renderer.js";

const loginScreen = document.getElementById("login-screen");
const channelScreen = document.getElementById("channel-screen");
const chatScreen = document.getElementById("chat-screen");

const loginTabBtn = document.getElementById("login-tab-btn");
const registerTabBtn = document.getElementById("register-tab-btn");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");

const loginEmail = document.getElementById("login-email");
const loginPassword = document.getElementById("login-password");
const loginError = document.getElementById("login-error");

const regUsername = document.getElementById("reg-username");
const regEmail = document.getElementById("reg-email");
const regPassword = document.getElementById("reg-password");
const registerError = document.getElementById("register-error");

const leaveBtn = document.getElementById("leave-btn");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const onlineCount = document.getElementById("online-count");
const myNameEl = document.getElementById("my-name");
const createChannelName = document.getElementById("create-channel-name");
const createChannelBtn = document.getElementById("create-channel-btn");
const refreshChannelsBtn = document.getElementById("refresh-channels-btn");
const backToLoginBtn = document.getElementById("back-to-login-btn");
const currentChannelName = document.getElementById("current-channel-name");

let myUsername = "";
let currentChannel = "";

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
  onAuthError() {
    auth.clear();
    showLogin("로그인이 만료되었습니다. 다시 로그인해주세요.");
  },
});

function setError(target, message) {
  if (!message) {
    target.textContent = "";
    target.classList.add("hidden");
    return;
  }
  target.textContent = message;
  target.classList.remove("hidden");
}

function showAuthTab(tab) {
  const isLogin = tab === "login";
  loginTabBtn.classList.toggle("active", isLogin);
  registerTabBtn.classList.toggle("active", !isLogin);
  loginForm.classList.toggle("hidden", !isLogin);
  registerForm.classList.toggle("hidden", isLogin);

  setError(loginError, "");
  setError(registerError, "");

  if (isLogin) {
    loginEmail.focus();
  } else {
    regUsername.focus();
  }
}

async function apiFetch(path, options = {}, retry = true) {
  const accessToken = auth.getAccessToken();
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401 && retry && auth.getRefreshToken()) {
    try {
      await auth.refresh();
      return apiFetch(path, options, false);
    } catch {
      auth.clear();
      showLogin("로그인이 만료되었습니다. 다시 로그인해주세요.");
      throw new Error("Unauthorized");
    }
  }

  return res;
}

async function loadChannels() {
  try {
    const res = await apiFetch("/channels");
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const channels = await res.json();
    renderChannelList(channels, joinChannel, deleteChannel, myUsername);
  } catch (err) {
    console.error("Failed to load channels:", err);
  }
}

async function createChannel(name) {
  try {
    const res = await apiFetch("/channels", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    await loadChannels();
  } catch (err) {
    console.error("Failed to create channel:", err);
  }
}

async function deleteChannel(name) {
  try {
    const res = await apiFetch(`/channels/${encodeURIComponent(name)}`, {
      method: "DELETE",
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    await loadChannels();
  } catch (err) {
    console.error("Failed to delete channel:", err);
  }
}

function showChannelScreen() {
  myUsername = auth.getUsername() || "";

  if (!myUsername || !auth.getAccessToken()) {
    showLogin();
    return;
  }

  myNameEl.textContent = myUsername;
  loginScreen.classList.add("hidden");
  chatScreen.classList.add("hidden");
  channelScreen.classList.remove("hidden");
  loadChannels();
}

function joinChannel(channelName) {
  const token = auth.getAccessToken();
  if (!token) {
    showLogin("로그인이 필요합니다.");
    return;
  }

  currentChannel = channelName;
  currentChannelName.textContent = `#${channelName}`;
  channelScreen.classList.add("hidden");
  chatScreen.classList.remove("hidden");
  messageInput.focus();

  socket.connect(channelName, token);
}

function showChannels() {
  socket.disconnect();
  chatScreen.classList.add("hidden");
  channelScreen.classList.remove("hidden");
  clearMessages();
  onlineCount.textContent = "● 0명 접속중";
  currentChannel = "";
  currentChannelName.textContent = "";
  loadChannels();
}

function showLogin(message = "") {
  socket.disconnect();
  channelScreen.classList.add("hidden");
  chatScreen.classList.add("hidden");
  loginScreen.classList.remove("hidden");

  clearMessages();
  onlineCount.textContent = "● 0명 접속중";
  myUsername = "";
  currentChannel = "";
  myNameEl.textContent = "";
  currentChannelName.textContent = "";

  loginForm.reset();
  registerForm.reset();
  setError(loginError, message);
  setError(registerError, "");
  showAuthTab("login");
}

function sendMessage() {
  const text = messageInput.value.trim();
  if (!text || !socket.isOpen) {
    return;
  }
  socket.send({ type: "message", text });
  messageInput.value = "";
  messageInput.focus();
}

loginTabBtn.addEventListener("click", () => showAuthTab("login"));
registerTabBtn.addEventListener("click", () => showAuthTab("register"));

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  setError(loginError, "");

  const email = loginEmail.value.trim();
  const password = loginPassword.value;

  if (!email || !password) {
    setError(loginError, "이메일과 비밀번호를 입력해주세요.");
    return;
  }

  try {
    await auth.login(email, password);
    showChannelScreen();
  } catch (err) {
    setError(loginError, err instanceof Error ? err.message : "로그인에 실패했습니다.");
  }
});

registerForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  setError(registerError, "");

  const username = regUsername.value.trim();
  const email = regEmail.value.trim();
  const password = regPassword.value;

  if (!username || !email || !password) {
    setError(registerError, "모든 항목을 입력해주세요.");
    return;
  }

  try {
    await auth.register(username, email, password);
    await auth.login(email, password);
    showChannelScreen();
  } catch (err) {
    setError(registerError, err instanceof Error ? err.message : "회원가입에 실패했습니다.");
  }
});

leaveBtn.addEventListener("click", showChannels);

backToLoginBtn.addEventListener("click", async () => {
  await auth.logout();
  showLogin();
});

createChannelBtn.addEventListener("click", () => {
  const name = createChannelName.value.trim();
  if (!name) {
    createChannelName.focus();
    return;
  }
  createChannel(name);
  createChannelName.value = "";
});

createChannelName.addEventListener("keyup", (e) => {
  if (e.key === "Enter" && !e.isComposing) {
    createChannelBtn.click();
  }
});

refreshChannelsBtn.addEventListener("click", loadChannels);

sendBtn.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    sendMessage();
  }
});

if (auth.isLoggedIn() && auth.getUsername()) {
  showChannelScreen();
} else {
  showLogin();
}
