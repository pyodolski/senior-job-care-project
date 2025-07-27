"""
소셜 로그인 공통 로직 헬퍼
"""
import logging
from flask import redirect, url_for
from flask_login import login_user
from typing import Optional, Dict, Any, Tuple
from models import db, User
from services.onboarding import OnboardingService
from services.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class SocialLoginHelper:
    """소셜 로그인 공통 로직을 처리하는 헬퍼 클래스"""
    
    @staticmethod
    def process_social_login(social_type: str, social_id: str, basic_info: Optional[Dict[str, Any]] = None):
        """
        소셜 로그인 공통 처리 로직
        
        Args:
            social_type: 소셜 로그인 타입 ('google', 'naver', 'kakao')
            social_id: 소셜 계정 ID
            basic_info: 기본 정보 (name, email 등)
            
        Returns:
            Flask redirect response
        """
        if basic_info is None:
            basic_info = {}
            
        # 기존 사용자인지 확인
        logger.info(f"Checking for existing {social_type} user with social_id: {social_id}")
        existing_user = User.query.filter_by(social_type=social_type, social_id=social_id).first()
        logger.info(f"Existing user found: {existing_user.id if existing_user else 'None'}")
        
        if existing_user:
            # 기존 사용자 처리
            return SocialLoginHelper._handle_existing_user(existing_user, basic_info)
        else:
            # 신규 사용자 처리
            return SocialLoginHelper._handle_new_user(social_type, social_id, basic_info)
    
    @staticmethod
    def _handle_existing_user(existing_user: User, basic_info: dict):
        """기존 사용자 처리"""
        logger.info(f"Existing {existing_user.social_type} user login: {existing_user.id}")
        
        try:
            # 소셜 계정 정보 업데이트 (변경된 경우)
            updated = False
            if basic_info.get('name') and existing_user.name != basic_info['name']:
                existing_user.name = basic_info['name']
                updated = True
            
            if updated:
                db.session.commit()
                logger.info(f"Updated user {existing_user.id} with new info")
            
            # 로그인 처리
            login_user(existing_user)
            
            # 온보딩 상태에 따른 리다이렉트
            return SocialLoginHelper._redirect_based_on_onboarding_status(existing_user)
            
        except Exception as e:
            db.session.rollback()
            raise DatabaseError(f"기존 사용자 정보 업데이트 실패: {str(e)}", "update", "user")
    
    @staticmethod
    def _handle_new_user(social_type: str, social_id: str, basic_info: dict):
        """신규 사용자 처리"""
        logger.info(f"New {social_type} user registration: {social_id}")
        
        try:
            # 임시 사용자 생성
            new_user = OnboardingService.create_temp_user(
                social_type=social_type,
                social_id=social_id,
                basic_info=basic_info
            )
            
            # 로그인 처리
            login_user(new_user)
            
            # 온보딩 페이지로 리다이렉트
            return redirect(url_for("onboarding.onboarding"))
            
        except Exception as e:
            db.session.rollback()
            raise DatabaseError(f"신규 사용자 생성 실패: {str(e)}", "create", "user")
    
    @staticmethod
    def _redirect_based_on_onboarding_status(user: User):
        """온보딩 상태에 따른 리다이렉트 결정"""
        if user.onboarding_status == 'completed':
            # 완료된 사용자는 로그인 완료 페이지로
            logger.info(f"User {user.id} has completed onboarding, redirecting to login_complete")
            return redirect(url_for("user_session.login_complete"))
        else:
            # 미완료 사용자는 온보딩 데이터가 있으면 재개 페이지로, 없으면 기본 온보딩으로
            if user.onboarding_data and user.onboarding_step > 0:
                logger.info(f"User {user.id} has partial onboarding data, redirecting to resume")
                return redirect(url_for("onboarding.resume_onboarding"))
            else:
                logger.info(f"User {user.id} needs to start onboarding, redirecting to onboarding")
                return redirect(url_for("onboarding.onboarding"))
    
    @staticmethod
    def extract_google_user_info(google_response):
        """Google OAuth 응답에서 사용자 정보 추출"""
        info = google_response.json()
        social_id = info.get("id")
        
        if not social_id:
            return None, None
        
        # 기본 정보 구성 (제한적 수집)
        basic_info = {}
        if info.get("name"):
            basic_info['name'] = info["name"]
        if info.get("email"):
            basic_info['email'] = info["email"]
            
        return social_id, basic_info
    
    @staticmethod
    def extract_naver_user_info(user_info):
        """Naver OAuth 응답에서 사용자 정보 추출"""
        profile = user_info.get('response', {})
        social_id = str(profile.get('id'))
        
        if not social_id:
            return None, None
        
        # 기본 정보 구성 (제한적 수집)
        basic_info = {}
        if profile.get('name'):
            basic_info['name'] = profile['name']
            
        return social_id, basic_info
    
    @staticmethod
    def extract_kakao_user_info(user_info):
        """Kakao OAuth 응답에서 사용자 정보 추출"""
        social_id = str(user_info['id'])
        
        # 기본 정보 구성 (제한적 수집)
        basic_info = {}
        properties = user_info.get('properties', {})
        if properties.get('nickname'):
            basic_info['name'] = properties['nickname']
            
        return social_id, basic_info 