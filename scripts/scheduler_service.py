from models import db, JobPost, JobBookmark, JobApplication, ChatRoom, JobSuggestion
from models import get_kst_now  # KST 시간 헬퍼
import logging

logger = logging.getLogger(__name__)


def delete_expired_job_posts():
    try:
        today = get_kst_now().date()
        logger.info(f"[Scheduler] 만료된 공고 삭제 작업 실행 (기준일: {today})")

        expired_jobs_query = JobPost.query.filter(
            JobPost.recruitment_end_date.isnot(None),
            JobPost.recruitment_end_date < today
        )

        expired_job_ids = [job.id for job in expired_jobs_query.all()]
        count = len(expired_job_ids)

        if count > 0:
            logger.info(f"[Scheduler] {count}개의 만료된 공고를 찾았습니다. 종속 데이터 삭제를 시작합니다.")

            JobBookmark.query.filter(JobBookmark.job_id.in_(expired_job_ids)).delete(synchronize_session=False)

            JobApplication.query.filter(JobApplication.job_id.in_(expired_job_ids)).delete(synchronize_session=False)

            expired_chat_rooms = ChatRoom.query.filter(ChatRoom.job_id.in_(expired_job_ids)).all()
            expired_room_ids = [room.id for room in expired_chat_rooms]

            if expired_room_ids:
                from models import ChatMessage
                ChatMessage.query.filter(ChatMessage.room_id.in_(expired_room_ids)).delete(synchronize_session=False)

            # ChatRoom 삭제
            ChatRoom.query.filter(ChatRoom.job_id.in_(expired_job_ids)).delete(synchronize_session=False)

            # 제안 삭제
            JobSuggestion.query.filter(JobSuggestion.job_id.in_(expired_job_ids)).delete(synchronize_session=False)

            logger.info("[Scheduler] 모든 종속 데이터 삭제 완료. JobPost 삭제를 시작합니다.")

            # 공고 삭제

            JobPost.query.filter(JobPost.id.in_(expired_job_ids)).delete(synchronize_session=False)

            db.session.commit()
            logger.info(f"[Scheduler] {count}개의 만료된 공고 및 연관 데이터 삭제 완료.")
        else:
            logger.info("[Scheduler] 만료된 공고가 없습니다.")

    except Exception as e:
        logger.error(f"[Scheduler] 만료된 공고 삭제 중 오류 발생: {e}")
        db.session.rollback()

