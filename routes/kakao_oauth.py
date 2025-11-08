# routes/kakao_oauth.py
import os
import requests
from flask import Blueprint, redirect, request, url_for, session
from config import Config
import secrets

# OAuth insecure transport 허용 (개발 환경용)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# 카카오 OAuth 블루프린트
kakao_bp = Blueprint("kakao", __name__)

# 카카오 OAuth URL
KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"


@kakao_bp.route("/login")
def login():
    """카카오 로그인 시작 - 카카오 인증 서버로 리다이렉트"""
    # CSRF 방지를 위한 state 생성
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state

    # 카카오 인증 URL 생성
    redirect_uri = "https://senior-job-care-project-production.up.railway.app/kakao_login_callback"
    auth_url = f"{KAKAO_AUTH_URL}?" \
               f"client_id={Config.KAKAO_CLIENT_ID}&" \
               f"redirect_uri={redirect_uri}&" \
               f"response_type=code&" \
               f"state={state}"

    return redirect(auth_url)