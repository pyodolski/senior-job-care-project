from models import db, JobSuggestion, User, Resume
from flask_login import current_user
from services.chat_service import ChatService

class SuggestionService:
    @staticmethod
    def get_resume_for_suggestion_page(resume_id):
        """
        [읽기 기능] 제안 페이지를 보여주는 데 필요한 이력서 정보를 가져옵니다.
        """
        return Resume.query.get_or_404(resume_id)

    @staticmethod
    def create_suggestions(suggester_id, resume_id, job_ids):
        """
        [생성 기능] 여러 공고를 한번에 제안합니다.
        """
        resume = Resume.query.get_or_404(resume_id)

        existing_suggestions = JobSuggestion.query.filter(
            JobSuggestion.suggester_id == suggester_id,
            JobSuggestion.resume_id == resume_id,
            JobSuggestion.job_id.in_(job_ids)
        ).all()
        existing_job_ids = {str(s.job_id) for s in existing_suggestions}

        new_suggestions_count = 0
        for job_id in job_ids:
            if job_id not in existing_job_ids:
                suggestion = JobSuggestion(
                    suggester_id=suggester_id,
                    suggestee_id=resume.user_id,
                    job_id=int(job_id),
                    resume_id=resume.id
                )
                db.session.add(suggestion)
                new_suggestions_count += 1

        if new_suggestions_count > 0:
            db.session.commit()

        return new_suggestions_count

    @staticmethod
    def get_received_suggestions(user_id):
        """
        - '받은 제안' 페이지에서 사용됩니다.
        """
        return JobSuggestion.query.filter_by(suggestee_id=user_id)\
            .order_by(JobSuggestion.created_at.desc())\
            .all()

    @staticmethod
    def update_suggestion_status(suggestion_id, user_id, new_status):
        """
        - '응답하기'기능에서 사용됩니다.
        """
        suggestion = JobSuggestion.query.get_or_404(suggestion_id)

        # 제안을 받은 당사자 권한을 확인
        if suggestion.suggestee_id != user_id:
            raise PermissionError("You are not authorized to change the status of this suggestion.")

        # 허용된 상태 값인지 확인
        allowed_statuses = ['sent', 'viewed', 'accepted', 'rejected']
        if new_status not in allowed_statuses:
            raise ValueError(f"Invalid status: {new_status}")

        suggestion.status = new_status
        db.session.commit()
        return suggestion

    @staticmethod
    def accept_suggestion_and_get_chat(suggestion_id, user_id):
        """
        [수정 + 호출] 제안을 '수락' 상태로 변경하고, ChatService를 호출하여
        채팅방을 찾거나 생성하여 ID를 반환합니다.
        """
        # 제안 상태'accepted' (수락)로 변경
        try:
            suggestion = SuggestionService.update_suggestion_status(
                suggestion_id=suggestion_id,
                user_id=user_id,
                new_status='accepted'
            )
        except Exception as e:
            db.session.rollback()
            raise e

        #  ChatService의 채팅방 생성/조회 기능
        chat_room = ChatService.create_or_get_chat_room(
            job_id=suggestion.job_id,
            applicant_id=suggestion.suggestee_id,  # 제안 받은 사람
            employer_id=suggestion.suggester_id  # 제안 보낸 사람
        )

        return chat_room.id
