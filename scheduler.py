"""백그라운드 스케줄러 - 공공데이터 자동 수집, 마감 기한 지난 공고 삭제"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from scripts.scheduler_service import delete_expired_job_posts
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_senior_jobs_task():
    """공공데이터 수집 작업"""
    try:
        logger.info("🔄 공공데이터 수집 시작...")
        from app import app
        from scripts.fetch_senior_jobs import fetch_and_store_jobs
        
        with app.app_context():
            fetch_and_store_jobs()
        
        logger.info("✅ 공공데이터 수집 완료!")
    except Exception as e:
        logger.error(f"❌ 공공데이터 수집 실패: {e}")


def delete_expired_jobs_task():
    """만료된 공고 삭제 작업"""
    try:
        logger.info("🗑️ 만료된 공고 삭제 시작...")
        from app import app


        with app.app_context():
            delete_expired_job_posts()

        logger.info("✅ 만료된 공고 삭제 완료!")
    except Exception as e:
        logger.error(f"❌ 만료된 공고 삭제 실패: {e}")

def start_scheduler():
    """스케줄러 시작"""
    scheduler = BackgroundScheduler()
    
    # 매일 오전 3시에 실행
    scheduler.add_job(
        func=fetch_senior_jobs_task,
        trigger=CronTrigger(hour=3, minute=0),
        id='fetch_senior_jobs',
        name='공공데이터 수집',
        replace_existing=True
    )
    
    # 앱 시작 시 한 번 실행 (선택사항)
    # scheduler.add_job(
    #     func=fetch_senior_jobs_task,
    #     trigger='date',
    #     id='fetch_senior_jobs_startup',
    #     name='공공데이터 수집 (시작시)'
    # )

    scheduler.add_job(
        func=delete_expired_jobs_task,
        trigger=CronTrigger(hour=4, minute=0),
        id='delete_expired_jobs',
        name='만료 공고 삭제',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("⏰ 스케줄러 시작됨 - 매일 오전 3시 실행")
    
    return scheduler
