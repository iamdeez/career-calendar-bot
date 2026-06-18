# 디스코드에 구글 캘린더 연동하기

Discord 슬래시 커맨드로 Google Calendar에 일정을 추가·조회하고, 매일 D-3 이내 임박 일정을 자동 알림하는 봇.

---

## 기술 스택

| 항목 | 선택 |
|---|---|
| 언어 | Python 3.11 |
| 패키지 관리 | uv |
| Discord API | discord.py 2.x |
| Google API | google-api-python-client, google-auth-oauthlib |
| 배포 | Docker + fly.io |

---

## 프로젝트 구조

```
career-calendar-bot/
├── main.py                  # 진입점
├── src/
│   ├── bot.py               # Discord 클라이언트, 슬래시 커맨드, 자동 알림
│   ├── calendar_service.py  # Google Calendar API 래퍼
│   └── cert_data.py         # IT 자격증 정보 데이터
├── credentials.json         # Google OAuth 클라이언트 (git 제외)
├── token.json               # Google OAuth 토큰 (git 제외)
├── Dockerfile
├── fly.toml
└── pyproject.toml
```

---

## 슬래시 커맨드

| 커맨드 | 설명 |
|---|---|
| `/일정추가` | Google Calendar에 일정 추가 |
| `/일정목록` | 특정 월의 일정 조회 |
| `/다음일정` | N일 이내 예정 일정 조회 |
| `/디데이` | 일정 또는 자격증 D-day 조회 |
| `/자격증정보` | IT 자격증 정보 조회 |

자동 알림: 24시간마다 실행 — D-3 이내 임박 일정이 있으면 지정 채널에 알림.

---

## 로컬 실행

### 1. Google Cloud Console에서 credentials.json 발급

1. [Google Cloud Console](https://console.cloud.google.com) → 새 프로젝트 생성
2. **API 및 서비스 → 라이브러리** → Google Calendar API 활성화
3. **사용자 인증 정보 → OAuth 2.0 클라이언트 ID** 생성 (데스크톱 앱)
4. `credentials.json` 다운로드 후 프로젝트 루트에 위치

### 2. 환경변수 설정

```bash
cp .env.example .env
# .env 파일에 값 입력
```

| 변수 | 설명 |
|---|---|
| `DISCORD_TOKEN` | Discord 봇 토큰 |
| `DISCORD_GUILD_ID` | Discord 서버 ID |
| `CALENDAR_ID` | Google Calendar ID |
| `REMINDER_CHANNEL_ID` | 자동 알림 채널 ID (선택) |

### 3. 실행

```bash
uv run python main.py
```

최초 실행 시 브라우저가 열리며 Google 계정 승인 요청 → 승인하면 `token.json` 자동 생성.

---

## fly.io 배포

### 1. 앱 생성

```bash
fly apps create career-calendar-bot
```

### 2. 환경변수 등록

```bash
fly secrets set \
  DISCORD_TOKEN="..." \
  DISCORD_GUILD_ID="..." \
  CALENDAR_ID="..." \
  REMINDER_CHANNEL_ID="..." \
  GOOGLE_CREDENTIALS_JSON="$(cat credentials.json)" \
  GOOGLE_TOKEN_JSON="$(cat token.json)"
```

> `GOOGLE_CREDENTIALS_JSON`, `GOOGLE_TOKEN_JSON`은 로컬에서 먼저 실행해 `token.json`을 발급받은 뒤 등록한다.

### 3. 배포

```bash
fly deploy
```

### 4. 로그 확인

```bash
fly logs
```

---

## 주의사항

- `fly.toml`에 `[http_service]` 블록이 있으면 트래픽 없을 때 머신이 꺼진다. 반드시 제거.
- `credentials.json`, `token.json`은 `.gitignore`에 포함되어 있으므로 git에 커밋되지 않는다.
