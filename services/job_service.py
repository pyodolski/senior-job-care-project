import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import and_, or_

from models import db, JobPost, User
from .exceptions import ValidationError, DatabaseError
from .db_utils import safe_db_operation, safe_db_transaction

logger = logging.getLogger(__name__)

class JobService:
    """구인구직 서비스 클래스"""

    @staticmethod
    @safe_db_operation("get_job_list")
    def get_job_list(filters: Optional[Dict[str, Any]] = None, page: int = 1, per_page: int = 20) -> Tuple[List[JobPost], int]:
        """
        공고 목록 조회 (필터링 및 페이징 지원)
        
        Args:
            filters: 필터링 조건 (q, region, senior_only, age 등)
            page: 페이지 번호
            per_page: 페이지당 항목 수
            
        Returns:
            Tuple[List[JobPost], int]: (공고 리스트, 전체 항목 수)
        """
        try:
            filters = filters or {}
            
            # 기본 쿼리
            query = JobPost.query.order_by(JobPost.created_at.desc())
            
            # 검색어 필터링
            search_query = filters.get('q')
            if search_query:
                search_term = f'%{search_query}%'
                query = query.filter(
                    or_(
                        JobPost.title.ilike(search_term),
                        JobPost.description.ilike(search_term),
                        JobPost.company.ilike(search_term)
                    )
                )
                logger.info(f"Applied search filter: {search_query}")
            
            # 지역 필터링
            region = filters.get('region')
            if region:
                query = query.filter(JobPost.region == region)
                logger.info(f"Applied region filter: {region}")
            
            # 시니어 친화적 필터링
            senior_only = filters.get('senior_only')
            if senior_only:
                query = query.filter(JobPost.is_senior_friendly.is_(True))
                logger.info("Applied senior-friendly filter")
            
            # 나이 필터링
            age = filters.get('age')
            if age is not None:
                try:
                    age = int(age)
                    query = query.filter(
                        and_(
                            or_(JobPost.preferred_age_min.is_(None), JobPost.preferred_age_min <= age),
                            or_(JobPost.preferred_age_max.is_(None), JobPost.preferred_age_max >= age)
                        )
                    )
                    logger.info(f"Applied age filter: {age}")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid age filter value: {age}")
            
            # 활성 상태 필터링 (필요시)
            if filters.get('active_only', True):
                # 삭제되지 않은 공고만 조회 (실제 deleted_at 필드가 있다면)
                # query = query.filter(JobPost.deleted_at.is_(None))
                pass
            
            # 전체 항목 수 계산
            total_count = query.count()
            
            # 페이징 적용
            if page > 0 and per_page > 0:
                offset = (page - 1) * per_page
                query = query.offset(offset).limit(per_page)
                logger.info(f"Applied pagination: page={page}, per_page={per_page}")
            
            jobs = query.all()
            logger.info(f"Retrieved {len(jobs)} jobs from {total_count} total")
            
            return jobs, total_count
            
        except Exception as e:
            logger.error(f"Error retrieving job list: {str(e)}")
            raise DatabaseError(f"공고 목록 조회 중 오류가 발생했습니다: {str(e)}")

    @staticmethod
    @safe_db_operation("get_job_by_id")
    def get_job_by_id(job_id: int) -> Optional[JobPost]:
        """
        ID로 공고 조회
        
        Args:
            job_id: 공고 ID
            
        Returns:
            Optional[JobPost]: 공고 객체 (없으면 None)
        """
        try:
            job = JobPost.query.get(job_id)
            if job:
                logger.info(f"Retrieved job {job_id}: {job.title}")
            else:
                logger.warning(f"Job not found: {job_id}")
            return job
            
        except Exception as e:
            logger.error(f"Error retrieving job {job_id}: {str(e)}")
            raise DatabaseError(f"공고 조회 중 오류가 발생했습니다: {str(e)}")

    @staticmethod
    def create_job(job_data: Dict[str, Any], author_id: int) -> JobPost:
        """
        새 공고 생성
        
        Args:
            job_data: 공고 데이터
            author_id: 작성자 ID
            
        Returns:
            JobPost: 생성된 공고 객체
        """
        try:
            # 데이터 검증
            validation_errors = JobService.validate_job_data(job_data)
            if validation_errors:
                raise ValidationError("공고 데이터 검증 실패", validation_errors)
            
            # 작성자 권한 확인
            author = User.query.get(author_id)
            if not author:
                raise ValidationError("작성자를 찾을 수 없습니다.")
            
            if author.user_type != 1:  # 기업 회원만 작성 가능
                raise ValidationError("기업 회원만 공고를 작성할 수 있습니다.")
            
            # 트랜잭션 내에서 공고 생성
            with safe_db_transaction():
                new_job = JobPost(
                    title=job_data.get('title', '').strip(),
                    company=job_data.get('company', '').strip(),
                    description=job_data.get('description', '').strip(),
                    preferred_age_min=JobService._parse_int(job_data.get('preferred_age_min')),
                    preferred_age_max=JobService._parse_int(job_data.get('preferred_age_max')),
                    region=job_data.get('region', '').strip() if job_data.get('region') else None,
                    is_senior_friendly=bool(job_data.get('is_senior_friendly')),
                    work_hours=job_data.get('work_hours', '').strip() if job_data.get('work_hours') else None,
                    contact_phone=job_data.get('contact_phone', '').strip() if job_data.get('contact_phone') else None,
                    author_id=author_id
                )
                
                db.session.add(new_job)
            
            logger.info(f"Created job {new_job.id}: {new_job.title} by user {author_id}")
            return new_job
            
        except ValidationError:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            raise DatabaseError(f"공고 생성 중 오류가 발생했습니다: {str(e)}")

    @staticmethod
    def update_job(job_id: int, job_data: Dict[str, Any], user_id: int) -> JobPost:
        """
        공고 수정
        
        Args:
            job_id: 공고 ID
            job_data: 수정할 데이터
            user_id: 수정 요청자 ID
            
        Returns:
            JobPost: 수정된 공고 객체
        """
        try:
            # 공고 조회
            job = JobPost.query.get(job_id)
            if not job:
                raise ValidationError("공고를 찾을 수 없습니다.")
            
            # 권한 확인 (작성자만 수정 가능)
            if job.author_id != user_id:
                raise ValidationError("수정 권한이 없습니다.")
            
            # 데이터 검증
            validation_errors = JobService.validate_job_data(job_data)
            if validation_errors:
                raise ValidationError("공고 데이터 검증 실패", validation_errors)
            
            # 트랜잭션 내에서 공고 수정
            with safe_db_transaction():
                job.title = job_data.get('title', '').strip()
                job.company = job_data.get('company', '').strip()
                job.description = job_data.get('description', '').strip()
                job.preferred_age_min = JobService._parse_int(job_data.get('preferred_age_min'))
                job.preferred_age_max = JobService._parse_int(job_data.get('preferred_age_max'))
                job.region = job_data.get('region', '').strip() if job_data.get('region') else None
                job.work_hours = job_data.get('work_hours', '').strip() if job_data.get('work_hours') else None
                job.contact_phone = job_data.get('contact_phone', '').strip() if job_data.get('contact_phone') else None
                job.is_senior_friendly = bool(job_data.get('is_senior_friendly'))
            
            logger.info(f"Updated job {job_id}: {job.title} by user {user_id}")
            return job
            
        except ValidationError:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {str(e)}")
            raise DatabaseError(f"공고 수정 중 오류가 발생했습니다: {str(e)}")

    @staticmethod
    def delete_job(job_id: int, user_id: int) -> bool:
        """
        공고 삭제
        
        Args:
            job_id: 공고 ID
            user_id: 삭제 요청자 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 공고 조회
            job = JobPost.query.get(job_id)
            if not job:
                raise ValidationError("공고를 찾을 수 없습니다.")
            
            # 권한 확인 (작성자 또는 관리자만 삭제 가능)
            user = User.query.get(user_id)
            if not user:
                raise ValidationError("사용자를 찾을 수 없습니다.")
            
            if job.author_id != user_id and user.user_type != 2:  # 관리자 권한
                raise ValidationError("삭제 권한이 없습니다.")
            
            # 트랜잭션 내에서 공고 삭제
            with safe_db_transaction():
                db.session.delete(job)
            
            logger.info(f"Deleted job {job_id} by user {user_id}")
            return True
            
        except ValidationError:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {str(e)}")
            raise DatabaseError(f"공고 삭제 중 오류가 발생했습니다: {str(e)}")

    @staticmethod
    def validate_job_data(job_data: Dict[str, Any]) -> Dict[str, str]:
        """
        공고 데이터 검증
        
        Args:
            job_data: 검증할 공고 데이터
            
        Returns:
            Dict[str, str]: 검증 오류 메시지 (필드명: 오류메시지)
        """
        errors = {}
        
        # 필수 필드 검증
        required_fields = ['title', 'company', 'description']
        for field in required_fields:
            value = job_data.get(field, '').strip()
            if not value:
                errors[field] = f'{field}을(를) 입력해주세요.'
            elif len(value) > 200:  # title 길이 제한
                if field == 'title':
                    errors[field] = '제목은 200자 이하로 입력해주세요.'
                elif field == 'company':
                    errors[field] = '회사명은 200자 이하로 입력해주세요.'
        
        # 설명 길이 검증
        description = job_data.get('description', '').strip()
        if description and len(description) > 2000:
            errors['description'] = '설명은 2000자 이하로 입력해주세요.'
        
        # 나이 범위 검증
        min_age = JobService._parse_int(job_data.get('preferred_age_min'))
        max_age = JobService._parse_int(job_data.get('preferred_age_max'))
        
        if min_age is not None and (min_age < 14 or min_age > 100):
            errors['preferred_age_min'] = '최소 나이는 14세 이상 100세 이하로 입력해주세요.'
        
        if max_age is not None and (max_age < 14 or max_age > 100):
            errors['preferred_age_max'] = '최대 나이는 14세 이상 100세 이하로 입력해주세요.'
        
        if min_age is not None and max_age is not None and min_age > max_age:
            errors['preferred_age_max'] = '최대 나이는 최소 나이보다 크거나 같아야 합니다.'
        
        # 전화번호 형식 검증 (선택적)
        contact_phone = job_data.get('contact_phone', '').strip()
        if contact_phone:
            import re
            phone_pattern = r'^01[0-9]-\d{4}-\d{4}$'
            if not re.match(phone_pattern, contact_phone):
                errors['contact_phone'] = '올바른 전화번호 형식으로 입력해주세요. (010-XXXX-XXXX)'
        
        return errors

    @staticmethod
    def get_jobs_by_author(author_id: int, page: int = 1, per_page: int = 10) -> Tuple[List[JobPost], int]:
        """
        작성자별 공고 조회
        
        Args:
            author_id: 작성자 ID
            page: 페이지 번호
            per_page: 페이지당 항목 수
            
        Returns:
            Tuple[List[JobPost], int]: (공고 리스트, 전체 항목 수)
        """
        try:
            query = JobPost.query.filter_by(author_id=author_id).order_by(JobPost.created_at.desc())
            
            total_count = query.count()
            
            if page > 0 and per_page > 0:
                offset = (page - 1) * per_page
                query = query.offset(offset).limit(per_page)
            
            jobs = query.all()
            logger.info(f"Retrieved {len(jobs)} jobs for author {author_id}")
            
            return jobs, total_count
            
        except Exception as e:
            logger.error(f"Error retrieving jobs for author {author_id}: {str(e)}")
            raise DatabaseError(f"작성자별 공고 조회 중 오류가 발생했습니다: {str(e)}")

    @staticmethod
    def search_jobs(search_term: str, filters: Optional[Dict[str, Any]] = None) -> List[JobPost]:
        """
        공고 검색
        
        Args:
            search_term: 검색어
            filters: 추가 필터 조건
            
        Returns:
            List[JobPost]: 검색 결과
        """
        try:
            if not search_term.strip():
                return []
            
            filters = filters or {}
            filters['q'] = search_term.strip()
            
            jobs, _ = JobService.get_job_list(filters, page=1, per_page=100)  # 최대 100개 결과
            
            logger.info(f"Search '{search_term}' returned {len(jobs)} results")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching jobs with term '{search_term}': {str(e)}")
            raise DatabaseError(f"공고 검색 중 오류가 발생했습니다: {str(e)}")

    @staticmethod
    def _parse_int(value: Any) -> Optional[int]:
        """
        안전한 정수 변환
        
        Args:
            value: 변환할 값
            
        Returns:
            Optional[int]: 변환된 정수 (실패시 None)
        """
        if value is None or value == '':
            return None
        
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def get_job_statistics() -> Dict[str, Any]:
        """
        공고 통계 정보 조회
        
        Returns:
            Dict[str, Any]: 통계 정보
        """
        try:
            total_jobs = JobPost.query.count()
            senior_friendly_jobs = JobPost.query.filter_by(is_senior_friendly=True).count()
            
            # 지역별 통계
            from sqlalchemy import func
            region_stats = db.session.query(
                JobPost.region,
                func.count(JobPost.id).label('count')
            ).filter(JobPost.region.isnot(None)).group_by(JobPost.region).all()
            
            stats = {
                'total_jobs': total_jobs,
                'senior_friendly_jobs': senior_friendly_jobs,
                'senior_friendly_percentage': (senior_friendly_jobs / total_jobs * 100) if total_jobs > 0 else 0,
                'region_distribution': {region: count for region, count in region_stats}
            }
            
            logger.info(f"Generated job statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error generating job statistics: {str(e)}")
            raise DatabaseError(f"통계 생성 중 오류가 발생했습니다: {str(e)}") 