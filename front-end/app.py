import streamlit as st
import requests
import json
from typing import Dict, Any
import os
from dotenv import load_dotenv

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

def analyze_customer_etf(customer_id: str, name: str) -> Dict[str, Any]:
    """고객 ETF 분석 요청"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/customer-etf-analysis",
            json={"customer_id": customer_id, "name": name}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 중 오류 발생: {str(e)}")
        return {}

def main():
    st.set_page_config(
        page_title="ETF 추천 시스템",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 ETF 추천 및 포트폴리오 분석 시스템")
    
    # API 서버 상태 확인
    if not check_api_health():
        st.error("API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return
    
    # 사이드바 설정
    st.sidebar.title("고객 정보 입력")
    customer_id = st.sidebar.text_input("고객 ID", value="30a06289-187f-4ed5-bbb1-1900f8f08def")
    customer_name = st.sidebar.text_input("고객 이름", value="김준서")
    
    if st.sidebar.button("분석 시작"):
        with st.spinner("ETF 분석 중..."):
            result = analyze_customer_etf(customer_id, customer_name)
            
            if result:
                st.success("분석이 완료되었습니다!")
                
                # 분석 정보 표시
                st.header("📅 분석 정보")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**고객 ID:** {result.get('customer_id', 'N/A')}")
                with col2:
                    st.write(f"**분석일자:** {result.get('analysis_date', 'N/A')}")
                
                # 포트폴리오 성과 분석
                st.header("📊 포트폴리오 성과 분석")
                st.write(result.get("performance_analysis", "성과 분석 정보가 없습니다."))
                
                # 리밸런싱 필요성
                st.header("🔄 리밸런싱 필요성")
                rebalancing_needed = result.get("rebalancing_needed", False)
                st.write(f"**리밸런싱 필요 여부:** {'필요함' if rebalancing_needed else '필요하지 않음'}")
                
                # 리밸런싱 제안
                st.header("💡 리밸런싱 제안")
                st.write(result.get("suggestions", "리밸런싱 제안 정보가 없습니다."))
                

if __name__ == "__main__":
    main() 