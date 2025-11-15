# routes/naver_oauth.py
import os
import requests
from flask import Blueprint, redirect, url_for, request, session, flash
from flask_login import login_user
from models import db, User
from config import Config

naver_bp = Blueprint("naver", __name__)

NAVER_CLIENT_ID = Config.NAVER_CLIENT_ID
NAVER_CLIENT_SECRET = Config.NAVER_CLIENT_SECRET
NAVER_REDIRECT_URI = Config.NAVER_REDIRECT_URI

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

# 네이버 로그인 콜백
@naver_bp.route("/naver_login_callback")
def naver_login_callback():
    code = request.args.get("code")
    state = request.args.get("state")
    if not state or state != session.get("naver_auth_state"):
        return "잘못된 접근입니다.", 400

    # 토큰 요청
    token_res = requests.get(
        "https://nid.naver.com/oauth2.0/token",
        params={
            "grant_type": "authorization_code",
            "client_id": NAVER_CLIENT_ID,
            "client_secret": NAVER_CLIENT_SECRET,
            "code": code,
            "state": state,
        }
    )
    token_json = token_res.json()
    access_token = token_json.get("access_token")
    if not access_token:
        return "네이버 로그인 실패(토큰 없음)", 400

    # 프로필 요청
    profile_res = requests.get(
        "https://openapi.naver.com/v1/nid/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if not profile_res.ok:
        return "네이버 프로필 정보 요청 실패", 400
    profile = profile_res.json().get("response", {})

    social_id = profile.get("id")
    name = profile.get("name")
    nickname = profile.get("nickname") or name
    gender = profile.get("gender")
    birthyear = profile.get("birthyear")
    birthday = profile.get("birthday")
    birth_date = None
    if birthyear and birthday:
        birth_date = f"{birthyear}-{birthday}"

    user = User.query.filter_by(social_type="naver", social_id=social_id).first()
    if not user:
        user = User(
            name=name,
            nickname=nickname,
            gender=gender,
            birth_date=birth_date,
            username=None,
            password=None,
            user_type=0,
            social_type="naver",
            social_id=social_id
        )
        db.session.add(user)
        db.session.commit()
    login_user(user)
    
    # 프로필 완성 여부 확인
    if not is_profile_complete(user):
        flash("추가 정보를 입력해주세요.", "info")
        return redirect(url_for("auth.onboarding"))
    
    return redirect(url_for("auth.main"))
