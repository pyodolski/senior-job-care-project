"""
데이터 검증 로직 및 규칙
"""
import re
import logging
from datetime import date, datetime
from typing import Dict, List, Any, Optional, Tuple

from .exceptions import ValidationError

logger = logging.getLogger(__name__)

# 필수 정보 검증 규칙 정의
REQUIRED_FIELDS = {
    'name': {
        'required': True,
        'min_length': 1,
        'max_length': 100,
        'pattern': r'^[a-zA-Z가-힣\s]+$',  # 한글, 영문, 공백만 허용
        'error_messages': {
            'required': '이름을 입력해주세요.',
            'min_length': '이름은 최소 1자 이상 입력해주세요.',
            'max_length': '이름은 100자 이하로 입력해주세요.',
            'pattern': '이름은 한글 또는 영문만 입력 가능합니다.'
        }
    },
    'nickname': {
        'required': True,
        'min_length': 2,
        'max_length': 20,
        'pattern': r'^[a-zA-Z가-힣0-9_]+$',  # 한글, 영문, 숫자, 언더스코어만 허용
        'unique': True,  # 중복 검사 필요
        'error_messages': {
            'required': '닉네임을 입력해주세요.',
            'min_length': '닉네임은 최소 2자 이상 입력해주세요.',
            'max_length': '닉네임은 20자 이하로 입력해주세요.',
            'pattern': '닉네임은 한글, 영문, 숫자, 언더스코어(_)만 사용 가능합니다.',
            'unique': '이미 사용 중인 닉네임입니다.'
        }
    },
    'gender': {
        'required': True,
        'choices': ['male', 'female'],
        'error_messages': {
            'required': '성별을 선택해주세요.',
            'choices': '올바른 성별을 선택해주세요.'
        }
    },
    'birth_date': {
        'required': True,
        'format': '%Y-%m-%d',
        'min_age': 14,
        'max_age': 120,
        'error_messages': {
            'required': '생년월일을 입력해주세요.',
            'format': '올바른 날짜 형식으로 입력해주세요. (YYYY-MM-DD)',
            'min_age': '만 14세 이상만 가입 가능합니다.',
            'max_age': '올바른 생년월일을 입력해주세요.',
            'future_date': '미래 날짜는 입력할 수 없습니다.'
        }
    }
}

# 선택적 정보 검증 규칙
OPTIONAL_FIELDS = {
    'email': {
        'required': False,
        'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'error_messages': {
            'pattern': '올바른 이메일 형식으로 입력해주세요.'
        }
    },
    'phone': {
        'required': False,
        'pattern': r'^010-\d{4}-\d{4}$',
        'error_messages': {
            'pattern': '올바른 전화번호 형식으로 입력해주세요. (010-XXXX-XXXX)'
        }
    }
}


def validate_required_info(data: Dict[str, Any], exclude_user_id: Optional[int] = None) -> Dict[str, str]:
    """
    필수 정보 검증
    
    Args:
        data: 검증할 데이터
        exclude_user_id: 중복 검사 시 제외할 사용자 ID (본인 제외)
    
    Returns:
        Dict[str, str]: 검증 오류 메시지 (필드명: 오류메시지)
    """
    errors = {}
    
    logger.info(f"Starting validation for data: {list(data.keys())}")
    
    # 필수 필드 검증
    for field_name, rules in REQUIRED_FIELDS.items():
        error = validate_field(field_name, data.get(field_name), rules, exclude_user_id)
        if error:
            errors[field_name] = error
    
    # 선택적 필드 검증 (값이 있는 경우만)
    for field_name, rules in OPTIONAL_FIELDS.items():
        if field_name in data and data[field_name]:
            error = validate_field(field_name, data[field_name], rules, exclude_user_id)
            if error:
                errors[field_name] = error
    
    logger.info(f"Validation completed. Errors: {list(errors.keys())}")
    return errors


