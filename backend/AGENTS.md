# AGENTS.md — backend

FastAPI WebSocket 서버. `uv run uvicorn main:app --reload`로 실행.

## 디렉토리 구조

```
backend/
├── main.py                         # FastAPI 앱, lifespan, 미들웨어, 라우터 등록
├── pyproject.toml
└── app/
    ├── config.py                   # DATABASE_URL, REDIS_URL, CORS_ORIGINS
    ├── database.py                 # async 엔진, AsyncSessionLocal, init_db()
    ├── models.py                   # SQLAlchemy ORM — Message, Channel 모델
    ├── domain/
    │   └── channel.py              # 도메인 예외: ChannelAlreadyExistsError, ChannelNotFoundError, ChannelPermissionError
    ├── infrastructure/
    │   ├── redis.py                # get_redis(), channel_key(name), online_users_key(name)
    │   ├── pubsub.py               # redis_subscriber() — 채널별 pub/sub 브로드캐스트
    │   ├── connection_manager.py   # ConnectionManager + manager 싱글톤
    │   └── repositories/
    │       ├── channel_repository.py
    │       ├── message_repository.py
    │       └── __init__.py         # channel_repo_factory, message_repo_factory
    ├── services/
    │   ├── channel_service.py      # ChannelService: list/create/delete
    │   └── chat_service.py         # ChatService: join/message/leave/history
    ├── schemas/
    │   ├── channel.py              # ChannelResponse, CreateChannelRequest (BaseModel)
    │   └── message.py              # MessageHistoryItem (BaseModel)
    └── routers/
        ├── channels.py             # HTTP REST — /channels (GET, POST, DELETE)
        └── chat.py                 # WebSocket — /ws/{channel_name}/{username}
```

## 레이어 규칙

```
router → service → repository
```

- router는 HTTP/WS 처리만, 비즈니스 로직은 service에 위임
- service는 도메인 예외를 raise, router에서 HTTP 오류로 변환
- repository는 DB I/O 전담

## 환경 변수

| 변수 | 기본값 |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://chatuser:chatpass@localhost:5432/chatdb` |
| `REDIS_URL` | `redis://localhost:6379` |
| `CORS_ORIGINS` | `["http://localhost:3000"]` |

## HTTP 엔드포인트 (`/channels`)

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/channels` | 채널 목록 조회 |
| `POST` | `/channels` | 채널 생성 (`{ name, created_by }`) |
| `DELETE` | `/channels/{channel_name}?username=...` | 채널 삭제 (생성자만 가능) |

오류 코드: 409 이름 충돌, 404 미존재, 403 권한 없음

## WS 엔드포인트: `GET /ws/{channel_name}/{username}`

1. 연결 수락 → 해당 채널 최근 50개 `history` 전송
2. `ConnectionManager`에 등록, Redis Set에 `SADD`
3. `chat:{channel_name}` 채널에 입장 system 메시지 publish
4. 루프: 클라이언트 메시지 수신 → DB 저장 → Redis publish
5. 연결 종료(`WebSocketDisconnect`): `SREM` → 퇴장 system 메시지 publish

## WS 메시지 포맷

```json
// 클라이언트 → 서버
{ "type": "message", "text": "안녕" }

// 서버 → 클라이언트
{ "type": "history",  "messages": [{ "username", "text", "time" }] }
{ "type": "message",  "username": "홍길동", "text": "안녕", "time": "14:30" }
{ "type": "system",   "text": "홍길동님이 입장했습니다.", "count": 3 }
```

## Redis 키 (채널별 격리)

| 키 패턴 | 타입 | 용도 |
|---|---|---|
| `chat:channel:{name}` | pub/sub | 채널 메시지 브로드캐스트 |
| `chat:online_users:{name}` | Set | 채널 접속자 관리 (SADD/SREM/SCARD) |

## PostgreSQL 스키마

```sql
messages(id SERIAL PK, channel_name VARCHAR(100), username VARCHAR(50), text TEXT, created_at TIMESTAMPTZ DEFAULT NOW())
channels(id SERIAL PK, name VARCHAR(100) UNIQUE, created_by VARCHAR(50), is_private BOOLEAN DEFAULT FALSE, created_at TIMESTAMPTZ DEFAULT NOW())
```

`init_db()`가 앱 시작 시 테이블을 자동 생성. Alembic 없음 — 컬럼 변경 시 수동 ALTER 필요.

## 주의사항

- **redis_subscriber**: `lifespan`에서 `asyncio.create_task()`로 실행. Redis를 경유하는 이유는 수평 확장 시 모든 인스턴스에 전달하기 위함.
- **비정상 종료**: 서버 크래시 시 `chat:online_users:{name}`에 잔류 항목이 생길 수 있음.
- **인증 없음**: username은 URL 파라미터뿐, 중복 접속 방지 로직 없음.
- **CORS**: `app/config.py`의 `CORS_ORIGINS`에서 관리.
