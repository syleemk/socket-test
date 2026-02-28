# 동적 채널(채팅방) 구현 계획

## Context

현재 앱은 단일 글로벌 채팅방만 지원하며 (`chat:channel` 하드코딩), 인증도 없음.
목표: 사용자가 채널(채팅방)을 직접 생성하고, 채널별로 독립된 메시지/접속자/pub-sub 운영.
병렬 작업 충돌 방지를 위해 **git worktree** 사용.

---

## Phase 0: Worktree 생성

```bash
# 이 기능 전용 격리 브랜치 생성
EnterWorktree 도구 사용 → name: "dynamic-channels"
```

---

## Phase 1: 데이터베이스 (models.py, database.py)

### 파일: `backend/app/models.py`
- `Channel` 모델 추가:
  ```python
  class Channel(Base):
      __tablename__ = "channels"
      id = Column(Integer, primary_key=True, autoincrement=True)
      name = Column(String(100), nullable=False, unique=True)
      created_by = Column(String(50), nullable=False)
      is_private = Column(Boolean, nullable=False, default=False)  # 비공개 확장용
      created_at = Column(DateTime(timezone=True), server_default=func.now())
  ```
- `Message` 모델에 `channel_name` 컬럼 추가:
  ```python
  channel_name = Column(String(100), nullable=False, default="general")
  ```

---

## Phase 2: Repository 레이어

### 파일: `backend/app/repositories/channel_repository.py` (신규)
- `create(name, created_by) -> Channel`
- `get_all() -> list[Channel]`
- `exists(name) -> bool`

### 파일: `backend/app/repositories/message_repository.py` (수정)
- `get_history(channel_name, limit)` → channel_name 필터 추가
- `save(username, text, channel_name)` → channel_name 파라미터 추가

### 파일: `backend/app/repositories/__init__.py` (수정)
- `ChannelRepository` 팩토리 추가

---

## Phase 3: Connection Manager (manager.py)

### 파일: `backend/app/routers/manager.py`
```python
class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, dict[str, WebSocket]] = {}
        # { channel_name: { username: websocket } }

    def add(self, channel: str, username: str, ws: WebSocket)
    def remove(self, channel: str, username: str)
    async def broadcast_to_channel(self, channel: str, data: str)
    def count(self, channel: str) -> int
```

---

## Phase 4: Redis 키 구조 변경

```
기존: chat:channel           → 신규: chat:channel:{channel_name}
기존: chat:online_users      → 신규: chat:online_users:{channel_name}
```

### 파일: `backend/app/core/redis.py`
- `CHANNEL`, `ONLINE_USERS_KEY` 상수 제거
- 패턴 기반 동적 키 생성 함수로 교체:
  ```python
  def channel_key(name: str) -> str: return f"chat:channel:{name}"
  def online_users_key(name: str) -> str: return f"chat:online_users:{name}"
  ```

### 파일: `backend/app/core/pubsub.py`
- 단일 채널 구독 → **패턴 구독** (`chat:channel:*`) 으로 변경
- 수신된 메시지의 채널명을 파싱하여 `manager.broadcast_to_channel(channel_name, data)` 호출

---

## Phase 5: ChatService 수정

### 파일: `backend/app/services/chat_service.py`
- 모든 메서드에 `channel_name: str` 파라미터 추가
- `handle_join(username, channel_name)`
- `handle_message(username, text, channel_name)`
- `handle_leave(username, channel_name)`
- `get_history(channel_name)`

---

## Phase 6: HTTP API 라우터 (채널 CRUD)

### 파일: `backend/app/routers/channels.py` (신규)
```python
@router.get("/channels")                    # 전체 채널 목록
@router.post("/channels")                   # 채널 생성 (name, created_by)
@router.delete("/channels/{channel_name}")  # 채널 삭제 (생성자만 가능)
```
- 중복 채널명 체크 (409 반환)
- 삭제 시 `created_by == username` 검증 (403 반환)
- `is_private` 컬럼을 Channel 모델에 추가해두되, 현재는 모두 `False`로 생성 (비공개 확장 용이)

### 파일: `backend/main.py`
- `channels.router` include 추가

---

## Phase 7: WebSocket 엔드포인트 수정

### 파일: `backend/app/routers/chat.py`
```python
# 기존: /ws/{username}
# 신규: /ws/{channel_name}/{username}
@router.websocket("/ws/{channel_name}/{username}")
async def websocket_endpoint(websocket, channel_name: str, username: str):
    ...
```

---

## Phase 8: 스키마 추가

### 파일: `backend/app/schemas.py`
- `ChannelInfo` TypedDict: `{ id, name, created_by, created_at }`
- `CreateChannelRequest` Pydantic 모델

---

## Phase 9: Frontend 수정

### 파일: `frontend/index.html`
- 채널 목록 화면(`#channel-screen`) 추가 (login ↔ channel-list ↔ chat)
- 채널 생성 모달/폼 추가

### 파일: `frontend/js/app.js`
- 흐름 변경: 로그인 → 채널 목록 → 채팅
- `loadChannels()`: `GET /channels` API 호출
- `createChannel(name)`: `POST /channels` API 호출
- `joinChannel(channelName)`: WebSocket 연결

### 파일: `frontend/js/socket.js`
- `connect(username, channelName)` 으로 변경
- WebSocket URL: `${WS_BASE}/{channelName}/{encodeURIComponent(username)}`

### 파일: `frontend/js/renderer.js`
- 채널 목록 렌더링 함수 추가
- 현재 채널명 표시

### 파일: `frontend/js/config.js`
- `API_BASE` URL 추가 (HTTP REST용)

---

## 변경 파일 요약

| 파일 | 작업 |
|------|------|
| `backend/app/models.py` | Channel 모델 추가, Message에 channel_name 추가 |
| `backend/app/repositories/channel_repository.py` | 신규 생성 |
| `backend/app/repositories/message_repository.py` | channel_name 필터 추가 |
| `backend/app/repositories/__init__.py` | ChannelRepository 팩토리 추가 |
| `backend/app/routers/manager.py` | 채널별 ConnectionManager |
| `backend/app/core/redis.py` | 동적 키 함수 |
| `backend/app/core/pubsub.py` | 패턴 구독 |
| `backend/app/services/chat_service.py` | channel_name 파라미터 |
| `backend/app/routers/chat.py` | 새 WebSocket URL |
| `backend/app/routers/channels.py` | 신규 HTTP API |
| `backend/app/schemas.py` | ChannelInfo 추가 |
| `backend/main.py` | channels router include |
| `frontend/index.html` | 채널 화면 추가 |
| `frontend/js/app.js` | 채널 로직 추가 |
| `frontend/js/socket.js` | channel 파라미터 추가 |
| `frontend/js/renderer.js` | 채널 목록 렌더링 |
| `frontend/js/config.js` | API_BASE 추가 |

---

## 검증 방법

1. `docker-compose up -d` (Redis, PostgreSQL 기동)
2. `uvicorn main:app --reload` (백엔드)
3. 브라우저에서 `frontend/index.html` 열기
4. 체크리스트:
   - [ ] 사용자A 로그인 → "general" 채널 생성
   - [ ] 사용자B 로그인 → 채널 목록에 "general" 보임
   - [ ] 사용자B가 "general" 입장
   - [ ] 두 사용자 간 실시간 메시지 확인
   - [ ] 사용자A가 "dev" 채널 생성, 사용자B가 "general" 유지
   - [ ] 채널 간 메시지 격리 확인 (dev 메시지가 general에 안 보임)
   - [ ] 새로고침 후 채널 목록 유지 (DB 영속성)
