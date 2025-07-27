from flask import render_template, request, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from . import community_bp
from models import db, JobPost
from .utils import calculate_age
from services.job_service import JobService
from services.exceptions import ValidationError, DatabaseError
import logging

logger = logging.getLogger(__name__)


@community_bp.route('/jobs')
def job_list():
    """공고 목록 페이지"""
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
        jobs, total_count = JobService.get_job_list(filters, page, per_page)
        
        # 페이징 정보 계산
        has_next = (page * per_page) < total_count
        has_prev = page > 1
        
        pagination_info = {
            'page': page,
            'per_page': per_page,
            'total': total_count,
            'has_next': has_next,
            'has_prev': has_prev,
            'next_page': page + 1 if has_next else None,
            'prev_page': page - 1 if has_prev else None
        }
        
        return render_template('community/jobs/list.html', 
                             jobs=jobs, 
                             pagination=pagination_info,
                             filters=filters)
                             
    except DatabaseError as e:
        logger.error(f"Database error in job_list: {str(e)}")
        flash("공고 목록을 불러오는 중 오류가 발생했습니다.", "error")
        return render_template('community/jobs/list.html', jobs=[], pagination=None)
    except Exception as e:
        logger.error(f"Unexpected error in job_list: {str(e)}")
        flash("예상치 못한 오류가 발생했습니다.", "error")
        return render_template('community/jobs/list.html', jobs=[], pagination=None)


@community_bp.route('/jobs/new', methods=['GET', 'POST'])
@login_required
def job_create():
    """공고 생성 페이지"""
    try:
        if request.method == 'GET':
            return render_template('community/jobs/form.html')
        
        # POST 요청 처리
        job_data = {
            'title': request.form.get('title'),
            'company': request.form.get('company'),
            'description': request.form.get('description'),
            'preferred_age_min': request.form.get('preferred_age_min'),
            'preferred_age_max': request.form.get('preferred_age_max'),
            'region': request.form.get('region'),
            'is_senior_friendly': request.form.get('is_senior_friendly') == 'on',
            'work_hours': request.form.get('work_hours'),
            'contact_phone': request.form.get('contact_phone')
        }
        
        # JobService를 통해 공고 생성
        new_job = JobService.create_job(job_data, current_user.id)
        
        flash(f"공고 '{new_job.title}'이(가) 성공적으로 등록되었습니다.", "success")
        return redirect(url_for('community.job_list'))
        
    except ValidationError as e:
        logger.warning(f"Validation error in job_create: {str(e)}")
        flash(f"입력 데이터 오류: {str(e)}", "error")
        return render_template('community/jobs/form.html'), 400
    except DatabaseError as e:
        logger.error(f"Database error in job_create: {str(e)}")
        flash("공고 등록 중 데이터베이스 오류가 발생했습니다.", "error")
        return render_template('community/jobs/form.html'), 500
    except Exception as e:
        logger.error(f"Unexpected error in job_create: {str(e)}")
        flash("공고 등록 중 예상치 못한 오류가 발생했습니다.", "error")
        return render_template('community/jobs/form.html'), 500


@community_bp.route('/jobs/<int:job_id>')
def job_detail(job_id):
    """공고 상세 페이지"""
    try:
        # JobService를 통해 공고 조회
        job = JobService.get_job_by_id(job_id)
        
        if not job:
            flash("요청하신 공고를 찾을 수 없습니다.", "error")
            return redirect(url_for('community.job_list'))
        
        # 사용자 나이 계산 (나이 조건 표시용)
        user_age = None
        if current_user.is_authenticated and current_user.birth_date:
            user_age = calculate_age(current_user.birth_date)
        
        # 나이 적합성 확인
        age_suitable = True
        if user_age and (job.preferred_age_min or job.preferred_age_max):
            if job.preferred_age_min and user_age < job.preferred_age_min:
                age_suitable = False
            if job.preferred_age_max and user_age > job.preferred_age_max:
                age_suitable = False
        
        return render_template('community/jobs/detail.html', 
                             job=job, 
                             user_age=user_age,
                             age_suitable=age_suitable)
                             
    except DatabaseError as e:
        logger.error(f"Database error in job_detail: {str(e)}")
        flash("공고 조회 중 오류가 발생했습니다.", "error")
        return redirect(url_for('community.job_list'))
    except Exception as e:
        logger.error(f"Unexpected error in job_detail: {str(e)}")
        flash("예상치 못한 오류가 발생했습니다.", "error")
        return redirect(url_for('community.job_list'))


@community_bp.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
def job_delete(job_id):
    """공고 삭제"""
    try:
        # JobService를 통해 공고 삭제
        success = JobService.delete_job(job_id, current_user.id)
        
        if success:
            flash("공고가 성공적으로 삭제되었습니다.", "success")
        else:
            flash("공고 삭제에 실패했습니다.", "error")
            
        return redirect(url_for('community.job_list'))
        
    except ValidationError as e:
        logger.warning(f"Validation error in job_delete: {str(e)}")
        flash(f"삭제 권한 오류: {str(e)}", "error")
        return redirect(url_for('community.job_detail', job_id=job_id))
    except DatabaseError as e:
        logger.error(f"Database error in job_delete: {str(e)}")
        flash("공고 삭제 중 데이터베이스 오류가 발생했습니다.", "error")
        return redirect(url_for('community.job_detail', job_id=job_id))
    except Exception as e:
        logger.error(f"Unexpected error in job_delete: {str(e)}")
        flash("공고 삭제 중 예상치 못한 오류가 발생했습니다.", "error")
        return redirect(url_for('community.job_detail', job_id=job_id))


