"""관리자 전용 - 데이터 동기화"""
from flask import Blueprint, render_template, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from functools import wraps

data_sync_bp = Blueprint('data_sync', __name__)

def admin_required(f):
    """관리자 권한 확인 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != 2:
            flash('관리자만 접근할 수 있습니다.', 'error')
            return redirect(url_for('auth.main'))
        return f(*args, **kwargs)
    return decorated_function

@data_sync_bp.route('/admin/data-sync')
@login_required
@admin_required
def data_sync_page():
    """데이터 동기화 페이지"""
    return render_template('admin/data_sync.html')

@data_sync_bp.route('/admin/fetch-senior-jobs', methods=['POST'])
@login_required
@admin_required
def fetch_senior_jobs_manual():
    """공공데이터 수동 수집"""
    try:
        from scripts.fetch_senior_jobs import fetch_and_store_jobs
        
        # 백그라운드에서 실행하는 것이 좋지만, 간단하게 동기 실행
        fetch_and_store_jobs()
        
        return jsonify({
            'success': True,
            'message': '공공데이터 수집이 완료되었습니다!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류 발생: {str(e)}'
        }), 500

@data_sync_bp.route('/admin/analyze-jobs', methods=['POST'])
@login_required
@admin_required
def analyze_jobs_manual():
    """AI 분석 수동 실행"""
    try:
        from app import app, db
        from models import JobPost
        from services.ai_analyzer_service import AIAnalyzerService
        import json
        from datetime import datetime
        
        # 분석되지 않은 공고 가져오기 (최대 10개)
        jobs = JobPost.query.filter(
            JobPost.ai_analyzed_at.is_(None)
        ).limit(10).all()
        
        if not jobs:
            return jsonify({
                'success': True,
                'message': '분석할 공고가 없습니다.',
                'count': 0
            })
        
        success_count = 0
        for job in jobs:
            try:
                result = AIAnalyzerService.analyze_job_post(
                    title=job.title,
                    description=job.description,
                    company=job.company
                )
                
                job.ai_category = result['category']
                job.ai_keywords = json.dumps(result['keywords'], ensure_ascii=False)
                job.ai_skills = json.dumps(result['skills'], ensure_ascii=False)
                job.ai_summary = result['summary']
                job.ai_difficulty = result['difficulty']
                job.ai_analyzed_at = datetime.now()
                
                success_count += 1
            except Exception as e:
                print(f"분석 실패 (ID: {job.id}): {e}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{success_count}개 공고 분석 완료!',
            'count': success_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류 발생: {str(e)}'
        }), 500
