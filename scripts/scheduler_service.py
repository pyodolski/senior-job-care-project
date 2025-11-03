from models import db, JobPost
from models import get_kst_now  # KST 시간 헬퍼
import logging

# 로깅 설정
logger = logging.getLogger(__name__)


def delete_expired_job_posts():
    try:
        today = get_kst_now().date()
        logger.info(f"[Scheduler] 만료된 공고 삭제 작업 실행 (기준일: {today})")

        expired_jobs_query = JobPost.query.filter(
            JobPost.recruitment_end_date.isnot(None),
            JobPost.recruitment_end_date < today
        )

        # 삭제 전 로그를 위해 카운트
        count = expired_jobs_query.count()

        if count > 0:
            logger.info(f"[Scheduler] {count}개의 만료된 공고를 찾았습니다. 삭제를 시작합니다.")

            expired_jobs_query.delete(synchronize_session=False)

            db.session.commit()
            logger.info(f"[Scheduler] {count}개의 만료된 공고 삭제 완료.")
        else:
            logger.info("[Scheduler] 만료된 공고가 없습니다.")

    except Exception as e:
        logger.error(f"[Scheduler] 만료된 공고 삭제 중 오류 발생: {e}")
        db.session.rollback()