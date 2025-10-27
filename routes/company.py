"""
기업 이음 관련 라우트 모듈
=========================

기업 회원 전용 공고 관리 기능을 처리합니다.

주요 기능:
- 기업 공고 목록 조회 (기업 회원만 작성한 공고들)
- 기업 공고 작성 (기업 회원만 가능)
- 기업 공고 수정/삭제
- 지원자 관리

작성자: [팀명]
최종 수정일: 2025-01-09
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, JobPost
from services.job_service import JobService
from services.application_service import ApplicationService
from utils.helpers import format_datetime, get_work_days
from datetime import datetime, time

# 기업 이음 관련 블루프린트 생성
company_bp = Blueprint("company", __name__)

def check_company_permission():
    """기업 회원 권한 확인"""
    if not current_user.is_authenticated:
        return False
    # user_type 1: 기업, is_verified True: 승인됨
    return current_user.user_type == 1 and current_user.is_verified

@company_bp.route("/company")
@login_required
def company_list():
    """
    기업 이음 메인 페이지 (기업 공고 목록)
    ====================================
    
    기능:
    - 기업 회원들이 작성한 공고 목록 조회
    - 검색 및 필터링 지원
    - 정렬 기능 (최신순, 인기순, 조회순)
    
    URL: GET /company
    템플릿: company/company_list.html
    
    반환값:
    - jobs_with_status: 공고 목록과 지원 상태
    - current_region: 현재 선택된 지역
    - current_sort: 현재 정렬 기준
    - can_create: 공고 작성 권한 여부
    """
    
    # URL 쿼리 파라미터에서 검색 및 필터 조건 추출
    query = request.args.get('q', '')
    region = request.args.get('region', '')
    recruitment_type = request.args.get('recruitment_type', '')
    work_period = request.args.get('work_period', '')
    sort_by = request.args.get('sort', 'latest')
    
    # 필터 조건 구성
    filters = {}
    if region:
        filters['region'] = region
    if recruitment_type:
        filters['recruitment_type'] = recruitment_type
    if work_period:
        filters['work_period'] = work_period
    
    # 기업이음 공고만 조회 (job_category가 있는 공고)
    company_condition = JobPost.job_category.isnot(None)
    conditions = [company_condition]
    
    if query or filters:
        jobs = JobService.search_jobs(query, filters, conditions, sort_by)
    else:
        jobs_pagination = JobService.get_all_jobs(page=1, per_page=20, sort_by=sort_by, conditions=conditions)
        jobs = jobs_pagination.items
    
    # 각 공고의 지원 상태 확인 (일반 사용자만)
    jobs_with_status = []
    for job in jobs:
        if current_user.user_type == 0:  # 일반 사용자인 경우만 지원 상태 확인
            application_status = ApplicationService.check_application_status(current_user.id, job.id)
        else:
            application_status = {'applied': False, 'status': None}
        
        job_data = {
            'job': job,
            'application_status': application_status
        }
        jobs_with_status.append(job_data)
    
    # 공고 작성 권한 확인
    can_create = check_company_permission()
    
    return render_template("company/company_list.html", 
                         jobs_with_status=jobs_with_status, 
                         current_region=region,
                         current_sort=sort_by,
                         can_create=can_create)

@company_bp.route("/company/create", methods=["GET", "POST"])
@login_required
def create_company_job():
    """
    기업 공고 작성 - 새로운 스크롤 방식으로 리다이렉트
    ==============
    
    기능:
    - 기업 회원만 공고 작성 가능
    - 승인된 기업 회원만 접근 허용
    - /jobs/create_company로 리다이렉트
    
    URL: GET/POST /company/create
    
    권한:
    - user_type == 1 (기업)
    - is_verified == True (승인됨)
    """
    
    # 기업 회원 권한 확인
    if not check_company_permission():
        flash("기업 회원만 공고를 작성할 수 있습니다. 기업 회원 인증을 완료해주세요.", "error")
        return redirect(url_for("company.company_list"))
    
    # 새로운 스크롤 방식 페이지로 리다이렉트
    return redirect(url_for("jobs.create_company_job"))

@company_bp.route("/company/<int:job_id>")
@login_required
def company_job_detail(job_id):
    """
    기업 공고 상세보기
    ==================
    
    기능:
    - 기업 공고 상세 정보 표시
    - 일반 사용자는 지원 가능
    - 기업 회원은 지원자 관리 가능
    
    URL: GET /company/<job_id>
    템플릿: company/job_detail.html
    """
    
    job = JobService.get_job_by_id(job_id)
    
    # 조회수 증가
    JobService.increment_view_count(job_id)
    
    # 현재 사용자가 이 공고를 찜했는지 확인
    is_bookmarked = JobService.is_bookmarked(current_user.id, job_id)
    
    # 현재 사용자의 지원 상태 확인 (일반 사용자만)
    if current_user.user_type == 0:
        application_status = ApplicationService.check_application_status(current_user.id, job_id)
    else:
        application_status = {'applied': False, 'status': None}
    
    # 지원자 목록 (공고 작성자만)
    applications = []
    if current_user.id == job.author_id:
        applications = ApplicationService.get_job_applications(job_id, current_user.id)
    
    return render_template("company/job_detail.html", 
                         job=job, 
                         is_bookmarked=is_bookmarked,
                         application_status=application_status,
                         applications=applications)

@company_bp.route("/company/<int:job_id>/applications")
@login_required
def company_job_applications(job_id):
    """
    기업 공고 지원자 목록
    ====================
    
    기능:
    - 공고에 지원한 사용자 목록 조회
    - 지원 상태 관리 (승인/거절)
    
    URL: GET /company/<job_id>/applications
    템플릿: company/job_applications.html
    
    권한:
    - 공고 작성자만 접근 가능
    """
    
    try:
        # 지원자 목록 조회 (권한 확인 포함)
        applications = ApplicationService.get_job_applications(job_id, current_user.id)
        
        # 공고 정보
        job = JobService.get_job_by_id(job_id)
        
        return render_template("company/job_applications.html", 
                             job=job, 
                             applications=applications)
        
    except Exception as e:
        flash("지원자 목록을 조회할 수 없습니다.", "error")
        return redirect(url_for("company.company_job_detail", job_id=job_id))

@company_bp.route("/applications/<int:application_id>/status", methods=["POST"])
@login_required
def update_application_status(application_id):
    status = request.json.get('status')
    result = ApplicationService.update_application_status(
        application_id, current_user.id, status
    )
    return jsonify(result)


# 기업 회원 전용 - 좋아요 페이지 (올린 공고 + 공개 이력서)
@company_bp.route("/company/favorites")
@login_required
def company_favorites():
    """
    기업 회원 전용 좋아요 페이지
    ===========================
    
    기능:
    - 올린 모집공고 탭: 기업이 작성한 공고 목록
    - 이력서 탭: 공개 동의된 일반 유저 이력서 목록
    
    URL: GET /company/favorites
    템플릿: company/favorites.html
    
    권한: 기업 회원만 접근 가능
    """
    
    # 기업 회원 권한 확인
    if not check_company_permission():
        flash("기업 회원만 접근할 수 있습니다.", "error")
        return redirect(url_for("auth.main"))
    
    # 탭 파라미터 (기본값: 올린 공고)
    tab = request.args.get('tab', 'jobs')
    
    # 올린 모집공고 조회 (기업이 작성한 공고)
    my_jobs = JobPost.query.filter_by(author_id=current_user.id).order_by(JobPost.created_at.desc()).all()
    
    # 공개 이력서 조회 (Resume 모델 사용)
    from models import Resume
    public_resumes = Resume.query.filter_by(is_public=True).order_by(Resume.updated_at.desc()).all()
    
    return render_template("company/favorites.html",
                         my_jobs=my_jobs,
                         public_resumes=public_resumes,
                         current_tab=tab)


# 이력서 목록 페이지 (메인 페이지 스타일)
@company_bp.route("/resumes")
@login_required
def resume_list():
    """
    이력서 목록 페이지 (메인 페이지 통합)
    ===============================
    
    기능:
    - 공개된 이력서 목록 조회
    - 직무 분야, 근무 요일, 신체 능력, 이동 거리로 필터링
    - 이력서 상세보기 및 제안하기
    
    URL: GET /resumes
    템플릿: company/resume_list.html
    
    권한: 로그인한 사용자만 접근 가능
    """
    
    # 공개된 이력서 조회 (user 관계 포함)
    from models import Resume, User
    public_resumes = Resume.query.join(User).filter(Resume.is_public == True).order_by(Resume.updated_at.desc()).all()
    
    return render_template("company/resume_list.html", resumes=public_resumes)
