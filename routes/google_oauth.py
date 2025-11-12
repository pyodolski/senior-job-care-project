# routes/google_oauth.py
import os
from flask_dance.contrib.google import make_google_blueprint, google
from flask import redirect, url_for, flash
from flask_login import login_user
from models import db, User
from config import Config

# Railway 환경에서는 HTTPS 사용
redirect_url = None
if Config.IS_RAILWAY:
    # Railway 배포 환경 - Flask-Dance 기본 경로 사용
    redirect_url = "https://senior-job-care-project-production.up.railway.app/login/google/authorized"
    print(f"🔒 Railway OAuth 리디렉션: {redirect_url}")

# Google OAuth 블루프린트
google_bp = make_google_blueprint(
    client_id=Config.GOOGLE_CLIENT_ID,
    client_secret=Config.GOOGLE_CLIENT_SECRET,
    scope=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ],
    redirect_url=redirect_url,  # Railway에서는 명시적 URL 사용
    redirect_to="auth.main"  # 로그인 후 메인으로 직접 이동
)

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

# Flask-Dance authorized 시그널 핸들러
from flask_dance.consumer import oauth_authorized
from flask import Blueprint

@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    """Google OAuth 인증 완료 후 자동 호출되는 핸들러"""
    if not token:
        flash("Google 로그인에 실패했습니다.", "error")
        return False

    # 사용자 정보 요청
    resp = blueprint.session.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Google 사용자 정보를 가져올 수 없습니다.", "error")
        return False

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

    # 로그인 처리
    login_user(user)
    
    # 프로필 완성 여부 확인하여 리다이렉트
    if user.user_type != 2 and not is_profile_complete(user):
        flash("추가 정보를 입력해주세요.", "info")
        return redirect(url_for("auth.onboarding"))
    
    # 토큰을 저장하지 않음 (보안상 이유)
    return False
