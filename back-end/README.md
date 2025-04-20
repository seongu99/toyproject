# ETF 추천 시스템

ETF 추천 시스템은 고객의 프로필과 투자 성향을 분석하여 적절한 ETF를 추천하고, 포트폴리오 리밸런싱을 제안하는 서비스입니다.

## 주요 기능

1. 고객 프로필 기반 ETF 추천
2. 포트폴리오 리밸런싱 분석
3. ETF 지식 베이스 업데이트
4. 시스템 상태 모니터링

## API 엔드포인트

### 1. 시스템 상태 확인
- `GET /api/v1/health`
  - 시스템 상태 확인
  - 응답: `{"status": "healthy"}`

- `GET /api/v1/health/openai`
  - OpenAI API 상태 확인
  - 응답: `{"status": "success/error", "openai_api_key": "valid/invalid"}`

### 2. 고객 ETF 분석
- `POST /api/v1/customer-etf-analysis`
  - 고객의 ETF 포트폴리오 분석 및 추천
  - 요청:
    ```json
    {
      "customer_id": "string",
      "name": "string"
    }
    ```
  - 응답: ETF 추천 또는 리밸런싱 리포트

### 3. ETF 추천
- `POST /api/v1/recommend-etf`
  - 고객 프로필 기반 ETF 추천
  - 요청:
    ```json
    {
      "customer_id": "string",
      "risk_tolerance": "string",
      "age": "integer",
      "financial_status": {
        "income": "integer",
        "savings": "integer",
        "monthly_investment": "integer"
      },
      "current_etf_holdings": "string"
    }
    ```
  - 응답: 추천 ETF 목록 및 이유

### 4. 리밸런싱 리포트
- `POST /api/v1/rebalance-report`
  - ETF 포트폴리오 리밸런싱 분석
  - 요청:
    ```json
    {
      "customer_id": "string",
      "current_etf_holdings": "string",
      "risk_tolerance": "string",
      "age": "integer",
      "financial_status": {
        "income": "integer",
        "savings": "integer",
        "monthly_investment": "integer"
      }
    }
    ```
  - 응답: 포트폴리오 분석 및 리밸런싱 제안

### 5. ETF 지식 업데이트
- `POST /api/v1/update-etf-knowledge`
  - 새로운 ETF 정보 업데이트
  - 요청: PDF 파일 업로드
  - 응답:
    ```json
    {
      "status": "success",
      "message": "string",
      "filename": "string",
      "update_time": "string"
    }
    ```

## 시스템 요구사항

- Python 3.8 이상
- FastAPI
- OpenAI API
- FAISS (Vector DB)
- PyMuPDF (PDF 처리)
- pandas (데이터 처리)

## 설치 및 실행

1. 가상 환경 생성 및 활성화:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 또는
   .\venv\Scripts\activate  # Windows
   ```

2. 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```

3. 환경 변수 설정:
   - `.env` 파일 생성
   - OpenAI API 키 설정

4. 서버 실행:
   ```bash
   uvicorn main:app --reload
   ```

## 데이터 구조

### 고객 데이터
- CSV 형식
- 위치: `data/customer/customer_data_YYYYMMDD_HHMMSS.csv`
- 필드:
  - customer_id
  - name
  - age
  - risk_tolerance
  - financial_status
  - has_etf
  - current_etf_holdings

### ETF 문서
- PDF 형식
- 위치: `data/docs/`
- Vector DB에 저장되어 검색 및 추천에 활용

## 모니터링

- Prometheus 메트릭 수집
- Grafana 대시보드 연동
- 토큰 사용량 모니터링

## 에러 처리

- HTTP 예외 처리
- 기본 ETF 추천 제공
- 상세한 로깅 