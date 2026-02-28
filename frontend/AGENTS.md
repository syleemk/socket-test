# AGENTS.md — frontend

Vanilla JS + ES 모듈. 빌드 도구 없음. HTTP로 서빙해야 동작 (`file://` 프로토콜은 ES 모듈 CORS 제약으로 불가).

> 로컬에서 직접 테스트하려면: `python3 -m http.server 3000` (frontend/ 디렉토리에서 실행)

## 디렉토리 구조

```
frontend/
├── index.html
├── css/
│   ├── base.css        # 리셋, CSS 변수, 공유 요소 (input, button)
│   ├── login.css       # 로그인 카드
│   ├── channels.css    # 채널 목록 화면
│   └── chat.css        # 채팅 레이아웃 (header, main, footer, 말풍선)
└── js/
    ├── config.js       # 상수 (WS_BASE, API_BASE)
    ├── utils.js        # 순수 헬퍼 (getInitial, avatarColor)
    ├── socket.js       # ChatSocket 클래스
    ├── renderer.js     # DOM 렌더링 (메시지, 시스템, 채널 목록)
    └── app.js          # 진입점 — DOM refs, 이벤트, 화면 전환, Channel API 호출
```

## 화면 흐름

```
[로그인 화면] → (username 입력) → [채널 목록 화면] → (채널 선택) → [채팅 화면]
                                         ↑ (채팅에서 나가기)              ↑
                                   (로그인으로 돌아가기)
```

## 모듈별 역할

### js/config.js
```js
WS_BASE   — WebSocket 서버 주소 ("ws://localhost:8000/ws")
API_BASE  — REST API 서버 주소 ("http://localhost:8000")
```
서버 주소 변경 시 이 파일만 수정.

### js/utils.js
```
getInitial(name)    — 이름 첫 글자 대문자
avatarColor(name)   — username 해시 → 7가지 색 중 하나
```

### js/socket.js — `ChatSocket` 클래스
```
new ChatSocket({ onMessage(data), onError() })
  .connect(username, channelName)   — WebSocket 연결 (/ws/{channelName}/{username})
  .disconnect()                     — ws.close()
  .send(data)                       — JSON 직렬화 후 전송
  .isOpen                           — 연결 상태 getter
```

### js/renderer.js
```
appendMessage(msg, myUsername, animate?)          — 말풍선 DOM 생성
appendSystem(text)                                — 시스템 메시지 DOM 생성
loadHistory(messages, myUsername)                 — 전체 기록 렌더링
clearMessages()                                   — messages 영역 초기화
renderChannelList(channels, onJoin, onDelete, myUsername) — 채널 카드 목록 렌더링
```

### js/app.js
```
showChat(username)        — 로그인 화면 숨김, 채널 목록 화면 표시
joinChannel(channelName)  — 채널 목록 숨김, 채팅 화면 표시, socket.connect()
showChannels()            — socket.disconnect(), 채팅 → 채널 목록 복귀
showLogin()               — 전체 초기화, 로그인 화면으로 복귀
sendMessage()             — messageInput → socket.send()
loadChannels()            — GET /channels → renderChannelList()
createChannel(name)       — POST /channels
deleteChannel(name)       — DELETE /channels/{name}?username=...
```

## 수신 메시지 처리

| type | 처리 |
|---|---|
| `history` | `loadHistory(data.messages, myUsername)` |
| `message` | `appendMessage(data, myUsername)` |
| `system` | `appendSystem(data.text)` + 접속자 수 갱신 |

## 채널 REST API 호출

| 액션 | 메서드/경로 |
|---|---|
| 채널 목록 | `GET /channels` |
| 채널 생성 | `POST /channels` (`{ name, created_by }`) |
| 채널 삭제 | `DELETE /channels/{name}?username=...` |

## 스타일 주요 변수 (css/base.css `:root`)

```css
--accent: #6c63ff       /* 버튼, 내 말풍선 색 */
--bubble-other: #252836 /* 상대방 말풍선 */
--online: #22c55e       /* 접속자 수 표시 */
```

## 주의사항

- WS/API 주소 변경 시 `js/config.js`의 `WS_BASE` / `API_BASE`만 수정.
- ES 모듈(`type="module"`)은 HTTP 서빙 필수. `file://`로 직접 열면 동작하지 않음.
- 채널 삭제 버튼은 `created_by === myUsername`인 경우에만 렌더링됨.
