# AGENTS.md — socket-test

WebSocket 실시간 채팅. FastAPI + Redis pub/sub + PostgreSQL. JWT 인증.

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

## Plans
프로젝트 관련 플랜은 `.claude/plans/` 에 저장하고 관리한다.

```
.claude/plans/
├── containerization.md     # Docker Compose → K8s 전환 로드맵
├── jwt-auth.md             # JWT 인증 백엔드 구현 계획
└── jwt-auth-frontend.md    # JWT 인증 프론트엔드 연동 계획
```

- 새 플랜 작성 시 `.claude/plans/<이름>.md` 에 저장
- 플랜 목록 조회: `.claude/plans/` 디렉토리 확인
- 플랜 실행: 해당 파일 읽고 단계별 진행

## 메시지 흐름
```
Client ──WS──▶ FastAPI ──publish──▶ Redis(chat:channel:{name})
                  │                        │ subscribe
                  ▼                        ▼
             PostgreSQL          ConnectionManager.broadcast()
```

## 인증 흐름
```
[회원가입] POST /auth/register
[로그인]   POST /auth/login → { access_token, refresh_token }
[WS 연결]  /ws/{channel}?token={access_token}
[API 요청] Authorization: Bearer {access_token}
[갱신]     POST /auth/refresh → { access_token }
[로그아웃] POST /auth/logout  (Redis refresh 토큰 삭제)
```
