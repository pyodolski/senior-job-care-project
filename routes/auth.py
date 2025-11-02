from flask import Blueprint, render_template, redirect, url_for, request, session, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from flask_dance.contrib.google import google
from models import db, User, JobApplication, JobSuggestion, JobPost
import requests
from config import Config
import os
from flask import current_app, flash
import uuid
import bcrypt
from flask import request, flash
from services.job_service import JobService
from services.application_service import ApplicationService
from services.naver_news_service import NaverNewsService
import boto3
from utils.files_handler import upload_file, generate_presigned_get_url
from urllib.parse import urlparse
from services.resume_service import ResumeService

# 인증 관련 라우트를 담당하는 블루프린트 생성
auth_bp = Blueprint("auth", __name__)

# 홈 화면 렌더링 (로그인 전)
@auth_bp.route("/")
def home():
    # ?logout=true 파라미터가 있으면 강제 로그아웃
    if request.args.get('logout') == 'true':
        if current_user.is_authenticated:
            logout_user()
            flash("로그아웃되었습니다.", "info")
        return render_template("home.html")

    if current_user.is_authenticated:
        return redirect(url_for("auth.main"))
    return render_template("home.html")

@auth_bp.route("/check_username", methods=["POST"])
def check_username():
    """AJAX 아이디 중복 확인 엔드포인트"""
    data = request.get_json()
    username = data.get("username")

    if not username:
        return jsonify({"available": False, "message": "아이디를 입력해주세요."}), 400

    if User.query.filter_by(username=username).first():
        # 아이디가 이미 존재함
        return jsonify({"available": False, "message": "이미 존재하는 아이디입니다."})
    else:
        # 아이디 사용 가능
        return jsonify({"available": True, "message": "사용 가능한 아이디입니다."})

# 첫 로그인 페이지 (회원가입/로그인 선택 화면)
@auth_bp.route("/first_login_page")
def first_login_page():
    if current_user.is_authenticated:
        return redirect(url_for("auth.main"))
    return render_template("first_login_page.html")

# 프로필 완성 여부 체크 함수
def is_profile_complete(user):
    """사용자 프로필이 완성되었는지 확인하는 함수"""
    return all([
        user.gender,
        user.birth_date,
        user.sido,
        user.sigungu,
        user.dong,
        user.phone
    ])

# Google OAuth 로그인 후 콜백 처리
@auth_bp.route("/google_login_callback")
def google_login_callback():
    # 인증되지 않았으면 Google 로그인 페이지로 리다이렉트
    if not google.authorized:
        return redirect(url_for("google.login"))

    # 사용자 정보 요청
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return "Google login failed", 400

    # 사용자 정보 파싱
    info = resp.json()
    social_id = info["id"]
    email = info.get("email")
    name = info.get("name")

    # 기존 사용자인지 확인하고 없으면 새로 등록
    user = User.query.filter_by(social_type="google", social_id=social_id).first()
    if not user:
        user = User(
            name=name,
            nickname=name or email,
            social_type="google",
            social_id=social_id
        )
        db.session.add(user)
        db.session.commit()

    # 로그인 처리 후 프로필 완성 여부 확인
    login_user(user)
    # 관리자가 아닌 경우에만 프로필 완성 여부 확인
    if user.user_type != 2 and not is_profile_complete(user):
        return redirect(url_for("auth.onboarding"))
    return redirect(url_for("auth.main"))

# 카카오 OAuth 로그인 후 콜백 처리
@auth_bp.route("/kakao_login_callback")
def kakao_login_callback():
    # state 파라미터 검증 (CSRF 방지) - 임시로 완화
    state = request.args.get('state')
    session_state = session.get('oauth_state')
    print(f"Received state: {state}")
    print(f"Session state: {session_state}")


    code = request.args.get('code')
    if not code:
        return "Authorization code not found", 400

    # 액세스 토큰 요청
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': Config.KAKAO_CLIENT_ID,
        'client_secret': Config.KAKAO_CLIENT_SECRET,
        'redirect_uri': 'http://localhost:5002/kakao_login_callback',
        'code': code
    }

    token_response = requests.post('https://kauth.kakao.com/oauth/token', data=token_data)
    if not token_response.ok:
        return "Failed to get access token", 400

    token_info = token_response.json()
    access_token = token_info.get('access_token')

    # 사용자 정보 요청
    headers = {'Authorization': f'Bearer {access_token}'}
    user_response = requests.get('https://kapi.kakao.com/v2/user/me', headers=headers)
    if not user_response.ok:
        return "Failed to get user info", 400

    user_info = user_response.json()
    social_id = str(user_info['id'])
    nickname = user_info.get('properties', {}).get('nickname', 'Unknown')

    # 기존 사용자인지 확인하고 없으면 새로 등록
    user = User.query.filter_by(social_type="kakao", social_id=social_id).first()
    if not user:
        user = User(
            name=nickname,
            nickname=nickname,
            social_type="kakao",
            social_id=social_id
        )
        db.session.add(user)
        db.session.commit()

    session.pop('oauth_state', None)


    login_user(user)
    # 관리자가 아닌 경우에만 프로필 완성 여부 확인
    if user.user_type != 2 and not is_profile_complete(user):
        return redirect(url_for("auth.onboarding"))
    return redirect(url_for("auth.main"))

