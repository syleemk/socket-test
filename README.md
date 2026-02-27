# socket-test — 실시간 채팅

WebSocket 기반 실시간 채팅 앱.

- **Backend**: Python + FastAPI
- **Frontend**: Vanilla HTML/CSS/JS (빌드 도구 없음)
- **Broker**: Redis pub/sub
- **DB**: PostgreSQL

## 구조

```
socket-test/
├── docker-compose.yml
├── backend/
│   ├── main.py          ← FastAPI WS 엔드포인트, ConnectionManager
│   ├── models.py        ← SQLAlchemy ORM (Message)
│   ├── database.py      ← async PostgreSQL 엔진
│   ├── redis_client.py  ← Redis 연결 싱글톤
│   └── pyproject.toml
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js           ← WebSocket 클라이언트, DOM 렌더링
```

```
Browser ──── WebSocket ────▶ FastAPI ──── publish ────▶ Redis
                               │                          │
                               │◀──── subscribe ──────────┘
                               │
                               └──── INSERT ────▶ PostgreSQL
```

## 사전 요구사항

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 패키지 매니저)

## 실행

### 1. 인프라 (Redis + PostgreSQL)

```bash
cd socket-test
docker-compose up -d
```

### 2. Backend

```bash
cd backend
uv sync
uv run uvicorn main:app --reload
```

서버가 `http://localhost:8000`에서 실행됩니다.

### 3. Frontend

```bash
open frontend/index.html   # macOS
# Windows: start frontend/index.html
# 또는 브라우저 주소창에 파일 경로 직접 입력
```

## 종료

```bash
# 인프라 중지
docker-compose down

# 데이터까지 삭제하려면
docker-compose down -v
```

## 검증

브라우저 탭 2개를 열고 서로 다른 이름으로 입장해 메시지를 주고받습니다.

```bash
# Redis에서 접속자 목록 확인
docker exec -it redis redis-cli SMEMBERS chat:online_users
```
