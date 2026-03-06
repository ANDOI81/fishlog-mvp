# FishLog MVP Heroku 배포 가이드

이 문서는 **혼자 운영하는 비전문 개발자** 기준으로 작성되었습니다.

## 0) 사전 준비
- Heroku 계정
- GitHub 저장소(또는 로컬 git)
- Heroku CLI 설치

---

## 1) Heroku 앱 생성
터미널에서 프로젝트 루트(`FishLog_MVP...`)로 이동 후:

```bash
heroku login
heroku create <원하는-앱-이름>
```

앱 URL 확인:

```bash
heroku apps:info
```

---

## 2) Heroku Postgres 연결

```bash
heroku addons:create heroku-postgresql:essential-0
```

연결 확인:

```bash
heroku config:get DATABASE_URL
```

값이 나오면 정상입니다.

---

## 3) 환경변수 설정
필수 환경변수:

```bash
heroku config:set SESSION_SECRET="충분히긴랜덤문자열"
heroku config:set BASE_URL="https://<앱이름>.herokuapp.com"
```

선택 환경변수(로컬 SQLite 테스트용):
- `DB_PATH` (Heroku 운영에는 필요 없음)

> 운영 기준은 `DATABASE_URL` 입니다.

---

## 4) 배포 방법

```bash
git add .
git commit -m "Prepare Heroku deployment"
git push heroku main
```

브랜치가 `master`면:

```bash
git push heroku master
```

---

## 5) 로그 확인 방법

```bash
heroku logs --tail
```

정상 기동 시 예시:
- `Application startup complete`
- `Uvicorn running on ...`

---

## 6) 재배포 방법
코드 수정 후 동일하게:

```bash
git add .
git commit -m "update"
git push heroku main
```

---

## 7) 기능 점검 체크리스트
배포 후 아래 URL을 실제로 확인하세요.

1. `/` 홈 접속
2. `/admin/login` 로그인
3. 거래처 주문 링크(`/o/{token}`) 접속
4. 주문 생성
5. `/admin/dispatch` 배차
6. `/driver` 기사 화면
7. 배송 완료 / 되돌리기

---

## 8) 자주 발생하는 문제

### 문제 A) 앱이 바로 죽음
- `heroku logs --tail` 확인
- 대부분 `SESSION_SECRET` 누락, `DATABASE_URL` 문제

### 문제 B) 주문 링크가 localhost로 생성됨
- `BASE_URL`이 잘못됨
- 다음처럼 수정:
  ```bash
  heroku config:set BASE_URL="https://<앱이름>.herokuapp.com"
  ```

### 문제 C) DB 테이블 관련 에러
- 앱 시작 시 `init_db()`가 테이블/컬럼을 생성
- 그래도 에러면 로그 확인 후 재배포:
  ```bash
  git push heroku main
  ```

### 문제 D) 정적 파일(CSS) 미반영
- 캐시 문제일 수 있음: 강력 새로고침(Ctrl+F5)

---

## 9) 운영 팁
- 관리자 비밀번호(`owner1234`)는 운영 전에 반드시 변경하세요.
- `SESSION_SECRET`은 절대 코드에 하드코딩하지 마세요.
- Heroku 무료/저가 플랜 특성상 슬립/성능 제한이 있을 수 있습니다.

---

## 10) 운영 안전장치 (중요)
- Heroku/DYNO 환경에서 `DATABASE_URL`이 없으면 앱이 **의도적으로 시작 실패**합니다.
- 이유: 운영에서 SQLite fallback으로 조용히 실행되는 사고를 막기 위함입니다.

권장 설정:
```bash
heroku config:set APP_ENV=production
```

로컬 개발에서만 SQLite fallback을 사용하세요.