# 로그인 후 메인 홈화면
@auth_bp.route("/main")
@login_required
def main():
    # 관리자가 아닌 경우에만 프로필 완성 여부 체크
    if current_user.user_type != 2 and not is_profile_complete(current_user):
        return redirect(url_for("auth.onboarding"))

    # AI 추천 공고 가져오기 (일반 회원만)
    ai_recommended_jobs = []
    if current_user.user_type == 0:  # 일반 회원
        try:
            from services.recommendation_service import RecommendationService
            recommendations = RecommendationService.get_recommendations(
                user_id=current_user.id,
                limit=2  # 2개만
            )

            # 추천 공고에 지원 상태 추가
            for job, score, reasons in recommendations:
                application_status = ApplicationService.check_application_status(current_user.id, job.id)
                ai_recommended_jobs.append({
                    'job': job,
                    'score': round(score, 1),
                    'reasons': reasons,
                    'application_status': application_status
                })
        except Exception as e:
            print(f"AI 추천 오류: {e}")
            ai_recommended_jobs = []

    # 기업 회원 전용 데이터
    my_company_jobs_with_status = []
    public_resumes_with_status = []

    if current_user.user_type == 1:  # 기업 회원
        # 내가 올린 공고들 (최신순 2개)
        try:
            from models import JobPost
            my_jobs = JobPost.query.filter_by(author_id=current_user.id) \
                .order_by(JobPost.created_at.desc()) \
                .limit(2) \
                .all()

            for job in my_jobs:
                application_status = ApplicationService.check_application_status(current_user.id, job.id)
                my_company_jobs_with_status.append({
                    'job': job,
                    'application_status': application_status
                })
        except Exception as e:
            print(f"내 공고 가져오기 오류: {e}")
            my_company_jobs_with_status = []

        # 등록된 이력서들 (최신순 2개)
        try:
            from models import ResumeFavorite
            resumes_pagination = ResumeService.get_public_resumes_paginated(page=1, per_page=2)

            for resume in resumes_pagination.items:
                # 좋아요 상태 확인
                is_favorited = ResumeFavorite.query.filter_by(
                    user_id=current_user.id,
                    resume_id=resume.id
                ).first() is not None

                public_resumes_with_status.append({
                    'resume': resume,
                    'is_favorited': is_favorited
                })
        except Exception as e:
            print(f"공개 이력서 가져오기 오류: {e}")
            public_resumes_with_status = []

    # 기업 공고 데이터 가져오기 (최신순으로 최대 3개)
    try:
        jobs_pagination = JobService.get_all_jobs(page=1, per_page=10, sort_by='latest')
        # 기업 회원이 작성한 공고만 필터링
        company_jobs = [job for job in jobs_pagination.items if job.author.user_type == 1][:3]
        people_jobs = [job for job in jobs_pagination.items if job.author.user_type == 0][:3]

        # 각 공고에 대한 지원 상태 및 북마크 상태 확인
        company_jobs_with_status = []
        for job in company_jobs:
            # 모든 사용자에 대해 지원 상태와 북마크 상태 확인
            application_status = ApplicationService.check_application_status(current_user.id, job.id)

            job_data = {
                'job': job,
                'application_status': application_status
            }
            company_jobs_with_status.append(job_data)

        # 각 사람 이음 공고에 대한 지원 상태 및 북마크 상태 확인
        person_jobs_with_status = []
        for job in people_jobs:
            # 모든 사용자에 대해 지원 상태와 북마크 상태 확인
            application_status = ApplicationService.check_application_status(current_user.id, job.id)

            job_data = {
                'job': job,
                'application_status': application_status
            }
            person_jobs_with_status.append(job_data)

    except Exception as e:
        print(f"Error getting company jobs: {e}")
        company_jobs_with_status = []
        person_jobs_with_status = []

    # 뉴스 데이터 가져오기 (상위 3개)
    try:
        news_service = NaverNewsService()
        news_data = news_service.search_news(query='시니어 일자리', display=3, start=1, sort='date')
        news_list = news_data['items']
    except Exception as e:
        print(f"Error getting news: {e}")
        news_list = []

    return render_template("main.html", user=current_user, ai_recommended_jobs=ai_recommended_jobs,
                         company_jobs=company_jobs_with_status, people_jobs=person_jobs_with_status,
                         news_list=news_list, my_company_jobs=my_company_jobs_with_status,
                         public_resumes=public_resumes_with_status)

