# 스타트업 지원사업 공고 알림 봇 - 셋업 가이드

> 이 가이드를 따라 순차적으로 진행하면 매일 오전 11시에 Slack #series_a 채널로 자동 공고 알림이 동작합니다.

---

## 전체 진행 순서

```
Step 1. 공공데이터포털 API 키 발급 (10~20분)
Step 2. Slack App 생성 + Webhook 설정 (10분)
Step 3. 로컬에서 동작 테스트 (5분)
Step 4. GitHub 리포지토리 생성 + 코드 Push (10분)
Step 5. GitHub Secrets 등록 (5분)
Step 6. GitHub Actions 수동 실행 테스트 (5분)
Step 7. 자동 스케줄 확인 + 완료
```

---

## Step 1. 공공데이터포털 API 키 발급

### 1-1. 회원가입
1. https://www.data.go.kr 접속
2. 우측 상단 "회원가입" 클릭
3. 일반회원으로 가입 (이메일 인증 필요)

### 1-2. API 활용 신청 (3개)

각 API 페이지에서 "활용신청" 버튼을 클릭합니다.

| API | 신청 페이지 |
|-----|-----------|
| 기업마당 지원사업 | https://www.data.go.kr 에서 "기업마당" 검색 → "중소기업 지원사업 공고 조회 서비스" 신청 |
| 중소벤처24 공고정보 | https://www.data.go.kr/data/15113191/openapi.do |
| K-Startup 창업지원 | https://www.data.go.kr 에서 "K-Startup" 검색 → "창업지원사업 공고정보" 신청 |

**활용신청 시 입력 사항:**
- 활용목적: "스타트업 지원사업 정보 수집 및 팀 내부 공유"
- 활용방법: "일 1회 자동 수집"

### 1-3. API 키 확인
1. 마이페이지 → "Open API" → "인증키 발급현황"
2. **일반 인증키(Encoding)** 를 복사하여 메모장에 저장
3. 보통 자동승인이지만, 최대 1~2일 소요될 수 있음

> ⚠️ API 키가 승인 대기 중이라면 Step 2~4를 먼저 진행하고, 승인 후 Step 5에서 등록하면 됩니다.

---

## Step 2. Slack App 생성 + Incoming Webhook 설정

### 2-1. Slack App 생성
1. https://api.slack.com/apps 접속 (워크스페이스 로그인 필요)
2. **"Create New App"** 클릭
3. **"From scratch"** 선택
4. App Name: `스타트업 공고 알리미` (또는 원하는 이름)
5. Workspace: 본인 워크스페이스 선택
6. **"Create App"** 클릭

### 2-2. Incoming Webhook 활성화
1. 왼쪽 사이드바 → **"Incoming Webhooks"** 클릭
2. 상단 토글을 **"On"** 으로 변경
3. 하단 **"Add New Webhook to Workspace"** 클릭
4. 채널 선택: **#series_a** (없으면 먼저 Slack에서 채널 생성)
5. **"Allow"** 클릭

### 2-3. Webhook URL 복사
```
xoxb-your-bot-token (Bot User OAuth Token)
```
이 URL을 안전한 곳에 복사해 둡니다.

### 2-4. Webhook 테스트 (터미널에서)
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"✅ 스타트업 공고 알림 봇 테스트 메시지입니다!"}' \
  "여기에_Webhook_URL_붙여넣기"
```
#series_a 채널에 메시지가 오면 성공!

---

## Step 3. 로컬에서 동작 테스트

### 3-1. 환경 설정
```bash
cd /Users/derek/Desktop/Claude_folder/Research_for_wyyyes/startup-alert-bot

