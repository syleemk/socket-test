const { protocol, hostname, port } = window.location;
const wsProtocol = protocol === "https:" ? "wss:" : "ws:";
const origin = `${hostname}${port ? `:${port}` : ""}`;

export const WS_BASE = `${wsProtocol}//${origin}/ws`;
export const API_BASE = `${protocol}//${origin}/api`;
