from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from routers.etf_router import router as etf_router
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from services.etf_service import vector_db_manager
from config import BASE_DIR
import logging
from datetime import datetime
import os
from contextlib import asynccontextmanager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작/종료 시 스케줄러 관리"""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        perform_incremental_update,
        trigger=CronTrigger(hour=23, minute=59),
        id="incremental_update",
        replace_existing=True
    )
    scheduler.start()
    logger.info("백그라운드 스케줄러 시작")
    yield
    scheduler.shutdown()
    logger.info("백그라운드 스케줄러 종료")

app = FastAPI(
    title="ETF Recommendation API",
    description="ETF 추천 및 포트폴리오 리밸런싱 서비스",
    version="1.0.0",
    lifespan=lifespan
)

# Prometheus 메트릭 노출
Instrumentator().instrument(app).expose(app)

# 라우터 등록
app.include_router(etf_router)

def perform_incremental_update():
    """매일 밤 11시 59분에 실행되는 증분 업데이트 작업"""
    try:
        logger.info(f"증분 업데이트 시작: {datetime.now()}")
        csv_path = os.path.join(BASE_DIR, "data", "docs", "etf_info.csv")
        success = vector_db_manager.update_etf_data(csv_path)
        if success:
            logger.info("증분 업데이트 성공")
        else:
            logger.error("증분 업데이트 실패")
    except Exception as e:
        logger.error(f"증분 업데이트 중 오류 발생: {str(e)}")

@app.get("/")
def home():
    return {"message": "ETF Recommendation API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
