from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from services.job_service import JobService
from services.exceptions import ValidationError, DatabaseError
from routes.community.utils import calculate_age
import logging

logger = logging.getLogger(__name__)

components_bp = Blueprint('components', __name__)

@components_bp.route('/api/debug/db-status')
@login_required
def debug_db_status():
    """데이터베이스 상태 확인 (디버깅용)"""
    try:
        from models import JobPost, db
        
        # 테이블 존재 확인
        table_exists = db.engine.dialect.has_table(db.engine, 'job_post')
        
        # 공고 수 확인
        job_count = 0
        try:
            job_count = JobPost.query.count()
        except Exception as e:
            job_count = f"Error: {str(e)}"
        
        # 사용자 정보 확인
        user_info = {
            'id': current_user.id,
            'authenticated': current_user.is_authenticated,
            'birth_date': str(current_user.birth_date) if current_user.birth_date else None
        }
        
        return jsonify({
            'success': True,
            'db_status': {
                'job_post_table_exists': table_exists,
                'job_count': job_count,
                'user_info': user_info
            }
        })
        
    except Exception as e:
        logger.error(f"Error in debug_db_status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@components_bp.route('/api/components/jobs')
@login_required
def get_jobs_content():
    """구인구직 페이지 컴포넌트를 반환합니다."""
    try:
        return render_template('components/jobs_content.html')
    except Exception as e:
        logger.error(f"Error loading jobs component: {str(e)}")
        return jsonify({'error': '구인구직 페이지를 불러올 수 없습니다.'}), 500

@components_bp.route('/api/components/community')
@login_required
def get_community_content():
    """커뮤니티 페이지 컴포넌트를 반환합니다."""
    try:
        return render_template('components/community_content.html')
    except Exception as e:
        logger.error(f"Error loading community component: {str(e)}")
        return jsonify({'error': '커뮤니티 페이지를 불러올 수 없습니다.'}), 500

# 구인구직 AJAX 엔드포인트들

@components_bp.route('/api/jobs/list')
@login_required
def get_jobs_list():
    """공고 목록 조회 (AJAX)"""
    try:
        # 쿼리 파라미터 수집
        filters = {
            'q': request.args.get('q'),
            'region': request.args.get('region'),
            'senior_only': request.args.get('senior_only') == 'true',
            'age': request.args.get('age', type=int)
        }
        
        # 페이징 파라미터
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # JobService를 통해 공고 목록 조회
        try:
            jobs, total_count = JobService.get_job_list(filters, page, per_page)
            logger.info(f"Successfully retrieved {len(jobs)} jobs from {total_count} total")
        except Exception as e:
            logger.error(f"Error in JobService.get_job_list: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'데이터베이스 오류: {str(e)}',
                'details': 'JobService.get_job_list 실패'
            }), 500
        
        # JSON 형태로 변환
        jobs_data = []
        for job in jobs:
            # 생성일 기준으로 배지 결정
            from datetime import datetime, timedelta
            days_since_created = (datetime.now() - job.created_at).days
            
            badge = Noneㅊㅊ
            if days_since_created <= 1:
                badge = 'new'
            elif job.is_senior_friendly:
                badge = 'senior'
            
            # 사용자 나이에 따른 적합성 확인
            age_suitable = True
            user_age = None
            if current_user.birth_date:
                user_age = calculate_age(current_user.birth_date)
                if user_age and (job.preferred_age_min or job.preferred_age_max):
                    if job.preferred_age_min and user_age < job.preferred_age_min:
                        age_suitable = False
                    if job.preferred_age_max and user_age > job.preferred_age_max:
                        age_suitable = False
            
            jobs_data.append({
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'description': job.description,
                'region': job.region or '지역 미지정',
                'work_hours': job.work_hours or '시간 미지정',
                'contact_phone': job.contact_phone,
                'is_senior_friendly': job.is_senior_friendly,
                'preferred_age_min': job.preferred_age_min,
                'preferred_age_max': job.preferred_age_max,
                'created_at': job.created_at.strftime('%Y-%m-%d'),
                'author_id': job.author_id,
                'badge': badge,
                'age_suitable': age_suitable,
                'can_edit': current_user.id == job.author_id,
                'can_delete': current_user.id == job.author_id or current_user.user_type == 2
            })
        
        # 페이징 정보
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total_count,
            'pages': (total_count + per_page - 1) // per_page,
            'has_next': (page * per_page) < total_count,
            'has_prev': page > 1
        }
        
        return jsonify({
            'success': True,
            'jobs': jobs_data,
            'pagination': pagination,
            'filters': filters,
            'user_can_create': current_user.user_type == 1  # 기업 회원만 생성 가능
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in get_jobs_list: {str(e)}")
        return jsonify({'success': False, 'error': '데이터베이스 오류가 발생했습니다.'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_jobs_list: {str(e)}")
        return jsonify({'success': False, 'error': '예상치 못한 오류가 발생했습니다.'}), 500

@components_bp.route('/api/jobs/<int:job_id>')
@login_required
def get_job_detail(job_id):
    """공고 상세 조회 (AJAX)"""
    try:
        # JobService를 통해 공고 조회
        job = JobService.get_job_by_id(job_id)
        
        if not job:
            return jsonify({'success': False, 'error': '공고를 찾을 수 없습니다.'}), 404
        
        # 사용자 나이 계산
        user_age = None
        age_suitable = True
        age_message = None
        
        if current_user.birth_date:
            user_age = calculate_age(current_user.birth_date)
            
            if user_age and (job.preferred_age_min or job.preferred_age_max):
                if job.preferred_age_min and user_age < job.preferred_age_min:
                    age_suitable = False
                    age_message = f"권장 최소 연령({job.preferred_age_min}세)보다 낮습니다."
                elif job.preferred_age_max and user_age > job.preferred_age_max:
                    age_suitable = False
                    age_message = f"권장 최대 연령({job.preferred_age_max}세)보다 높습니다."
                else:
                    age_message = "연령 조건에 적합합니다."
        
        job_data = {
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'description': job.description,
            'region': job.region,
            'work_hours': job.work_hours,
            'contact_phone': job.contact_phone,
            'is_senior_friendly': job.is_senior_friendly,
            'preferred_age_min': job.preferred_age_min,
            'preferred_age_max': job.preferred_age_max,
            'created_at': job.created_at.strftime('%Y-%m-%d %H:%M'),
            'author_id': job.author_id,
            'user_age': user_age,
            'age_suitable': age_suitable,
            'age_message': age_message,
            'can_edit': current_user.id == job.author_id,
            'can_delete': current_user.id == job.author_id or current_user.user_type == 2
        }
        
        return jsonify({
            'success': True,
            'job': job_data
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in get_job_detail: {str(e)}")
        return jsonify({'success': False, 'error': '데이터베이스 오류가 발생했습니다.'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_job_detail: {str(e)}")
        return jsonify({'success': False, 'error': '예상치 못한 오류가 발생했습니다.'}), 500

@components_bp.route('/api/jobs/create', methods=['POST'])
@login_required
def create_job():
    """공고 생성 (AJAX)"""
    try:
        # JSON 데이터 파싱
        if not request.is_json:
            return jsonify({'success': False, 'error': 'JSON 데이터가 필요합니다.'}), 400
        
        job_data = request.get_json()
        if not job_data:
            return jsonify({'success': False, 'error': '공고 데이터가 없습니다.'}), 400
        
        # JobService를 통해 공고 생성
        new_job = JobService.create_job(job_data, current_user.id)
        
        return jsonify({
            'success': True,
            'message': '공고가 성공적으로 등록되었습니다.',
            'job': {
                'id': new_job.id,
                'title': new_job.title,
                'company': new_job.company,
                'created_at': new_job.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error in create_job: {str(e)}")
        return jsonify({
            'success': False, 
            'error': '입력 데이터 검증 실패',
            'validation_errors': e.details if hasattr(e, 'details') else {}
        }), 400
    except DatabaseError as e:
        logger.error(f"Database error in create_job: {str(e)}")
        return jsonify({'success': False, 'error': '공고 등록 중 데이터베이스 오류가 발생했습니다.'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in create_job: {str(e)}")
        return jsonify({'success': False, 'error': '공고 등록 중 예상치 못한 오류가 발생했습니다.'}), 500

@components_bp.route('/api/jobs/<int:job_id>/update', methods=['PUT'])
@login_required
def update_job(job_id):
    """공고 수정 (AJAX)"""
    try:
        # JSON 데이터 파싱
        if not request.is_json:
            return jsonify({'success': False, 'error': 'JSON 데이터가 필요합니다.'}), 400
        
        job_data = request.get_json()
        if not job_data:
            return jsonify({'success': False, 'error': '공고 데이터가 없습니다.'}), 400
        
        # JobService를 통해 공고 수정
        updated_job = JobService.update_job(job_id, job_data, current_user.id)
        
        return jsonify({
            'success': True,
            'message': '공고가 성공적으로 수정되었습니다.',
            'job': {
                'id': updated_job.id,
                'title': updated_job.title,
                'company': updated_job.company,
                'updated_at': updated_job.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
        
    except ValidationError as e:
        logger.warning(f"Validation error in update_job: {str(e)}")
        return jsonify({
            'success': False, 
            'error': '입력 데이터 검증 실패',
            'validation_errors': e.details if hasattr(e, 'details') else {}
        }), 400
    except DatabaseError as e:
        logger.error(f"Database error in update_job: {str(e)}")
        return jsonify({'success': False, 'error': '공고 수정 중 데이터베이스 오류가 발생했습니다.'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in update_job: {str(e)}")
        return jsonify({'success': False, 'error': '공고 수정 중 예상치 못한 오류가 발생했습니다.'}), 500

@components_bp.route('/api/jobs/<int:job_id>/delete', methods=['DELETE'])
@login_required
def delete_job(job_id):
    """공고 삭제 (AJAX)"""
    try:
        # JobService를 통해 공고 삭제
        success = JobService.delete_job(job_id, current_user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '공고가 성공적으로 삭제되었습니다.'
            })
        else:
            return jsonify({'success': False, 'error': '공고 삭제에 실패했습니다.'}), 500
            
    except ValidationError as e:
        logger.warning(f"Validation error in delete_job: {str(e)}")
        return jsonify({'success': False, 'error': f'삭제 권한 오류: {str(e)}'}), 403
    except DatabaseError as e:
        logger.error(f"Database error in delete_job: {str(e)}")
        return jsonify({'success': False, 'error': '공고 삭제 중 데이터베이스 오류가 발생했습니다.'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in delete_job: {str(e)}")
        return jsonify({'success': False, 'error': '공고 삭제 중 예상치 못한 오류가 발생했습니다.'}), 500

@components_bp.route('/api/jobs/search')
@login_required
def search_jobs():
    """공고 검색 (AJAX)"""
    try:
        search_term = request.args.get('q', '').strip()
        
        if not search_term:
            return jsonify({
                'success': True,
                'jobs': [],
                'total': 0,
                'search_term': search_term,
                'message': '검색어를 입력해주세요.'
            })
        
        # 추가 필터 조건
        filters = {
            'region': request.args.get('region'),
            'senior_only': request.args.get('senior_only') == 'true',
            'age': request.args.get('age', type=int)
        }
        
        # JobService를 통해 검색
        jobs = JobService.search_jobs(search_term, filters)
        
        # JSON 형태로 변환
        jobs_data = []
        for job in jobs:
            jobs_data.append({
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'description': job.description[:200] + '...' if len(job.description) > 200 else job.description,
                'region': job.region,
                'is_senior_friendly': job.is_senior_friendly,
                'created_at': job.created_at.strftime('%Y-%m-%d'),
                'can_edit': current_user.id == job.author_id,
                'can_delete': current_user.id == job.author_id or current_user.user_type == 2
            })
        
        return jsonify({
            'success': True,
            'jobs': jobs_data,
            'total': len(jobs_data),
            'search_term': search_term,
            'filters': filters
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in search_jobs: {str(e)}")
        return jsonify({'success': False, 'error': '검색 중 데이터베이스 오류가 발생했습니다.'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in search_jobs: {str(e)}")
        return jsonify({'success': False, 'error': '검색 중 예상치 못한 오류가 발생했습니다.'}), 500

@components_bp.route('/api/jobs/validate', methods=['POST'])
@login_required
def validate_job_data():
    """공고 데이터 검증 (AJAX) - 실시간 검증용"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'JSON 데이터가 필요합니다.'}), 400
        
        job_data = request.get_json()
        if not job_data:
            return jsonify({'success': False, 'error': '검증할 데이터가 없습니다.'}), 400
        
        # JobService를 통해 데이터 검증
        validation_errors = JobService.validate_job_data(job_data)
        
        return jsonify({
            'success': len(validation_errors) == 0,
            'errors': validation_errors,
            'message': '검증 완료' if len(validation_errors) == 0 else '검증 오류가 있습니다.'
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in validate_job_data: {str(e)}")
        return jsonify({'success': False, 'error': '데이터 검증 중 오류가 발생했습니다.'}), 500

@components_bp.route('/api/jobs/statistics')
@login_required
def get_job_statistics():
    """공고 통계 정보 조회 (AJAX)"""
    try:
        # JobService를 통해 통계 정보 조회
        stats = JobService.get_job_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in get_job_statistics: {str(e)}")
        return jsonify({'success': False, 'error': '통계 조회 중 데이터베이스 오류가 발생했습니다.'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_job_statistics: {str(e)}")
        return jsonify({'success': False, 'error': '통계 조회 중 예상치 못한 오류가 발생했습니다.'}), 500