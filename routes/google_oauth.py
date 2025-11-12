# routes/google_oauth.py
import os
from flask_dance.contrib.google import make_google_blueprint, google
from flask import redirect, url_for
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
    redirect_to="auth.google_login_callback"  # auth.py의 콜백 라우트
)
