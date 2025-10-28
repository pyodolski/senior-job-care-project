"""
기존 공고의 주소를 위도/경도로 변환하는 스크립트
"""
import os
import requests
from app import app, db
from models import JobPost

KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY')

def geocode_address(address):
    """주소를 위도/경도로 변환"""
    if not address or not KAKAO_REST_API_KEY:
        return None
    
    try:
        url = "https://dapi.kakao.com/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
        params = {"query": address}
        
        response = requests.get(url, headers=headers, params=params, timeout=5)
        
        if response.status_code != 200:
            print(f"  ❌ API 오류: {response.status_code}")
            return None
        
        data = response.json()
        
        if data.get('documents'):
            doc = data['documents'][0]
            result = {
                'latitude': float(doc.get('y', 0)),
                'longitude': float(doc.get('x', 0)),
                'region_1depth': doc.get('address', {}).get('region_1depth_name', ''),
                'region_2depth': doc.get('address', {}).get('region_2depth_name', ''),
                'region_3depth': doc.get('address', {}).get('region_3depth_name', ''),
            }
            return result
        return None
    except Exception as e:
        print(f"  ❌ 오류: {e}")
        return None

def update_all_coordinates():
    """위도/경도가 없는 모든 공고 업데이트"""
    with app.app_context():
        # 주소는 있지만 위도/경도가 없는 공고 조회
        jobs = JobPost.query.filter(
            JobPost.full_address.isnot(None),
            JobPost.latitude.is_(None)
        ).all()
        
        print(f"📍 총 {len(jobs)}개의 공고 주소를 변환합니다...")
        
        success_count = 0
        fail_count = 0
        
        for i, job in enumerate(jobs, 1):
            print(f"\n[{i}/{len(jobs)}] {job.title[:30]}...")
            print(f"  주소: {job.full_address[:50]}...")
            
            geo_data = geocode_address(job.full_address)
            
            if geo_data:
                job.latitude = geo_data['latitude']
                job.longitude = geo_data['longitude']
                job.region_1depth_name = geo_data['region_1depth']
                job.region_2depth_name = geo_data['region_2depth']
                job.region_3depth_name = geo_data['region_3depth']
                
                db.session.commit()
                print(f"  ✅ 성공: ({geo_data['latitude']}, {geo_data['longitude']})")
                success_count += 1
            else:
                print(f"  ❌ 실패")
                fail_count += 1
        
        print(f"\n{'='*50}")
        print(f"✅ 완료: {success_count}개 성공, {fail_count}개 실패")

if __name__ == '__main__':
    update_all_coordinates()
