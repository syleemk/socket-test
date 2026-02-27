# AGENTS.md — socket-test

WebSocket 실시간 채팅. FastAPI + Redis pub/sub + PostgreSQL.

## 구조
```
backend/   → FastAPI WS 서버  (→ backend/AGENTS.md)
frontend/  → Vanilla HTML/JS  (→ frontend/AGENTS.md)
```

## 인프라
```bash
docker-compose up -d   # Redis:6379 / PostgreSQL:5432
```
| 서비스 | 이미지 | 인증 |
|---|---|---|
| redis | redis:7-alpine | 없음 |
| postgres | postgres:16-alpine | chatuser / chatpass / chatdb |

## 메시지 흐름
```
Client ──WS──▶ FastAPI ──publish──▶ Redis(chat:channel)
                  │                        │ subscribe
                  ▼                        ▼
             PostgreSQL          ConnectionManager.broadcast()
```
