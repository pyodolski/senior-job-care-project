import requests
from app import db
from models import JobPost, User
from config import Config
from datetime import datetime
import xml.etree.ElementTree as ET
from utils.address_converter import convert_full_address_to_depths

# API 정보
API_URL_LIST = "http://apis.data.go.kr/B552474/SenuriService/getJobList"
API_URL_DETAIL = "http://apis.data.go.kr/B552474/SenuriService/getJobInfo"  # 상세 API 주소
API_SERVICE_KEY = Config.SENIOR_API_KEY


def get_text(element, tag_name, default=''):
    """XML 요소에서 텍스트를 안전하게 추출"""
    found = element.find(tag_name)
    return found.text if found is not None and found.text else default


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
                'job_detail_desc': get_text(detail_item, 'detCnts')  # 상세 설명 태그
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

        print(f"총 {len(items)}개의 공고 상세 정보를 조회합니다.")

        for item in items:
            job_id = get_text(item, 'jobId')

            # 1. 상세 정보 API 호출 (공고마다 개별 호출)
            detail_data = fetch_job_detail(job_id)

            full_addr = detail_data.get('full_address')
            depth_data = {}
            if full_addr:
                # 카카오 REST API를 호출하여 주소를 시/도/군/구로 분해
                depth_data = convert_full_address_to_depths(full_addr)
                #  변환 결과 디버깅
                if not depth_data:
                    print(f"*** 주소 변환 실패! (입력 주소: {full_addr}) ***")
                else:
                    print(
                        f"*** 주소 변환 성공: {depth_data.get('region_1depth_name')} {depth_data.get('region_2depth_name')} ***")

            # 2. 데이터 매핑
            job_data = {
                'title': get_text(item, 'recrtTitle'),
                'company': get_text(item, 'oranNm'),
                'recruitment_type': get_text(item, 'emplymShpNm'),
                'application_method': get_text(item, 'acptMthd'),
                'region': get_text(item, 'workPlcNm'),
                'recruitment_start_date': datetime.strptime(get_text(item, 'frDd'), '%Y%m%d').date() if get_text(item,
                                                                                                                 'frDd') else None,
                'recruitment_end_date': datetime.strptime(get_text(item, 'toDd'), '%Y%m%d').date() if get_text(item,
                                                                                                               'toDd') else None,

                # 3. 상세 정보 필드 병합
                'description': detail_data.get(
                    'job_detail_desc') or f"직종: {get_text(item, 'jobclsNm')}\n\n상세 설명은 기관에 문의해주세요.",
                'full_address': detail_data.get('full_address'),
                'homepage_url': detail_data.get('homepage_url'),
                'contact_phone': detail_data.get('contact_phone'),
                'contact_name': detail_data.get('contact_name'),

                'region_1depth_name': depth_data.get('region_1depth_name'),
                'region_2depth_name': depth_data.get('region_2depth_name'),
                'region_3depth_name': depth_data.get('region_3depth_name'),

                'author_id': system_user.id,
                'source': 'K-Senior',
                'external_id': job_id
            }

            if not job_data['external_id']: continue

            existing_job = JobPost.query.filter_by(external_id=job_data['external_id']).first()

            if existing_job:
                for key, value in job_data.items():
                    setattr(existing_job, key, value)
                updated_jobs_count += 1
            else:
                new_job = JobPost(**job_data)
                db.session.add(new_job)
                new_jobs_count += 1

        db.session.commit()
        print(f"✅ 성공: {new_jobs_count}개 신규 추가, {updated_jobs_count}개 업데이트 완료. (상세 정보 포함)")

    except requests.exceptions.RequestException as e:
        print(f"❌ API 호출 중 네트워크 오류 발생: {e}")
    except ET.ParseError as e:
        print(f"❌ XML 파싱 오류 발생: 서버로부터 유효한 XML을 받지 못했습니다. {e}")
    except Exception as e:
        db.session.rollback()
        print(f"❌ 데이터 처리 중 오류 발생: {e}")

