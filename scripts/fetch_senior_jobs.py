import requests
from app import db
from models import JobPost, User
from config import Config
from datetime import datetime
import xml.etree.ElementTree as ET
import os

EMPLOYMENT_TYPE_MAP = {
    'CM0101': '정규직',
    'CM0102': '계약직',
    'CM0103': '시간제일자리',
    'CM0104': '일당직',
    'CM0105': '기타',
}

APPLICATION_METHOD_MAP = {
    'CM0801': '온라인',
    'CM0802': '이메일',
    'CM0803': '팩스',
    'CM0804': '방문',
}


# API 정보
API_URL_LIST = "http://apis.data.go.kr/B552474/SenuriService/getJobList"
API_URL_DETAIL = "http://apis.data.go.kr/B552474/SenuriService/getJobInfo"  # 상세 API 주소
API_SERVICE_KEY = Config.SENIOR_API_KEY

# 카카오 지도 API 정보
KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY')


def get_text(element, tag_name, default=''):
    """XML 요소에서 텍스트를 안전하게 추출"""
    found = element.find(tag_name)
    return found.text if found is not None and found.text else default


def geocode_address(address):
    """카카오 지도 API를 사용하여 주소를 위도/경도로 변환"""
    if not address or not KAKAO_REST_API_KEY:
        if not KAKAO_REST_API_KEY:
            print("  ⚠️ KAKAO_REST_API_KEY가 설정되지 않았습니다. 주소 변환을 건너뜁니다.")
        return None
    
    # 우편번호 제거 (앞의 5자리 숫자 + 공백)
    import re
    clean_address = re.sub(r'^\d{5}\s+', '', address.strip())
    
    print(f"  🔍 주소 변환 시도: {clean_address[:40]}...")
    
    try:
        # 먼저 주소 검색 API 시도
        url = "https://dapi.kakao.com/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
        params = {"query": clean_address}
        
        response = requests.get(url, headers=headers, params=params, timeout=5)
        
        # 403 오류 시 키워드 검색 API로 재시도
        if response.status_code == 403:
            print(f"  ⚠️ 주소 검색 API 권한 없음. 키워드 검색으로 재시도...")
            url = "https://dapi.kakao.com/v2/local/search/keyword.json"
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            if response.status_code == 403:
                print(f"  ⚠️ 카카오 API 인증 실패 (403): Local API 권한을 활성화하세요.")
                print(f"     https://developers.kakao.com/console/app → 제품 설정 → 지도/로컬")
                return None
        
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('documents'):
            doc = data['documents'][0]
            
            # 좌표 정보
            result = {
                'latitude': float(doc.get('y', 0)),
                'longitude': float(doc.get('x', 0)),
            }
            
            # 주소 정보
            address_info = doc.get('address', {}) if 'address' in doc else doc.get('road_address', {})
            if address_info:
                result['region_1depth'] = address_info.get('region_1depth_name', '')
                result['region_2depth'] = address_info.get('region_2depth_name', '')
                result['region_3depth'] = address_info.get('region_3depth_name', '')
            
            print(f"  ✅ 변환 성공: ({result['latitude']}, {result['longitude']})")
            return result
        else:
            # 검색 결과 없음 - 키워드 검색으로 재시도
            print(f"  ⚠️ 주소 검색 실패, 키워드 검색 재시도...")
            url = "https://dapi.kakao.com/v2/local/search/keyword.json"
            response = requests.get(url, headers=headers, params={"query": clean_address}, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('documents'):
                    doc = data['documents'][0]
                    result = {
                        'latitude': float(doc.get('y', 0)),
                        'longitude': float(doc.get('x', 0)),
                        'region_1depth': doc.get('address_name', '').split()[0] if doc.get('address_name') else '',
                        'region_2depth': doc.get('address_name', '').split()[1] if len(doc.get('address_name', '').split()) > 1 else '',
                        'region_3depth': doc.get('address_name', '').split()[2] if len(doc.get('address_name', '').split()) > 2 else '',
                    }
                    print(f"  ✅ 키워드 검색 성공: ({result['latitude']}, {result['longitude']})")
                    return result
            
            return None
            
    except Exception as e:
        return None


def fetch_job_detail(job_id):
    """특정 jobId의 상세 정보를 조회합니다."""
    params = {
        'serviceKey': API_SERVICE_KEY,
        'id': job_id,  # 상세 조회의 필수 파라미터는 'id' 태그
    }
    try:
        # 상세 정보 조회 시 타임아웃을 넉넉하게 설정 (15초)
        response = requests.get(API_URL_DETAIL, params=params, timeout=15)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        detail_item = root.find('.//item')

        if detail_item is not None:
            # 상세 정보에서 필요한 값 추출
            return {
                'homepage_url': get_text(detail_item, 'homepage'),
                'full_address': get_text(detail_item, 'plDetAddr'),
                'contact_phone': get_text(detail_item, 'clerkContt'),
                'contact_name': get_text(detail_item, 'clerk'),
                'job_detail_desc': get_text(detail_item, 'detCnts'),  # 상세 설명 태그
                'application_code': get_text(detail_item, 'acptMthdCd')
            }
        return {}

    except Exception as e:
        # 상세 API 호출 실패 시 경고만 출력하고 넘어갑니다. (무한루프 방지)
        print(f"⚠️ 상세 정보 조회 실패 (jobId: {job_id}): {e}")
        return {}


def fetch_and_store_jobs(page_number=1):
    """한국노인인력개발원 API에서 공고를 가져와 DB에 저장/업데이트합니다."""

    if not API_SERVICE_KEY:
        print("❌ 오류: .env 파일에 SENIOR_API_KEY가 설정되지 않았습니다.")
        return
    
    # 카카오 API 키 확인
    if not KAKAO_REST_API_KEY:
        print("⚠️ 경고: KAKAO_REST_API_KEY가 설정되지 않았습니다.")
        print("   주소를 위도/경도로 변환할 수 없어 지도에 표시되지 않습니다.")
        print("   https://developers.kakao.com/console/app 에서 REST API 키를 발급받으세요.")
    else:
        print(f"✓ 카카오 REST API 키 확인: {KAKAO_REST_API_KEY[:10]}...")

    params = {
        'serviceKey': API_SERVICE_KEY,
        'pageNo': str(page_number),
        'numOfRows': '100',
    }

    try:
        print(">> 목록 조회 API 서버에 요청 중...")
        response = requests.get(API_URL_LIST, params=params, timeout=15)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        items = root.findall('.//item')

        if not items:
            print("INFO: API로부터 가져올 새로운 공고가 없습니다.")
            return

        # 시스템 계정 확인/생성
        system_user = User.query.filter_by(username="k_senior_admin").first()
        if not system_user:
            system_user = User(username="k_senior_admin", nickname="노인일자리여기", user_type=1, is_verified=True)
            db.session.add(system_user)
            db.session.commit()

        new_jobs_count = 0
        updated_jobs_count = 0
        ai_analyzed_count = 0
        skipped_jobs_count = 0
        AI_ANALYSIS_LIMIT = 100  # AI 분석 제한 (토큰 절약)

        today = datetime.now().date()

        print(f"총 {len(items)}개의 공고 상세 정보를 조회합니다.")
        print(f"⚠️  AI 분석은 상위 {AI_ANALYSIS_LIMIT}개만 수행합니다.")
        print(f"(오늘 날짜: {today} / 마감일이 지난 공고는 건너뜁니다)")

        for idx, item in enumerate(items, 1):
            job_id = get_text(item, 'jobId')

            end_date_str = get_text(item, 'toDd')
            recruitment_end_date_obj = None

            if end_date_str:
                try:
                    recruitment_end_date_obj = datetime.strptime(end_date_str, '%Y%m%d').date()
                    # 마감일이 오늘보다 이전이면 건너뜀
                    if recruitment_end_date_obj < today:
                        print(f"  ⏭️  공고 건너뜀 (ID: {job_id}): 마감일({recruitment_end_date_obj})이 지났습니다.")
                        skipped_jobs_count += 1
                        continue
                except ValueError:
                    # 날짜 형식이 잘못된 경우
                    print(f"  ⚠️  마감일 형식 오류 (ID: {job_id}): {end_date_str}. 일단 처리합니다.")

            # 1. 상세 정보 API 호출 (공고마다 개별 호출)
            detail_data = fetch_job_detail(job_id)

            employment_code = get_text(item, 'emplymShp')
            application_code = detail_data.get('application_code')

            recruitment_type_korean = EMPLOYMENT_TYPE_MAP.get(employment_code, '기타')
            application_method_korean = APPLICATION_METHOD_MAP.get(application_code, '기타')


            # 2. 데이터 매핑
            full_address = detail_data.get('full_address')
            
            # 디버깅: 주소 확인
            if full_address:
                print(f"  🏠 주소 발견: {full_address[:50]}...")
            
            # 3. 주소를 위도/경도로 변환
            geo_data = None
            if full_address:
                geo_data = geocode_address(full_address)
            else:
                print(f"  ⚠️ 주소 없음 (jobId: {job_id})")
            
            job_data = {
                'title': get_text(item, 'recrtTitle'),
                'company': get_text(item, 'oranNm'),
                'recruitment_type': recruitment_type_korean,  # 변환된 값 사용
                'application_method': application_method_korean,
                'region': get_text(item, 'workPlcNm'),
                'recruitment_start_date': datetime.strptime(get_text(item, 'frDd'), '%Y%m%d').date() if get_text(item,
                                                                                                                 'frDd') else None,
                'recruitment_end_date': recruitment_end_date_obj,

                # 4. 상세 정보 필드 병합
                'description': detail_data.get(
                    'job_detail_desc') or f"직종: {get_text(item, 'jobclsNm')}\n\n상세 설명은 기관에 문의해주세요.",
                'full_address': full_address,
                'homepage_url': detail_data.get('homepage_url'),
                'contact_phone': detail_data.get('contact_phone'),
                'contact_name': detail_data.get('contact_name'),

                'region_1depth_name': '',
                'region_2depth_name': '',
                'region_3depth_name': '',

                'author_id': system_user.id,
                'source': 'K-Senior',
                'external_id': job_id
            }
            
            # 5. 위도/경도 정보 추가
            if geo_data:
                job_data['latitude'] = geo_data['latitude']
                job_data['longitude'] = geo_data['longitude']
                job_data['region_1depth_name'] = geo_data.get('region_1depth', '')
                job_data['region_2depth_name'] = geo_data.get('region_2depth', '')
                job_data['region_3depth_name'] = geo_data.get('region_3depth', '')

            if not job_data['external_id']: continue

            existing_job = JobPost.query.filter_by(external_id=job_data['external_id']).first()

            if existing_job:
                for key, value in job_data.items():
                    setattr(existing_job, key, value)
                updated_jobs_count += 1
                job_to_analyze = existing_job
            else:
                new_job = JobPost(**job_data)
                db.session.add(new_job)
                new_jobs_count += 1
                job_to_analyze = new_job

            # DB에 먼저 저장 (ID 생성을 위해)
            db.session.flush()

            # AI 자동 분석 (상위 5개만)
            if ai_analyzed_count < AI_ANALYSIS_LIMIT:
                try:
                    from services.ai_analyzer_service import AIAnalyzerService
                    import json
                    
                    print(f"  🤖 AI 분석 중... ({ai_analyzed_count + 1}/{AI_ANALYSIS_LIMIT})")
                    
                    result = AIAnalyzerService.analyze_job_post(
                        title=job_to_analyze.title,
                        description=job_to_analyze.description,
                        company=job_to_analyze.company
                    )
                    
                    job_to_analyze.ai_category = result['category']
                    job_to_analyze.ai_keywords = json.dumps(result['keywords'], ensure_ascii=False)
                    job_to_analyze.ai_skills = json.dumps(result['skills'], ensure_ascii=False)
                    job_to_analyze.ai_summary = result['summary']
                    job_to_analyze.ai_difficulty = result['difficulty']
                    job_to_analyze.ai_analyzed_at = datetime.now()
                    
                    ai_analyzed_count += 1
                    print(f"  ✅ AI 분석 완료: {result['category']} - {', '.join(result['keywords'][:3])}")
                except Exception as e:
                    print(f"  ⚠️ AI 분석 실패: {e}")
            else:
                print(f"  ⏭️  AI 분석 건너뜀 (제한: {AI_ANALYSIS_LIMIT}개)")

        db.session.commit()
        print(f"\n{'='*60}")
        print(f"✅ 성공: {new_jobs_count}개 신규 추가, {updated_jobs_count}개 업데이트 완료")
        print(f"🤖 AI 분석: {ai_analyzed_count}개 완료 (제한: {AI_ANALYSIS_LIMIT}개)")
        print(f"{'='*60}")

    except requests.exceptions.RequestException as e:
        print(f"❌ API 호출 중 네트워크 오류 발생: {e}")
    except ET.ParseError as e:
        print(f"❌ XML 파싱 오류 발생: 서버로부터 유효한 XML을 받지 못했습니다. {e}")
    except Exception as e:
        db.session.rollback()
        print(f"❌ 데이터 처리 중 오류 발생: {e}")