# 로그인한 사용자의 프로필 페이지
@auth_bp.route("/profile")
@login_required
def profile():
    # 프로필 이미지 URL 생성
    profile_url = None
    if current_user.profile_image:
        profile_url = generate_presigned_get_url(current_user.profile_image, expires=900)
        print(f"프로필 페이지 - 이미지 키: {current_user.profile_image}")  # 디버깅
        print(f"프로필 페이지 - 생성된 URL: {profile_url}")  # 디버깅
    else:
        print("프로필 페이지 - 프로필 이미지가 설정되지 않음")  # 디버깅
    
    # 기업 회원과 일반 회원 분리
    if current_user.user_type == 1:
        # 기업 회원 - 통계 데이터 조회
        
        # 내 구인글 수
        job_count = JobPost.query.filter_by(author_id=current_user.id).count()
        
        # 보낸 제안 수
        sent_suggestions_count = JobSuggestion.query.filter_by(suggester_id=current_user.id).count()
        
        # 받은 이력서 수 (내 공고에 지원한 사람들)
        my_job_ids = [job.id for job in JobPost.query.filter_by(author_id=current_user.id).all()]
        received_applications_count = JobApplication.query.filter(JobApplication.job_id.in_(my_job_ids)).count() if my_job_ids else 0
        
        return render_template("company/company_profile.html", 
                             user=current_user, 
                             profile_url=profile_url, 
                             job_count=job_count,
                             sent_suggestions_count=sent_suggestions_count,
                             received_applications_count=received_applications_count)
    else:
        # 일반 회원 - 이력서 수 조회
        resume_count = ResumeService.get_resume_count_by_user(current_user.id)

        my_apps = JobApplication.query.filter_by(user_id=current_user.id).all()
        jobs_dict = {}
        for app in my_apps:
            if app.job:  # 삭제된 공고는 제외
                jobs_dict[app.job_id] = app.job
        applications_count = len(jobs_dict)

        received_offers_count = JobSuggestion.query.filter_by(suggestee_id=current_user.id).count()

        return render_template("profile.html",
                               user=current_user,
                               profile_url=profile_url,
                               resume_count=resume_count,
                               applications=applications_count,
                               received_offers=received_offers_count
                               )

@auth_bp.route("/profile/detail")
@login_required
def profile_detail():
    # /profile/detail 경로에 접속하면 profile_detail.html을 렌더링
    return render_template("profile_detail.html", user=current_user)

# 온보딩 (추가 정보 입력) 페이지
@auth_bp.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    if request.method == "POST":
        # 사용자 정보 업데이트
        current_user.gender = request.form.get("gender")
        current_user.birth_date = request.form.get("birth_date") if request.form.get("birth_date") else None
        current_user.phone = request.form.get("phone")
        current_user.sido = request.form.get("sido")
        current_user.sigungu = request.form.get("sigungu")
        current_user.dong = request.form.get("dong")
        
        try:
            db.session.commit()
            return redirect(url_for("auth.main"))
        except Exception as e:
            db.session.rollback()
            flash("정보 저장 중 오류가 발생했습니다.", "error")
            print("Onboarding update failed:", e)
    
    kakao_key = current_app.config.get("KAKAO_MAP_API_KEY")
    return render_template("onboarding.html", user=current_user, kakao_key=kakao_key)

