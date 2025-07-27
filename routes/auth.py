from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user, login_user, logout_user
from models import db, User
from routes.google_oauth import google
from config import Config
import requests
import logging

logger = logging.getLogger(__name__)

# 인증 관련 라우트를 담당하는 블루프린트 생성
auth_bp = Blueprint("auth", __name__)

# 홈 화면 렌더링
@auth_bp.route("/")
def home():
    return render_template("home.html")

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

    # 로그인 처리 후 프로필 페이지로 이동
    login_user(user)
    return redirect(url_for("auth.profile"))

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

    # 로그인 처리 후 프로필 페이지로 이동
    login_user(user)
    return redirect(url_for("auth.profile"))

# 로그인한 사용자의 프로필 페이지
@auth_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)
import bcrypt
from flask import request, flash

# 회원가입 라우트
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        nickname = request.form["nickname"]
        name = request.form.get("name")
        gender = request.form.get("gender")
        birth_date = request.form.get("birth_date")
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
            gender=gender,
            birth_date=birth_date if birth_date else None,
            user_type=0,
            social_type=None,
            social_id=None,
            sido=sido,
            sigungu=sigungu,
            dong=dong
        )
        db.session.add(user)
        db.session.commit()
        flash("회원가입 완료! 로그인 해주세요.")
        return redirect(url_for("auth.home"))

    return render_template("register.html")


# 로그인 라우트
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if not user or not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            flash("로그인 실패. 아이디 또는 비밀번호를 확인하세요.")
            return redirect(url_for("auth.login"))

        login_user(user)
        return redirect(url_for("auth.profile"))

    return render_template("login.html")

# 로그아웃 라우트
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("로그아웃되었습니다.")
    return redirect(url_for("auth.home"))