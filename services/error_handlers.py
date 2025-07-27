"""
오류 처리 데코레이터 및 핸들러
"""
import logging
import traceback
from functools import wraps
from typing import Callable, Any, Optional

from flask import flash, redirect, url_for, request, render_template, jsonify
from flask_login import current_user

from .exceptions import (
    SocialLoginError, OnboardingError, ValidationError, DatabaseError,
    get_friendly_message
)

logger = logging.getLogger(__name__)


def handle_social_login_errors(f: Callable) -> Callable:
    """소셜 로그인 관련 오류를 처리하는 데코레이터"""
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
            
        except SocialLoginError as e:
            logger.error(f"소셜 로그인 오류: {e}")
            error_code = e.error_code or 'general_error'
            error_message = get_friendly_message(error_code, e.message)
            flash(error_message, 'error')
            return redirect(url_for('auth.home'))
            
        except OnboardingError as e:
            logger.error(f"온보딩 오류: {e}")
            error_message = get_friendly_message('onboarding_validation_failed', e.message)
            flash(error_message, 'error')
            
            # 온보딩 페이지로 리다이렉트 (에러 정보 포함)
            if e.step:
                return redirect(url_for('onboarding.onboarding', step=e.step))
            else:
                return redirect(url_for('onboarding.onboarding'))
                
        except ValidationError as e:
            logger.error(f"검증 오류: {e}")
            error_message = get_friendly_message('onboarding_validation_failed', e.message)
            flash(error_message, 'error')
            
            # AJAX 요청인 경우 JSON 응답
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': error_message,
                    'field': e.field
                }), 400
            
            # 일반 요청인 경우 이전 페이지로 리다이렉트
            return redirect(request.referrer or url_for('auth.home'))
            
        except DatabaseError as e:
            logger.error(f"데이터베이스 오류: {e}")
            error_message = get_friendly_message('db_save_error', e.message)
            flash(error_message, 'error')
            
            # AJAX 요청인 경우 JSON 응답
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': error_message
                }), 500
            
            return redirect(url_for('auth.home'))
            
        except Exception as e:
            # 예상치 못한 오류
            logger.error(f"예상치 못한 오류 발생: {str(e)}")
            logger.error(f"스택 트레이스: {traceback.format_exc()}")
            
            error_message = get_friendly_message('general_error')
            flash(error_message, 'error')
            
            # AJAX 요청인 경우 JSON 응답
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': error_message
                }), 500
            
            return redirect(url_for('auth.home'))
    
    return decorated_function


def handle_onboarding_errors(f: Callable) -> Callable:
    """온보딩 관련 오류를 처리하는 데코레이터"""
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
            
        except OnboardingError as e:
            logger.error(f"온보딩 오류: {e}")
            
            # AJAX 요청인 경우
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': e.message,
                    'validation_errors': e.validation_errors,
                    'step': e.step
                }), 400
            
            # 일반 요청인 경우
            error_message = get_friendly_message('onboarding_validation_failed', e.message)
            flash(error_message, 'error')
            
            # 현재 단계 정보가 있으면 해당 단계로, 없으면 시작 페이지로
            if hasattr(current_user, 'onboarding_step') and current_user.onboarding_step:
                return redirect(url_for('onboarding.onboarding', step=current_user.onboarding_step))
            else:
                return redirect(url_for('onboarding.onboarding'))
                
        except ValidationError as e:
            logger.error(f"검증 오류: {e}")
            
            # AJAX 요청인 경우
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': e.message,
                    'field': e.field,
                    'value': e.value
                }), 400
            
            # 일반 요청인 경우
            flash(e.message, 'error')
            return redirect(request.referrer or url_for('onboarding.onboarding'))
            
        except Exception as e:
            logger.error(f"온보딩 처리 중 예상치 못한 오류: {str(e)}")
            logger.error(f"스택 트레이스: {traceback.format_exc()}")
            
            error_message = get_friendly_message('general_error')
            
            # AJAX 요청인 경우
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': error_message
                }), 500
            
            flash(error_message, 'error')
            return redirect(url_for('auth.home'))
    
    return decorated_function


def handle_api_errors(f: Callable) -> Callable:
    """API 엔드포인트용 오류 처리 데코레이터"""
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
            
        except ValidationError as e:
            logger.error(f"API 검증 오류: {e}")
            return jsonify({
                'success': False,
                'error': e.message,
                'field': e.field,
                'error_code': 'validation_error'
            }), 400
            
        except DatabaseError as e:
            logger.error(f"API 데이터베이스 오류: {e}")
            return jsonify({
                'success': False,
                'error': get_friendly_message('db_save_error'),
                'error_code': 'database_error'
            }), 500
            
        except Exception as e:
            logger.error(f"API 예상치 못한 오류: {str(e)}")
            logger.error(f"스택 트레이스: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': get_friendly_message('general_error'),
                'error_code': 'internal_error'
            }), 500
    
    return decorated_function


def log_error_context(error: Exception, context: Optional[dict] = None):
    """오류 발생 시 추가 컨텍스트 정보를 로깅"""
    
    error_info = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'user_id': getattr(current_user, 'id', None) if current_user.is_authenticated else None,
        'request_url': request.url if request else None,
        'request_method': request.method if request else None,
        'user_agent': request.headers.get('User-Agent') if request else None,
        'ip_address': request.remote_addr if request else None,
    }
    
    if context:
        error_info['context'] = context
    
    logger.error(f"오류 컨텍스트: {error_info}")
    logger.error(f"스택 트레이스: {traceback.format_exc()}")


def create_error_response(error_code: str, message: Optional[str] = None, status_code: int = 400, **kwargs):
    """표준화된 오류 응답 생성"""
    
    friendly_message = get_friendly_message(error_code, message)
    
    response_data = {
        'success': False,
        'error': friendly_message,
        'error_code': error_code,
        **kwargs
    }
    
    return jsonify(response_data), status_code 