# 회원가입 라우트
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        nickname = request.form["nickname"]
        name = request.form.get("name")
        birth_date = request.form.get("birth_date")
        gender = request.form.get("gender")
        phone = request.form.get("phone")
        sido = request.form.get("sido")
        sigungu = request.form.get("sigungu")
        dong = request.form.get("dong")

        if password != confirm_password:
            flash("비밀번호가 일치하지 않습니다.")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(username=username).first():
            flash("이미 존재하는 사용자입니다.")
            return redirect(url_for("auth.register"))

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        user = User(
            username=username,
            password=hashed_pw.decode("utf-8"),
            nickname=nickname,
            name=name,
            birth_date=birth_date if birth_date else None,
            gender=gender,
            phone=phone,
            sido=sido,
            sigungu=sigungu,
            dong=dong,
            user_type=0,
            social_type=None,
            social_id=None
        )
        db.session.add(user)
        db.session.commit()

        # 자동 로그인
        login_user(user)

        # 회원가입 완료 후 메인으로 이동
        return redirect(url_for("auth.main"))

    kakao_key = current_app.config.get("KAKAO_MAP_API_KEY")
    return render_template("register.html", kakao_key=kakao_key)

    # ----------- 기업 회원가입 (관리자 승인 대기) ----------------->


@auth_bp.route("/register_company", methods=["GET", "POST"])
def register_company():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        nickname = request.form["nickname"]
        name = request.form.get("name")
        email = request.form.get("email")
        
        # 회사 주소 정보
        company_sido = request.form.get("company_sido")
        company_sigungu = request.form.get("company_sigungu")
        company_dong = request.form.get("company_dong")
        company_full_address = request.form.get("company_full_address")

        # 1. 비밀번호 확인
        if password != confirm_password:
            flash("비밀번호가 일치하지 않습니다.")
            return redirect(url_for("auth.register_company"))

        # 2. 아이디 중복 확인
        if User.query.filter_by(username=username).first():
            flash("이미 존재하는 사용자입니다.")
            return redirect(url_for("auth.register_company"))

        # 3. 파일 업로드 처리
        file = request.files.get("business_registration")

        if not file or file.filename == "":
            flash("사업자등록증 파일을 업로드해주세요.")
            return redirect(url_for("auth.register_company"))

        # S3에 파일 업로드 (resume_service.py에서 사용한 방식과 동일)
        # 'business_registrations' 라는 폴더(sub_path)에 저장됩니다.
        s3_url = upload_file(file=file, sub_path='business_registrations')  #

        # S3 업로드 실패 시 처리
        if not s3_url:
            flash("파일을 S3에 업로드하는 중 오류가 발생했습니다.")
            return redirect(url_for("auth.register_company"))

        # 4. 비밀번호 해시 처리
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # 5. User 객체 생성 및 DB 저장
        user = User(
            username=username,
            password=hashed_pw.decode("utf-8"),
            nickname=nickname,
            name=name,
            email=email,
            user_type=1,  # 기업회원
            is_verified=False,  # 승인 대기
            business_registration_file = s3_url,  # 업로드 파일명 저장
            business_registration_original = file.filename,
            company_sido=company_sido,
            company_sigungu=company_sigungu,
            company_dong=company_dong,
            company_full_address=company_full_address,
        )


        db.session.add(user)
        db.session.commit()

        return redirect(url_for("auth.home"))

    kakao_key = current_app.config.get("KAKAO_MAP_API_KEY")
    return render_template("register_company.html", kakao_key=kakao_key)


# 로그인 라우트
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        
        # 사용자가 없으면 로그인 실패
        if not user:
            flash("로그인 실패. 아이디 또는 비밀번호를 확인하세요.", "warning")
            return redirect(url_for("auth.login"))
        
        # 비밀번호 검증
        password_valid = False
        try:
            # bcrypt로 해시된 비밀번호 검증 시도
            password_valid = bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8"))
        except (ValueError, AttributeError):
            # bcrypt 형식이 아닌 경우 평문 비교 (레거시 데이터)
            password_valid = (user.password == password)
            
            # 평문 비밀번호를 bcrypt로 업데이트
            if password_valid:
                try:
                    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
                    user.password = hashed.decode("utf-8")
                    db.session.commit()
                    print(f"✅ 사용자 {username}의 비밀번호를 bcrypt로 업데이트했습니다.")
                except Exception as e:
                    print(f"⚠️ 비밀번호 업데이트 실패: {e}")
                    db.session.rollback()
        
        if not password_valid:
            flash("로그인 실패. 아이디 또는 비밀번호를 확인하세요.", "warning")
            return redirect(url_for("auth.login"))

        # 기업회원인 경우 승인 여부 검사
        if user.user_type == 1 and not user.is_verified:
            flash("기업회원 승인 대기 중입니다. 관리자의 승인이 필요합니다.", "warning")
            return redirect(url_for("auth.login"))

        login_user(user)

        # 관리자가 아닌 경우에만 프로필 완성 여부 확인
        if user.user_type != 2 and not is_profile_complete(user):
            flash("추가 정보를 입력해주세요.", "info")
            return redirect(url_for("auth.onboarding"))

        return redirect(url_for("auth.main"))

    return render_template("login.html")


