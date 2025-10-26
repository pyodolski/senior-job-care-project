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
    
    # 기업 회원들이 작성한 공고만 조회
    if query or filters:
        all_jobs = JobService.search_jobs(query, filters, None, sort_by)
        # 기업 회원이 작성한 공고만 필터링
        jobs = [job for job in all_jobs if job.author.user_type == 1]
    else:
        jobs_pagination = JobService.get_all_jobs(page=1, per_page=20, sort_by=sort_by)
        # 기업 회원이 작성한 공고만 필터링
        jobs = [job for job in jobs_pagination.items if job.author.user_type == 1]
    
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
    기업 공고 작성
    ==============
    
    기능:
    - 기업 회원만 공고 작성 가능
    - 승인된 기업 회원만 접근 허용
    
    URL: GET/POST /company/create
    템플릿: company/create_job.html
    
    권한:
    - user_type == 1 (기업)
    - is_verified == True (승인됨)
    """
    
    # 기업 회원 권한 확인
    if not check_company_permission():
        flash("기업 회원만 공고를 작성할 수 있습니다. 기업 회원 인증을 완료해주세요.", "error")
        return redirect(url_for("company.company_list"))
    
    if request.method == "POST":
        try:
            # 기본 정보
            title = request.form.get("title", "").strip()
            company = request.form.get("company", "").strip()
            description = request.form.get("description", "").strip()
            
            # 직무 내용
            job_category = request.form.get("job_category", "일반")
            job_category_custom = request.form.get("job_category_custom", "").strip()
            
            # 임금 정보
            salary_min = request.form.get("salary_min", type=int)
            salary_max = request.form.get("salary_max", type=int)
            salary_negotiable = bool(request.form.get("salary_negotiable"))
            
            # 경력
            experience_required = request.form.get("experience_required", "")
            
            # 복리후생
            benefit_commute_bus = bool(request.form.get("benefit_commute_bus"))
            benefit_lunch = bool(request.form.get("benefit_lunch"))
            benefit_uniform = bool(request.form.get("benefit_uniform"))
            benefit_health_checkup = bool(request.form.get("benefit_health_checkup"))
            benefit_other = request.form.get("benefit_other", "").strip()
            
            # 장애인용 복지시설
            disabled_parking = bool(request.form.get("disabled_parking"))
            disabled_elevator = bool(request.form.get("disabled_elevator"))
            disabled_ramp = bool(request.form.get("disabled_ramp"))
            disabled_restroom = bool(request.form.get("disabled_restroom"))
            
            # 고용형태 및 근무조건
            recruitment_type = request.form.get("recruitment_type", "")
            region = request.form.get("region", "").strip()
            contact_phone = request.form.get("contact_phone", "").strip()
            recruitment_count = request.form.get("recruitment_count", type=int)
            
            # 근무 시간
            work_start_time_str = request.form.get("work_start_time", "")
            work_end_time_str = request.form.get("work_end_time", "")
            
            work_start_time = None
            work_end_time = None
            
            if work_start_time_str:
                work_start_time = datetime.strptime(work_start_time_str, "%H:%M").time()
            if work_end_time_str:
                work_end_time = datetime.strptime(work_end_time_str, "%H:%M").time()
            
            # 근무 요일
            work_monday = bool(request.form.get("work_monday"))
            work_tuesday = bool(request.form.get("work_tuesday"))
            work_wednesday = bool(request.form.get("work_wednesday"))
            work_thursday = bool(request.form.get("work_thursday"))
            work_friday = bool(request.form.get("work_friday"))
            work_saturday = bool(request.form.get("work_saturday"))
            work_sunday = bool(request.form.get("work_sunday"))
            
            # 모집기간
            recruitment_start_date_str = request.form.get("recruitment_start_date", "")
            recruitment_end_date_str = request.form.get("recruitment_end_date", "")
            
            recruitment_start_date = None
            recruitment_end_date = None
            
            if recruitment_start_date_str:
                recruitment_start_date = datetime.strptime(recruitment_start_date_str, "%Y-%m-%d").date()
            if recruitment_end_date_str:
                recruitment_end_date = datetime.strptime(recruitment_end_date_str, "%Y-%m-%d").date()
            
            # 필수 필드 검증
            if not all([title, company, description]):
                flash("채용 제목, 회사명, 상세 설명은 필수 입력 항목입니다.", "error")
                return render_template("company/create_job.html")
            
            # 임금 정보 처리
            salary = ""
            if salary_negotiable:
                salary = "협의"
            elif salary_min or salary_max:
                if salary_min and salary_max:
                    salary = f"{salary_min}~{salary_max}만원"
                elif salary_min:
                    salary = f"{salary_min}만원 이상"
                elif salary_max:
                    salary = f"{salary_max}만원 이하"
            
            # 새 공고 생성
            new_job = JobPost(
                title=title,
                company=company,
                description=description,
                job_category=job_category,
                job_category_custom=job_category_custom if job_category == "기타" else None,
                salary=salary,
                salary_min=salary_min if not salary_negotiable else None,
                salary_max=salary_max if not salary_negotiable else None,
                salary_negotiable=salary_negotiable,
                experience_required=experience_required,
                benefit_commute_bus=benefit_commute_bus,
                benefit_lunch=benefit_lunch,
                benefit_uniform=benefit_uniform,
                benefit_health_checkup=benefit_health_checkup,
                benefit_other=benefit_other,
                disabled_parking=disabled_parking,
                disabled_elevator=disabled_elevator,
                disabled_ramp=disabled_ramp,
                disabled_restroom=disabled_restroom,
                recruitment_type=recruitment_type,
                region=region,
                contact_phone=contact_phone,
                recruitment_count=recruitment_count,
                work_start_time=work_start_time,
                work_end_time=work_end_time,
                work_monday=work_monday,
                work_tuesday=work_tuesday,
                work_wednesday=work_wednesday,
                work_thursday=work_thursday,
                work_friday=work_friday,
                work_saturday=work_saturday,
                work_sunday=work_sunday,
                recruitment_start_date=recruitment_start_date,
                recruitment_end_date=recruitment_end_date,
                author_id=current_user.id
            )
            
            db.session.add(new_job)
            db.session.commit()
            
            flash("기업 공고가 성공적으로 등록되었습니다!", "success")
            return redirect(url_for("company.company_list"))
            
        except Exception as e:
            db.session.rollback()
            flash("공고 등록 중 오류가 발생했습니다. 다시 시도해주세요.", "error")
            return render_template("company/create_job.html")
    
    return render_template("company/create_job.html")

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