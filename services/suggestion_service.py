from models import db, JobSuggestion, User, Resume, JobPost
from flask_login import current_user
from services.chat_service import ChatService

class SuggestionService:
    @staticmethod
    def get_resume_for_suggestion_page(resume_id):
        """ 제안 페이지를 보여주는 데 필요한 이력서 정보를 가져옵니다."""
        return Resume.query.get_or_404(resume_id)

    @staticmethod
    def create_suggestions(suggester_id, resume_id, job_ids):
        """ 여러 공고를 한번에 제안합니다. """
        resume = Resume.query.get_or_404(resume_id)

        existing_suggestions = JobSuggestion.query.filter(
            JobSuggestion.suggester_id == suggester_id,
            JobSuggestion.resume_id == resume_id,
            JobSuggestion.job_id.in_(job_ids),
            JobSuggestion.status.in_(['sent', 'accepted'])
        ).all()
        existing_job_ids = {str(s.job_id) for s in existing_suggestions}

        new_suggestions_count = 0
        for job_id in job_ids:
            if job_id not in existing_job_ids:
                suggestion = JobSuggestion(
                    suggester_id=suggester_id,
                    suggestee_id=resume.user_id,
                    job_id=int(job_id),
                    resume_id=resume.id,
                    status='sent'
                )
                db.session.add(suggestion)
                new_suggestions_count += 1

        if new_suggestions_count > 0:
            db.session.commit()

        return new_suggestions_count

    @staticmethod
    def get_received_suggestions(user_id):
        """ 받은 제안 페이지에서 사용 """
        return JobSuggestion.query.filter_by(
            suggestee_id=user_id,
            status='sent'
        ).order_by(JobSuggestion.created_at.desc()).all()

    @staticmethod
    def update_suggestion_status(suggestion_id, user_id, new_status):
        """ '응답하기'기능에서 사용됩니다. """
        suggestion = JobSuggestion.query.get_or_404(suggestion_id)

        if suggestion.suggestee_id != user_id:
            raise PermissionError("You are not authorized to change the status of this suggestion.")

        allowed_statuses = ['sent', 'viewed', 'accepted', 'rejected']
        if new_status not in allowed_statuses:
            raise ValueError(f"Invalid status: {new_status}")

        suggestion.status = new_status
        db.session.commit()
        return suggestion

    @staticmethod
    def accept_suggestion_and_get_chat(suggestion_id, user_id):
        """ 제안을 수락 상태로 변경, chat방 찾기"""
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

        chat_room = ChatService.create_or_get_chat_room(
            job_id=suggestion.job_id,
            applicant_id=suggestion.suggestee_id,  # 제안 받은 사람
            employer_id=suggestion.suggester_id  # 제안 보낸 사람
        )

        return chat_room.id

    @staticmethod
    def get_jobs_for_suggestion(suggester_id, resume_id):
        """ 이력서를 제안할 수 있는 상태의 공고를 가져옴 """
        # 올린 모든 공고 목록을 가져옴
        my_jobs = JobPost.query.filter_by(author_id=suggester_id) \
            .order_by(JobPost.created_at.desc()) \
            .all()

        # 이미 보낸 상태 체크
        existing_suggestions = JobSuggestion.query.filter_by(
            suggester_id=suggester_id,
            resume_id=resume_id
        ).all()
        suggestion_statuses = {s.job_id: s.status for s in existing_suggestions}

        jobs_for_suggestion = []
        for job in my_jobs:
            status = suggestion_statuses.get(job.id)


            if status != 'accepted':
                jobs_for_suggestion.append({
                    'job': job,
                    'status': status
                })

        return jobs_for_suggestion
