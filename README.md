# Consumables Order Automation API

Excel 거래명세서를 업로드하면 품목과 입고 데이터를 자동으로 읽어 SQLite DB에 저장하고, 재고 및 사용 이력을 기준으로 발주 시점과 추천 발주수량을 계산해 발주요청서 Excel을 생성하는 FastAPI 프로젝트입니다.

실제 소모품 구매·재고 관리 업무에서 Excel 거래명세서를 수기로 확인하고 재고와 발주수량을 관리하던 과정을 자동화하는 것을 목표로 제작했습니다.

---

## 1. 주요 기능

- Excel 거래명세서 업로드
- 거래명세서 데이터 자동 파싱
- 기존 품목 자동 매칭
- 신규 품목 자동 등록
- 동일 거래명세서 중복 등록 방지
- 입고 이력 SQLite DB 저장
- 현재 재고 자동 계산
- 품목별 평균 사용량 계산
- 안전재고 계산
- 재발주점 계산
- 예상 발주일 계산
- 추천 발주수량 계산
- 발주요청서 Excel 자동 생성
- FastAPI Swagger를 통한 API 테스트

---

## 2. 프로젝트 개발 배경

소모품 관리 업무를 수행하면서 다음과 같은 문제를 경험했습니다.

- 거래명세서 내용을 수기로 관리대장에 입력해야 하는 문제
- 품목별 사용량을 직접 확인해야 하는 문제
- 안전재고 부족으로 긴급 발주가 발생하는 문제
- 반대로 필요 이상으로 재고를 보유하는 문제
- 발주 시점과 발주수량을 담당자의 경험에 의존하는 문제

이 프로젝트에서는 거래명세서 Excel을 입력 데이터로 사용하고, 데이터를 DB에 누적한 뒤 과거 재고 및 사용 이력을 기준으로 필요한 발주수량을 계산하도록 구성했습니다.

---

## 3. 전체 처리 흐름

```text
거래명세서 Excel
        ↓
FastAPI 업로드
        ↓
Excel 데이터 파싱
        ↓
품목 정보 확인
        ↓
기존 품목 매칭 / 신규 품목 생성
        ↓
SQLite DB 저장
        ↓
현재 재고 계산
        ↓
사용량 분석
        ↓
안전재고 및 재발주점 계산
        ↓
예상 발주일 및 추천 발주수량 계산
        ↓
발주요청서 Excel 생성
```

---

## 4. 기술 스택

### Backend

- Python 3.11
- FastAPI
- Uvicorn

### Database

- SQLite

### Excel 처리

- OpenPyXL

### API 문서 및 테스트

- Swagger UI

---

## 5. 프로젝트 구조

```text
consumables-order-api/
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── excel_service.py
│   ├── inbound_service.py
│   ├── inventory_service.py
│   ├── order_service.py
│   └── seed_demo.py
│
├── sample/
│   ├── make_sample_excel.py
│   └── sample_purchase_statement.xlsx
│
├── data/
│
├── output/
│
├── requirements.txt
├── .gitignore
└── README.md
```

### 주요 파일 설명

`main.py`

FastAPI 애플리케이션과 API 엔드포인트를 관리합니다.

`database.py`

SQLite 연결 및 데이터베이스 테이블 생성을 담당합니다.

`excel_service.py`

업로드된 Excel 거래명세서를 읽고 필요한 데이터를 추출합니다.

`inbound_service.py`

거래명세서 데이터를 기존 품목과 매칭하고 DB에 입고 이력을 저장합니다.

`inventory_service.py`

현재 재고, 평균 사용량, 안전재고, 재발주점, 예상 발주일 및 추천 발주수량을 계산합니다.

`order_service.py`

발주 대상 품목을 정리하여 발주요청서 Excel 파일을 생성합니다.

`seed_demo.py`

프로젝트 테스트에 사용할 샘플 품목 및 사용 이력을 생성합니다.

---

# 6. 설치 방법

## 6-1. 프로젝트 다운로드

GitHub에서 프로젝트를 다운로드하거나 Git을 사용하는 경우 clone 합니다.

```bash
git clone https://github.com/사용자아이디/consumables-order-api.git
```

프로젝트 폴더로 이동합니다.

```bash
cd consumables-order-api
```

Git을 사용하지 않는 경우 GitHub의 `Code → Download ZIP`을 이용해 다운로드한 뒤 압축을 풀어도 됩니다.

---

## 6-2. Python 버전 확인

Python 3.11 사용을 권장합니다.

```bash
python3 --version
```

또는 Windows에서는 다음 명령어를 사용할 수 있습니다.

```bash
python --version
```

예시:

```text
Python 3.11.x
```

---

## 6-3. 가상환경 생성

### macOS / Linux

```bash
python3 -m venv .venv
```

### Windows

```powershell
python -m venv .venv
```

---

## 6-4. 가상환경 활성화

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### Windows CMD

```cmd
.venv\Scripts\activate
```

가상환경이 정상적으로 활성화되면 터미널 앞에 다음과 같이 표시됩니다.

```text
(.venv)
```

---

## 6-5. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

주요 패키지는 다음과 같습니다.

```text
fastapi
uvicorn
python-multipart
openpyxl
```

---

# 7. 테스트 데이터 생성

이 프로젝트에는 실제 회사 데이터가 포함되어 있지 않습니다.

API 기능을 테스트하기 위해 샘플 데이터를 먼저 생성할 수 있습니다.

