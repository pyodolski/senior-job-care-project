"""
User 테이블에 회사 주소 관련 컬럼 추가 마이그레이션
"""
from app import app, db
from sqlalchemy import text

def add_user_company_address_columns():
    """User 테이블에 회사 주소 관련 컬럼 추가"""
    
    with app.app_context():
        try:
            columns_to_add = [
                ('company_sido', 'VARCHAR(30)'),
                ('company_sigungu', 'VARCHAR(30)'),
                ('company_dong', 'VARCHAR(40)'),
                ('company_full_address', 'VARCHAR(255)')
            ]
            
            for column_name, column_type in columns_to_add:
                # 컬럼 존재 여부 확인
                check_query = text("""
                    SELECT COUNT(*) as count
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'user' 
                    AND COLUMN_NAME = :column_name
                """)
                
                result = db.session.execute(check_query, {'column_name': column_name}).fetchone()
                
                if result[0] == 0:
                    print(f"✅ {column_name} 컬럼을 추가합니다...")
                    
                    # 컬럼 추가
                    alter_query = text(f"ALTER TABLE user ADD COLUMN {column_name} {column_type} NULL")
                    db.session.execute(alter_query)
                    db.session.commit()
                    print(f"✅ {column_name} 컬럼 추가 완료!")
                else:
                    print(f"ℹ️ {column_name} 컬럼이 이미 존재합니다.")
                    
        except Exception as e:
            db.session.rollback()
            print(f"❌ 마이그레이션 실패: {e}")
            raise

if __name__ == "__main__":
    add_user_company_address_columns()