@auth_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = current_user

    if request.method == 'POST':
        user.name = request.form.get('name')
        user.nickname = request.form.get('nickname')
        user.phone = request.form.get('phone')
        user.birth_date = request.form.get('birth_date')
        user.sido = request.form.get('sido')
        user.sigungu = request.form.get('sigungu')
        user.dong = request.form.get('dong')

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Profile update failed:", e)

        return redirect(url_for('auth.profile'))

    kakao_key = current_app.config.get("KAKAO_MAP_API_KEY")
    return render_template('edit_profile.html', user=user, kakao_key=kakao_key)


@auth_bp.route('/notice')
@login_required
def notice():
    """공지사항 페이지"""
    return render_template('notice.html')


@auth_bp.route('/inquiry')
@login_required
def inquiry():
    """문의 목록 페이지 (관리자는 전체 문의, 일반 사용자는 본인 문의만)"""
    # 관리자인 경우 관리자용 페이지로 리다이렉트
    if current_user.user_type == 2:
        return redirect(url_for('auth.admin_inquiry_list'))
    
    from models import Inquiry
    
    # 사용자의 문의 내역 조회 (최신순)
    inquiries = Inquiry.query.filter_by(user_id=current_user.id).order_by(Inquiry.created_at.desc()).all()
    
    return render_template('inquiry_list.html', inquiries=inquiries)


@auth_bp.route('/admin/inquiry')
@login_required
def admin_inquiry_list():
    """관리자 전용 문의 관리 페이지"""
    if current_user.user_type != 2:
        flash("관리자만 접근할 수 있습니다.", "error")
        return redirect(url_for('auth.profile'))
    
    from models import Inquiry
    
    # 전체 문의 내역 조회 (최신순)
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    
    # 통계 계산
    total_count = len(inquiries)
    pending_count = sum(1 for i in inquiries if i.status == 'pending')
    answered_count = sum(1 for i in inquiries if i.status == 'answered')
    
    return render_template('admin_inquiry_list.html', 
                         inquiries=inquiries,
                         total_count=total_count,
                         pending_count=pending_count,
                         answered_count=answered_count)


@auth_bp.route('/admin/inquiry/<int:inquiry_id>')
@login_required
def admin_inquiry_detail(inquiry_id):
    """관리자 전용 문의 상세 페이지"""
    if current_user.user_type != 2:
        flash("관리자만 접근할 수 있습니다.", "error")
        return redirect(url_for('auth.profile'))
    
    from models import Inquiry
    
    # 문의 상세 조회
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    
    return render_template('admin_inquiry_detail.html', inquiry=inquiry)


