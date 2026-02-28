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

## Plans
프로젝트 관련 플랜은 `.claude/plans/` 에 저장하고 관리한다.

```
.claude/plans/
├── chat-project-init.md        # 실시간 채팅 프로젝트 초기 계획
├── chat-layer-separation.md    # chat.py 레이어 분리
├── ddd-layer-refactoring.md    # DDD 레이어 리팩토링 (domain/infra/service/router)
├── dynamic-channels.md         # 동적 채널(채팅방) 구현
└── containerization.md         # Docker Compose → K8s 전환 로드맵
```

- 새 플랜 작성 시 `.claude/plans/<이름>.md` 에 저장
- 플랜 목록 조회: `.claude/plans/` 디렉토리 확인
- 플랜 실행: 해당 파일 읽고 단계별 진행

## 메시지 흐름
```
Client ──WS──▶ FastAPI ──publish──▶ Redis(chat:channel)
                  │                        │ subscribe
                  ▼                        ▼
             PostgreSQL          ConnectionManager.broadcast()
```
