from flask import Blueprint, render_template,current_app, request, jsonify
from flask_login import login_required
from models import db, JobPost
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
    # 모든 일자리 데이터를 DB에서 한 번에 불러옴
    jobs = JobPost.query.filter(
        JobPost.latitude.isnot(None),
        JobPost.longitude.isnot(None)
    ).all()

    job_locations = [
        {'title': job.title, 'lat': job.latitude, 'company': job.company,
         'salary': job.salary, 'lng': job.longitude}
        for job in jobs
    ]

    return jsonify({'jobs': job_locations})

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