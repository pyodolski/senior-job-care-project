from models import db, JobPost, JobBookmark, User
from sqlalchemy import desc
from flask_login import current_user

class JobService:
    @staticmethod
    def get_all_jobs(page=1, per_page=10, sort_by='latest', conditions=None):
        """
        모든 공고 조회 (페이지네이션 및 정렬)
        
        Args:
            page: 페이지 번호
            per_page: 페이지당 항목 수
            sort_by: 정렬 기준 ('latest', 'popular', 'views')
            conditions: 추가 필터 조건 리스트
        """
        query = JobPost.query
        
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
    def delete_job(job_id):
        """공고 삭제"""
        job = JobPost.query.get_or_404(job_id)
        db.session.delete(job)
        db.session.commit()
        return True
    
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
    def search_jobs(query, filters=None, conditions=None, sort_by='latest'):
        """
        공고 검색
        
        Args:
            query: 검색어
            filters: 필터 조건 (정확 일치)
            conditions: 추가 검색 조건 (LIKE 검색 등)
            sort_by: 정렬 기준 ('latest', 'popular', 'views')
        """
        jobs_query = JobPost.query
        
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