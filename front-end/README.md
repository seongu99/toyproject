# ETF 추천 시스템 Front-end

이 프로젝트는 ETF 추천 및 포트폴리오 분석을 위한 Streamlit 기반의 프론트엔드 애플리케이션입니다.

## 설치 방법

1. Python 3.8 이상이 설치되어 있어야 합니다.
2. 필요한 패키지를 설치합니다:
   ```bash
   pip install -r requirements.txt
   ```

## 실행 방법

1. 백엔드 API 서버가 실행 중인지 확인합니다.
2. `.env` 파일에서 API_BASE_URL을 백엔드 서버 주소로 설정합니다.
3. 다음 명령어로 Streamlit 애플리케이션을 실행합니다:
   ```bash
   streamlit run app.py
   ```

## 기능

- 고객 ID와 이름을 입력하여 ETF 분석 요청
- ETF 추천 결과 확인
- 포트폴리오 리밸런싱 리포트 확인
- API 서버 상태 모니터링

## 환경 변수

- `API_BASE_URL`: 백엔드 API 서버의 기본 URL (기본값: http://localhost:8000) 