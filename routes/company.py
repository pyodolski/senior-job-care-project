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
from models import db, JobPost, User
from services.job_service import JobService
from services.application_service import ApplicationService
from services.suggestion_service import SuggestionService
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

    page = request.args.get('page', 1, type=int)
    per_page = 10

    # URL 쿼리 파라미터에서 검색 및 필터 조건 추출
    query = request.args.get('q', '')
    region = request.args.get('region', '')
    recruitment_type = request.args.get('recruitment_type', '')
    work_period = request.args.get('work_period', '')
    sort_by = request.args.get('sort', 'latest')

    region1 = request.args.get('region1')
    region2 = request.args.get('region2')
    region3 = request.args.get('region3')

    filters = {}
    if recruitment_type:
        filters['recruitment_type'] = recruitment_type
    if work_period:
        filters['work_period'] = work_period

    # 지역 필터 조건 및 기업 공고 조건을 위한 리스트
    conditions = []

    # 1. 기업 공고 조건: 기업이 작성했거나 외부 데이터(K-Senior 등)
    company_condition = db.or_(
        User.user_type == 1,  # 기업이 작성한 공고
        JobPost.source.isnot(None)  # 외부 데이터 (K-Senior 등)
    )
    conditions.append(company_condition)

    # 2. 지역 필터링 조건 추가
    if region1:
        conditions.append(JobPost.region_1depth_name.like(f"{region1}%"))
    if region2:
        conditions.append(JobPost.region_2depth_name.like(f"{region2}%"))
    if region3:
        conditions.append(JobPost.region_3depth_name.like(f"{region3}%"))

    # 기업이음 공고만 조회 (LEFT JOIN으로 변경 - 외부 데이터는 author가 없을 수 있음)
    base_query = JobPost.query.outerjoin(User)

    if query or filters or len(conditions) > 1:  # 기업 조건 외에 다른 필터가 있는 경우
        jobs = JobService.search_jobs(query, filters, conditions, sort_by, base_query=base_query)
        jobs_pagination = None  # search_jobs는 페이지네이션을 반환하지 않음
    else:
        # 지역 필터링 조건이 없는 순수 전체 기업 공고 리스트 조회
        jobs_pagination = JobService.get_all_jobs(page=page, per_page=per_page, sort_by=sort_by, conditions=conditions,
                                                  base_query=base_query)
        jobs = jobs_pagination.items

    # 각 공고의 지원 상태 확인 (일반 사용자만)
    jobs_with_status = []
    for job in jobs:
        if current_user.user_type == 0:  # 일반 사용자인 경우만 지원 상태 확인
            application_status = ApplicationService.check_application_status(current_user.id, job.id)
        else:
            application_status = {'applied': False, 'status': None}

        # 북마크 상태 추가
        application_status['bookmarked'] = JobService.is_bookmarked(current_user.id, job.id)

        job_data = {
            'job': job,
            'application_status': application_status
        }
        jobs_with_status.append(job_data)

    # 공고 작성 권한 확인
    can_create = check_company_permission()

    # 현재 적용된 필터 정보를 템플릿으로 전달
    current_filters = filters.copy()
    current_filters['region_1depth_name'] = region1
    current_filters['region_2depth_name'] = region2
    current_filters['region_3depth_name'] = region3
    current_filters['sort'] = sort_by

    return render_template("company/company_list.html",
                         jobs_with_status=jobs_with_status,
                         current_filters=current_filters,
                         current_sort=sort_by,
                         can_create=can_create,
                         pagination=jobs_pagination)

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
    
    # 좋아요한 이력서 조회 (ResumeFavorite 모델 사용)
    from models import Resume, ResumeFavorite, User
    
    # 현재 사용자가 좋아요한 이력서 ID 목록
    favorite_resume_ids = [fav.resume_id for fav in ResumeFavorite.query.filter_by(user_id=current_user.id).all()]
    
    # 좋아요한 이력서 목록 조회
    favorited_resumes = Resume.query.join(User).filter(
        Resume.id.in_(favorite_resume_ids) if favorite_resume_ids else False,
        Resume.is_public == True
    ).order_by(Resume.updated_at.desc()).all()
    
    return render_template("company/favorites.html",
                         my_jobs=my_jobs,
                         favorited_resumes=favorited_resumes,
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


@company_bp.route("/company/jobs/json")
@login_required
def company_jobs_json():
    """
    기업 공고 목록을 JSON 형식으로 반환 (AJAX 전용)
    ======================================

    URL: GET /company/jobs/json?page=<page_num>&sort=<sort_by>...
    """

    page = request.args.get('page', 1, type=int)
    per_page = 10
    query = request.args.get('q', '')
    region = request.args.get('region', '')
    recruitment_type = request.args.get('recruitment_type', '')
    work_period = request.args.get('work_period', '')
    sort_by = request.args.get('sort', 'latest')

    # 계층적 지역 필터링을 위한 쿼리 파라미터
    region1 = request.args.get('region1')
    region2 = request.args.get('region2')
    region3 = request.args.get('region3')

    # 필터 조건 구성
    filters = {}
    if recruitment_type:
        filters['recruitment_type'] = recruitment_type
    if work_period:
        filters['work_period'] = work_period

    base_query = JobPost.query.join(User)
    conditions = []

    # 1. 기업 공고 조건
    conditions.append(User.user_type == 1)

    # 2. 지역 필터링 조건 추가
    if region1:
        conditions.append(JobPost.region_1depth_name.like(f"{region1}%"))
    if region2:
        conditions.append(JobPost.region_2depth_name.like(f"{region2}%"))
    if region3:
        conditions.append(JobPost.region_3depth_name.like(f"{region3}%"))

    try:
        jobs_pagination = JobService.get_all_jobs(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            conditions=conditions,
            base_query=base_query,
        )

        # JSON으로 반환하기 위해 데이터 가공
        jobs_data = []
        for job in jobs_pagination.items:
            # 각 공고의 지원 상태 확인 (일반 사용자만)
            application_status = {'applied': False, 'status': None}
            if current_user.user_type == 0:
                application_status = ApplicationService.check_application_status(current_user.id, job.id)

            # 북마크 상태 확인
            is_bookmarked = JobService.is_bookmarked(current_user.id, job.id)

            jobs_data.append({
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'salary': job.salary,
                'recruitment_type': job.recruitment_type,
                'work_period': job.work_period,
                'view_count': job.view_count,
                'bookmark_count': job.bookmark_count,
                'application_count': job.application_count,
                'author_id': job.author_id,  # author_id를 사용하여 클라이언트에서 '내 공고' 구분
                'is_applied': application_status['applied'],
                'is_bookmarked': is_bookmarked,
                'created_at': job.created_at.isoformat()
            })

        return jsonify({
            'success': True,
            'jobs': jobs_data,
            'has_next': jobs_pagination.has_next,
            'next_num': jobs_pagination.next_num if jobs_pagination.has_next else None,
            'total_pages': jobs_pagination.pages,
            'current_user_id': current_user.id,
            'current_user_type': current_user.user_type
        })
    except Exception as e:
        # 오류 발생 시 빈 목록 반환
        return jsonify({'success': False, 'message': str(e), 'jobs': []}), 500

# 기업이 공고를 제안하는 페이지 및 로직
@company_bp.route("/resume/<int:resume_id>/suggest", methods=["GET", "POST"])
@login_required
def suggest_job(resume_id):
    """
    이력서에 공고 제안하기
    =====================
    GET: 제안할 수 있는 내 공고 목록을 보여주는 페이지
    POST: 선택된 공고들을 제안으로 보냄
    """
    # 1. 기업 회원 권한 확인
    if not check_company_permission():
        flash("기업 회원만 공고를 제안할 수 있습니다.", "error")
        return redirect(url_for("company.resume_list"))

    # 2. POST 요청 처리 (제안 보내기 버튼을 눌렀을 때)
    if request.method == "POST":
        # 공고 ID 목록을 가져옵니다.
        selected_job_ids = request.form.getlist('job_ids')

        if not selected_job_ids:
            flash("제안할 공고를 하나 이상 선택해주세요.", "warning")
            return redirect(url_for("company.suggest_job", resume_id=resume_id))

        new_count = SuggestionService.create_suggestions(
            suggester_id=current_user.id,
            resume_id=resume_id,
            job_ids=selected_job_ids
        )

        return redirect(url_for("company.resume_list"))

    # 3. GET 요청 처리 (제안할 공고 선택 페이지를 보여줄 때)
    resume = SuggestionService.get_resume_for_suggestion_page(resume_id)
    # 현재 기업이 올린 공고 목록
    jobs_for_suggestion = SuggestionService.get_jobs_for_suggestion(
        suggester_id=current_user.id,
        resume_id=resume_id
    )

    return render_template("company/suggest_job.html", resume=resume, jobs_for_suggestion=jobs_for_suggestion)


# 일반 사용자가 받은 제안 목록을 보는 페이지
@company_bp.route("/suggestions/received")
@login_required
def received_suggestions():
    """
    받은 제안 목록 페이지 (일반 사용자용)
    ================================
    """
    # 일반 사용자(user_type=0)
    if current_user.user_type != 0:
        flash("일반 사용자만 접근할 수 있는 페이지입니다.", "error")
        return redirect(url_for("auth.main"))

    # 현재 사용자가 받은 제안 목록
    suggestions = SuggestionService.get_received_suggestions(user_id=current_user.id)

    return render_template("company/received_suggestions.html", suggestions=suggestions)


@company_bp.route("/api/suggestions/<int:suggestion_id>/accept", methods=["POST"])
@login_required
def accept_suggestion(suggestion_id):
    """
    [API] 제안을 수락하고 채팅방으로 연결합니다.
    """
    try:
        # 서비스의 '제안 수락 및 채팅방 생성' 기능을 호출합니다.
        chat_room_id = SuggestionService.accept_suggestion_and_get_chat(
            suggestion_id=suggestion_id,
            user_id=current_user.id
        )

        # 성공하면, 채팅방 ID를 포함하여 JSON 형태로 응답합니다.
        return jsonify({
            'success': True,
            'chat_room_id': chat_room_id
        })

    except PermissionError:
        return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403
    except Exception as e:
        print(f"제안 수락 오류: {e}")
        return jsonify({'success': False, 'message': '오류가 발생했습니다.'}), 500


@company_bp.route("/api/suggestions/<int:suggestion_id>/reject", methods=["POST"])
@login_required
def reject_suggestion(suggestion_id):
    """
    제안을 거절 상태로 변경
    """
    try:
        # 상태 rejected로 변경
        SuggestionService.update_suggestion_status(
            suggestion_id=suggestion_id,
            user_id=current_user.id,
            new_status='rejected'
        )

        return jsonify({
            'success': True,
            'message': '제안을 거절했습니다.'
        })

    except PermissionError:
        return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403
    except Exception as e:
        print(f"제안 거절 오류: {e}")
        return jsonify({'success': False, 'message': '오류가 발생했습니다.'}), 500