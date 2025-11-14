"""기존 공고를 AI로 분석하는 배치 스크립트"""
import json
from app import app, db
from models import JobPost
from services.ai_analyzer_service import AIAnalyzerService
from datetime import datetime


def analyze_all_jobs(force=False, limit=100):
    """
    공고를 AI로 분석
    
    Args:
        force: True면 이미 분석된 공고도 재분석
        limit: 분석할 최대 개수 (기본 5개)
    """
    with app.app_context():
        # 분석할 공고 가져오기
        if force:
            jobs = JobPost.query.limit(limit).all()
        else:
            jobs = JobPost.query.filter(JobPost.ai_analyzed_at.is_(None)).limit(limit).all()
        
        if not jobs:
            print("✅ 분석할 공고가 없습니다.")
            return
        
        print(f"📊 총 {len(jobs)}개의 공고를 분석합니다... (최대 {limit}개)")
        
        success_count = 0
        fail_count = 0
        
        for i, job in enumerate(jobs, 1):
            try:
                print(f"\n[{i}/{len(jobs)}] 분석 중: {job.title[:50]}...")
                
                # AI 분석
                result = AIAnalyzerService.analyze_job_post(
                    title=job.title,
                    description=job.description,
                    company=job.company
                )
                
                # 결과 저장
                job.ai_category = result['category']
                job.ai_keywords = json.dumps(result['keywords'], ensure_ascii=False)
                job.ai_skills = json.dumps(result['skills'], ensure_ascii=False)
                job.ai_summary = result['summary']
                job.ai_difficulty = result['difficulty']
                job.ai_analyzed_at = datetime.now()
                
                db.session.commit()
                
                print(f"  ✅ 카테고리: {result['category']}")
                print(f"  ✅ 키워드: {', '.join(result['keywords'])}")
                print(f"  ✅ 난이도: {result['difficulty']}")
                
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ 실패: {e}")
                db.session.rollback()
                fail_count += 1
                continue
        
        print(f"\n{'='*50}")
        print(f"분석 완료!")
        print(f"성공: {success_count}개")
        print(f"실패: {fail_count}개")
        print(f"{'='*50}")


if __name__ == '__main__':
    import sys
    
    force = '--force' in sys.argv
    
    # limit 파라미터 확인
    limit = 5
    for arg in sys.argv:
        if arg.startswith('--limit='):
            try:
                limit = int(arg.split('=')[1])
            except:
                pass
    
    if force:
        print("⚠️  강제 모드: 공고를 재분석합니다.")
    
    analyze_all_jobs(force=force, limit=limit)
