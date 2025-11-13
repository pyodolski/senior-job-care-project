# routes/kakao_oauth.py
import requests
from flask import Blueprint, redirect, request, url_for, session
from config import Config
import secrets

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

    # 환경에 따라 동적으로 Redirect URI 생성
    redirect_uri = url_for('kakao_login_callback', _external=True, _scheme='https' if Config.IS_RAILWAY else 'http')
    
    # 카카오 인증 URL 생성
    auth_url = f"{KAKAO_AUTH_URL}?" \
               f"client_id={Config.KAKAO_CLIENT_ID}&" \
               f"redirect_uri={redirect_uri}&" \
               f"response_type=code&" \
               f"state={state}"

    return redirect(auth_url)


@kakao_bp.route("/kakao_login_callback")
def kakao_login_callback():
    """카카오 로그인 콜백 - 인증 코드를 받아서 토큰 교환"""
    from models import db, User
    from flask_login import login_user
    
    # State 검증
    state = request.args.get('state')
    if state != session.get('oauth_state'):
        return "Invalid state parameter", 400
    
    # 인증 코드 받기
    code = request.args.get('code')
    if not code:
        error = request.args.get('error')
        error_description = request.args.get('error_description')
        return f"카카오 로그인 실패: {error} - {error_description}", 400
    
    # 환경에 따라 동적으로 Redirect URI 생성
    redirect_uri = url_for('kakao.kakao_login_callback', _external=True, _scheme='https' if Config.IS_RAILWAY else 'http')
    
    # 액세스 토큰 요청
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': Config.KAKAO_CLIENT_ID,
        'client_secret': Config.KAKAO_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'code': code
    }
    
    token_response = requests.post(KAKAO_TOKEN_URL, data=token_data)
    token_json = token_response.json()
    
    if 'error' in token_json:
        return f"토큰 요청 실패: {token_json.get('error_description')}", 400
    
    access_token = token_json.get('access_token')
    
    # 사용자 정보 요청
    user_info_url = "https://kapi.kakao.com/v2/user/me"
    headers = {'Authorization': f'Bearer {access_token}'}
    user_response = requests.get(user_info_url, headers=headers)
    user_info = user_response.json()
    
    if 'id' not in user_info:
        return "사용자 정보 조회 실패", 400
    
    # 카카오 사용자 정보 추출
    kakao_id = str(user_info['id'])
    kakao_account = user_info.get('kakao_account', {})
    profile = kakao_account.get('profile', {})
    
    email = kakao_account.get('email')
    nickname = profile.get('nickname', '카카오 사용자')
    profile_image = profile.get('profile_image_url')
    
    # 기존 사용자 확인 또는 새 사용자 생성
    user = User.query.filter_by(kakao_id=kakao_id).first()
    
    if not user:
        # 이메일로도 확인 (이미 다른 방법으로 가입한 경우)
        if email:
            user = User.query.filter_by(email=email).first()
            if user:
                # 기존 계정에 카카오 ID 연결
                user.kakao_id = kakao_id
            else:
                # 새 사용자 생성
                user = User(
                    email=email,
                    username=nickname,
                    kakao_id=kakao_id,
                    profile_image=profile_image
                )
                db.session.add(user)
        else:
            # 이메일 없이 카카오 ID만으로 생성
            user = User(
                username=nickname,
                kakao_id=kakao_id,
                profile_image=profile_image
            )
            db.session.add(user)
        
        db.session.commit()
    
    # 로그인 처리
    login_user(user)
    session.pop('oauth_state', None)
    
    return redirect(url_for('auth.main'))
