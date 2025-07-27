from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import community_bp
import logging

logger = logging.getLogger(__name__)

# ===================================================================
# 기존 jobs 관련 라우트들은 /api/jobs/* AJAX 엔드포인트로 대체되었습니다.
# components.py에서 처리됩니다:
# - /api/jobs/list - 공고 목록 조회
# - /api/jobs/<id> - 공고 상세 조회  
# - /api/jobs/create - 공고 생성
# - /api/jobs/<id>/update - 공고 수정
# - /api/jobs/<id>/delete - 공고 삭제
# - /api/jobs/search - 공고 검색
# ===================================================================

# 향후 다른 커뮤니티 기능들 (공지사항, 질문/답변 등)을 위한 라우트들을 
# 여기에 추가할 수 있습니다.

@community_bp.route('/')
def index():
    """커뮤니티 메인 페이지"""
    return redirect(url_for('auth.home'))
