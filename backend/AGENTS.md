# AGENTS.md — backend

FastAPI WebSocket 서버. `uv run uvicorn main:app --reload`로 실행.

## 디렉토리 구조

```
backend/
├── main.py                         # FastAPI 앱, lifespan, 미들웨어, 라우터 등록
├── pyproject.toml
└── app/
    ├── config.py                   # DATABASE_URL, REDIS_URL, CORS_ORIGINS, JWT 설정 등
    ├── database.py                 # async 엔진, AsyncSessionLocal, init_db()
    ├── models.py                   # SQLAlchemy ORM — Message, Channel, User 모델
    ├── dependencies/
    │   └── auth.py                 # get_current_user() — Bearer 토큰 검증 FastAPI Dependency
    ├── domain/
    │   ├── channel.py              # 도메인 예외: ChannelAlreadyExistsError, ChannelNotFoundError, ChannelPermissionError
    │   └── user.py                 # 도메인 예외: UserAlreadyExistsError, UserNotFoundError, InvalidCredentialsError, InvalidTokenError
    ├── infrastructure/
    │   ├── auth.py                 # hash_password(), verify_password(), create_access_token(), create_refresh_token(), decode_token()
    │   ├── redis.py                # get_redis(), channel_key(name), online_users_key(name)
    │   ├── pubsub.py               # redis_subscriber() — 채널별 pub/sub 브로드캐스트
    │   ├── connection_manager.py   # ConnectionManager + manager 싱글톤
    │   ├── logging.py              # 로깅 설정
    │   └── repositories/
    │       ├── channel_repository.py
    │       ├── message_repository.py
    │       ├── user_repository.py
    │       └── __init__.py         # channel_repo_factory, message_repo_factory, user_repo_factory
    ├── services/
    │   ├── auth_service.py         # AuthService: register/login/refresh/logout/get_user_by_username
    │   ├── channel_service.py      # ChannelService: list/create/delete
    │   └── chat_service.py         # ChatService: join/message/leave/history
    ├── schemas/
    │   ├── auth.py                 # RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, AccessTokenResponse, UserResponse
    │   ├── channel.py              # ChannelResponse, CreateChannelRequest (BaseModel)
    │   └── message.py              # MessageHistoryItem (BaseModel)
    └── routers/
        ├── auth.py                 # HTTP REST — /auth (register, login, refresh, logout, me)
        ├── channels.py             # HTTP REST — /channels (GET, POST, DELETE)
        └── chat.py                 # WebSocket — /ws/{channel_name}?token=...
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
| `DATABASE_URL` | `postgresql+asyncpg://...` |
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` | 개별 DB 연결 파라미터 |
| `REDIS_URL` | `redis://localhost:6379` |
| `CORS_ORIGINS` | `*` |
| `JWT_SECRET_KEY` | `""` (필수 — 반드시 설정) |
| `JWT_ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
| `MESSAGE_HISTORY_LIMIT` | `50` |

## HTTP 엔드포인트 (`/auth`)

| 메서드 | 경로 | 인증 | 설명 |
|---|---|---|---|
| `POST` | `/auth/register` | 없음 | 회원가입 (`{ username, email, password }`) → UserResponse |
| `POST` | `/auth/login` | 없음 | 로그인 (`{ username, password }`) → `{ access_token, refresh_token }` |
| `POST` | `/auth/refresh` | 없음 | 토큰 갱신 (`{ refresh_token }`) → `{ access_token }` |
| `POST` | `/auth/logout` | Bearer | 로그아웃 (Redis refresh 토큰 삭제) |
| `GET` | `/auth/me` | Bearer | 현재 사용자 정보 |

오류 코드: 409 중복 사용자, 401 인증 실패

## HTTP 엔드포인트 (`/channels`)

| 메서드 | 경로 | 인증 | 설명 |
|---|---|---|---|
| `GET` | `/channels` | 없음 | 채널 목록 조회 |
| `POST` | `/channels` | Bearer | 채널 생성 (`{ name }`) — created_by는 토큰에서 추출 |
| `DELETE` | `/channels/{channel_name}` | Bearer | 채널 삭제 (생성자만 가능) |

오류 코드: 409 이름 충돌, 404 미존재, 403 권한 없음

## WS 엔드포인트: `GET /ws/{channel_name}?token={access_token}`

1. `token` 쿼리 파라미터에서 JWT access token 검증 → 실패 시 `close(code=4001)`
2. 연결 수락 → 해당 채널 최근 50개 `history` 전송
3. `ConnectionManager`에 등록, Redis Set에 `SADD`
4. `chat:{channel_name}` 채널에 입장 system 메시지 publish
5. 루프: 클라이언트 메시지 수신 → DB 저장 → Redis publish
6. 연결 종료(`WebSocketDisconnect`): `SREM` → 퇴장 system 메시지 publish

## WS 메시지 포맷

```json
// 클라이언트 → 서버
{ "type": "message", "text": "안녕" }

// 서버 → 클라이언트
{ "type": "history",  "messages": [{ "username", "text", "time" }] }
{ "type": "message",  "username": "홍길동", "text": "안녕", "time": "14:30" }
{ "type": "system",   "text": "홍길동님이 입장했습니다.", "count": 3 }
```

## Redis 키

| 키 패턴 | 타입 | 용도 |
|---|---|---|
| `chat:channel:{name}` | pub/sub | 채널 메시지 브로드캐스트 |
| `chat:online_users:{name}` | Set | 채널 접속자 관리 (SADD/SREM/SCARD) |
| `auth:refresh:{username}` | String | refresh token 저장 (TTL: REFRESH_TOKEN_EXPIRE_DAYS일) |

## PostgreSQL 스키마

```sql
channels(id SERIAL PK, name VARCHAR(100) UNIQUE, created_by VARCHAR(50), is_private BOOLEAN DEFAULT FALSE, created_at TIMESTAMPTZ DEFAULT NOW())
messages(id SERIAL PK, channel_name VARCHAR(100), username VARCHAR(50), text TEXT, created_at TIMESTAMPTZ DEFAULT NOW())
users(id SERIAL PK, username VARCHAR(50) UNIQUE, email VARCHAR(254) UNIQUE, hashed_password VARCHAR(255), is_active BOOLEAN DEFAULT TRUE, created_at TIMESTAMPTZ DEFAULT NOW())
```

`init_db()`가 앱 시작 시 테이블을 자동 생성. Alembic 없음 — 컬럼 변경 시 수동 ALTER 필요.

## 인증 구조

- **비밀번호 해싱**: SHA-256 prehash → base64 → bcrypt (72바이트 제한 우회)
- **JWT**: `python-jose` 사용. access(15분) / refresh(7일) 두 종류.
- **refresh token**: Redis에 저장. `/auth/refresh` 시 일치 여부 검증. `/auth/logout` 시 삭제.
- **WS 인증**: HTTP 헤더 미지원 → `?token=` 쿼리 파라미터로 전달. 실패 시 WS close code `4001`.
- **FastAPI Dependency**: `get_current_user()` — `dependencies/auth.py`. 채널 생성/삭제, 로그아웃, `/auth/me`에서 사용.

## 주의사항

- **redis_subscriber**: `lifespan`에서 `asyncio.create_task()`로 실행.
- **비정상 종료**: 서버 크래시 시 `chat:online_users:{name}`에 잔류 항목이 생길 수 있음.
- **JWT_SECRET_KEY**: 빈 문자열 기본값 — 프로덕션에서 반드시 강력한 키로 설정.
- **CORS**: `app/config.py`의 `CORS_ORIGINS`에서 관리.
