from fastapi import APIRouter, HTTPException, UploadFile, File
from services.etf_service import recommend_etf, generate_rebalance_report, check_openai_api_key, vector_db
from schemas import CustomerProfile, ETFRecommendation, RebalanceReport, RebalanceReportRequest, CustomerRequest, FinancialStatus
import pandas as pd
import os
import shutil
from config import BASE_DIR, DOCS_PATH
from datetime import datetime
import logging
from typing import Dict, Any

router = APIRouter(prefix="/api/v1", tags=["etf"])
logger = logging.getLogger(__name__)

@router.get("/health")
def health_check():
    return {"status": "healthy"}

@router.get("/health/openai")
def openai_health_check():
    try:
        is_valid = check_openai_api_key()
        return {
            "status": "success" if is_valid else "error",
            "openai_api_key": "valid" if is_valid else "invalid"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/customer-etf-analysis", response_model=Dict[str, Any])
async def analyze_customer_etf(request: CustomerRequest) -> Dict[str, Any]:
    """
    고객의 ETF 포트폴리오를 분석하고 추천합니다.
    
    Args:
        request: 고객 정보 요청
        
    Returns:
        Dict[str, Any]: ETF 분석 결과
    """
    try:
        logger.info(f"ETF 분석 요청 수신: customer_id={request.customer_id}, name={request.name}")
        
        # 고객 데이터 파일 경로
        customer_data_path = os.path.join(BASE_DIR, "data", "customer", "customer_data_20250420_004757.csv")
        
        if not os.path.exists(customer_data_path):
            raise HTTPException(status_code=404, detail="고객 데이터 파일을 찾을 수 없습니다.")
        
        # CSV 파일에서 고객 정보 읽기
        df = pd.read_csv(customer_data_path)
        customer_data = df[df['customer_id'] == request.customer_id]
        
        if customer_data.empty:
            raise HTTPException(status_code=404, detail="고객을 찾을 수 없습니다.")
        
        # 고객 프로필 정보 가져오기
        financial_status = eval(customer_data['financial_status'].iloc[0])
        risk_tolerance = customer_data['risk_tolerance'].iloc[0]
        age = customer_data['age'].iloc[0]
        has_etf = customer_data['has_etf'].iloc[0]
        current_etf_holdings = customer_data['current_etf_holdings'].iloc[0]
        
        # ETF 보유 여부에 따른 처리
        if has_etf and pd.notna(current_etf_holdings):
            # ETF 보유 고객의 경우 리밸런싱 리포트 생성
            logger.info(f"ETF 보유 고객 리밸런싱 리포트 생성: {request.customer_id}")
            result = await get_rebalance_report(RebalanceReportRequest(
                customer_id=request.customer_id,
                current_etf_holdings=current_etf_holdings,
                risk_tolerance=risk_tolerance,
                age=age,
                financial_status=financial_status
            ))
        else:
            # ETF 미보유 고객의 경우 ETF 추천
            logger.info(f"ETF 미보유 고객 추천: {request.customer_id}")
            result = await recommend_etf(
                customer_id=request.customer_id,
                risk_tolerance=risk_tolerance,
                age=age,
                financial_status=financial_status,
                etfs_owned=None
            )
        
        logger.info(f"ETF 분석 완료: {result}")
        return result
        
    except HTTPException as e:
        logger.error(f"HTTP 에러 발생: {str(e)}")
        raise
        
    except Exception as e:
        logger.error(f"ETF 분석 중 오류 발생: {str(e)}")
        # 기본 ETF 추천 반환
        return {
            "recommendations": ["SPY - SPDR S&P 500 ETF Trust", "QQQ - Invesco QQQ Trust", "VTI - Vanguard Total Stock Market ETF"],
            "reasons": "죄송합니다. 현재 시스템에 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주시기 바랍니다."
        }

@router.post("/recommend-etf", response_model=ETFRecommendation)
async def get_etf_recommendation(customer: CustomerProfile):
    try:
        # Convert comma-separated string to list
        etfs_owned = customer.current_etf_holdings.split(',') if customer.current_etf_holdings else []
        
        result = await recommend_etf(
            customer_id=customer.customer_id,
            risk_tolerance=customer.risk_tolerance,
            age=customer.age,
            financial_status=customer.financial_status,
            etfs_owned=etfs_owned
        )
        return ETFRecommendation(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rebalance-report", response_model=Dict[str, Any])
async def get_rebalance_report(request: RebalanceReportRequest):
    try:
        # 고객 데이터 파일 경로
        customer_data_path = os.path.join(BASE_DIR, "data", "customer", "customer_data_20250420_004757.csv")
        
        if not os.path.exists(customer_data_path):
            raise HTTPException(status_code=404, detail="고객 데이터 파일을 찾을 수 없습니다.")
        
        # CSV 파일에서 고객 정보 읽기
        df = pd.read_csv(customer_data_path)
        customer_data = df[df['customer_id'] == request.customer_id]
        
        if customer_data.empty:
            raise HTTPException(status_code=404, detail="고객을 찾을 수 없습니다.")
        
        # Convert comma-separated string to list
        etfs_owned = request.current_etf_holdings.split(',') if request.current_etf_holdings else []
        
        # 고객 프로필 정보 가져오기
        financial_status = eval(customer_data['financial_status'].iloc[0])
        risk_tolerance = customer_data['risk_tolerance'].iloc[0]
        age = customer_data['age'].iloc[0]
        
        result = await generate_rebalance_report(
            customer_id=request.customer_id,
            etfs_owned=etfs_owned,
            risk_tolerance=risk_tolerance,
            age=age,
            financial_status=financial_status
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-etf-knowledge")
async def update_etf_knowledge(pdf_file: UploadFile = File(...)):
    """
    새로운 ETF 정보를 PDF 파일과 함께 업데이트합니다.
    
    Args:
        pdf_file: 업로드된 PDF 파일
        
    Returns:
        Dict[str, Any]: 업데이트 결과
    """
    try:
        logger.info(f"ETF 지식 업데이트 요청 수신: {pdf_file.filename}")
        
        # PDF 파일 저장 경로
        pdf_path = os.path.join(DOCS_PATH, pdf_file.filename)
        
        # PDF 파일 저장
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)
        
        # Vector DB 업데이트
        update_result = vector_db.update_etf_data(pdf_path)
        
        if not update_result:
            raise HTTPException(status_code=500, detail="Vector DB 업데이트 실패")
        
        return {
            "status": "success",
            "message": "ETF 지식이 성공적으로 업데이트되었습니다.",
            "filename": pdf_file.filename,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        logger.error(f"ETF 지식 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 