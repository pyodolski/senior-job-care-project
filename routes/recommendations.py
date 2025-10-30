"""추천 시스템 라우트"""
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from services.recommendation_service import RecommendationService

recommendations_bp = Blueprint('recommendations', __name__)


@recommendations_bp.route('/api/recommendations')
@login_required
def api_recommendations():
    """사용자 맞춤 추천 공고 API"""
    try:
        # 추천 공고 가져오기
        recommendations = RecommendationService.get_recommendations(
            user_id=current_user.id,
            limit=20
        )
        
        # JSON 형식으로 변환
        result = []
        for job, score, reasons in recommendations:
            result.append({
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'region': job.region or f"{job.region_1depth_name} {job.region_2depth_name}".strip(),
                'salary': job.salary,
                'score': round(score, 1),
                'reasons': reasons,
                'created_at': job.created_at.strftime('%Y-%m-%d') if job.created_at else None,
                'view_count': job.view_count,
                'bookmark_count': job.bookmark_count,
                'ai_category': job.ai_category,
                'ai_summary': job.ai_summary,
                'latitude': job.latitude,
                'longitude': job.longitude
            })
        
        return jsonify({
            'success': True,
            'recommendations': result,
            'count': len(result)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
