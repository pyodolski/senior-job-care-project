"""
JobPost 테이블에 people_category 컬럼 추가 마이그레이션
"""
from app import app, db
from sqlalchemy import text

def add_people_category_column():
    """JobPost 테이블에 people_category 컬럼 추가"""
    
    with app.app_context():
        try:
            # 컬럼 존재 여부 확인
            check_query = text("""
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'job_post' 
                AND COLUMN_NAME = 'people_category'
            """)
            
            result = db.session.execute(check_query).fetchone()
            
            if result[0] == 0:
                print("✅ people_category 컬럼을 추가합니다...")
                
                # 컬럼 추가
                alter_query = "ALTER TABLE job_post ADD COLUMN people_category VARCHAR(20) AFTER contact_phone"
                db.session.execute(text(alter_query))
                
                db.session.commit()
                print("✅ people_category 컬럼 추가 완료!")
            else:
                print("ℹ️ people_category 컬럼이 이미 존재합니다.")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ 마이그레이션 실패: {e}")
            raise

if __name__ == "__main__":
    add_people_category_column()
