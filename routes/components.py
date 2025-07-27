from flask import Blueprint, render_template, jsonify
from flask_login import login_required

components_bp = Blueprint('components', __name__)

@components_bp.route('/api/components/jobs')
@login_required
def get_jobs_content():
    """구인구직 페이지 컴포넌트를 반환합니다."""
    try:
        return render_template('components/jobs_content.html')
    except Exception as e:
        return jsonify({'error': '구인구직 페이지를 불러올 수 없습니다.'}), 500

@components_bp.route('/api/components/community')
@login_required
def get_community_content():
    """커뮤니티 페이지 컴포넌트를 반환합니다."""
    try:
        return render_template('components/community_content.html')
    except Exception as e:
        return jsonify({'error': '커뮤니티 페이지를 불러올 수 없습니다.'}), 500