import { WS_BASE } from "./config.js";

export class ChatSocket {
  #ws = null;
  #handlers;

  constructor(handlers = {}) {
    this.#handlers = handlers;
  }

  connect(username) {
    this.#ws = new WebSocket(`${WS_BASE}/${encodeURIComponent(username)}`);

    this.#ws.addEventListener("open", () => {
      console.log("WebSocket connected");
    });

    this.#ws.addEventListener("message", (event) => {
      let data;
      try { data = JSON.parse(event.data); } catch { return; }
      this.#handlers.onMessage?.(data);
    });

    this.#ws.addEventListener("close", () => {
      console.log("WebSocket disconnected");
    });

    this.#ws.addEventListener("error", (err) => {
      console.error("WebSocket error:", err);
      this.#handlers.onError?.();
    });
  }

  disconnect() {
    this.#ws?.close();
    this.#ws = null;
  }

  send(data) {
    if (this.#ws?.readyState === WebSocket.OPEN) {
      this.#ws.send(JSON.stringify(data));
    }
  }

  get isOpen() {
    return this.#ws?.readyState === WebSocket.OPEN;
  }
}
