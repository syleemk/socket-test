import { API_BASE } from "./config.js";

const KEYS = {
  access: "access_token",
  refresh: "refresh_token",
  user: "username",
};

async function parseErrorMessage(res, fallback) {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string" && data.detail) {
      return data.detail;
    }
  } catch {
    return fallback;
  }
  return fallback;
}

export const auth = {
  save(accessToken, refreshToken, username) {
    localStorage.setItem(KEYS.access, accessToken);
    localStorage.setItem(KEYS.refresh, refreshToken);
    localStorage.setItem(KEYS.user, username);
  },

  clear() {
    localStorage.removeItem(KEYS.access);
    localStorage.removeItem(KEYS.refresh);
    localStorage.removeItem(KEYS.user);
  },

  getAccessToken() {
    return localStorage.getItem(KEYS.access);
  },

  getRefreshToken() {
    return localStorage.getItem(KEYS.refresh);
  },

  getUsername() {
    return localStorage.getItem(KEYS.user);
  },

  isLoggedIn() {
    return Boolean(this.getAccessToken());
  },

  async register(username, email, password) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    });

    if (!res.ok) {
      throw new Error(await parseErrorMessage(res, "회원가입에 실패했습니다."));
    }

    return res.json();
  },

  async login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      throw new Error(await parseErrorMessage(res, "로그인에 실패했습니다."));
    }

    const data = await res.json();
    this.save(data.access_token, data.refresh_token, data.username);
    return data;
  },

  async refresh() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      this.clear();
      throw new Error("리프레시 토큰이 없습니다.");
    }

    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) {
      this.clear();
      throw new Error(await parseErrorMessage(res, "토큰 갱신에 실패했습니다."));
    }

    const data = await res.json();
    localStorage.setItem(KEYS.access, data.access_token);
    return data.access_token;
  },

  async logout() {
    const accessToken = this.getAccessToken();

    try {
      if (accessToken) {
        await fetch(`${API_BASE}/auth/logout`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
      }
    } finally {
      this.clear();
    }
  },
};
