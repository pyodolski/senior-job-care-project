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
from utils.helpers import format_datetime, get_work_days, calculate_time_ago
from utils.files_handler import generate_presigned_get_url
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
    recruitment_type = request.args.get('recruitment_type', '')  # 모집형태 필터
    work_period = request.args.get('work_period', '')  # 근무기간 필터
    sort_by = request.args.get('sort', 'latest')  # 정렬 기준

    # 필터 조건을 딕셔너리로 구성 (정확 일치용)
    filters = {}
    if recruitment_type:
        filters['recruitment_type'] = recruitment_type
    if work_period:
        filters['work_period'] = work_period

    # LIKE 검색 조건 (부분 일치용)
    conditions = []
    if request.args.get('region1'):
        region1 = request.args.get('region1')
        conditions.append(JobPost.region_1depth_name.like(f"{region1}%"))
    if request.args.get('region2'):
        region2 = request.args.get('region2')
        conditions.append(JobPost.region_2depth_name.like(f"{region2}%"))
    if request.args.get('region3'):
        region3 = request.args.get('region3')
        conditions.append(JobPost.region_3depth_name.like(f"{region3}%"))

    # 사람이음 공고만 필터링 (job_category가 없는 공고)
    people_condition = JobPost.job_category.is_(None)
    if conditions:
        conditions.append(people_condition)
    else:
        conditions = [people_condition]
    
    # 검색어나 필터가 있으면 검색 실행, 없으면 전체 목록 조회
    if query or filters or len(conditions) > 1:  # people_condition 외에 다른 조건이 있으면
        jobs = JobService.search_jobs(query, filters, conditions, sort_by)
    else:
        jobs_pagination = JobService.get_all_jobs(page=1, per_page=20, sort_by=sort_by, conditions=conditions)
        jobs = jobs_pagination.items

    # 각 공고의 지원 상태 및 북마크 상태 확인
    jobs_with_status = []
    for job in jobs:
        application_status = ApplicationService.check_application_status(current_user.id, job.id)
        # 북마크 상태 추가
        application_status['bookmarked'] = JobService.is_bookmarked(current_user.id, job.id)
        # 시간 경과 계산 추가
        job.time_ago = calculate_time_ago(job.created_at)
        job_data = {
            'job': job,
            'application_status': application_status
        }
        jobs_with_status.append(job_data)

    current_filters = filters.copy()
    current_filters['q'] = query
    current_filters['sort'] = sort_by

    return render_template("jobs/job_list.html",
                           jobs_with_status=jobs_with_status,
                           current_filters=current_filters
                           )


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
            
            # 사람이음 카테고리 (업무, 이웃, 과외, 제능, 문화)
            people_category = request.form.get("people_category", "").strip()

            # --- 행정구역 정보 추가로 받기 ---
            region_1depth_name = request.form.get("region_1depth_name")
            region_2depth_name = request.form.get("region_2depth_name")
            region_3depth_name = request.form.get("region_3depth_name")

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
            
            # 근무 요일 (문자열 "true"/"false"를 Boolean으로 변환)
            work_monday = request.form.get("work_monday") == "true"
            work_tuesday = request.form.get("work_tuesday") == "true"
            work_wednesday = request.form.get("work_wednesday") == "true"
            work_thursday = request.form.get("work_thursday") == "true"
            work_friday = request.form.get("work_friday") == "true"
            work_saturday = request.form.get("work_saturday") == "true"
            work_sunday = request.form.get("work_sunday") == "true"
            
            # 필수 필드 검증
            if not all([title, company, description]):
                flash("제목, 회사명, 설명은 필수 입력 항목입니다.", "error")
                return render_template("jobs/create_job_scroll.html")
            
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
                latitude=latitude,
                longitude=longitude,
                contact_phone=contact_phone,
                recruitment_count=recruitment_count,
                people_category=people_category,  # 사람이음 카테고리 추가
                work_start_time=work_start_time,
                work_end_time=work_end_time,
                work_monday=work_monday,
                work_tuesday=work_tuesday,
                work_wednesday=work_wednesday,
                work_thursday=work_thursday,
                work_friday=work_friday,
                work_saturday=work_saturday,
                work_sunday=work_sunday,
                region_1depth_name=region_1depth_name,
                region_2depth_name=region_2depth_name,
                region_3depth_name=region_3depth_name,
                author_id=current_user.id
            )
            
            db.session.add(new_job)
            db.session.commit()
            
            flash("공고가 성공적으로 등록되었습니다!", "success")
            return redirect(url_for("jobs.job_list"))
            
        except Exception as e:
            db.session.rollback()
            print(f"공고 등록 오류: {e}")
            import traceback
            traceback.print_exc()
            flash(f"공고 등록 중 오류가 발생했습니다: {str(e)}", "error")
            return render_template("jobs/create_job_scroll.html")
    
    return render_template("jobs/create_job_scroll.html", kakao_key=kakao_api_key)