@auth_bp.route('/admin/inquiry/<int:inquiry_id>/answer', methods=['POST'])
@login_required
def admin_inquiry_answer(inquiry_id):
    """관리자 전용 문의 답변 등록"""
    if current_user.user_type != 2:
        flash("관리자만 접근할 수 있습니다.", "error")
        return redirect(url_for('auth.profile'))
    
    from models import Inquiry, db
    from datetime import datetime
    
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    answer = request.form.get('answer')
    
    try:
        inquiry.answer = answer
        inquiry.status = 'answered'
        inquiry.answered_at = datetime.now()
        inquiry.answered_by = current_user.id
        
        db.session.commit()
        flash('답변이 등록되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('답변 등록 중 오류가 발생했습니다.', 'error')
        print(f"Answer creation error: {e}")
    
    return redirect(url_for('auth.admin_inquiry_list'))


@auth_bp.route('/inquiry/form', methods=['GET', 'POST'])
@login_required
def inquiry_form():
    """문의 작성 페이지"""
    if request.method == 'POST':
        from models import Inquiry, db
        
        # 문의 생성
        inquiry = Inquiry(
            user_id=current_user.id,
            inquiry_type=request.form.get('inquiry_type'),
            title=request.form.get('title'),
            content=request.form.get('content'),
            contact=request.form.get('contact'),
            email=request.form.get('email'),
            privacy_consent='privacy_consent' in request.form,
            status='pending'
        )
        
        try:
            db.session.add(inquiry)
            db.session.commit()
            flash('문의가 접수되었습니다. 빠른 시일 내에 답변 드리겠습니다.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('문의 접수 중 오류가 발생했습니다.', 'error')
            print(f"Inquiry creation error: {e}")
        
        return redirect(url_for('auth.inquiry'))
    
    return render_template('inquiry_form.html', user=current_user)


@auth_bp.route('/edit_company_profile', methods=['GET', 'POST'])
@login_required
def edit_company_profile():
    """기업 회원 프로필 수정"""
    if current_user.user_type != 1:
        flash("기업 회원만 접근할 수 있습니다.", "error")
        return redirect(url_for('auth.profile'))
    
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.representative_name = request.form.get('representative_name')
        current_user.business_number = request.form.get('business_number')
        current_user.phone = request.form.get('phone')
        current_user.address = request.form.get('address')
        current_user.description = request.form.get('description')
        
        try:
            db.session.commit()
            flash("프로필이 수정되었습니다.", "success")
        except Exception as e:
            db.session.rollback()
            flash("프로필 수정 중 오류가 발생했습니다.", "error")
            print("Company profile update failed:", e)
        
        return redirect(url_for('auth.profile'))
    
    return render_template('company/edit_company_profile.html', user=current_user)


@auth_bp.route('/edit_profile_image', methods=['GET', 'POST'])
@login_required
def edit_profile_image():
    user = current_user

    if request.method == 'POST':
        file = request.files.get('profile_image')
        print(f"=== 프로필 이미지 업로드 시작 ===")
        print(f"파일 객체: {file}")
        print(f"파일 이름: {file.filename if file else None}")
        print(f"파일 타입: {file.content_type if file else None}")
        
        if file and file.filename:
            print(f"S3 업로드 시도 중...")
            url = upload_file(file, sub_path='profiles')  # URL 반환
            print(f"S3 업로드 결과 URL: {url}")
            
            if url:
                key = urlparse(url).path.lstrip('/')       # 키 추출
                print(f"추출된 S3 키: {key}")
                user.profile_image = key                   # 키 저장
                
                try:
                    db.session.commit()
                    print(f"✅ 프로필 이미지 업데이트 성공: {key}")
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ DB 저장 실패:", e)
            else:
                print("❌ S3 업로드 실패: upload_file()이 None을 반환함")
                print("AWS 설정 확인 필요:")
                print(f"  - AWS_ACCESS_KEY_ID 설정됨: {bool(current_app.config.get('AWS_ACCESS_KEY_ID'))}")
                print(f"  - AWS_SECRET_ACCESS_KEY 설정됨: {bool(current_app.config.get('AWS_SECRET_ACCESS_KEY'))}")
                print(f"  - AWS_S3_BUCKET_NAME: {current_app.config.get('AWS_S3_BUCKET_NAME')}")
                print(f"  - AWS_S3_REGION: {current_app.config.get('AWS_S3_REGION')}")
        else:
            print("❌ 파일이 선택되지 않음")

        return redirect(url_for('auth.profile'))

    profile_url = None
    if user.profile_image:
        profile_url = generate_presigned_get_url(user.profile_image, expires=900)
        print(f"현재 프로필 URL 생성: {profile_url}")  # 디버깅

    return render_template('edit_profile_image.html', user=user, profile_url=profile_url)


# 사용자 정보 업데이트 (이력서 작성 전)
@auth_bp.route("/update-user-info", methods=["POST"])
@login_required
def update_user_info():
    """이력서 작성 전 사용자 기본 정보를 업데이트"""
    from flask import jsonify
    from datetime import datetime
    
    try:
        data = request.get_json()
        user = current_user
        
        # 사용자 정보 업데이트
        if 'name' in data:
            user.name = data['name']
        if 'gender' in data:
            user.gender = data['gender']
        if 'birthdate' in data:
            try:
                user.birthdate = datetime.strptime(data['birthdate'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"success": False, "message": "잘못된 생년월일 형식입니다."}), 400
        if 'sido' in data:
            user.sido = data['sido']
        if 'sigungu' in data:
            user.sigungu = data['sigungu']
        if 'dong' in data:
            user.dong = data['dong']
        if 'detail_address' in data:
            user.detail_address = data['detail_address']
        
        db.session.commit()
        return jsonify({"success": True, "message": "정보가 업데이트되었습니다."})
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ 사용자 정보 업데이트 실패:", e)
        return jsonify({"success": False, "message": "정보 업데이트에 실패했습니다."}), 500


# 로그아웃 처리
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.home"))


# 회원탈퇴 처리
@auth_bp.route("/withdraw", methods=["POST"])
@login_required
def withdraw():
    """회원탈퇴 처리 - 사용자와 관련된 모든 데이터 삭제"""
    from flask import jsonify
    from models import JobPost, JobBookmark, JobApplication, ChatRoom, ChatMessage, Resume, Certificate, ResumeFavorite, JobSuggestion

    try:
        user_id = current_user.id

        # 1. 사용자가 작성한 공고 삭제
        JobPost.query.filter_by(author_id=user_id).delete()

        # 2. 사용자의 북마크 삭제
        JobBookmark.query.filter_by(user_id=user_id).delete()

        # 3. 사용자의 지원내역 삭제
        JobApplication.query.filter_by(user_id=user_id).delete()

        # 4. 사용자가 보내거나 받은 공고 제안 삭제
        JobSuggestion.query.filter(
            (JobSuggestion.suggester_id == user_id) |
            (JobSuggestion.suggestee_id == user_id)
        ).delete(synchronize_session=False)

        # 5. 사용자가 좋아요한 이력서 삭제
        ResumeFavorite.query.filter_by(user_id=user_id).delete()

        # 6. 사용자의 채팅 메시지 삭제
        chat_rooms = ChatRoom.query.filter(
            (ChatRoom.applicant_id == user_id) |
            (ChatRoom.employer_id == user_id)
        ).all()

        for room in chat_rooms:
            ChatMessage.query.filter_by(room_id=room.id).delete()

        # 7. 사용자의 채팅방 삭제
        ChatRoom.query.filter(
            (ChatRoom.applicant_id == user_id) |
            (ChatRoom.employer_id == user_id)
        ).delete(synchronize_session=False)

        # 8. 사용자의 이력서와 자격증 삭제 (cascade로 자동 삭제됨)
        Resume.query.filter_by(user_id=user_id).delete()

        # 9. 프로필 이미지가 있으면 S3에서 삭제 (선택사항)
        if current_user.profile_image:
            try:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=current_app.config.get('AWS_SECRET_ACCESS_KEY'),
                    region_name=current_app.config.get('AWS_S3_REGION')
                )
                bucket_name = current_app.config.get('AWS_S3_BUCKET_NAME')
                s3_client.delete_object(Bucket=bucket_name, Key=current_user.profile_image)
                print(f"✅ S3에서 프로필 이미지 삭제: {current_user.profile_image}")
            except Exception as e:
                print(f"⚠️ S3 프로필 이미지 삭제 실패: {e}")

        # 10. 사업자등록증 파일이 있으면 S3에서 삭제 (기업 회원)
        if current_user.business_registration_file:
            try:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=current_app.config.get('AWS_SECRET_ACCESS_KEY'),
                    region_name=current_app.config.get('AWS_S3_REGION')
                )
                bucket_name = current_app.config.get('AWS_S3_BUCKET_NAME')
                # S3 URL에서 키 추출
                from urllib.parse import urlparse
                parsed_url = urlparse(current_user.business_registration_file)
                key = parsed_url.path.lstrip('/')
                s3_client.delete_object(Bucket=bucket_name, Key=key)
                print(f"✅ S3에서 사업자등록증 삭제: {key}")
            except Exception as e:
                print(f"⚠️ S3 사업자등록증 삭제 실패: {e}")

        # 11. 로그아웃 처리 (User 삭제 전에 해야 함)
        logout_user()

        # 12. 마지막으로 사용자 삭제
        User.query.filter_by(id=user_id).delete()

        # 모든 변경사항 커밋
        db.session.commit()

        print(f"✅ 회원탈퇴 완료: user_id={user_id}")
        return jsonify({"success": True, "message": "회원탈퇴가 완료되었습니다."})

    except Exception as e:
        db.session.rollback()
        print(f"❌ 회원탈퇴 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": "회원탈퇴 처리 중 오류가 발생했습니다."}), 500