@community_bp.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
def job_edit(job_id):
    """공고 수정 페이지"""
    try:
        # JobService를 통해 공고 조회
        job = JobService.get_job_by_id(job_id)
        
        if not job:
            flash("요청하신 공고를 찾을 수 없습니다.", "error")
            return redirect(url_for('community.job_list'))
        
        # 권한 확인 (편집 권한 체크는 JobService에서도 하지만 미리 확인)
        if job.author_id != current_user.id:
            flash("수정 권한이 없습니다.", "error")
            return redirect(url_for('community.job_detail', job_id=job_id))
        
        if request.method == 'GET':
            return render_template('community/jobs/form.html', job=job, is_edit=True)
        
        # POST 요청 처리
        job_data = {
            'title': request.form.get('title'),
            'company': request.form.get('company'),
            'description': request.form.get('description'),
            'preferred_age_min': request.form.get('preferred_age_min'),
            'preferred_age_max': request.form.get('preferred_age_max'),
            'region': request.form.get('region'),
            'work_hours': request.form.get('work_hours'),
            'contact_phone': request.form.get('contact_phone'),
            'is_senior_friendly': request.form.get('is_senior_friendly') == 'on'
        }
        
        # JobService를 통해 공고 수정
        updated_job = JobService.update_job(job_id, job_data, current_user.id)
        
        flash(f"공고 '{updated_job.title}'이(가) 성공적으로 수정되었습니다.", "success")
        return redirect(url_for('community.job_detail', job_id=job_id))
        
    except ValidationError as e:
        logger.warning(f"Validation error in job_edit: {str(e)}")
        flash(f"입력 데이터 오류: {str(e)}", "error")
        # 에러 시 기존 공고 데이터로 폼 재표시
        job = JobService.get_job_by_id(job_id)
        return render_template('community/jobs/form.html', job=job, is_edit=True), 400
    except DatabaseError as e:
        logger.error(f"Database error in job_edit: {str(e)}")
        flash("공고 수정 중 데이터베이스 오류가 발생했습니다.", "error")
        job = JobService.get_job_by_id(job_id)
        return render_template('community/jobs/form.html', job=job, is_edit=True), 500
    except Exception as e:
        logger.error(f"Unexpected error in job_edit: {str(e)}")
        flash("공고 수정 중 예상치 못한 오류가 발생했습니다.", "error")
        return redirect(url_for('community.job_detail', job_id=job_id))


@community_bp.route('/jobs/search')
def job_search():
    """공고 검색 (AJAX 지원)"""
    try:
        search_term = request.args.get('q', '').strip()
        
        if not search_term:
            return render_template('community/jobs/list.html', jobs=[], search_term=search_term)
        
        # 추가 필터 조건
        filters = {
            'region': request.args.get('region'),
            'senior_only': request.args.get('senior_only') == 'true',
            'age': request.args.get('age', type=int)
        }
        
        # JobService를 통해 검색
        jobs = JobService.search_jobs(search_term, filters)
        
        # AJAX 요청인 경우 JSON 응답
        if request.headers.get('Content-Type') == 'application/json':
            from flask import jsonify
            job_list = []
            for job in jobs:
                job_list.append({
                    'id': job.id,
                    'title': job.title,
                    'company': job.company,
                    'region': job.region,
                    'is_senior_friendly': job.is_senior_friendly,
                    'created_at': job.created_at.strftime('%Y-%m-%d'),
                    'url': url_for('community.job_detail', job_id=job.id)
                })
            
            return jsonify({
                'success': True,
                'jobs': job_list,
                'total': len(job_list),
                'search_term': search_term
            })
        
        return render_template('community/jobs/list.html', 
                             jobs=jobs, 
                             search_term=search_term,
                             filters=filters)
                             
    except DatabaseError as e:
        logger.error(f"Database error in job_search: {str(e)}")
        if request.headers.get('Content-Type') == 'application/json':
            from flask import jsonify
            return jsonify({'success': False, 'error': '검색 중 오류가 발생했습니다.'}), 500
        
        flash("검색 중 오류가 발생했습니다.", "error")
        return render_template('community/jobs/list.html', jobs=[], search_term=search_term)
    except Exception as e:
        logger.error(f"Unexpected error in job_search: {str(e)}")
        if request.headers.get('Content-Type') == 'application/json':
            from flask import jsonify
            return jsonify({'success': False, 'error': '예상치 못한 오류가 발생했습니다.'}), 500
        
        flash("예상치 못한 오류가 발생했습니다.", "error")
        return render_template('community/jobs/list.html', jobs=[], search_term=search_term)
