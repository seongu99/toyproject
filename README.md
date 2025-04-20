# ETF 추천 시스템

ETF 추천 시스템은 고객의 프로필과 투자 성향을 분석하여 적절한 ETF를 추천하고, 포트폴리오 리밸런싱을 제안하는 서비스입니다.

## 시스템 구성

### Back-end
- **기술 스택**: FastAPI, OpenAI API, FAISS (Vector DB)
- **주요 기능**:
  - 고객 프로필 기반 ETF 추천
  - 포트폴리오 리밸런싱 분석
  - ETF 지식 베이스 업데이트
  - 시스템 상태 모니터링 (Prometheus, Grafana)
- **API 엔드포인트**:
  - `/api/v1/health`: 시스템 상태 확인
  - `/api/v1/customer-etf-analysis`: 고객 ETF 분석
  - `/api/v1/update-etf-knowledge`: ETF 지식 업데이트

### Front-end
- **기술 스택**: Streamlit
- **주요 기능**:
  - 고객 정보 입력 및 ETF 분석 요청
  - ETF 추천 결과 표시
  - 포트폴리오 리밸런싱 리포트 표시
  - ETF 지식 업데이트를 위한 PDF 파일 업로드

## 설치 및 실행

### Back-end
```bash
cd back-end
pip install -r requirements.txt
uvicorn main:app --reload
```

### Front-end
```bash
cd front-end
pip install -r requirements.txt
streamlit run app.py
```

## 환경 변수 설정
`.env` 파일에 다음 변수들을 설정해야 합니다:
- `OPENAI_API_KEY`: OpenAI API 키
- `API_BASE_URL`: Back-end API 기본 URL

## 데이터 구조
- 고객 데이터: CSV 형식 (`data/customer/`)
- ETF 문서: PDF 형식 (`data/docs/`)
- Vector DB: FAISS 기반 (`data/vector_db/`) 