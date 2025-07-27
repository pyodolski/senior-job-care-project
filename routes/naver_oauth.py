# routes/naver_oauth.py
import os
import requests
from flask import Blueprint, redirect, url_for, request, session
from flask_login import login_user
from models import db, User
from config import Config

naver_bp = Blueprint("naver", __name__)

NAVER_CLIENT_ID = Config.NAVER_CLIENT_ID
NAVER_CLIENT_SECRET = Config.NAVER_CLIENT_SECRET
NAVER_REDIRECT_URI = Config.NAVER_REDIRECT_URI

# 네이버 로그인 시작
@naver_bp.route("/naver_login")
def naver_login():
    state = os.urandom(16).hex()
    session["naver_auth_state"] = state
    auth_url = (
        f"https://nid.naver.com/oauth2.0/authorize"
        f"?response_type=code"
        f"&client_id={NAVER_CLIENT_ID}"
        f"&redirect_uri={NAVER_REDIRECT_URI}"
        f"&state={state}"
    )
    return redirect(auth_url)

# 네이버 로그인 콜백 - auth.py의 통합 콜백으로 리다이렉트
@naver_bp.route("/naver_login_callback")
def naver_login_callback():
    # auth.py의 네이버 콜백 함수로 리다이렉트
    return redirect(url_for("social_oauth.naver_login_callback", **request.args))# routes/naver_oauth.py
