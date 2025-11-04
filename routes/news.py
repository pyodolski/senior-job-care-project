from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from services.naver_news_service import NaverNewsService

news_bp = Blueprint('news', __name__, url_prefix='/news')

@news_bp.route('/')
@login_required
def news_list():
    """뉴스 목록 페이지"""
    # 검색어 파라미터 받기 (기본값: 시니어 일자리)
    query = request.args.get('q', '시니어 일자리')
    page = int(request.args.get('page', 1))
    display = 5  # 한 페이지당 뉴스 개수
    start = (page - 1) * display + 1

    # 네이버 뉴스 서비스 인스턴스 생성
    news_service = NaverNewsService()

    # 뉴스 검색
    news_data = news_service.search_news(
        query=query,
        display=display,
        start=start,
        sort='date'
    )

    return render_template('news/news_list.html',
                         news_list=news_data['items'],
                         total=news_data['total'],
                         current_page=page,
                         query=query)

@news_bp.route('/<int:news_id>')
@login_required
def news_detail(news_id):
    """뉴스 상세 페이지"""
    # 뉴스 ID로 상세 정보 조회
    # 실제로는 캐시나 데이터베이스에서 조회해야 하지만,
    # 여기서는 다시 API를 호출해서 해당 뉴스를 찾습니다.
    
    news_service = NaverNewsService()
    news_data = news_service.search_news(display=50)  # 더 많은 뉴스를 가져와서 찾기
    
    # ID가 일치하는 뉴스 찾기
    news = None
    for item in news_data['items']:
        if item['id'] == news_id:
            news = item
            break
    
    if not news:
        return "뉴스를 찾을 수 없습니다.", 404
    
    return render_template('news/news_detail.html', news=news)

@news_bp.route('/category/<category>')
@login_required
def news_by_category(category):
    """카테고리별 뉴스 목록"""
    page = int(request.args.get('page', 1))
    display = 5
    start = (page - 1) * display + 1
    
    news_service = NaverNewsService()
    news_data = news_service.search_by_category(category=category, display=display)
    
    # 카테고리 이름 매핑
    category_names = {
        'senior_jobs': '시니어 일자리',
        'senior_policy': '시니어 정책', 
        'senior_welfare': '시니어 복지',
        'senior_education': '시니어 교육',
        'senior_startup': '시니어 창업'
    }
    
    category_name = category_names.get(category, '시니어 뉴스')
    
    return render_template('news/news_list.html',
                         news_list=news_data['items'],
                         total=news_data['total'],
                         current_page=page,
                         query=category_name,
                         category=category)

@news_bp.route('/search')
@login_required
def search_news():
    """뉴스 검색"""
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('news.news_list'))
    
    return redirect(url_for('news.news_list', q=query))