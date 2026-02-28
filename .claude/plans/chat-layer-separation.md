# Plan: chat.py 레이어 분리

## Context
`app/routers/chat.py`에 WebSocket 컨트롤러 로직, DB 접근(persistence), Redis 이벤트 퍼블리싱이 하나의 함수에 혼재되어 있다. 이를 3개 레이어로 분리하여 관심사 분리(SoC)를 달성하고 테스트 가능성을 높인다.

## 현재 상태
이미 생성된 파일:
- `app/repositories/__init__.py` (빈 파일)
- `app/services/__init__.py` (빈 파일)
- `app/repositories/message_repository.py` (완성)

## 레이어 구조

```
routers/chat.py       ← WebSocket 연결 생명주기만 처리
services/chat_service.py  ← 비즈니스 로직 (join/message/leave 이벤트 + Redis pub/sub)
repositories/message_repository.py  ← PostgreSQL CRUD (완성)
```

## 생성/수정할 파일

### 1. `app/services/chat_service.py` (신규)
```python
class ChatService:
    def __init__(self, r: Redis):
        self.r = r

    async def get_history(self, limit: int) -> list[dict]:
        """DB에서 메시지 히스토리를 조회하여 dict 리스트로 반환"""

    async def handle_join(self, username: str) -> None:
        """Redis Set에 username 추가 + join 시스템 메시지 publish"""

    async def handle_message(self, username: str, text: str) -> None:
        """DB에 메시지 저장 + Redis channel에 message publish"""

    async def handle_leave(self, username: str) -> None:
        """Redis Set에서 username 제거 + leave 시스템 메시지 publish"""
```
- `AsyncSessionLocal`과 `MessageRepository`를 내부에서 사용
- Redis 관련 상수(`CHANNEL`, `ONLINE_USERS_KEY`)도 여기서 처리

### 2. `app/routers/chat.py` (수정)
WebSocket 엔드포인트에서 다음만 담당:
1. `websocket.accept()`
2. `chat_service.get_history()` → `websocket.send_text()`
3. `manager.add()` + `chat_service.handle_join()`
4. 메시지 루프: `chat_service.handle_message()`
5. disconnect: `manager.remove()` + `chat_service.handle_leave()`

DB/Redis 직접 임포트 제거.

## 검증
- `docker-compose up` 또는 로컬 서버 실행 후 WebSocket 연결 테스트
- 메시지 전송 → 히스토리 조회 → 다중 클라이언트 브로드캐스트 동작 확인
