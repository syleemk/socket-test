# AGENTS.md — frontend

Vanilla JS + ES 모듈. 빌드 도구 없음. HTTP로 서빙해야 동작 (`file://` 프로토콜은 ES 모듈 CORS 제약으로 불가).

> 로컬에서 직접 테스트하려면: `python3 -m http.server 3000` (frontend/ 디렉토리에서 실행)

## 디렉토리 구조

```
frontend/
├── index.html
├── nginx.conf          # Docker Nginx 서빙 설정
├── Dockerfile
├── css/
│   ├── base.css        # 리셋, CSS 변수, 공유 요소 (input, button)
│   ├── login.css       # 로그인/회원가입 카드 (탭 UI 포함)
│   ├── channels.css    # 채널 목록 화면
│   └── chat.css        # 채팅 레이아웃 (header, main, footer, 말풍선)
└── js/
    ├── config.js       # 상수 (WS_BASE, API_BASE)
    ├── utils.js        # 순수 헬퍼 (getInitial, avatarColor)
    ├── auth.js         # auth 객체 — JWT 토큰 관리 및 인증 API 호출
    ├── socket.js       # ChatSocket 클래스
    ├── renderer.js     # DOM 렌더링 (메시지, 시스템, 채널 목록)
    └── app.js          # 진입점 — DOM refs, 이벤트, 화면 전환, 채널 API 호출
```

## 화면 흐름

```
[로그인/회원가입 화면] → (로그인 또는 가입+자동로그인) → [채널 목록 화면] → (채널 선택) → [채팅 화면]
                                                                   ↑ (채팅에서 나가기)
                                                           (로그아웃 → 로그인 화면)
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

### js/auth.js — `auth` 객체
토큰을 `localStorage`에 저장하고 인증 API를 호출하는 모듈.

```
auth.save(accessToken, refreshToken, username)  — 토큰/유저명 저장
auth.clear()                                    — 토큰 전체 삭제
auth.getAccessToken()                           — access_token 반환
auth.getRefreshToken()                          — refresh_token 반환
auth.getUsername()                              — 저장된 username 반환
auth.isLoggedIn()                               — access_token 존재 여부
auth.register(username, email, password)        — POST /auth/register
auth.login(username, password)                  — POST /auth/login → 토큰 저장
auth.refresh()                                  — POST /auth/refresh → access_token 갱신
auth.logout()                                   — POST /auth/logout → 토큰 전체 삭제
```

### js/socket.js — `ChatSocket` 클래스
```
new ChatSocket({ onMessage(data), onError(), onAuthError() })
  .connect(channelName, token)   — WebSocket 연결 (/ws/{channelName}?token=...)
  .disconnect()                  — ws.close()
  .send(data)                    — JSON 직렬화 후 전송
  .isOpen                        — 연결 상태 getter
```
- WS close code `4001` 수신 시 `onAuthError()` 호출 (토큰 만료/무효)

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
showAuthTab(tab)          — 로그인/회원가입 탭 전환
apiFetch(path, options, retry) — Bearer 토큰 자동 첨부 + 401 시 토큰 갱신 재시도
showChannelScreen()       — 로그인 화면 숨김, 채널 목록 화면 표시
joinChannel(channelName)  — 채널 목록 숨김, 채팅 화면 표시, socket.connect(channelName, token)
showChannels()            — socket.disconnect(), 채팅 → 채널 목록 복귀
showLogin(message?)       — 전체 초기화, 로그인 화면으로 복귀
sendMessage()             — messageInput → socket.send()
loadChannels()            — apiFetch GET /channels → renderChannelList()
createChannel(name)       — apiFetch POST /channels
deleteChannel(name)       — apiFetch DELETE /channels/{name}
```

## 수신 메시지 처리

| type | 처리 |
|---|---|
| `history` | `loadHistory(data.messages, myUsername)` |
| `message` | `appendMessage(data, myUsername)` |
| `system` | `appendSystem(data.text)` + 접속자 수 갱신 |

## 채널 REST API 호출

| 액션 | 메서드/경로 | 인증 |
|---|---|---|
| 채널 목록 | `GET /channels` | 없음 |
| 채널 생성 | `POST /channels` (`{ name }`) | Bearer |
| 채널 삭제 | `DELETE /channels/{name}` | Bearer |

인증이 필요한 요청은 `apiFetch()`로 처리 — 자동으로 `Authorization: Bearer {token}` 헤더 첨부.
401 응답 시 refresh token으로 자동 갱신 후 재시도. 갱신도 실패하면 로그인 화면으로 전환.

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
- 앱 초기화 시 `auth.isLoggedIn()`이면 채널 목록 화면으로 바로 진입.
