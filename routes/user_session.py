from flask import Blueprint, render_template, redirect, url_for, session, flash, jsonify
from flask_login import login_required, logout_user, current_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 사용자 세션 관리 관련 라우트를 담당하는 블루프린트 생성
user_session_bp = Blueprint("user_session", __name__)

# 로그인 완료 페이지
@user_session_bp.route("/login-complete")
@login_required
def login_complete():
    """로그인 완료 페이지"""
    try:
        # 사용자 정보 로깅
        logger.info(f"User {current_user.id} accessed login complete page")
        
        # 소셜 로그인 사용자만 온보딩 상태 체크 (일반 로그인 사용자는 체크하지 않음)
        if current_user.social_type and current_user.onboarding_status != 'completed':
            logger.warning(f"User {current_user.id} tried to access login complete page without completing onboarding")
            flash("먼저 회원가입을 완료해주세요.")
            return redirect(url_for("onboarding.onboarding"))
        
        # 소셜 로그인 사용자만 프로필 완성도 체크 (일반 로그인 사용자는 체크하지 않음)
        if current_user.social_type and not current_user.is_profile_complete:
            logger.warning(f"User {current_user.id} has incomplete profile information")
            flash("프로필 정보가 불완전합니다. 추가 정보를 입력해주세요.")
        
        # 템플릿에 전달할 데이터 준비
        template_data = {
            'user': current_user,
            'login_time': datetime.now(),
            'social_type_display': {
                'google': 'Google',
                'naver': '네이버',
                'kakao': '카카오'
            }.get(current_user.social_type, current_user.social_type.title() if current_user.social_type else '일반 로그인')
        }
        
        # 성공 메시지 설정
        welcome_name = current_user.nickname or current_user.name or "사용자"
        flash(f"환영합니다, {welcome_name}님! 성공적으로 로그인되었습니다.", "success")
        
        logger.info(f"Successfully rendered login complete page for user {current_user.id}")
        return render_template("success/login_complete.html", **template_data)
        
    except Exception as e:
        logger.error(f"Error in login_complete route: {str(e)}")
        flash("페이지를 불러오는 중 오류가 발생했습니다. 다시 시도해주세요.", "error")
        return redirect(url_for("auth.home"))

# 로그아웃 라우트
@user_session_bp.route("/logout")
@login_required
def logout():
    """사용자 로그아웃"""
    try:
        # 로그아웃 전 사용자 정보 로깅
        user_id = current_user.id
        user_name = current_user.nickname or current_user.name or "Unknown"
        logger.info(f"User {user_id} ({user_name}) is logging out")
        
        # Flask-Login 로그아웃 처리
        logout_user()
        
        # 세션 정리
        session.clear()
        
        # 성공 메시지
        flash("성공적으로 로그아웃되었습니다.", "success")
        logger.info(f"User {user_id} successfully logged out")
        
        return redirect(url_for("auth.home"))
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        flash("로그아웃 중 오류가 발생했습니다.", "error")
        return redirect(url_for("auth.home"))

# 사용자 지역 정보 조회 API
@user_session_bp.route("/api/user/region", methods=["GET"])
@login_required
def get_user_region():
    """현재 로그인한 사용자의 지역 정보 조회 API"""
    try:
        # 사용자 인증 확인
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'error': '로그인이 필요합니다.',
                'error_code': 'AUTH_REQUIRED'
            }), 401
        
        # 지역 정보 확인
        if not all([current_user.sido, current_user.sigungu, current_user.dong]):
            return jsonify({
                'success': False,
                'error': '지역 정보가 설정되지 않았습니다.',
                'error_code': 'REGION_NOT_SET',
                'missing_fields': {
                    'sido': not bool(current_user.sido),
                    'sigungu': not bool(current_user.sigungu),
                    'dong': not bool(current_user.dong)
                }
            }), 404
        
        # 성공적인 응답
        logger.info(f"Region info requested for user {current_user.id}: {current_user.dong}")
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': current_user.id,
                'sido': current_user.sido,
                'sigungu': current_user.sigungu,
                'dong': current_user.dong,
                'full_address': f"{current_user.sido} {current_user.sigungu} {current_user.dong}",
                'display_name': current_user.dong  # 동 이름만 표시용
            },
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_user_region API for user {current_user.id if current_user.is_authenticated else 'anonymous'}: {str(e)}")
        return jsonify({
            'success': False,
            'error': '서버 오류가 발생했습니다.',
            'error_code': 'INTERNAL_ERROR'
        }), 500