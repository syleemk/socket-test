# AGENTS.md — frontend

Vanilla JS. 빌드 도구 없음. `index.html`을 브라우저에서 직접 열어 사용.

## 파일 역할
| 파일 | 역할 |
|---|---|
| `index.html` | 로그인 화면(`#login-screen`) + 채팅 화면(`#chat-screen`) |
| `style.css` | 다크 테마, 말풍선 레이아웃 (CSS 변수로 색상 관리) |
| `app.js` | WS 연결, 메시지 렌더링, DOM 이벤트 처리 |

## app.js 구조
```
WS_BASE = "ws://localhost:8000/ws"

connect(username)   — WebSocket 생성, 메시지 타입별 핸들러 연결
disconnect()        — ws.close()
sendMessage()       — input 값을 { type:"message", text } 으로 전송

appendMessage()     — 말풍선 DOM 생성 (me / other 구분)
appendSystem()      — 시스템 메시지 DOM 생성
loadHistory()       — history 메시지 배열을 일괄 렌더링 (애니메이션 없음)
updateOnlineCount() — 헤더 접속자 수 갱신
```

## 수신 메시지 처리
| type | 처리 |
|---|---|
| `history` | `loadHistory(data.messages)` — 기존 DOM 초기화 후 재렌더 |
| `message` | `appendMessage(data)` — 말풍선 추가 |
| `system` | `appendSystem(data.text)` + `updateOnlineCount(data.count)` |

## UI 상태 전환
- **입장**: `showChat(username)` → login 숨김, chat 표시, `connect()` 호출
- **나가기**: `leaveBtn` 클릭 → `disconnect()` → `showLogin()`

## 스타일 주요 변수 (style.css `:root`)
```css
--accent: #6c63ff       /* 버튼, 내 말풍선 색 */
--bubble-other: #252836 /* 상대방 말풍선 */
--online: #22c55e       /* 접속자 수 표시 */
```
아바타 색은 `app.js`의 `avatarColor(name)`에서 username 해시로 결정 (7가지 색 순환).

## 주의사항
- WS URL이 `localhost:8000` 하드코딩 — 서버 주소 변경 시 `app.js` 상단 `WS_BASE` 수정.
- `file://` 프로토콜로 열어도 동작하나, CORS preflight 없는 WS 연결만 사용하므로 문제없음.
