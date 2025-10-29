from flask import Blueprint, render_template,current_app, request, jsonify
from flask_login import login_required, current_user
from models import db, JobPost, JobBookmark, JobApplication
import requests
from services.job_service import JobService

map_bp = Blueprint("map", __name__)

@map_bp.route("/map")
@login_required
def show_map():
    kakao_key = current_app.config.get("KAKAO_MAP_API_KEY")

    # 기존처럼 전체 데이터를 한 번에 가져오는 대신,
    # 지도 로딩만 담당하고 뷰포트 기반 조회는 별도 API로 처리하도록 분리
    return render_template("map.html", kakao_key=kakao_key)

@map_bp.route('/jobs_all')
@login_required
def jobs_all():
    # 필터 파라미터 받기 (all, company, people)
    job_type = request.args.get('type', 'all')
    
    # 기본 쿼리 (위치 정보가 있는 공고만)
    query = JobPost.query.filter(
        JobPost.latitude.isnot(None),
        JobPost.longitude.isnot(None)
    )
    
    # 필터 적용
    if job_type == 'company':
        # 기업 이음: job_category가 있거나 외부 데이터(K-Senior 등)인 공고
        query = query.filter(
            db.or_(
                JobPost.job_category.isnot(None),
                JobPost.source.isnot(None)  # 외부 데이터는 모두 기업 이음
            )
        )
    elif job_type == 'people':
        # 사람 이음: job_category가 없고 외부 데이터가 아닌 공고
        query = query.filter(
            JobPost.job_category.is_(None),
            JobPost.source.is_(None)
        )
    
    jobs = query.all()

    # 현재 사용자의 북마크와 지원 정보 조회
    user_bookmarks = set()
    user_applications = set()
    
    if current_user.is_authenticated:
        bookmarks = JobBookmark.query.filter_by(user_id=current_user.id).all()
        user_bookmarks = {b.job_id for b in bookmarks}
        
        applications = JobApplication.query.filter_by(user_id=current_user.id).all()
        user_applications = {a.job_id for a in applications}

    job_locations = [
        {
            'id': job.id,
            'title': job.title, 
            'lat': job.latitude, 
            'company': job.company,
            'salary': job.salary, 
            'lng': job.longitude,
            'type': 'company' if (job.job_category or job.source) else 'people',
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'recruitment_end_date': job.recruitment_end_date.isoformat() if job.recruitment_end_date else None,
            'recruitment_type': job.recruitment_type,
            'work_period': job.work_period,
            'author': {
                'user_type': job.author.user_type if job.author else None,
                'nickname': job.author.nickname if job.author else None,
                'id': job.author.id if job.author else None
            } if job.author else None,
            'bookmarked': job.id in user_bookmarks,
            'applied': job.id in user_applications
        }
        for job in jobs
    ]

    return jsonify({'jobs': job_locations, 'count': len(job_locations)})

@map_bp.route('/api/address_search')
@login_required
def address_search():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'query parameter is required'}), 400

    kakao_rest_api_key = current_app.config.get('KAKAO_REST_API_KEY')
    if not kakao_rest_api_key:
        return jsonify({'error': 'KAKAO_REST_API_KEY is not set'}), 500

    headers = {"Authorization": f"KakaoAK {kakao_rest_api_key}"}
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    params = {"query": query}

    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        return jsonify({'error': 'Failed to fetch from Kakao API'}), 502

    return jsonify(resp.json())