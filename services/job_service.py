from models import db, JobPost, JobBookmark, User
from sqlalchemy import desc
from flask_login import current_user
from models import JobApplication, ChatRoom, ChatMessage, JobSuggestion

class JobService:
    @staticmethod
    def get_all_jobs(page=1, per_page=10, sort_by='latest', conditions=None, base_query=None):
        """
        모든 공고 조회 (페이지네이션 및 정렬)
        
        Args:
            page: 페이지 번호
            per_page: 페이지당 항목 수
            sort_by: 정렬 기준 ('latest', 'popular', 'views')
            conditions: 추가 필터 조건 리스트
        """
        query = base_query if base_query is not None else JobPost.query
        
        # 추가 조건 적용
        if conditions:
            for condition in conditions:
                query = query.filter(condition)
        
        if sort_by == 'latest':
            # 최신순 (기본값)
            query = query.order_by(desc(JobPost.created_at))
        elif sort_by == 'popular':
            # 인기순 (찜 개수 + 지원 개수)
            query = query.order_by(
                desc(JobPost.bookmark_count + JobPost.application_count),
                desc(JobPost.created_at)
            )
        elif sort_by == 'views':
            # 조회수순
            query = query.order_by(
                desc(JobPost.view_count),
                desc(JobPost.created_at)
            )
        else:
            # 기본값: 최신순
            query = query.order_by(desc(JobPost.created_at))
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_job_by_id(job_id):
        """ID로 공고 조회"""
        return JobPost.query.get_or_404(job_id)
    
    @staticmethod
    def create_job(job_data):
        """새 공고 생성"""
        job = JobPost(**job_data)
        db.session.add(job)
        db.session.commit()
        return job
    
    @staticmethod
    def update_job(job_id, job_data):
        """공고 수정"""
        job = JobPost.query.get_or_404(job_id)
        for key, value in job_data.items():
            setattr(job, key, value)
        db.session.commit()
        return job

    @staticmethod
    def update_job_by_type(job_id, form_data):
        """
        공고 타입에 따라 폼 데이터를 받아 공고를 수정합니다.
        """
        job = JobPost.query.get_or_404(job_id)

        # 폼 데이터에서 공통 필드 업데이트
        job.title = form_data.get("title", "").strip()
        job.company = form_data.get("company", "").strip()
        job.description = form_data.get("description", "").strip()
        job.recruitment_type = form_data.get("recruitment_type", "")
        job.work_period = form_data.get("work_period", "")
        job.salary = form_data.get("salary", "").strip()
        job.region = form_data.get("region", "").strip()
        job.contact_phone = form_data.get("contact_phone", "").strip()
        job.recruitment_count = form_data.get("recruitment_count", type=int)

        # 지역, 위도/경도 업데이트
        job.region_1depth_name = form_data.get("region_1depth_name")
        job.region_2depth_name = form_data.get("region_2depth_name")
        job.region_3depth_name = form_data.get("region_3depth_name")

        latitude = form_data.get("latitude", type=float)
        longitude = form_data.get("longitude", type=float)
        if latitude is not None:
            job.latitude = latitude
        if longitude is not None:
            job.longitude = longitude

        # 근무 시간 업데이트
        work_start_time_str = form_data.get("work_start_time", "")
        work_end_time_str = form_data.get("work_end_time", "")

        from datetime import datetime
        if work_start_time_str:
            job.work_start_time = datetime.strptime(work_start_time_str, "%H:%M").time()
        else:
            job.work_start_time = None

        if work_end_time_str:
            job.work_end_time = datetime.strptime(work_end_time_str, "%H:%M").time()
        else:
            job.work_end_time = None

        # 근무 요일 업데이트
        job.work_monday = form_data.get("work_monday") == "true"
        job.work_tuesday = form_data.get("work_tuesday") == "true"
        job.work_wednesday = form_data.get("work_wednesday") == "true"
        job.work_thursday = form_data.get("work_thursday") == "true"
        job.work_friday = form_data.get("work_friday") == "true"
        job.work_saturday = form_data.get("work_saturday") == "true"
        job.work_sunday = form_data.get("work_sunday") == "true"

        # --- 공고 타입별 필드 업데이트 ---

        if job.job_category is None:
            # 사람이음 공고 (
            job.people_category = form_data.get("people_category", "").strip()
            #  모집 기간 업데이트
            job.recruitment_start_date = form_data.get("recruitment_start_date")
            job.recruitment_end_date = form_data.get("recruitment_end_date")
        else:
            # 기업이음 공고
            job.job_category = form_data.get("job_category", "").strip()

            recruitment_end_date_str = form_data.get("recruitment_end_date")
            if recruitment_end_date_str:
                job.recruitment_end_date = datetime.strptime(recruitment_end_date_str, "%Y-%m-%d").date()
            else:
                job.recruitment_end_date = None


            job.people_category = None

        db.session.commit()
        return job

    @staticmethod
    def is_company_job(job_id):

        job = JobPost.query.get(job_id)
        if job and job.job_category:
            return True
        return False

    @staticmethod
    def delete_job_safely(job_id):
        """
        공고와 연관된 모든 데이터 삭제
        """
        job = JobPost.query.get_or_404(job_id)

        # 1. 공고 ID를 가져옵니다.
        job_id_to_delete = job.id

        # 2. ChatRoom과 ChatMessage 삭제 (순서 중요: 메시지 -> 방)

        # 2-1. 해당 공고의 모든 채팅방 ID를 찾습니다.
        expired_chat_rooms = ChatRoom.query.filter(ChatRoom.job_id == job_id_to_delete).all()
        expired_room_ids = [room.id for room in expired_chat_rooms]

        if expired_room_ids:
            # 2-2. ChatMessage 삭제 (가장 하위)
            ChatMessage.query.filter(ChatMessage.room_id.in_(expired_room_ids)).delete(synchronize_session=False)

        # 2-3. ChatRoom 삭제
        ChatRoom.query.filter(ChatRoom.job_id == job_id_to_delete).delete(synchronize_session=False)

        # 3. JobApplication (지원 내역) 삭제
        JobApplication.query.filter(JobApplication.job_id == job_id_to_delete).delete(synchronize_session=False)

        # 4. JobBookmark (찜 목록) 삭제
        JobBookmark.query.filter(JobBookmark.job_id == job_id_to_delete).delete(synchronize_session=False)

        # 5. JobSuggestion (공고 제안) 삭제
        JobSuggestion.query.filter(JobSuggestion.job_id == job_id_to_delete).delete(synchronize_session=False)

        # 6. JobPost 본체 삭제 (마지막)
        db.session.delete(job)

        db.session.commit()
        return True

    @staticmethod
    def delete_job(job_id):
        """공고 삭제"""
        return JobService.delete_job_safely(job_id)
    
    @staticmethod
    def increment_view_count(job_id):
        """조회수 증가"""
        job = JobPost.query.get(job_id)
        if job:
            job.view_count += 1
            db.session.commit()
    
    @staticmethod
    def get_user_bookmarks(user_id):
        """사용자의 찜 목록 조회"""
        bookmarks = JobBookmark.query.filter_by(user_id=user_id).all()
        return [bookmark.job for bookmark in bookmarks]
    
    @staticmethod
    def toggle_bookmark(user_id, job_id):
        """찜하기/찜 해제 토글"""
        bookmark = JobBookmark.query.filter_by(
            user_id=user_id, job_id=job_id
        ).first()
        
        if bookmark:
            # 찜 해제
            db.session.delete(bookmark)
            job = JobPost.query.get(job_id)
            if job:
                job.bookmark_count = max(0, job.bookmark_count - 1)
            db.session.commit()
            return False
        else:
            # 찜하기
            bookmark = JobBookmark(user_id=user_id, job_id=job_id)
            db.session.add(bookmark)
            job = JobPost.query.get(job_id)
            if job:
                job.bookmark_count += 1
            db.session.commit()
            return True
    
    @staticmethod
    def is_bookmarked(user_id, job_id):
        """찜 여부 확인"""
        if not user_id:
            return False
        return JobBookmark.query.filter_by(
            user_id=user_id, job_id=job_id
        ).first() is not None
    
    @staticmethod
    def search_jobs(query, filters=None, conditions=None, sort_by='latest', base_query=None):
        """
        공고 검색
        
        Args:
            query: 검색어
            filters: 필터 조건 (정확 일치)
            conditions: 추가 검색 조건 (LIKE 검색 등)
            sort_by: 정렬 기준 ('latest', 'popular', 'views')
        """
        jobs_query = base_query if base_query is not None else JobPost.query
        
        if query:
            jobs_query = jobs_query.filter(
                JobPost.title.contains(query) |
                JobPost.company.contains(query) |
                JobPost.description.contains(query)
            )
        
        if filters:
            # [핵심 수정] 계층적 지역 필터링 (정확한 일치 검색)
            if filters.get('region_1depth_name'):
                jobs_query = jobs_query.filter(JobPost.region_1depth_name == filters['region_1depth_name'])
            if filters.get('region_2depth_name'):
                jobs_query = jobs_query.filter(JobPost.region_2depth_name == filters['region_2depth_name'])
            if filters.get('region_3depth_name'):
                jobs_query = jobs_query.filter(JobPost.region_3depth_name == filters['region_3depth_name'])

            if filters.get('recruitment_type'):
                jobs_query = jobs_query.filter(
                    JobPost.recruitment_type == filters['recruitment_type']
                )
            if filters.get('work_period'):
                jobs_query = jobs_query.filter(
                    JobPost.work_period == filters['work_period']
                )
        
        # 추가 조건 적용 (LIKE 검색 등)
        if conditions:
            for condition in conditions:
                jobs_query = jobs_query.filter(condition)
        
        # 정렬 적용
        if sort_by == 'latest':
            jobs_query = jobs_query.order_by(desc(JobPost.created_at))
        elif sort_by == 'popular':
            jobs_query = jobs_query.order_by(
                desc(JobPost.bookmark_count + JobPost.application_count),
                desc(JobPost.created_at)
            )
        elif sort_by == 'views':
            jobs_query = jobs_query.order_by(
                desc(JobPost.view_count),
                desc(JobPost.created_at)
            )
        else:
            jobs_query = jobs_query.order_by(desc(JobPost.created_at))
        
        return jobs_query.all()