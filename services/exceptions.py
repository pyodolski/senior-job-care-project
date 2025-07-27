"""
소셜 로그인 및 온보딩 관련 예외 클래스
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SocialLoginError(Exception):
    """소셜 로그인 관련 오류"""
    
    def __init__(self, message: str, provider: Optional[str] = None, error_code: Optional[str] = None):
        self.message = message
        self.provider = provider
        self.error_code = error_code
        super().__init__(self.message)
        
    def __str__(self):
        return f"SocialLoginError({self.provider}): {self.message}"


class OnboardingError(Exception):
    """온보딩 과정 관련 오류"""
    
    def __init__(self, message: str, step: Optional[int] = None, validation_errors: Optional[Dict[str, Any]] = None):
        self.message = message
        self.step = step
        self.validation_errors = validation_errors or {}
        super().__init__(self.message)
        
    def __str__(self):
        step_info = f" (Step {self.step})" if self.step else ""
        return f"OnboardingError{step_info}: {self.message}"


class ValidationError(Exception):
    """데이터 검증 관련 오류"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[str] = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)
        
    def __str__(self):
        field_info = f" ({self.field})" if self.field else ""
        return f"ValidationError{field_info}: {self.message}"


class DatabaseError(Exception):
    """데이터베이스 작업 관련 오류"""
    
    def __init__(self, message: str, operation: Optional[str] = None, table: Optional[str] = None):
        self.message = message
        self.operation = operation
        self.table = table
        super().__init__(self.message)
        
    def __str__(self):
        op_info = f" ({self.operation})" if self.operation else ""
        return f"DatabaseError{op_info}: {self.message}"


# 사용자 친화적 오류 메시지 매핑
FRIENDLY_ERROR_MESSAGES = {
    # 소셜 로그인 오류
    'google_auth_failed': '구글 로그인에 실패했습니다. 다시 시도해주세요.',
    'naver_auth_failed': '네이버 로그인에 실패했습니다. 다시 시도해주세요.',
    'kakao_auth_failed': '카카오 로그인에 실패했습니다. 다시 시도해주세요.',
    'social_token_expired': '로그인 세션이 만료되었습니다. 다시 로그인해주세요.',
    'social_permission_denied': '소셜 로그인 권한이 거부되었습니다.',
    'social_network_error': '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
    
    # 온보딩 오류
    'onboarding_incomplete': '필수 정보 입력이 완료되지 않았습니다.',
    'onboarding_validation_failed': '입력하신 정보에 오류가 있습니다. 확인 후 다시 시도해주세요.',
    'onboarding_save_failed': '정보 저장 중 오류가 발생했습니다. 다시 시도해주세요.',
    'onboarding_step_invalid': '올바르지 않은 단계입니다.',
    
    # 검증 오류
    'nickname_duplicate': '이미 사용 중인 닉네임입니다.',
    'nickname_invalid': '닉네임은 2-20자 이내로 입력해주세요.',
    'name_required': '이름을 입력해주세요.',
    'gender_required': '성별을 선택해주세요.',
    'birth_date_required': '생년월일을 입력해주세요.',
    'birth_date_invalid': '올바른 생년월일을 입력해주세요.',
    'age_restriction': '만 14세 이상만 가입 가능합니다.',
    
    # 데이터베이스 오류
    'db_connection_error': '데이터베이스 연결에 실패했습니다.',
    'db_save_error': '데이터 저장 중 오류가 발생했습니다.',
    'db_user_not_found': '사용자 정보를 찾을 수 없습니다.',
    'db_integrity_error': '데이터 무결성 오류가 발생했습니다.',
    
    # 일반 오류
    'general_error': '예상치 못한 오류가 발생했습니다. 관리자에게 문의해주세요.',
    'session_expired': '세션이 만료되었습니다. 다시 로그인해주세요.',
    'access_denied': '접근 권한이 없습니다.',
}


def get_friendly_message(error_code: str, default_message: Optional[str] = None) -> str:
    """사용자 친화적 오류 메시지 반환"""
    message = FRIENDLY_ERROR_MESSAGES.get(error_code, default_message)
    if not message:
        message = FRIENDLY_ERROR_MESSAGES['general_error']
    
    logger.debug(f"Error code '{error_code}' mapped to message: {message}")
    return message 