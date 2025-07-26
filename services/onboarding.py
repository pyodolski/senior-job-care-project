import json
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional

from models import db, User
from .validation import validate_required_info, validate_step_data, validate_complete_profile, sanitize_data
from .exceptions import OnboardingError, ValidationError, DatabaseError
from .db_utils import safe_db_operation, safe_db_transaction

logger = logging.getLogger(__name__)

class OnboardingService:
    """온보딩 프로세스를 관리하는 서비스 클래스"""

    @staticmethod
    @safe_db_operation("create_temp_user")
    def create_temp_user(social_type: str, social_id: str, basic_info: Optional[Dict[str, Any]] = None) -> User:
        """
        소셜 로그인 후 임시 사용자 생성
        
        Args:
            social_type: 소셜 플랫폼 타입 ('google', 'naver', 'kakao')
            social_id: 소셜 플랫폼에서 제공하는 사용자 고유 ID
            basic_info: 소셜 플랫폼에서 제공하는 기본 정보 (선택사항)
        
        Returns:
            User: 생성된 임시 사용자 객체
        """
        basic_info = basic_info or {}
        
        try:
            # 기존 사용자 확인
            logger.info(f"Checking for existing user: social_type={social_type}, social_id={social_id}")
            existing_user = User.query.filter_by(
                social_type=social_type,
                social_id=social_id
            ).first()
            
            if existing_user:
                logger.info(f"Existing user found: {existing_user.id}, status: {existing_user.onboarding_status}")
                return existing_user
            
            logger.info(f"No existing user found, creating new temp user")
            
            # 임시 닉네임 생성 (소셜 타입 + 타임스탬프)
            temp_nickname = f"{social_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 새 임시 사용자 생성
            temp_user = User(
                social_type=social_type,
                social_id=social_id,
                nickname=temp_nickname
            )
            
            # 소셜 로그인에서 받은 기본 정보 설정
            if 'name' in basic_info and basic_info['name']:
                temp_user.name = basic_info['name']
            
            # 온보딩 데이터 초기화
            initial_onboarding_data = {
                'step': 0,
                'progress': basic_info,
                'timestamp': datetime.now().isoformat(),
                'source': social_type
            }
            temp_user.onboarding_data = json.dumps(initial_onboarding_data)
            
            db.session.add(temp_user)
            db.session.commit()
            
            logger.info(f"Created temp user: {temp_user.id} for {social_type}")
            return temp_user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating temp user: {str(e)}")
            raise

    @staticmethod
    def get_onboarding_data(user: User) -> Dict[str, Any]:
        """
        저장된 온보딩 데이터 조회
        
        Args:
            user: 사용자 객체
            
        Returns:
            Dict: 온보딩 데이터
        """
        try:
            if user.onboarding_data:
                return json.loads(user.onboarding_data)
            else:
                # 기본 온보딩 데이터 구조 반환
                return {
                    'step': 0,
                    'progress': {},
                    'timestamp': datetime.now().isoformat(),
                    'source': user.social_type or 'unknown'
                }
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Error parsing onboarding data for user {user.id}: {str(e)}")
            # 파싱 오류 시 기본 구조 반환
            return {
                'step': 0,
                'progress': {},
                'timestamp': datetime.now().isoformat(),
                'source': user.social_type or 'unknown'
            }

    @staticmethod
    @safe_db_operation("save_onboarding_progress")
    def save_onboarding_progress(user: User, form_data: Dict[str, Any], step: int) -> bool:
        """
        온보딩 진행 상황 저장
        
        Args:
            user: 사용자 객체
            form_data: 입력된 폼 데이터
            step: 현재 진행 단계
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 기존 온보딩 데이터 조회
            current_data = OnboardingService.get_onboarding_data(user)
            
            # 진행 상황 업데이트
            current_data['step'] = step
            current_data['timestamp'] = datetime.now().isoformat()
            
            # 폼 데이터를 progress에 병합
            if 'progress' not in current_data:
                current_data['progress'] = {}
            
            current_data['progress'].update(form_data)
            
            # 사용자 객체 업데이트
            user.onboarding_data = json.dumps(current_data)
            user.onboarding_step = step
            
            # 부분적으로 사용자 정보 업데이트 (검증된 데이터만)
            if 'name' in form_data and form_data['name']:
                user.name = form_data['name']
            if 'nickname' in form_data and form_data['nickname']:
                user.nickname = form_data['nickname']
            if 'gender' in form_data and form_data['gender']:
                user.gender = form_data['gender']
            if 'birth_date' in form_data and form_data['birth_date']:
                try:
                    birth_date_value = form_data['birth_date']
                    logger.info(f"Saving birth_date: {birth_date_value} (type: {type(birth_date_value)})")
                    
                    # 간단한 방법: 문자열을 그대로 date로 변환
                    user.birth_date = datetime.strptime(birth_date_value, '%Y-%m-%d').date()
                    logger.info(f"Successfully saved birth_date: {user.birth_date}")
                except Exception as e:
                    logger.error(f"Error saving birth_date: {str(e)} - value was: {birth_date_value}")
                    # 생년월일 저장 실패해도 다른 데이터는 저장되도록 함
            
            # 프로필 완성 상태 업데이트
            user.update_profile_complete_status()
            
            db.session.commit()
            logger.info(f"Saved onboarding progress for user {user.id}, step {step}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving onboarding progress for user {user.id}: {str(e)}")
            return False

    @staticmethod
    @safe_db_operation("complete_onboarding")
    def complete_onboarding(user: User, final_data: Dict[str, Any]) -> bool:
        """
        온보딩 완료 처리
        
        Args:
            user: 사용자 객체
            final_data: 최종 입력 데이터
            
        Returns:
            bool: 완료 처리 성공 여부
        """
        try:
            logger.info(f"Starting complete_onboarding for user {user.id} with data: {final_data}")
            
            # 최종 데이터로 사용자 정보 업데이트
            if 'name' in final_data and final_data['name']:
                user.name = final_data['name']
                logger.info(f"Updated name: {user.name}")
            if 'nickname' in final_data and final_data['nickname']:
                user.nickname = final_data['nickname']
                logger.info(f"Updated nickname: {user.nickname}")
            if 'gender' in final_data and final_data['gender']:
                user.gender = final_data['gender']
                logger.info(f"Updated gender: {user.gender}")
            if 'birth_date' in final_data and final_data['birth_date']:
                try:
                    birth_date_value = final_data['birth_date']
                    logger.info(f"Completing birth_date: {birth_date_value} (type: {type(birth_date_value)})")
                    
                    # 간단한 방법: 문자열을 그대로 date로 변환
                    user.birth_date = datetime.strptime(birth_date_value, '%Y-%m-%d').date()
                    logger.info(f"Successfully completed birth_date: {user.birth_date}")
                except Exception as e:
                    logger.error(f"Error completing birth_date: {str(e)} - value was: {birth_date_value}")
                    # 생년월일 저장 실패해도 다른 데이터는 저장되도록 함
            
            # 온보딩 상태를 완료로 변경
            user.onboarding_status = 'completed'
            user.onboarding_step = 4  # 최종 단계
            user.update_profile_complete_status()
            
            # 최종 온보딩 데이터 저장
            final_onboarding_data = {
                'step': 4,
                'progress': final_data,
                'timestamp': datetime.now().isoformat(),
                'source': user.social_type or 'unknown',
                'completed_at': datetime.now().isoformat()
            }
            user.onboarding_data = json.dumps(final_onboarding_data)
            
            db.session.commit()
            logger.info(f"Completed onboarding for user {user.id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error completing onboarding for user {user.id}: {str(e)}")
            return False

    @staticmethod
    def is_required_info_complete(user: User) -> bool:
        """
        필수 정보 완성도 체크
        
        Args:
            user: 사용자 객체
            
        Returns:
            bool: 필수 정보 완성 여부
        """
        try:
            # 필수 필드 체크
            required_fields = [user.name, user.nickname, user.gender, user.birth_date]
            basic_complete = all(field is not None and str(field).strip() != '' for field in required_fields)
            
            if not basic_complete:
                return False
            
            # 추가 검증
            # 1. 닉네임 길이 체크
            if len(user.nickname) < 2 or len(user.nickname) > 20:
                return False
            
            # 2. 성별 값 체크
            if user.gender not in ['male', 'female']:
                return False
            
            # 3. 나이 체크 (만 14세 이상)
            if user.age is None or user.age < 14:
                return False
            
            # 4. 이름 길이 체크
            if len(user.name) < 2 or len(user.name) > 50:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking required info for user {user.id}: {str(e)}")
            return False

    @staticmethod
    def validate_onboarding_data(data: Dict[str, Any], step: int, exclude_user_id: Optional[int] = None) -> Dict[str, str]:
        """
        온보딩 데이터 검증 (새로운 검증 시스템 사용)
        
        Args:
            data: 검증할 데이터
            step: 현재 단계 (1-4)
            exclude_user_id: 중복 검사 시 제외할 사용자 ID (본인 제외)
        
        Returns:
            Dict[str, str]: 검증 오류 메시지 (필드명: 오류메시지)
        """
        try:
            logger.info(f"Validating onboarding data for step {step}")
            
            # 데이터 정제
            sanitized_data = sanitize_data(data)
            
            # 완전한 프로필 검증 (4단계인 경우)
            if step >= 4:
                is_complete, errors = validate_complete_profile(sanitized_data, exclude_user_id)
                if not is_complete:
                    logger.warning(f"Complete profile validation failed: {errors}")
                    return errors
            else:
                # 단계별 검증
                errors = validate_step_data(step, sanitized_data, exclude_user_id)
                if errors:
                    logger.warning(f"Step {step} validation failed: {errors}")
                    return errors
            
            logger.info(f"Validation passed for step {step}")
            return {}
            
        except Exception as e:
            logger.error(f"Error validating onboarding data: {str(e)}")
            return {'general': '데이터 검증 중 오류가 발생했습니다.'}

    @staticmethod
    def check_nickname_availability(nickname: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        닉네임 사용 가능 여부 체크
        
        Args:
            nickname: 체크할 닉네임
            exclude_user_id: 제외할 사용자 ID (본인 수정 시)
            
        Returns:
            bool: 사용 가능 여부
        """
        try:
            query = User.query.filter_by(nickname=nickname.strip())
            
            if exclude_user_id:
                query = query.filter(User.id != exclude_user_id)
            
            existing_user = query.first()
            return existing_user is None
            
        except Exception as e:
            logger.error(f"Error checking nickname availability: {str(e)}")
            return False

    @staticmethod
    def reset_onboarding(user: User) -> bool:
        """
        온보딩 상태 초기화 (처음부터 다시 시작)
        
        Args:
            user: 사용자 객체
            
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            user.onboarding_status = 'pending'
            user.onboarding_step = 0
            user.is_profile_complete = False
            
            # 온보딩 데이터 초기화
            initial_data = {
                'step': 0,
                'progress': {},
                'timestamp': datetime.now().isoformat(),
                'source': user.social_type or 'unknown',
                'reset_at': datetime.now().isoformat()
            }
            user.onboarding_data = json.dumps(initial_data)
            
            db.session.commit()
            logger.info(f"Reset onboarding for user {user.id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resetting onboarding for user {user.id}: {str(e)}")
            return False