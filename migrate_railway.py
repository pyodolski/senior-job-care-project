#!/usr/bin/env python3
"""
Railway 데이터베이스 마이그레이션 스크립트
==========================================

이 스크립트는 Railway 환경에서 자동으로 실행되어
새로운 테이블을 생성합니다.

사용법:
1. Railway에 배포 시 자동 실행 (Procfile의 release 명령)
2. 또는 로컬에서 Railway DB에 연결하여 실행:
   python migrate_railway.py
"""

import os
import sys

def run_migration():
    """마이그레이션 실행"""
    try:
        print("🚀 마이그레이션 시작...")
        
        # Flask 앱 컨텍스트 생성
        from app import app, db
        from models import ResumeFavorite
        
        with app.app_context():
            # 환경 확인
            env = os.getenv('RAILWAY_ENVIRONMENT', 'local')
            db_url = os.getenv('DATABASE_URL', 'not set')
            print(f"📊 환경: {env}")
            print(f"🗄️  데이터베이스: {db_url[:50]}..." if len(db_url) > 50 else f"🗄️  데이터베이스: {db_url}")
            
            # 테이블 생성 (이미 존재하면 무시됨)
            db.create_all()
            
            # 테이블 존재 확인
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'resume_favorite' in tables:
                print("✅ resume_favorite 테이블 확인됨")
            else:
                print("⚠️  resume_favorite 테이블이 생성되지 않았습니다")
            
            print("✅ Railway 데이터베이스 마이그레이션 완료")
            print(f"   총 {len(tables)}개의 테이블 존재")
            return True
            
    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
        # Railway에서는 실패해도 배포를 계속 진행
        return True  # 실패해도 0 반환 (앱 시작 시 db.create_all()이 다시 실행됨)

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
