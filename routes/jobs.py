"""
공고 관련 라우트 모듈
===================

이 모듈은 구인공고와 관련된 모든 웹 라우트를 처리합니다.

주요 기능:
- 공고 목록 조회 및 검색/필터링
- 공고 상세 정보 조회
- 공고 작성, 수정, 삭제 (CRUD)
- 찜하기/찜 해제 기능
- 사용자별 찜 목록 관리

작성자: [팀명]
최종 수정일: 2025-01-09
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify,  current_app
from flask_login import login_required, current_user
from models import db, JobPost
from services.job_service import JobService
from services.application_service import ApplicationService
from utils.helpers import format_datetime, get_work_days
from datetime import datetime, time

# 공고 관련 블루프린트 생성
jobs_bp = Blueprint("jobs", __name__)

@jobs_bp.route("/jobs")
@login_required
def job_list():
    """
    공고 목록 페이지
    ===============
    
    기능:
    - 전체 공고 목록 조회
    - 검색어로 공고 검색 (제목, 회사명, 설명 검색)
    - 지역, 모집형태, 근무기간으로 필터링
    - 페이지네이션 지원 (기본 20개씩)
    
    URL: GET /jobs
    템플릿: jobs/job_list.html
    
    쿼리 파라미터:
    - q: 검색어 (선택)
    - region: 지역 필터 (선택)
    - recruitment_type: 모집형태 필터 (선택)
    - work_period: 근무기간 필터 (선택)
    
    반환값:
    - jobs: 공고 목록
    - current_region: 현재 선택된 지역
    """
    
    # URL 쿼리 파라미터에서 검색 및 필터 조건 추출
    query = request.args.get('q', '')  # 검색어
    region = request.args.get('region', '')  # 지역 필터
    recruitment_type = request.args.get('recruitment_type', '')  # 모집형태 필터
    work_period = request.args.get('work_period', '')  # 근무기간 필터
    sort_by = request.args.get('sort', 'latest')  # 정렬 기준
    
    # 필터 조건을 딕셔너리로 구성
    filters = {}
    if region:
        filters['region'] = region
    if recruitment_type:
        filters['recruitment_type'] = recruitment_type
    if work_period:
        filters['work_period'] = work_period
    
    # 검색어나 필터가 있으면 검색 실행, 없으면 전체 목록 조회
    if query or filters:
        jobs = JobService.search_jobs(query, filters, sort_by)
    else:
        jobs_pagination = JobService.get_all_jobs(page=1, per_page=20, sort_by=sort_by)
        jobs = jobs_pagination.items
    
    # 각 공고의 지원 상태 확인
    jobs_with_status = []
    for job in jobs:
        application_status = ApplicationService.check_application_status(current_user.id, job.id)
        job_data = {
            'job': job,
            'application_status': application_status
        }
        jobs_with_status.append(job_data)
    
    return render_template("jobs/job_list.html", 
                         jobs_with_status=jobs_with_status, 
                         current_region=region,
                         current_sort=sort_by)

# 공고 작성 페이지
@jobs_bp.route("/jobs/create", methods=["GET", "POST"])
@login_required
def create_job():
    kakao_api_key = current_app.config.get('KAKAO_MAP_API_KEY')
    if request.method == "POST":
        try:
            # 폼 데이터 받기
            title = request.form.get("title", "").strip()
            company = request.form.get("company", "").strip()
            description = request.form.get("description", "").strip()
            recruitment_type = request.form.get("recruitment_type", "")
            work_period = request.form.get("work_period", "")
            salary = request.form.get("salary", "").strip()
            region = request.form.get("region", "").strip()
            contact_phone = request.form.get("contact_phone", "").strip()
            recruitment_count = request.form.get("recruitment_count", type=int)

            # 위도, 경도 폼 데이터
            latitude = request.form.get("latitude", type=float)
            longitude = request.form.get("longitude", type=float)
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
            
            # 필수 필드 검증
            if not all([title, company, description]):
                flash("제목, 회사명, 설명은 필수 입력 항목입니다.", "error")
                return render_template("jobs/create_job.html")
            
            # 정규직인 경우 work_period를 자동으로 설정
            if recruitment_type == "정규직":
                work_period = "장기"
            
            # 새 공고 생성
            new_job = JobPost(
                title=title,
                company=company,
                description=description,
                recruitment_type=recruitment_type,
                work_period=work_period,
                salary=salary,
                region=region,
                latitude=latitude,  # 여기에 추가
                longitude=longitude,  # 여기에 추가
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
                author_id=current_user.id
            )
            
            db.session.add(new_job)
            db.session.commit()
            
            flash("공고가 성공적으로 등록되었습니다!", "success")
            return redirect(url_for("jobs.job_list"))
            
        except Exception as e:
            db.session.rollback()
            flash("공고 등록 중 오류가 발생했습니다. 다시 시도해주세요.", "error")
            return render_template("jobs/create_job.html")
    
    return render_template("jobs/create_job.html", kakao_key=kakao_api_key)

# 공고 상세보기
@jobs_bp.route("/jobs/<int:job_id>")
@login_required
def job_detail(job_id):
    job = JobService.get_job_by_id(job_id)
    
    # 조회수 증가
    JobService.increment_view_count(job_id)
    
    # 현재 사용자가 이 공고를 찜했는지 확인
    is_bookmarked = JobService.is_bookmarked(current_user.id, job_id)
    
    # 현재 사용자의 지원 상태 확인
    application_status = ApplicationService.check_application_status(current_user.id, job_id)
    
    return render_template("jobs/job_detail.html", 
                         job=job, 
                         is_bookmarked=is_bookmarked,
                         application_status=application_status)

# 공고 수정
@jobs_bp.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
@login_required
def edit_job(job_id):
    job = JobPost.query.get_or_404(job_id)
    
    # 작성자만 수정 가능
    if job.author_id != current_user.id:
        flash("본인이 작성한 공고만 수정할 수 있습니다.", "error")
        return redirect(url_for("jobs.job_detail", job_id=job_id))
    
    if request.method == "POST":
        try:
            # 폼 데이터 업데이트
            job.title = request.form.get("title", "").strip()
            job.company = request.form.get("company", "").strip()
            job.description = request.form.get("description", "").strip()
            job.recruitment_type = request.form.get("recruitment_type", "")
            job.work_period = request.form.get("work_period", "")
            job.salary = request.form.get("salary", "").strip()
            job.region = request.form.get("region", "").strip()
            job.contact_phone = request.form.get("contact_phone", "").strip()
            job.recruitment_count = request.form.get("recruitment_count", type=int)

            latitude = request.form.get("latitude", type=float)
            longitude = request.form.get("longitude", type=float)
            if latitude is not None:
                job.latitude = latitude
            if longitude is not None:
                job.longitude = longitude

            # 근무 시간 업데이트
            work_start_time_str = request.form.get("work_start_time", "")
            work_end_time_str = request.form.get("work_end_time", "")
            
            if work_start_time_str:
                job.work_start_time = datetime.strptime(work_start_time_str, "%H:%M").time()
            if work_end_time_str:
                job.work_end_time = datetime.strptime(work_end_time_str, "%H:%M").time()
            
            # 근무 요일 업데이트
            job.work_monday = bool(request.form.get("work_monday"))
            job.work_tuesday = bool(request.form.get("work_tuesday"))
            job.work_wednesday = bool(request.form.get("work_wednesday"))
            job.work_thursday = bool(request.form.get("work_thursday"))
            job.work_friday = bool(request.form.get("work_friday"))
            job.work_saturday = bool(request.form.get("work_saturday"))
            job.work_sunday = bool(request.form.get("work_sunday"))
            
            db.session.commit()
            flash("공고가 성공적으로 수정되었습니다!", "success")
            return redirect(url_for("jobs.job_detail", job_id=job_id))
            
        except Exception as e:
            db.session.rollback()
            flash("공고 수정 중 오류가 발생했습니다.", "error")
    
    return render_template("jobs/edit_job.html", job=job)

# 공고 삭제
@jobs_bp.route("/jobs/<int:job_id>/delete", methods=["POST"])
@login_required
def delete_job(job_id):
    job = JobPost.query.get_or_404(job_id)
    
    # 작성자만 삭제 가능
    if job.author_id != current_user.id:
        flash("본인이 작성한 공고만 삭제할 수 있습니다.", "error")
        return redirect(url_for("jobs.job_detail", job_id=job_id))
    
    try:
        db.session.delete(job)
        db.session.commit()
        flash("공고가 삭제되었습니다.", "success")
        return redirect(url_for("jobs.job_list"))
    except Exception as e:
        db.session.rollback()
        flash("공고 삭제 중 오류가 발생했습니다.", "error")
        return redirect(url_for("jobs.job_detail", job_id=job_id))

@jobs_bp.route("/jobs/<int:job_id>/bookmark", methods=["POST"])
@login_required
def toggle_bookmark(job_id):
    """
    찜하기/찜 해제 토글
    ==================
    
    기능:
    - 공고를 찜 목록에 추가하거나 제거
    - AJAX 요청과 일반 폼 요청 모두 지원
    - 찜 상태에 따라 적절한 메시지 반환
    
    URL: POST /jobs/<job_id>/bookmark
    
    매개변수:
    - job_id: 찜할 공고의 ID
    
    반환값 (AJAX):
    - success: 성공 여부 (boolean)
    - is_bookmarked: 찜 상태 (boolean)
    - bookmark_count: 총 찜 개수 (int)
    - message: 결과 메시지 (string)
    
    반환값 (일반 요청):
    - 성공 시: 공고 상세 페이지로 리다이렉트
    - 실패 시: 에러 메시지와 함께 공고 상세 페이지로 리다이렉트
    """
    try:
        # JobService를 통해 찜 상태 토글 (True: 찜 추가, False: 찜 해제)
        is_bookmarked = JobService.toggle_bookmark(current_user.id, job_id)
        
        # 업데이트된 공고 정보 조회
        job = JobService.get_job_by_id(job_id)
        
        # 찜 상태에 따른 메시지 설정
        message = "찜 목록에 추가했습니다." if is_bookmarked else "찜을 취소했습니다."
        
        # AJAX 요청인 경우 JSON 응답 반환
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'success': True,
                'is_bookmarked': is_bookmarked,
                'bookmark_count': job.bookmark_count,
                'message': message
            })
        
        # 일반 요청인 경우 플래시 메시지와 함께 리다이렉트
        flash(message, "success")
        return redirect(url_for("jobs.job_detail", job_id=job_id))
        
    except Exception as e:
        # 에러 발생 시 처리
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'success': False,
                'message': '오류가 발생했습니다.'
            }), 500
        
        flash("오류가 발생했습니다.", "error")
        return redirect(url_for("jobs.job_detail", job_id=job_id))

@jobs_bp.route("/bookmarks")
@login_required
def bookmark_list():
    """
    사용자 찜 목록 페이지
    ===================
    
    기능:
    - 현재 로그인한 사용자의 찜한 공고 목록 조회
    - 찜한 순서대로 정렬 (최신순)
    - 찜 해제 기능 포함
    
    URL: GET /bookmarks
    템플릿: jobs/bookmark_list.html
    
    반환값:
    - jobs: 사용자가 찜한 공고 목록
    
    주의사항:
    - 로그인이 필요한 페이지
    - 찜 목록이 비어있을 경우 빈 상태 메시지 표시
    """
    
    # 정렬 기준 추출
    sort_by = request.args.get('sort', 'latest')
    
    # JobService를 통해 현재 사용자의 찜 목록 조회
    jobs = JobService.get_user_bookmarks(current_user.id)
    
    # 정렬 적용
    if sort_by == 'popular':
        jobs.sort(key=lambda x: x.bookmark_count + x.application_count, reverse=True)
    elif sort_by == 'views':
        jobs.sort(key=lambda x: x.view_count, reverse=True)
    else:  # latest
        jobs.sort(key=lambda x: x.created_at, reverse=True)
    
    # 각 공고의 지원 상태 확인
    jobs_with_status = []
    for job in jobs:
        application_status = ApplicationService.check_application_status(current_user.id, job.id)
        job_data = {
            'job': job,
            'application_status': application_status
        }
        jobs_with_status.append(job_data)
    
    return render_template("jobs/bookmark_list.html", 
                         jobs_with_status=jobs_with_status,
                         current_sort=sort_by)

@jobs_bp.route("/jobs/<int:job_id>/apply", methods=["POST"])
@login_required
def apply_job(job_id):
    """
    공고 지원하기
    ============
    
    기능:
    - 공고에 지원 신청
    - 자동으로 채팅방 생성
    - 지원 상태 관리
    
    URL: POST /jobs/<job_id>/apply
    
    매개변수:
    - job_id: 지원할 공고의 ID
    
    요청 데이터 (선택):
    - message: 지원 메시지
    
    반환값 (AJAX):
    - success: 성공 여부
    - message: 결과 메시지
    - chat_room_id: 생성된 채팅방 ID (성공 시)
    
    반환값 (일반 요청):
    - 성공 시: 공고 상세 페이지로 리다이렉트
    - 실패 시: 에러 메시지와 함께 공고 상세 페이지로 리다이렉트
    """
    
    try:
        print(f"지원하기 시작: user_id={current_user.id}, job_id={job_id}")
        
        # 지원 메시지 추출 (선택사항)
        message = None
        if request.is_json:
            try:
                data = request.get_json()
                message = data.get('message', '').strip() if data else None
            except Exception as json_error:
                print(f"JSON 파싱 오류: {json_error}")
                message = None
        else:
            message = request.form.get('message', '').strip()
        
        print(f"지원 메시지: {message}")
        
        # 지원 처리
        result = ApplicationService.apply_to_job(
            user_id=current_user.id,
            job_id=job_id,
            message=message
        )
        
        print(f"지원 결과: {result}")
        
        # AJAX 요청인 경우 JSON 응답
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': result['message'],
                    'chat_room_id': result.get('chat_room_id')
                })
            else:
                return jsonify({
                    'success': False,
                    'message': result['message']
                }), 400
        
        # 일반 요청인 경우 플래시 메시지와 리다이렉트
        if result['success']:
            flash(result['message'], "success")
        else:
            flash(result['message'], "error")
        
        return redirect(url_for("jobs.job_detail", job_id=job_id))
        
    except Exception as e:
        print(f"지원하기 오류: {e}")
        import traceback
        traceback.print_exc()
        
        error_message = f"지원 처리 중 오류가 발생했습니다: {str(e)}"
        
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'success': False,
                'message': error_message
            }), 500
        
        flash(error_message, "error")
        return redirect(url_for("jobs.job_detail", job_id=job_id))

@jobs_bp.route("/jobs/<int:job_id>/applications")
@login_required
def job_applications(job_id):
    """
    공고 지원자 목록 (고용주용)
    =========================
    
    기능:
    - 공고에 지원한 사용자 목록 조회
    - 지원 상태별 필터링
    - 지원자와의 채팅방 링크 제공
    
    URL: GET /jobs/<job_id>/applications
    템플릿: jobs/job_applications.html
    
    매개변수:
    - job_id: 공고 ID
    
    반환값:
    - job: 공고 정보
    - applications: 지원자 목록
    
    주의사항:
    - 공고 작성자만 접근 가능
    """
    
    try:
        # 지원자 목록 조회 (권한 확인 포함)
        applications = ApplicationService.get_job_applications(job_id, current_user.id)
        
        # 공고 정보
        job = JobService.get_job_by_id(job_id)
        
        return render_template("jobs/job_applications.html", 
                             job=job, 
                             applications=applications)
        
    except Exception as e:
        flash("지원자 목록을 조회할 수 없습니다.", "error")
        return redirect(url_for("jobs.job_detail", job_id=job_id))