# 기업이음 공고 작성 (스크롤 방식)
@jobs_bp.route("/jobs/create_company", methods=["GET", "POST"])
@login_required
def create_company_job():
    kakao_api_key = current_app.config.get('KAKAO_MAP_API_KEY')
    print(f"🗺️ 기업이음 글쓰기 - KAKAO_MAP_API_KEY: {kakao_api_key}")
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
            
            # 기업이음 카테고리 (안전·관리, 서비스·매장, 생활·돌봄 지원, 운전·배송, 사회·공공, 기타)
            job_category = request.form.get("job_category", "").strip()
            print(f"📝 기업이음 공고 작성 - job_category: '{job_category}'")

            # 행정구역 정보
            region_1depth_name = request.form.get("region_1depth_name")
            region_2depth_name = request.form.get("region_2depth_name")
            region_3depth_name = request.form.get("region_3depth_name")

            # 위도, 경도
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
            work_monday = request.form.get("work_monday") == "true"
            work_tuesday = request.form.get("work_tuesday") == "true"
            work_wednesday = request.form.get("work_wednesday") == "true"
            work_thursday = request.form.get("work_thursday") == "true"
            work_friday = request.form.get("work_friday") == "true"
            work_saturday = request.form.get("work_saturday") == "true"
            work_sunday = request.form.get("work_sunday") == "true"
            
            # 필수 필드 검증
            if not all([title, company, description]):
                flash("제목, 회사명, 설명은 필수 입력 항목입니다.", "error")
                return render_template("jobs/create_company_job_scroll.html", kakao_key=kakao_api_key)
            
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
                latitude=latitude,
                longitude=longitude,
                contact_phone=contact_phone,
                recruitment_count=recruitment_count,
                job_category=job_category,  # 기업이음 카테고리
                work_start_time=work_start_time,
                work_end_time=work_end_time,
                work_monday=work_monday,
                work_tuesday=work_tuesday,
                work_wednesday=work_wednesday,
                work_thursday=work_thursday,
                work_friday=work_friday,
                work_saturday=work_saturday,
                work_sunday=work_sunday,
                region_1depth_name=region_1depth_name,
                region_2depth_name=region_2depth_name,
                region_3depth_name=region_3depth_name,
                author_id=current_user.id
            )
            
            db.session.add(new_job)
            db.session.commit()
            
            print(f"✅ 기업이음 공고 저장 완료 - ID: {new_job.id}, job_category: '{new_job.job_category}'")
            
            flash("기업 공고가 성공적으로 등록되었습니다!", "success")
            return redirect(url_for("company.company_list"))
            
        except Exception as e:
            db.session.rollback()
            print(f"공고 등록 오류: {e}")
            import traceback
            traceback.print_exc()
            flash(f"공고 등록 중 오류가 발생했습니다: {str(e)}", "error")
            return render_template("jobs/create_company_job_scroll.html", kakao_key=kakao_api_key)
    
    return render_template("jobs/create_company_job_scroll.html", kakao_key=kakao_api_key)


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
    
    # 같은 지역의 다른 공고 추천 (최대 6개)
    related_jobs = []
    try:
        print(f"[DEBUG] 현재 공고 ID: {job_id}, 지역: {job.region}")
        print(f"[DEBUG] region_2depth_name: {job.region_2depth_name}, region_1depth_name: {job.region_1depth_name}")
        
        # 1차 시도: region_2depth_name으로 정확 매칭
        if job.region_2depth_name:
            related_jobs = JobPost.query.filter(
                JobPost.region_2depth_name == job.region_2depth_name,
                JobPost.id != job_id
            ).order_by(JobPost.created_at.desc()).limit(6).all()
            print(f"[DEBUG] region_2depth_name으로 조회: {len(related_jobs)}개 공고 발견")
        
        # 2차 시도: 결과가 없으면 region_1depth_name으로 시도
        if not related_jobs and job.region_1depth_name:
            related_jobs = JobPost.query.filter(
                JobPost.region_1depth_name == job.region_1depth_name,
                JobPost.id != job_id
            ).order_by(JobPost.created_at.desc()).limit(6).all()
            print(f"[DEBUG] region_1depth_name으로 조회: {len(related_jobs)}개 공고 발견")
        
        # 3차 시도: 여전히 결과가 없으면 region 필드로 LIKE 검색
        if not related_jobs and job.region:
            region_parts = job.region.split()
            if region_parts:
                # 첫 번째 단어(시/도)로 검색
                search_term = region_parts[0]
                print(f"[DEBUG] region으로 LIKE 검색 (폴백): '{search_term}'")
                related_jobs = JobPost.query.filter(
                    JobPost.region.like(f'%{search_term}%'),
                    JobPost.id != job_id
                ).order_by(JobPost.created_at.desc()).limit(6).all()
                print(f"[DEBUG] LIKE 검색 결과: {len(related_jobs)}개 공고 발견")
                for rj in related_jobs:
                    print(f"  - ID: {rj.id}, 제목: {rj.title}, 지역: {rj.region}, 등록일: {rj.created_at}")
        
        print(f"[DEBUG] 최종 관련 공고 수: {len(related_jobs)}")
    except Exception as e:
        print(f"관련 공고 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        related_jobs = []
    
    # Kakao Map API 키
    kakao_api_key = current_app.config.get('KAKAO_MAP_API_KEY')

    # 작성자 프로필 이미지 URL 생성
    author_profile_url = None
    if job.author and job.author.profile_image:
        author_profile_url = generate_presigned_get_url(job.author.profile_image, expires=900)

    # 공고 작성 시간 차이 계산
    time_ago = calculate_time_ago(job.created_at)

    # 관련 공고들의 즐겨찾기 상태 확인
    related_bookmarks = {}
    for related_job in related_jobs:
        related_bookmarks[related_job.id] = JobService.is_bookmarked(current_user.id, related_job.id)

    return render_template("jobs/job_detail.html",
                         job=job,
                         is_bookmarked=is_bookmarked,
                         application_status=application_status,
                         related_jobs=related_jobs,
                         kakao_key=kakao_api_key,
                         author_profile_url=author_profile_url,
                         time_ago=time_ago,
                         related_bookmarks=related_bookmarks)

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

            # --- 행정구역 정보 추가로 받기 ---
            job.region_1depth_name = request.form.get("region_1depth_name")
            job.region_2depth_name = request.form.get("region_2depth_name")
            job.region_3depth_name = request.form.get("region_3depth_name")

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
    
    # Kakao Map API 키 가져오기
    kakao_api_key = current_app.config.get("KAKAO_MAP_API_KEY")
    
    return render_template("jobs/edit_job.html", job=job, kakao_key=kakao_api_key)

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
    - 카테고리별 필터링 (사람 이음 / 기업 이음)
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

    # 정렬 기준 및 카테고리 추출
    sort_by = request.args.get('sort', 'latest')
    category = request.args.get('category', 'people')  # people(사람 이음) 또는 company(기업 이음)

    # JobService를 통해 현재 사용자의 찜 목록 조회
    jobs = JobService.get_user_bookmarks(current_user.id)

    # 카테고리별 필터링
    if category == 'company':
        # 기업 이음: user_type이 1인 작성자의 공고
        jobs = [job for job in jobs if job.author.user_type == 1]
    else:  # people
        # 사람 이음: user_type이 0인 작성자의 공고
        jobs = [job for job in jobs if job.author.user_type == 0]

    # 정렬 적용
    if sort_by == 'popular':
        jobs.sort(key=lambda x: x.bookmark_count + x.application_count, reverse=True)
    elif sort_by == 'views':
        jobs.sort(key=lambda x: x.view_count, reverse=True)
    else:  # latest
        jobs.sort(key=lambda x: x.created_at, reverse=True)

    # 각 공고의 지원 상태 및 북마크 상태 확인
    jobs_with_status = []
    for job in jobs:
        application_status = ApplicationService.check_application_status(current_user.id, job.id)
        # 북마크 상태 추가 (북마크 리스트에서는 항상 true)
        application_status['bookmarked'] = True
        job_data = {
            'job': job,
            'application_status': application_status
        }
        jobs_with_status.append(job_data)

    return render_template("jobs/bookmark_list.html",
                         jobs_with_status=jobs_with_status,
                         current_sort=sort_by,
                         current_category=category)

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


@jobs_bp.route("/jobs/ai-generate-description", methods=["POST"])
@login_required
def ai_generate_description():
    """
    AI 공고 설명 생성 API
    ===================
    
    기능:
    - 제목, 급여, 직무내용, 요구사항을 받아서 자동으로 상세 설명 생성
    - 템플릿 기반 텍스트 생성 (추후 실제 AI API 연동 가능)
    
    URL: POST /jobs/ai-generate-description
    
    Request Body (JSON):
    - title: 공고 제목
    - salary: 급여 정보
    - job_content: 직무 내용
    - requirements: 요구사항 (선택)
    
    Returns:
    - JSON: {"description": "생성된 설명"}
    """
    try:
        data = request.get_json()
        title = data.get('title', '')
        salary = data.get('salary', '')
        job_content = data.get('job_content', '')
        requirements = data.get('requirements', '')
        
        # 템플릿 기반 텍스트 생성
        description = f"""📌 모집 공고: {title}

💰 급여 정보
{salary}

📋 주요 업무
{job_content}
"""
        
        if requirements:
            description += f"""
✅ 지원 자격 및 요구사항
{requirements}
"""
        
        description += """
📞 지원 방법
- 본 공고에서 '지원하기' 버튼을 클릭해주세요
- 담당자가 확인 후 연락드리겠습니다

⭐ 우대사항
- 성실하고 책임감 있으신 분
- 원활한 의사소통이 가능하신 분
- 장기 근무 가능하신 분

🎯 근무 환경
- 쾌적한 근무 환경
- 상호 존중하는 직장 문화
- 성장할 수 있는 기회 제공

많은 관심과 지원 부탁드립니다! 😊
"""
        
        return jsonify({
            'success': True,
            'description': description.strip()
        })
        
    except Exception as e:
        current_app.logger.error(f"AI 설명 생성 중 오류: {e}")
        return jsonify({
            'success': False,
            'error': 'AI 설명 생성에 실패했습니다.'
        }), 500


@jobs_bp.route("/my-posts")
@login_required
def my_posts():
    """
    내가 올린 글 목록 페이지
    ======================

    기능:
    - 현재 로그인한 사용자가 작성한 공고 목록 조회
    - 작성일 기준 최신순 정렬

    URL: GET /my-posts
    템플릿: jobs/my_posts.html

    반환값:
    - jobs: 사용자가 작성한 공고 목록 (JobPost 객체 리스트)
    """
    try:
        # 현재 사용자가 작성한 공고 조회 (최신순)
        jobs = JobPost.query.filter_by(author_id=current_user.id)\
            .order_by(JobPost.created_at.desc())\
            .all()

        # 각 공고에 대한 지원자 수 계산
        for job in jobs:
            job.applicant_count = len(job.applications) if hasattr(job, 'applications') else 0
            job.time_ago = calculate_time_ago(job.created_at)
            job.work_days_text = get_work_days(job)

        return render_template(
            'jobs/my_posts.html',
            jobs=jobs,
            total_count=len(jobs)
        )

    except Exception as e:
        current_app.logger.error(f"내가 올린 글 조회 중 오류: {e}")
        flash("글 목록을 불러오는 중 오류가 발생했습니다.", "error")
        return redirect(url_for('auth.profile'))