# .env 파일 생성
cp .env.example .env
```

### 3-2. .env 파일 편집
.env 파일을 열어서 실제 값을 입력합니다:

```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL=series_a
BIZINFO_API_KEY=실제키
SMES_API_KEY=실제키
KSTARTUP_API_KEY=실제키
```

### 3-3. 의존성 설치 & 실행
```bash
# 가상환경 생성 (선택)
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 실행
python -m src.main
```

### 3-4. 확인
- 터미널에 수집 로그 출력 확인
- Slack #series_a 채널에 공고 메시지 수신 확인
- `data/postings.db` 파일 생성 확인

---

## Step 4. GitHub 리포지토리 생성 + 코드 Push

### 4-1. GitHub에서 리포지토리 생성
1. https://github.com/new 접속
2. Repository name: `startup-alert-bot`
3. **Public** 선택 (GitHub Actions 무료 사용을 위해)
4. "Add a README file" 체크 해제
5. **"Create repository"** 클릭

### 4-2. 코드 Push
```bash
cd /Users/derek/Desktop/Claude_folder/Research_for_wyyyes/startup-alert-bot

git init
git add -A
git commit -m "Initial commit: startup support alert bot"
git branch -M main
git remote add origin https://github.com/본인계정/startup-alert-bot.git
git push -u origin main
```

> ⚠️ `.env` 파일은 `.gitignore`에 포함되어 있어 push되지 않습니다 (API 키 보호)

---

## Step 5. GitHub Secrets 등록

GitHub Actions에서 사용할 환경변수를 Secrets로 등록합니다.

### 5-1. Secrets 설정 페이지 진입
1. GitHub 리포지토리 페이지 → **Settings** 탭
2. 왼쪽 사이드바 → **Secrets and variables** → **Actions**
3. **"New repository secret"** 클릭

### 5-2. 4개 Secret 등록

하나씩 추가합니다:

| Name | Value |
|------|-------|
| `SLACK_BOT_TOKEN` | `xoxb-...` (Bot User OAuth Token) |
| `SLACK_CHANNEL` | `series_a` |
| `BIZINFO_API_KEY` | 공공데이터포털 기업마당 API 인증키 |
| `SMES_API_KEY` | 공공데이터포털 중소벤처24 API 인증키 |
| `KSTARTUP_API_KEY` | 공공데이터포털 K-Startup API 인증키 |

---

## Step 6. GitHub Actions 수동 실행 테스트

### 6-1. 워크플로우 수동 실행
1. GitHub 리포지토리 → **Actions** 탭
2. 왼쪽 사이드바 → **"Daily Startup Support Postings Collector"** 클릭
3. 우측 **"Run workflow"** 버튼 클릭 → **"Run workflow"** 확인

### 6-2. 실행 결과 확인
1. 실행 중인 워크플로우 클릭 → 로그 확인
2. 각 Step(Checkout, Setup Python, Install, Run, Commit)이 녹색 체크인지 확인
3. Slack #series_a 채널에 공고 메시지가 도착하는지 확인

### 6-3. 문제 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| API 인증 실패 | 키 미승인 또는 오타 | data.go.kr 마이페이지에서 승인 상태 확인 |
| Slack 미수신 | Webhook URL 오류 | Secrets의 URL 재확인, curl로 테스트 |
| import 에러 | 의존성 문제 | requirements.txt 확인 |
| DB 커밋 실패 | 권한 부족 | workflow의 permissions: contents: write 확인 |

---

## Step 7. 자동 스케줄 확인 + 완료

### cron 스케줄
워크플로우는 다음 스케줄로 자동 실행됩니다:

```yaml
schedule:
  - cron: '0 2 * * *'   # UTC 02:00 = KST 11:00
```

**매일 한국시간 오전 11시**에 자동 실행됩니다.

### 주의사항
- GitHub Actions는 스케줄 실행 시 수분~수십분 지연이 발생할 수 있습니다
- **60일간 리포지토리 활동이 없으면** 스케줄이 비활성화됩니다
  → 최소 월 1회 커밋 또는 수동 실행 권장

### 운영 모니터링
- GitHub Actions 탭에서 매일 실행 로그 확인 가능
- 실패 시 GitHub에서 이메일 알림 발송
- `data/postings.db`에 수집 이력이 누적됨

---

## 완료! 🎉

이제 매일 오전 11시에 다음 흐름이 자동 실행됩니다:

```
공공데이터 API (기업마당 + 중소벤처24 + K-Startup)
    ↓ 수집
SQLite DB (중복 제거 + 신규 공고만 필터)
    ↓ 알림
Slack #series_a 채널 (Block Kit 포맷)
```
