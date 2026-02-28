# 실시간 채팅 프로젝트 계획

## Context
`socket-test/` 디렉토리에 WebSocket 기반 실시간 채팅 앱을 구현한다.
- Backend: Python + FastAPI (WebSocket 내장 지원)
- Frontend: Vanilla HTML/CSS/JS (빌드 도구 없이 브라우저에서 바로 실행)
- DB: Redis (실시간 pub/sub, 온라인 유저 관리) + PostgreSQL (메시지 영구 저장)

## 아키텍처

```
클라이언트 A ──WebSocket──┐
클라이언트 B ──WebSocket──┤  FastAPI  ──pub/sub──▶ Redis
클라이언트 C ──WebSocket──┘     │                    │
                                │◀──subscribe────────┘
                                │
                                └──▶ PostgreSQL (메시지 영구 저장)
```

**메시지 흐름:**
1. 클라이언트가 메시지 전송
2. FastAPI가 Redis에 publish
3. FastAPI의 Redis subscriber가 받아서 모든 WebSocket 클라이언트에 브로드캐스트
4. 동시에 PostgreSQL에 메시지 저장

## 프로젝트 구조
```
socket-test/
├── docker-compose.yml    # Redis + PostgreSQL 컨테이너
├── backend/
│   ├── main.py           # FastAPI WebSocket 서버
│   ├── database.py       # PostgreSQL 연결 (SQLAlchemy)
│   ├── redis_client.py   # Redis pub/sub 연결
│   ├── models.py         # DB 모델 (Message, User)
│   └── pyproject.toml    # uv 패키지 설정
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
```

## 구현 기능
1. 사용자 이름 입력 후 채팅방 입장
2. 실시간 메시지 전송/수신 (Redis pub/sub)
3. 입장/퇴장 시스템 메시지
4. 현재 접속자 수 표시 (Redis Set)
5. 입장 시 최근 메시지 50개 히스토리 로드 (PostgreSQL)

## 데이터 구조

### PostgreSQL - messages 테이블
```sql
id         SERIAL PRIMARY KEY
username   VARCHAR(50)
text       TEXT
created_at TIMESTAMP DEFAULT NOW()
```

### Redis
- `chat:online_users` (Set) - 현재 접속자 목록
- `chat:channel` (pub/sub channel) - 메시지 브로드캐스트

## WebSocket 메시지 포맷 (JSON)
```json
// 클라이언트 → 서버
{ "type": "message", "text": "안녕하세요" }

// 서버 → 클라이언트
{ "type": "message", "username": "홍길동", "text": "안녕하세요", "time": "14:30" }
{ "type": "system", "text": "홍길동님이 입장했습니다.", "count": 3 }
{ "type": "history", "messages": [...] }  // 입장 시 최초 1회
```

## Backend 핵심 로직
- `ConnectionManager`: 로컬 WebSocket 연결 관리
- Redis subscriber를 별도 asyncio task로 실행 → 모든 서버 인스턴스에 브로드캐스트 가능
- SQLAlchemy async로 PostgreSQL 비동기 처리
- 입장 시 PostgreSQL에서 히스토리 조회 후 전달

## 패키지
```toml
fastapi, uvicorn, redis[hiredis], sqlalchemy[asyncio], asyncpg, python-dotenv
```

## 실행 방법
```bash
# 인프라 실행
docker-compose up -d

# Backend
cd socket-test/backend
uv run uvicorn main:app --reload

# Frontend
# frontend/index.html을 브라우저에서 직접 열기
```

## 검증 방법
1. 브라우저 탭 2개로 접속해 서로 메시지 주고받기
2. 탭 닫으면 "퇴장" 시스템 메시지 + 접속자 수 감소 확인
3. 탭 새로 열면 이전 메시지 히스토리 로드 확인
4. `docker exec -it redis redis-cli` → `SMEMBERS chat:online_users` 로 접속자 확인
