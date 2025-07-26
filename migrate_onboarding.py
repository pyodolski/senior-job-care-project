#!/usr/bin/env python3
"""
온보딩 기능을 위한 데이터베이스 마이그레이션 스크립트
기존 User 테이블에 온보딩 관련 컬럼들을 추가합니다.
"""

from app import app
from models import db
import logging
from sqlalchemy import text

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_column_exists(connection, table_name, column_name):
    """컬럼이 존재하는지 확인"""
    try:
        result = connection.execute(text(f"SHOW COLUMNS FROM {table_name} LIKE '{column_name}'"))
        return result.fetchone() is not None
    except Exception as e:
        logger.error(f"컬럼 존재 확인 중 오류: {str(e)}")
        return False

def migrate_database():
    """데이터베이스 마이그레이션 실행"""
    with app.app_context():
        try:
            logger.info("현재 데이터베이스 연결 확인 중...")
            
            # 새로운 컬럼들과 기본값 정의
            columns_to_add = [
                ("onboarding_status", "VARCHAR(20)", "'pending'"),
                ("onboarding_data", "TEXT", "NULL"),
                ("onboarding_step", "INT", "0"),
                ("is_profile_complete", "BOOLEAN", "FALSE")
            ]
            
            logger.info("온보딩 관련 컬럼 추가 중...")
            
            with db.engine.connect() as connection:
                for column_name, column_type, default_value in columns_to_add:
                    if not check_column_exists(connection, 'user', column_name):
                        query = f"ALTER TABLE user ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
                        try:
                            connection.execute(text(query))
                            logger.info(f"컬럼 추가 완료: {column_name}")
                        except Exception as e:
                            logger.error(f"컬럼 추가 실패 {column_name}: {str(e)}")
                            raise
                    else:
                        logger.info(f"컬럼이 이미 존재함: {column_name}")
                
                # 변경사항 커밋
                connection.commit()
                
                # 기존 사용자들의 온보딩 상태 업데이트
                logger.info("기존 사용자들의 온보딩 상태 업데이트 중...")
                
                update_query = """
                    UPDATE user 
                    SET onboarding_status = 'completed', 
                        is_profile_complete = TRUE 
                    WHERE name IS NOT NULL 
                        AND name != '' 
                        AND nickname IS NOT NULL 
                        AND nickname != '' 
                        AND gender IS NOT NULL 
                        AND gender != '' 
                        AND birth_date IS NOT NULL
                        AND onboarding_status = 'pending'
                """
                
                connection.execute(text(update_query))
                connection.commit()
                logger.info("기존 사용자 온보딩 상태 업데이트 완료")
            
            logger.info("데이터베이스 마이그레이션이 성공적으로 완료되었습니다!")
            
        except Exception as e:
            logger.error(f"마이그레이션 중 오류 발생: {str(e)}")
            raise

def verify_migration():
    """마이그레이션 결과 확인"""
    with app.app_context():
        try:
            # 테이블 구조 확인
            with db.engine.connect() as connection:
                result = connection.execute(text("DESCRIBE user"))
                columns = [row[0] for row in result]
            
            required_columns = ['onboarding_status', 'onboarding_data', 'onboarding_step', 'is_profile_complete']
            
            logger.info("현재 user 테이블 컬럼들:")
            for col in columns:
                logger.info(f"  - {col}")
            
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                logger.error(f"누락된 컬럼들: {missing_columns}")
                return False
            else:
                logger.info("모든 필수 컬럼이 성공적으로 추가되었습니다!")
                return True
                
        except Exception as e:
            logger.error(f"마이그레이션 확인 중 오류: {str(e)}")
            return False

if __name__ == "__main__":
    logger.info("온보딩 데이터베이스 마이그레이션을 시작합니다...")
    
    try:
        migrate_database()
        
        if verify_migration():
            logger.info("마이그레이션이 성공적으로 완료되었습니다!")
        else:
            logger.error("마이그레이션 검증에 실패했습니다.")
            
    except Exception as e:
        logger.error(f"마이그레이션 실패: {str(e)}")
        exit(1)