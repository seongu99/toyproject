import streamlit as st
import requests
import json
from typing import Dict, Any
import os
from dotenv import load_dotenv
import io

# 환경 변수 로드
load_dotenv()

# API 기본 URL 설정
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def check_api_health() -> bool:
    """API 서버 상태 확인"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/health")
        return response.status_code == 200
    except:
        return False

def display_analysis_results(result: Dict[str, Any]):
    """분석 결과 표시"""
    if 'report' in result:
        # ETF 보유 고객의 경우
        st.header("📊 포트폴리오 성과 분석")
        st.markdown(result['performance_analysis'])
        
        st.header("🔄 리밸런싱 필요성")
        st.markdown(result['report'].split('2. 리밸런싱 필요성')[1].split('3. 리밸런싱 제안')[0])
        
        st.header("💡 리밸런싱 제안")
        st.markdown(result['suggestions'])
        
        if result['rebalancing_needed']:
            st.warning("⚠️ 포트폴리오 리밸런싱이 필요합니다.")
        else:
            st.success("✅ 현재 포트폴리오는 적절한 상태입니다.")
            
    elif 'recommendations' in result:
        # ETF 미보유 고객의 경우
        st.header("📈 ETF 추천")
        
        for i, (etf, reason) in enumerate(zip(result['recommendations'], result['reasons']), 1):
            st.subheader(f"추천 {i}: {etf}")
            st.markdown(reason)
            st.divider()  # 구분선 추가
                
        st.info("💡 위 추천은 고객님의 위험 감내도와 투자 여건을 고려하여 선정되었습니다.")

def analyze_customer_etf(customer_id: str, name: str) -> Dict[str, Any]:
    """고객 ETF 분석 API 호출"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/customer-etf-analysis",
            json={"customer_id": customer_id, "name": name}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 실패: {str(e)}")
        return None

def update_etf_knowledge(pdf_file: bytes, filename: str) -> Dict[str, Any]:
    """ETF 지식 업데이트 요청"""
    try:
        files = {
            'pdf_file': (filename, pdf_file, 'application/pdf')
        }
        response = requests.post(
            f"{API_BASE_URL}/api/v1/update-etf-knowledge",
            files=files
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"ETF 지식 업데이트 중 오류 발생: {str(e)}")
        return {}

def main():
    st.set_page_config(
        page_title="ETF 추천 시스템",
        page_icon="📈",
        layout="wide"
    )
    
    # API 상태 확인
    if not check_api_health():
        st.error("API 서버에 연결할 수 없습니다. 서버 상태를 확인해주세요.")
        return
    
    # 고객 정보 입력 섹션
    st.sidebar.header("👤 고객 정보 입력")
    customer_id = st.sidebar.text_input("고객 ID")
    name = st.sidebar.text_input("이름")
    
    if st.sidebar.button("분석 시작"):
        if not customer_id or not name:
            st.sidebar.error("고객 ID와 이름을 모두 입력해주세요.")
        else:
            with st.spinner("고객 ETF 분석 중..."):
                result = analyze_customer_etf(customer_id, name)
                if result:
                    display_analysis_results(result)
                else:
                    st.error("ETF 분석에 실패했습니다.")

    # PDF 업로더 섹션
    st.sidebar.header("📄 ETF 지식 업데이트")
    pdf_file = st.sidebar.file_uploader(
        "ETF 정보 PDF 파일을 업로드하세요",
        type=['pdf'],
        help="ETF 정보가 포함된 PDF 파일을 업로드하세요"
    )
    
    if pdf_file and st.sidebar.button("업데이트 시작"):
        with st.spinner("ETF 지식 업데이트 중..."):
            success = update_etf_knowledge(pdf_file, pdf_file.name)
            if success:
                st.sidebar.success("ETF 지식이 성공적으로 업데이트되었습니다.")
            else:
                st.sidebar.error("ETF 지식 업데이트에 실패했습니다.")
    
if __name__ == "__main__":
    main() 