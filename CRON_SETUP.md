# 외부 Cron 스케줄러 설정 가이드 (cron-job.org)

> GitHub Actions cron은 신뢰성이 낮아, 외부 스케줄러로 매일 workflow_dispatch API를 호출하여 확실한 실행을 보장합니다.

---

## 설정 순서

### Step 1. cron-job.org 회원가입

1. https://console.cron-job.org/signup 접속
2. 이메일로 회원가입 (무료)
3. 이메일 인증 완료

### Step 2. Cron Job 생성

로그인 후 **"CREATE CRONJOB"** 클릭, 아래와 같이 입력:

#### General 탭

| 항목 | 값 |
|------|-----|
| **Title** | `Startup Alert Bot - Daily Trigger` |
| **URL** | `https://api.github.com/repos/derekchang94/startup-alert-bot/actions/workflows/daily_collect.yml/dispatches` |
| **Enabled** | Yes (토글 ON) |

#### Schedule 탭

| 항목 | 값 |
|------|-----|
| **Schedule type** | Custom |
| **Timezone** | Asia/Seoul (UTC+9) |
| **Time** | 11:00 |
| **Days of week** | Every day (Mon~Sun 전부 선택) |

#### Advanced 탭 (중요!)

| 항목 | 값 |
|------|-----|
| **Request method** | POST |
| **Request body** | `{"ref":"main"}` |

**Headers** (Add Header 버튼으로 2개 추가):

| Header Key | Header Value |
|------------|--------------|
| `Authorization` | `Bearer <YOUR_GITHUB_TOKEN>` |
| `Accept` | `application/vnd.github.v3+json` |

### Step 3. 저장 및 테스트

1. **"CREATE"** 클릭하여 저장
2. 생성된 Job에서 **"Test Run"** 버튼 클릭
3. Response status가 **204** 이면 성공
4. GitHub Actions 탭에서 실행 확인: https://github.com/derekchang94/startup-alert-bot/actions

---

## 동작 구조

```
cron-job.org (KST 11:00 매일)
    ↓ POST /dispatches (workflow_dispatch 트리거)
GitHub Actions (workflow 실행)
    ↓ 공고 수집 + 필터링
Slack #series_a (알림 전송)
```

**백업:** GitHub Actions 자체 cron (`7 2 * * *` UTC)도 유지.
`concurrency` 설정으로 동시 실행 방지됨.

---

## 문제 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| Response 401 | 토큰 만료/무효 | `gh auth token`으로 새 토큰 확인 후 교체 |
| Response 404 | URL 오타 | URL을 다시 확인 |
| Response 422 | Body 형식 오류 | Body가 `{"ref":"main"}` 인지 확인 |
| 실행은 되지만 Slack 미수신 | GitHub Secrets 문제 | repo Settings > Secrets 확인 |

---

## 토큰 갱신

gh CLI 토큰(`gho_`)이 만료된 경우:
```bash
gh auth token
```
으로 새 토큰을 확인하고 cron-job.org의 Header에서 `Authorization` 값을 교체합니다.

더 안정적인 토큰이 필요하면 GitHub Classic PAT를 생성하세요:
Settings > Developer settings > Personal access tokens > Tokens (classic) > `repo`, `workflow` 스코프 선택
