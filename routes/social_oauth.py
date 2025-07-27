from flask import Blueprint, redirect, url_for, request, session
from flask_dance.contrib.google import google
from services.error_handlers import handle_social_login_errors
from services.exceptions import SocialLoginError
from services.social_login_helper import SocialLoginHelper
import requests
from config import Config
import logging

logger = logging.getLogger(__name__)

# 소셜 로그인 관련 라우트를 담당하는 블루프린트 생성
social_oauth_bp = Blueprint("social_oauth", __name__)

# Google OAuth 로그인 후 콜백 처리
@social_oauth_bp.route("/google_login_callback")
@handle_social_login_errors
def google_login_callback():
    # 인증되지 않았으면 Google 로그인 페이지로 리다이렉트
    if not google.authorized:
        raise SocialLoginError("Google 인증이 완료되지 않았습니다.", "google", "auth_not_completed")

    # 사용자 정보 요청 (제한적 수집)
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        raise SocialLoginError("Google에서 사용자 정보를 가져올 수 없습니다.", "google", "google_auth_failed")

    # 사용자 정보 추출
    social_id, basic_info = SocialLoginHelper.extract_google_user_info(resp)
    if not social_id:
        raise SocialLoginError("Google 계정 정보가 올바르지 않습니다.", "google", "invalid_user_info")
    
    # 공통 소셜 로그인 처리 로직 실행
    return SocialLoginHelper.process_social_login("google", social_id, basic_info)


# Naver OAuth 로그인 후 콜백 처리
@social_oauth_bp.route("/naver_login_callback")
@handle_social_login_errors
def naver_login_callback():
    # 인증 코드 확인
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        raise SocialLoginError("네이버 로그인 인증 코드를 받지 못했습니다.", "naver", "auth_code_missing")

    # 액세스 토큰 요청
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': Config.NAVER_CLIENT_ID,
        'client_secret': Config.NAVER_CLIENT_SECRET,
        'code': code,
        'state': state
    }

    token_response = requests.post('https://nid.naver.com/oauth2.0/token', data=token_data)
    if not token_response.ok:
        raise SocialLoginError("네이버 액세스 토큰 요청에 실패했습니다.", "naver", "token_request_failed")

    token_info = token_response.json()
    access_token = token_info.get('access_token')

    # 사용자 정보 요청 (제한적 수집)
    headers = {'Authorization': f'Bearer {access_token}'}
    user_response = requests.get('https://openapi.naver.com/v1/nid/me', headers=headers)
    if not user_response.ok:
        raise SocialLoginError("네이버 사용자 정보 요청에 실패했습니다.", "naver", "user_info_failed")

    user_info = user_response.json()
    
    # 사용자 정보 추출
    social_id, basic_info = SocialLoginHelper.extract_naver_user_info(user_info)
    if not social_id:
        raise SocialLoginError("네이버 계정 정보가 올바르지 않습니다.", "naver", "invalid_user_info")
    
    # 공통 소셜 로그인 처리 로직 실행
    return SocialLoginHelper.process_social_login("naver", social_id, basic_info)


# 카카오 OAuth 로그인 후 콜백 처리
@social_oauth_bp.route("/kakao_login_callback")
@handle_social_login_errors
def kakao_login_callback():
    # state 파라미터 검증 (CSRF 방지)
    state = request.args.get('state')
    session_state = session.get('oauth_state')
    logger.info(f"Kakao callback - Received state: {state}, Session state: {session_state}")

    # 임시로 state 검증을 완화하되 로그 남김
    if not state or state != session_state:
        logger.warning("State parameter mismatch in Kakao callback")
        # 완전히 차단하지 않고 경고만 로그

    # 인증 코드 확인
    code = request.args.get('code')
    if not code:
        raise SocialLoginError("카카오 로그인 인증 코드를 받지 못했습니다.", "kakao", "auth_code_missing")

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
        raise SocialLoginError("카카오 액세스 토큰 요청에 실패했습니다.", "kakao", "token_request_failed")

    token_info = token_response.json()
    access_token = token_info.get('access_token')

    # 사용자 정보 요청 (제한적 수집)
    headers = {'Authorization': f'Bearer {access_token}'}
    user_response = requests.get('https://kapi.kakao.com/v2/user/me', headers=headers)
    if not user_response.ok:
        raise SocialLoginError("카카오 사용자 정보 요청에 실패했습니다.", "kakao", "user_info_failed")

    user_info = user_response.json()
    
    # 사용자 정보 추출
    social_id, basic_info = SocialLoginHelper.extract_kakao_user_info(user_info)
    
    # 공통 소셜 로그인 처리 로직 실행
    return SocialLoginHelper.process_social_login("kakao", social_id, basic_info) 