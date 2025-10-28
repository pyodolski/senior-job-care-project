# utils/address_converter.py

import requests
from config import Config
import re

# 카카오 REST API 주소 변환 (Geocoding) End Point
KAKAO_GEOCODE_URL = "https://dapi.kakao.com/v2/local/search/address.json"
KAKAO_REST_API_KEY = Config.KAKAO_REST_API_KEY


def convert_full_address_to_depths(full_address):
    """
    전체 주소를 시/도, 시/군/구, 읍/면/동으로 분리하여 반환합니다.
    (카카오맵 REST API 사용)

    Returns:
        dict: 분리된 지역 정보 {region_1depth_name, region_2depth_name, region_3depth_name} 또는 빈 딕셔너리
    """
    if not full_address or not KAKAO_REST_API_KEY:
        return {}


    # 1. 우편번호 제거 (주소 시작 부분의 5자리 숫자와 공백 제거)
    cleaned_address = re.sub(r'^\d{5}\s*', '', full_address)

    # 2. 괄호 안의 상세 정보 제거 (예: (상동, 하이센스빌)) -> 검색 정확도 향상
    cleaned_address = re.sub(r'\s*\(.*\)\s*', ' ', cleaned_address).strip()

    # ▲▲▲ 주소 전처리 완료 ▲▲▲

    headers = {
        "Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"
    }
    params = {
        "query": cleaned_address  # 전처리된 주소를 사용
    }

    try:
        response = requests.get(KAKAO_GEOCODE_URL, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        # 2. 카카오 API에서 검색 결과가 없거나 오류가 있을 때 처리
        if not data.get('documents') or len(data['documents']) == 0:
            print(f"⚠️ 카카오 변환 실패: 검색 결과 없음 (입력 주소: {cleaned_address})")
            if data.get('error'):
                print(f"   API 에러 메시지: {data['error']['message']}")
            return {}

        # 첫 번째 검색 결과의 주소 정보 추출
        address_info = data['documents'][0].get('address')

        if address_info:
            return {
                'region_1depth_name': address_info.get('region_1depth_name'),
                'region_2depth_name': address_info.get('region_2depth_name'),
                'region_3depth_name': address_info.get('region_3depth_name') or address_info.get(
                    'region_3depth_h_name')
            }
        return {}

    except requests.exceptions.RequestException as e:
        print(f"❌ 카카오 API 호출 실패 (네트워크/HTTP 오류): {e}")
        return {}
    except Exception as e:
        print(f"⚠️ 카카오 주소 변환 중 일반 오류: {e}")
        return {}