def validate_field(field_name: str, value: Any, rules: Dict[str, Any], exclude_user_id: Optional[int] = None) -> Optional[str]:
    """
    개별 필드 검증
    
    Args:
        field_name: 필드명
        value: 검증할 값
        rules: 검증 규칙
        exclude_user_id: 중복 검사 시 제외할 사용자 ID
    
    Returns:
        Optional[str]: 오류 메시지 (오류 없으면 None)
    """
    error_messages = rules.get('error_messages', {})
    
    # 필수 필드 검증
    if rules.get('required', False):
        if not value or str(value).strip() == '':
            return error_messages.get('required', f'{field_name}을(를) 입력해주세요.')
    
    # 값이 없으면 더 이상 검증하지 않음 (선택적 필드인 경우)
    if not value or str(value).strip() == '':
        return None
    
    value_str = str(value).strip()
    
    # 길이 검증
    if 'min_length' in rules:
        if len(value_str) < rules['min_length']:
            return error_messages.get('min_length', f'{field_name}은(는) 최소 {rules["min_length"]}자 이상이어야 합니다.')
    
    if 'max_length' in rules:
        if len(value_str) > rules['max_length']:
            return error_messages.get('max_length', f'{field_name}은(는) 최대 {rules["max_length"]}자 이하여야 합니다.')
    
    # 패턴 검증
    if 'pattern' in rules:
        if not re.match(rules['pattern'], value_str):
            return error_messages.get('pattern', f'{field_name} 형식이 올바르지 않습니다.')
    
    # 선택지 검증
    if 'choices' in rules:
        if value_str not in rules['choices']:
            return error_messages.get('choices', f'올바른 {field_name}을(를) 선택해주세요.')
    
    # 날짜 형식 검증
    if 'format' in rules:
        try:
            date_obj = datetime.strptime(value_str, rules['format']).date()
            
            # 미래 날짜 검증
            if date_obj > date.today():
                return error_messages.get('future_date', '미래 날짜는 입력할 수 없습니다.')
            
            # 나이 검증
            if 'min_age' in rules or 'max_age' in rules:
                today = date.today()
                age = today.year - date_obj.year - ((today.month, today.day) < (date_obj.month, date_obj.day))
                
                if 'min_age' in rules and age < rules['min_age']:
                    return error_messages.get('min_age', f'만 {rules["min_age"]}세 이상만 가입 가능합니다.')
                
                if 'max_age' in rules and age > rules['max_age']:
                    return error_messages.get('max_age', '올바른 생년월일을 입력해주세요.')
                    
        except ValueError:
            return error_messages.get('format', '올바른 날짜 형식으로 입력해주세요.')
    
    # 중복 검증 (닉네임)
    if rules.get('unique', False) and field_name == 'nickname':
        from models import User  # 순환 import 방지
        
        query = User.query.filter_by(nickname=value_str)
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        
        if query.first():
            return error_messages.get('unique', '이미 사용 중인 닉네임입니다.')
    
    return None


def validate_step_data(step: int, data: Dict[str, Any], exclude_user_id: Optional[int] = None) -> Dict[str, str]:
    """
    단계별 데이터 검증
    
    Args:
        step: 온보딩 단계 (1-4)
        data: 검증할 데이터
        exclude_user_id: 중복 검사 시 제외할 사용자 ID
    
    Returns:
        Dict[str, str]: 검증 오류 메시지
    """
    errors = {}
    
    # 단계별 필수 필드 정의
    step_fields = {
        1: ['name'],
        2: ['nickname'],
        3: ['gender'],
        4: ['birth_date']
    }
    
    # 해당 단계의 필수 필드만 검증
    required_fields_for_step = step_fields.get(step, [])
    
    for field_name in required_fields_for_step:
        if field_name in REQUIRED_FIELDS:
            error = validate_field(field_name, data.get(field_name), REQUIRED_FIELDS[field_name], exclude_user_id)
            if error:
                errors[field_name] = error
    
    logger.info(f"Step {step} validation completed. Errors: {list(errors.keys())}")
    return errors


def validate_complete_profile(data: Dict[str, Any], exclude_user_id: Optional[int] = None) -> Tuple[bool, Dict[str, str]]:
    """
    프로필 완성도 검증 (모든 필수 정보가 입력되었는지 확인)
    
    Args:
        data: 검증할 데이터
        exclude_user_id: 중복 검사 시 제외할 사용자 ID
    
    Returns:
        Tuple[bool, Dict[str, str]]: (완성 여부, 오류 메시지)
    """
    errors = validate_required_info(data, exclude_user_id)
    is_complete = len(errors) == 0
    
    logger.info(f"Profile completeness check: {is_complete}")
    return is_complete, errors


def sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    데이터 정제 (XSS 방지, 공백 제거 등)
    
    Args:
        data: 정제할 데이터
    
    Returns:
        Dict[str, Any]: 정제된 데이터
    """
    sanitized = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            # 공백 제거
            cleaned_value = value.strip()
            
            # XSS 방지를 위한 기본적인 HTML 태그 제거
            cleaned_value = re.sub(r'<[^>]+>', '', cleaned_value)
            
            # 연속된 공백을 하나로 정리
            cleaned_value = re.sub(r'\s+', ' ', cleaned_value)
            
            sanitized[key] = cleaned_value
        else:
            sanitized[key] = value
    
    return sanitized 