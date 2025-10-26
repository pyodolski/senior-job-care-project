from flask import Blueprint, render_template, redirect, url_for, request, session
from flask_login import login_required, login_user, logout_user, current_user
from flask_dance.contrib.google import google
from models import db, User
import requests
from config import Config
import os
from flask import current_app, flash
from werkzeug.utils import secure_filename #필요 없을지도모름 ?
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
    if not is_profile_complete(user):
        flash("추가 정보를 입력해주세요.", "info")
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

    # 임시로 state 검증을 건너뛰고 진행
    # if not state or state != session.get('oauth_state'):
    #     return "Invalid state parameter", 400

    # 인증 코드 확인
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

    # 세션에서 state 제거
    session.pop('oauth_state', None)

    # 로그인 처리 후 프로필 완성 여부 확인
    login_user(user)
    if not is_profile_complete(user):
        flash("추가 정보를 입력해주세요.", "info")
        return redirect(url_for("auth.onboarding"))
    return redirect(url_for("auth.main"))

# 로그인 후 메인 홈화면
@auth_bp.route("/main")
@login_required
def main():
    # 프로필 완성 여부 체크
    if not is_profile_complete(current_user):
        flash("프로필 정보를 완성해주세요.", "warning")
        return redirect(url_for("auth.onboarding"))

    # 기업 공고 데이터 가져오기 (최신순으로 최대 3개)
    try:
        jobs_pagination = JobService.get_all_jobs(page=1, per_page=10, sort_by='latest')
        # 기업 회원이 작성한 공고만 필터링
        company_jobs = [job for job in jobs_pagination.items if job.author.user_type == 1][:3]
        people_jobs = [job for job in jobs_pagination.items if job.author.user_type == 0][:3]
        
        # 각 공고에 대한 지원 상태 확인
        company_jobs_with_status = []
        for job in company_jobs:
            if current_user.user_type == 0:  # 일반 사용자인 경우만 지원 상태 확인
                application_status = ApplicationService.check_application_status(current_user.id, job.id)
            else:
                application_status = {'applied': False, 'status': None}
            
            job_data = {
                'job': job,
                'application_status': application_status
            }
            company_jobs_with_status.append(job_data)

        # 각 사람 이음 공고에 대한 지원 상태 확인
        person_jobs_with_status = []
        for job in people_jobs:
            if current_user.user_type == 0 and current_user.id == job.author.id:  # 일반 사용자인 경우만 지원 상태 확인
                application_status = ApplicationService.check_application_status(current_user.id, job.id)
            else:
                application_status = {'applied': False, 'status': None}
            
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

    return render_template("main.html", user=current_user, company_jobs=company_jobs_with_status, people_jobs=person_jobs_with_status, news_list=news_list)

# 로그인한 사용자의 프로필 페이지
@auth_bp.route("/profile")
@login_required
def profile():
    resume_count = ResumeService.get_resume_count_by_user(current_user.id)

    # /profile 경로에 접속하면 profile.html을 렌더링
    profile_url = None
    if current_user.profile_image:
        profile_url = generate_presigned_get_url(current_user.profile_image, expires=900)
        print(f"프로필 페이지 - 이미지 키: {current_user.profile_image}")  # 디버깅
        print(f"프로필 페이지 - 생성된 URL: {profile_url}")  # 디버깅
    else:
        print("프로필 페이지 - 프로필 이미지가 설정되지 않음")  # 디버깅
    
    return render_template("profile.html", user=current_user, profile_url=profile_url, resume_count=resume_count)

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
            flash("프로필 정보가 완성되었습니다!", "success")
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
        flash("회원가입이 완료되었습니다!", "success")
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

        # 허용 확장자 검사 함수
        def allowed_file(filename):
            return '.' in filename and \
                filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

        filename = None
        if file and file.filename != "" and allowed_file(file.filename):
            original_filename = file.filename  # 원본 파일명 확보
            ext = original_filename.rsplit('.', 1)[1].lower()  # 확장자 분리

            # 🔸 파일명 충돌 완전 방지: UUID.확장자 로 저장
            unique_filename = f"{uuid.uuid4().hex}.{ext}"

            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            file.save(upload_path)
        else:
            flash("사업자등록증 파일을 업로드해주세요. (허용 확장자: png, jpg, jpeg, pdf)")
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
            business_registration_file = unique_filename,  # 업로드 파일명 저장
            business_registration_original = original_filename,
        )


        db.session.add(user)
        db.session.commit()

        flash("기업 회원가입 신청이 완료되었습니다. 관리자의 승인을 기다려 주세요.")
        return redirect(url_for("auth.home"))

    return render_template("register_company.html")


# 로그인 라우트
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if not user or not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            flash("로그인 실패. 아이디 또는 비밀번호를 확인하세요.", "warning")
            return redirect(url_for("auth.login"))

        # 기업회원인 경우 승인 여부 검사
        if user.user_type == 1 and not user.is_verified:
            flash("기업회원 승인 대기 중입니다. 관리자의 승인이 필요합니다.", "warning")
            return redirect(url_for("auth.login"))

        login_user(user)
        
        # 프로필 완성 여부 확인
        if not is_profile_complete(user):
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


# 로그아웃 처리
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.home"))
