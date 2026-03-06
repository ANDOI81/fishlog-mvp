# FishLog MVP (카톡 주문 링크용 웹 MVP)

이 폴더는 **주문(거래처) → 관리자 확인/배차 → 기사 진행 상태**까지 최소 기능을 갖춘 MVP입니다.

## 핵심 URL
- 홈: http://127.0.0.1:8000/
- 관리자 로그인: http://127.0.0.1:8000/admin/login
- 기사 로그인: http://127.0.0.1:8000/driver/login
- 거래처 주문 링크: 관리자 화면에서 복사

## 기본 계정(데모)
- 관리자: owner / owner1234
- 기사1: driver1 / driver1234
- 기사2: driver2 / driver1234

## 윈도우 원클릭 실행
run_windows.bat 더블클릭

## 휴대폰 시연(같은 Wi‑Fi)
```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
노트북 IP로 접속: http://192.168.x.x:8000


## v2 변경사항
- 주문 시 어종 선택(밀치/광어/우럭)
- 날짜 선택 UI 개선(어제/오늘/내일 버튼 + 달력)


## v3 변경사항
- 관리자: 날짜별 작업 가능 품목 설정(/admin/catalog)
- 관리자: 날짜별 단가 입력(/admin/prices) — 단가 미정 가능
- 주문: 어종+사이즈 선택, 단가/총액 표시(미정 가능)
- 거래처: 날짜별 주문내역(/o/{token}/history)


## v4-A 추가 기능(정산/미수금/할인)
- 주문 할인(원) 입력 + 실매출(net_total) 자동 계산
- 거래처 입금 내역(날짜별) 등록/삭제
- 월간 정산(전체 + 거래처별) 화면(/admin/settlement) + 엑셀 다운로드(/admin/settlement.xlsx)
- 거래처 상세 정산/입금 페이지(/admin/customers/{id})
