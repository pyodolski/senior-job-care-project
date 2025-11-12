# routes/google_oauth.py
import os
from flask_dance.contrib.google import make_google_blueprint, google
from flask import redirect, url_for
from flask_login import login_user
from models import db, User
from config import Config

# Google OAuth 블루프린트
google_bp = make_google_blueprint(
    client_id=Config.GOOGLE_CLIENT_ID,
    client_secret=Config.GOOGLE_CLIENT_SECRET,
    scope=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ],
    redirect_to="auth.google_login_callback"  # auth.py의 콜백 라우트
)
