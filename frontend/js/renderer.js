import { getInitial, avatarColor } from "./utils.js";

const messagesEl = document.getElementById("messages");

export function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

export function clearMessages() {
  messagesEl.innerHTML = "";
}

export function appendSystem(text) {
  const div = document.createElement("div");
  div.className = "msg-system";
  div.textContent = text;
  messagesEl.appendChild(div);
  scrollToBottom();
}

export function appendMessage({ username, text, time }, myUsername, animate = true) {
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

export function loadHistory(messages, myUsername) {
  clearMessages();
  if (messages.length === 0) {
    appendSystem("아직 메시지가 없습니다. 첫 번째 메시지를 보내보세요!");
    return;
  }
  for (const msg of messages) {
    appendMessage(msg, myUsername, false);
  }
  scrollToBottom();
}

export function renderChannelList(channels, onJoin, onDelete, myUsername) {
  const container = document.getElementById("channel-list");
  container.innerHTML = "";

  if (channels.length === 0) {
    container.innerHTML = '<p class="no-channels">채널이 없습니다. 첫 번째 채널을 만들어보세요!</p>';
    return;
  }

  channels.forEach((ch) => {
    const card = document.createElement("div");
    card.className = "channel-card";
    card.innerHTML = `
      <div class="channel-info">
        <span class="channel-name">#${ch.name}</span>
        <span class="channel-meta">만든이: ${ch.created_by}</span>
      </div>
      <div class="channel-actions">
        <button class="join-btn" data-name="${ch.name}">입장</button>
        ${ch.created_by === myUsername ? `<button class="delete-btn" data-name="${ch.name}">삭제</button>` : ""}
      </div>
    `;
    card.querySelector(".join-btn").addEventListener("click", () => onJoin(ch.name));
    const deleteBtn = card.querySelector(".delete-btn");
    if (deleteBtn) {
      deleteBtn.addEventListener("click", () => onDelete(ch.name));
    }
    container.appendChild(card);
  });
}
