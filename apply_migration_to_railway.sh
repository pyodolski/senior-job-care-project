#!/bin/bash

# Railway 데이터베이스 마이그레이션 스크립트
# ==========================================
# 
# 사용법:
# 1. Railway 환경변수를 설정한 후 실행
# 2. 또는 Railway CLI로 실행: railway run bash apply_migration_to_railway.sh

echo "🚂 Railway 데이터베이스 마이그레이션 시작..."

# Railway 환경변수 확인
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL 환경변수가 설정되지 않았습니다."
    echo "   Railway CLI를 사용하세요: railway run bash apply_migration_to_railway.sh"
    exit 1
fi

# DATABASE_URL 파싱
# 예: mysql+pymysql://user:pass@host:port/dbname
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')

echo "📊 데이터베이스 정보:"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"

# SQL 파일 실행
echo "📝 마이그레이션 SQL 실행 중..."
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASS $DB_NAME < migrations/add_resume_favorite_table.sql

if [ $? -eq 0 ]; then
    echo "✅ Railway 데이터베이스 마이그레이션 완료!"
else
    echo "❌ 마이그레이션 실패"
    exit 1
fi
