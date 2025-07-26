"""
데이터베이스 안전 작업 유틸리티
"""
import logging
from functools import wraps
from typing import Callable, Any, Optional, Type
from contextlib import contextmanager

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from models import db
from .exceptions import DatabaseError

logger = logging.getLogger(__name__)


@contextmanager
def safe_db_transaction():
    """
    안전한 데이터베이스 트랜잭션 컨텍스트 매니저
    
    Usage:
        with safe_db_transaction():
            # 데이터베이스 작업
            user.name = "New Name"
            db.session.add(user)
            # 자동으로 커밋됨
    """
    try:
        yield db.session
        db.session.commit()
        logger.debug("Database transaction committed successfully")
        
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise DatabaseError("데이터 무결성 오류가 발생했습니다.", "integrity_violation")
        
    except OperationalError as e:
        db.session.rollback()
        logger.error(f"Database operational error: {str(e)}")
        raise DatabaseError("데이터베이스 연결 오류가 발생했습니다.", "connection_error")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"SQLAlchemy error: {str(e)}")
        raise DatabaseError("데이터베이스 작업 중 오류가 발생했습니다.", "sql_error")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error in database transaction: {str(e)}")
        raise DatabaseError("예상치 못한 데이터베이스 오류가 발생했습니다.", "unexpected_error")


def safe_db_operation(operation_name: str = "Unknown"):
    """
    데이터베이스 작업을 안전하게 처리하는 데코레이터
    
    Args:
        operation_name: 작업 이름 (로깅용)
    
    Usage:
        @safe_db_operation("user_creation")
        def create_user(data):
            user = User(**data)
            db.session.add(user)
            db.session.commit()
            return user
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                logger.info(f"Starting database operation: {operation_name}")
                result = f(*args, **kwargs)
                logger.info(f"Database operation completed successfully: {operation_name}")
                return result
                
            except DatabaseError:
                # DatabaseError는 이미 적절히 처리되었으므로 그대로 전파
                raise
                
            except IntegrityError as e:
                db.session.rollback()
                logger.error(f"Integrity error in {operation_name}: {str(e)}")
                raise DatabaseError(
                    "데이터 무결성 오류가 발생했습니다. 중복된 정보가 있는지 확인해주세요.",
                    operation_name,
                    "user"
                )
                
            except OperationalError as e:
                db.session.rollback()
                logger.error(f"Operational error in {operation_name}: {str(e)}")
                raise DatabaseError(
                    "데이터베이스 연결에 문제가 있습니다. 잠시 후 다시 시도해주세요.",
                    operation_name
                )
                
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"SQLAlchemy error in {operation_name}: {str(e)}")
                raise DatabaseError(
                    "데이터베이스 작업 중 오류가 발생했습니다.",
                    operation_name
                )
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Unexpected error in {operation_name}: {str(e)}")
                raise DatabaseError(
                    "예상치 못한 오류가 발생했습니다. 관리자에게 문의해주세요.",
                    operation_name
                )
        
        return wrapper
    return decorator


def safe_commit() -> bool:
    """
    안전한 커밋 실행
    
    Returns:
        bool: 커밋 성공 여부
    """
    try:
        db.session.commit()
        logger.debug("Database commit successful")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database commit failed: {str(e)}")
        return False


def safe_rollback():
    """
    안전한 롤백 실행
    """
    try:
        db.session.rollback()
        logger.debug("Database rollback successful")
        
    except Exception as e:
        logger.error(f"Database rollback failed: {str(e)}")


def safe_delete(obj: Any) -> bool:
    """
    안전한 객체 삭제
    
    Args:
        obj: 삭제할 데이터베이스 객체
    
    Returns:
        bool: 삭제 성공 여부
    """
    try:
        db.session.delete(obj)
        db.session.commit()
        logger.debug(f"Object deleted successfully: {type(obj).__name__}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete object {type(obj).__name__}: {str(e)}")
        return False


def safe_bulk_insert(objects: list) -> bool:
    """
    안전한 대량 삽입
    
    Args:
        objects: 삽입할 객체 리스트
    
    Returns:
        bool: 삽입 성공 여부
    """
    try:
        db.session.bulk_save_objects(objects)
        db.session.commit()
        logger.info(f"Bulk insert successful: {len(objects)} objects")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Bulk insert failed: {str(e)}")
        return False


def check_db_connection() -> bool:
    """
    데이터베이스 연결 상태 확인
    
    Returns:
        bool: 연결 상태
    """
    try:
        # 간단한 쿼리로 연결 상태 확인
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return True
        
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False


def get_db_stats() -> dict:
    """
    데이터베이스 통계 정보 조회
    
    Returns:
        dict: 통계 정보
    """
    try:
        from models import User
        
        stats = {
            'total_users': User.query.count(),
            'completed_onboarding': User.query.filter_by(onboarding_status='completed').count(),
            'pending_onboarding': User.query.filter_by(onboarding_status='pending').count(),
            'google_users': User.query.filter_by(social_type='google').count(),
            'naver_users': User.query.filter_by(social_type='naver').count(),
            'kakao_users': User.query.filter_by(social_type='kakao').count(),
        }
        
        logger.debug(f"Database stats retrieved: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to retrieve database stats: {str(e)}")
        return {}


def cleanup_abandoned_users(days: int = 7) -> int:
    """
    일정 기간 동안 온보딩을 완료하지 않은 사용자 정리
    
    Args:
        days: 정리 기준 일수
    
    Returns:
        int: 정리된 사용자 수
    """
    try:
        from datetime import datetime, timedelta
        from models import User
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        abandoned_users = User.query.filter(
            User.onboarding_status == 'pending',
            User.created_at < cutoff_date,
            User.onboarding_step.is_(None) | (User.onboarding_step == 0)
        ).all()
        
        count = len(abandoned_users)
        
        if count > 0:
            for user in abandoned_users:
                db.session.delete(user)
            
            db.session.commit()
            logger.info(f"Cleaned up {count} abandoned users")
        
        return count
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to cleanup abandoned users: {str(e)}")
        return 0


def backup_user_data(user_id: int) -> Optional[dict]:
    """
    사용자 데이터 백업
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        Optional[dict]: 백업된 사용자 데이터
    """
    try:
        from models import User
        
        user = User.query.get(user_id)
        if not user:
            return None
        
        backup_data = {
            'id': user.id,
            'name': user.name,
            'nickname': user.nickname,
            'gender': user.gender,
            'birth_date': user.birth_date.isoformat() if user.birth_date else None,
            'social_type': user.social_type,
            'social_id': user.social_id,
            'onboarding_status': user.onboarding_status,
            'onboarding_step': user.onboarding_step,
            'onboarding_data': user.onboarding_data,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'is_profile_complete': user.is_profile_complete
        }
        
        logger.info(f"User data backed up: {user_id}")
        return backup_data
        
    except Exception as e:
        logger.error(f"Failed to backup user data {user_id}: {str(e)}")
        return None 