프로젝트 최상위 폴더에서 다음 명령어를 실행합니다.

```bash
python -m backend.seed_demo
```

정상적으로 실행되면 테스트용 품목과 재고 사용 이력이 SQLite DB에 생성됩니다.

예시:

```text
Demo data seeded.
```

SQLite DB 파일은 실행 과정에서 `data` 폴더에 생성됩니다.

---

# 8. FastAPI 서버 실행

프로젝트 최상위 폴더에서 다음 명령어를 실행합니다.

```bash
python -m uvicorn backend.main:app --reload
```

정상적으로 실행되면 다음과 비슷한 메시지가 표시됩니다.

```text
Uvicorn running on http://127.0.0.1:8000
```

서버가 실행 중인 터미널은 종료하지 않습니다.

---

# 9. Swagger 접속

웹 브라우저에서 다음 주소로 접속합니다.

```text
http://127.0.0.1:8000/docs
```

FastAPI에서 자동 생성한 Swagger 화면에서 각 API를 직접 실행할 수 있습니다.

---

# 10. 기본 사용 방법

API 사용 순서는 다음과 같습니다.

```text
1. 거래명세서 미리보기
2. 거래명세서 DB 반영
3. 재고 확인
4. 발주 분석 확인
5. 발주요청서 생성
```

---

# 11. 거래명세서 미리보기

Swagger에서 다음 API를 선택합니다.

```text
POST /imports/inbound/preview
```

`Try it out` 버튼을 누른 뒤 Excel 파일을 선택합니다.

테스트용 파일은 다음 위치에 있습니다.

```text
sample/sample_purchase_statement.xlsx
```

파일을 선택한 뒤 `Execute`를 누릅니다.

예시 결과:

```json
{
  "duplicate": false,
  "total_rows": 3,
  "existing_count": 2,
  "new_item_count": 1
}
```

각 항목의 의미는 다음과 같습니다.

```text
duplicate
동일한 거래명세서가 이미 등록되어 있는지 여부

total_rows
Excel에서 읽어온 전체 품목 수

existing_count
기존 DB 품목과 일치한 품목 수

new_item_count
신규로 등록될 품목 수
```

Preview API는 데이터를 확인하기 위한 기능이며 실제 DB에는 저장하지 않습니다.

---

# 12. 거래명세서 DB 반영

미리보기 결과에 문제가 없다면 다음 API를 사용합니다.

```text
POST /imports/inbound/commit
```

`Try it out`을 누른 뒤 같은 Excel 파일을 선택합니다.

`Execute`를 누르면 거래명세서 데이터가 DB에 저장됩니다.

예시:

```json
{
  "message": "입고 Excel DB 반영 완료",
  "saved_count": 3,
  "new_item_count": 1,
  "total_quantity": 6
}
```

기존에 존재하지 않는 품목은 자동으로 신규 품목 코드가 생성됩니다.

예:

```text
AUTO0001
AUTO0002
AUTO0003
```

---

# 13. 중복 거래명세서 방지

이미 DB에 반영한 Excel을 다시 `commit`하면 중복 등록을 방지합니다.

예상 응답:

```text
409 Conflict
```

예시 메시지:

```text
이미 DB에 반영된 Excel입니다.
```

거래명세서의 내용을 기준으로 fingerprint를 생성하여 동일 데이터의 중복 적재를 방지하도록 구성했습니다.

파일 이름만 변경한 경우에도 데이터 내용이 동일하면 중복으로 판단할 수 있도록 설계했습니다.

---

# 14. 품목 조회

등록된 품목은 다음 API에서 확인할 수 있습니다.

```text
GET /items
```

`Try it out → Execute`를 누르면 등록된 품목 목록이 표시됩니다.

---

# 15. 현재 재고 확인

다음 API를 실행합니다.

```text
GET /inventory
```

현재 재고는 다음 방식으로 계산합니다.

```text
현재 재고
=
기초재고
+
총 입고수량
-
총 출고수량
```

예시:

```json
{
  "item_code": "DEMO001",
  "item_name": "샘플 고무장갑 M",
  "current_stock": 15
}
```

---

# 16. 발주 분석 확인

전체 품목에 대한 발주 분석은 다음 API에서 확인할 수 있습니다.

```text
GET /analytics/reorder
```

특정 품목만 조회하려면 다음 API를 사용합니다.

```text
GET /analytics/reorder/{item_code}
```

예:

```text
GET /analytics/reorder/DEMO001
```

주요 분석 결과는 다음과 같습니다.

```text
current_stock
현재 재고

avg_daily_demand
일평균 사용량

lead_time_days
평균 구매 리드타임

safety_days
안전재고 확보 일수

recommended_safety_stock
추천 안전재고

reorder_point
재발주점

days_until_reorder
발주 필요 시점까지 남은 일수

predicted_order_date
예상 발주일

recommended_order_qty_now
현재 기준 추천 발주수량
```

---

# 17. 안전재고 및 재발주 계산 방식

현재 버전에서는 포트폴리오용 MVP 로직으로 과거 사용량, 품절 발생 여부 및 구매 리드타임을 이용하여 안전재고를 계산합니다.

기본 개념은 다음과 같습니다.

```text
평균 일사용량
=
전체 사용량 / 사용기간

추천 안전재고
=
평균 일사용량 × 안전일수
```

재발주점은 다음 개념을