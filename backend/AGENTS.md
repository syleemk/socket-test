# AGENTS.md — backend

FastAPI WebSocket 서버. `uv run uvicorn main:app --reload`로 실행.

## 파일 역할
| 파일 | 역할 |
|---|---|
| `main.py` | WS 엔드포인트, ConnectionManager, redis_subscriber task |
| `models.py` | SQLAlchemy ORM — `Message` 모델 |
| `database.py` | async 엔진, `AsyncSessionLocal`, `init_db()` |
| `redis_client.py` | Redis 싱글톤(`get_redis()`), 상수 정의 |

## 환경 변수
| 변수 | 기본값 |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://chatuser:chatpass@localhost:5432/chatdb` |
| `REDIS_URL` | `redis://localhost:6379` |

## Redis 키
| 키 | 타입 | 용도 |
|---|---|---|
| `chat:channel` | pub/sub | 메시지 브로드캐스트 |
| `chat:online_users` | Set | 접속자 관리 (SADD/SREM/SCARD) |

## PostgreSQL 스키마
```sql
messages(id SERIAL PK, username VARCHAR(50), text TEXT, created_at TIMESTAMPTZ DEFAULT NOW())
```
`init_db()`가 앱 시작 시 테이블을 자동 생성. Alembic 없음 — 컬럼 변경 시 수동 ALTER 필요.

## WS 엔드포인트: `GET /ws/{username}`
1. 연결 수락 → PostgreSQL에서 최근 50개 `history` 전송
2. `ConnectionManager`에 등록, Redis Set에 `SADD`
3. `chat:channel`에 입장 system 메시지 publish
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

## 주의사항
- **redis_subscriber**: `lifespan`에서 `asyncio.create_task()`로 실행. 직접 broadcast하지 않고 Redis를 경유하는 이유는 수평 확장 시 모든 인스턴스에 전달하기 위함.
- **비정상 종료**: 서버 크래시 시 `chat:online_users`에 잔류 항목이 생길 수 있음.
- **인증 없음**: username은 URL 파라미터뿐, 중복 접속 방지 로직 없음.
- **CORS**: 현재 `allow_origins=["*"]` — 운영 시 제한 필요.
