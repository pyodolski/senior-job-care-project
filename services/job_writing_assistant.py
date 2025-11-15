"""채용 공고 AI 글쓰기 도우미"""

import re
import json
from typing import Dict, List, Optional
from datetime import datetime

class JobWritingAssistant:
    
    def __init__(self):
        # 차별 표현 필터링 키워드
        self.discriminatory_keywords = {
            '나이': ['젊은', '청년', '20대', '30대', '40대', '50대', '60대', '나이', '연령'],
            '성별': ['남자', '여자', '남성', '여성', '미혼', '기혼', '미스', '미세스'],
            '외모': ['키', '몸무게', '외모', '미모', '잘생긴', '예쁜', '날씬한'],
            '출신': ['지역', '학벌', '출신대', '명문대', '지방대']
        }
        
        # 시니어 친화 대체 문구
        self.senior_friendly_replacements = {
            '체력이 좋은': '건강하신',
            '빠른 업무': '꼼꼼한 업무',
            '신속한': '정확한',
            '젊은 감각': '풍부한 경험',
            '트렌디한': '안정적인'
        }
        
        # 급여 단위 매핑
        self.pay_units = {
            'hourly': '시급',
            'daily': '일급', 
            'monthly': '월급',
            'yearly': '연봉',
            'negotiable': '협의'
        }

    def generate_job_description(self, job_data: Dict) -> Dict:
        """채용 공고 상세 설명 생성"""
        try:
            # 입력 데이터 검증
            validated_data = self._validate_input(job_data)
            
            # 공고 타입에 따른 다른 처리
            job_type = validated_data.get('job_type', 'company')
            
            if job_type == 'general':
                # 일반 공고용 생성
                title = self._generate_general_title(validated_data)
                summary = self._generate_general_summary(validated_data)
                description = self._generate_general_description(validated_data)
                hashtags = self._generate_general_hashtags(validated_data)
            else:
                # 기업 공고용 생성 (기존)
                title = self._generate_title(validated_data)
                summary = self._generate_summary(validated_data)
                description = self._generate_detailed_description(validated_data)
                hashtags = self._generate_hashtags(validated_data)
            
            # 차별 표현 필터링
            filtered_content = self._apply_discrimination_filter({
                'title': title,
                'summary': summary,
                'description': description,
                'hashtags': hashtags
            })
            
            return {
                'success': True,
                'content': filtered_content,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'senior_friendly': validated_data.get('senior_friendly', False),
                    'tone': validated_data.get('tone', '친절'),
                    'word_count': len(filtered_content['description'])
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'fallback_template': self._generate_fallback_template(job_data)
            }

    def _validate_input(self, job_data: Dict) -> Dict:
        """입력 데이터 검증 및 정규화"""
        validated = {}
        
        # 필수 필드 검증
        required_fields = ['title', 'employment_type', 'location', 'duties']
        for field in required_fields:
            if not job_data.get(field):
                raise ValueError(f"필수 필드 누락: {field}")
            validated[field] = job_data[field].strip()
        
        # 급여 정보 검증
        pay_info = job_data.get('pay', {})
        if pay_info:
            validated['pay'] = self._validate_pay_info(pay_info)
        
        # 근무 시간 검증
        schedule = job_data.get('schedule', {})
        if schedule:
            validated['schedule'] = self._validate_schedule(schedule)
        
        # 선택 필드
        optional_fields = ['requirements', 'benefits', 'apply', 'deadline', 'senior_friendly', 'tone']
        for field in optional_fields:
            if job_data.get(field):
                validated[field] = job_data[field]
        
        return validated

    def _validate_pay_info(self, pay_info: Dict) -> Dict:
        """급여 정보 검증"""
        validated_pay = {}
        
        pay_type = pay_info.get('type', 'negotiable')
        if pay_type not in self.pay_units:
            pay_type = 'negotiable'
        validated_pay['type'] = pay_type
        
        amount = pay_info.get('amount')
        if amount and isinstance(amount, (int, float)) and amount > 0:
            validated_pay['amount'] = int(amount)
        
        validated_pay['currency'] = pay_info.get('currency', 'KRW')
        
        return validated_pay

    def _validate_schedule(self, schedule: Dict) -> Dict:
        """근무 시간 검증"""
        validated_schedule = {}
        
        # 근무 요일
        if schedule.get('days'):
            validated_schedule['days'] = schedule['days']
        
        # 시간 형식 검증 (HH:MM)
        time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
        
        for time_field in ['start', 'end']:
            time_value = schedule.get(time_field)
            if time_value and time_pattern.match(time_value):
                validated_schedule[time_field] = time_value
        
        return validated_schedule

    def _generate_title(self, job_data: Dict) -> str:
        """채용 공고 제목 생성"""
        location = job_data.get('location', '').split()[0]  # 첫 번째 지역명만
        title = job_data['title']
        employment_type = job_data['employment_type']
        
        pay_info = job_data.get('pay', {})
        pay_text = ""
        if pay_info.get('amount') and pay_info.get('type') != 'negotiable':
            pay_unit = self.pay_units.get(pay_info['type'], '')
            amount = f"{pay_info['amount']:,}"
            pay_text = f"({pay_unit} {amount}원)"
        
        if location:
            return f"[{location}] {title} {employment_type}{pay_text}"
        else:
            return f"{title} {employment_type}{pay_text}"

    def _generate_summary(self, job_data: Dict) -> str:
        """핵심 요약 3줄 생성"""
        lines = []
        
        # 주요 업무
        duties = job_data['duties'][:50] + "..." if len(job_data['duties']) > 50 else job_data['duties']
        lines.append(f"업무내용: {duties}")
        
        # 근무 조건
        schedule_parts = []
        schedule = job_data.get('schedule', {})
        if schedule.get('days'):
            schedule_parts.append(schedule['days'])
        if schedule.get('start') and schedule.get('end'):
            schedule_parts.append(f"{schedule['start']}~{schedule['end']}")
        
        pay_info = job_data.get('pay', {})
        if pay_info.get('amount'):
            pay_unit = self.pay_units.get(pay_info['type'], '')
            amount = f"{pay_info['amount']:,}"
            schedule_parts.append(f"{pay_unit} {amount}원")
        
        if schedule_parts:
            lines.append("근무조건: " + " / ".join(schedule_parts))
        
        # 자격요건 및 혜택
        requirements_parts = []
        if job_data.get('requirements'):
            requirements_parts.append(job_data['requirements'])
        
        if job_data.get('training_provided'):
            requirements_parts.append("교육제공")
        
        if job_data.get('benefits'):
            benefits = job_data['benefits'][:30] + "..." if len(job_data['benefits']) > 30 else job_data['benefits']
            requirements_parts.append(benefits)
        
        if requirements_parts:
            lines.append("자격요건: " + " / ".join(requirements_parts))
        else:
            lines.append("자격요건: 성실하고 책임감 있는 분")
        
        return "\n".join(lines)

    def _generate_detailed_description(self, job_data: Dict) -> str:
        """상세 본문 생성"""
        sections = []
        
        # 주요업무
        sections.append(f"주요업무: {job_data['duties']}")
        
        # 근무조건
        conditions = []
        conditions.append(f"고용형태: {job_data['employment_type']}")
        conditions.append(f"근무지: {job_data['location']}")
        
        schedule = job_data.get('schedule', {})
        if schedule.get('days'):
            conditions.append(f"근무요일: {schedule['days']}")
        if schedule.get('start') and schedule.get('end'):
            conditions.append(f"근무시간: {schedule['start']}~{schedule['end']}")
        
        pay_info = job_data.get('pay', {})
        if pay_info.get('amount'):
            pay_unit = self.pay_units.get(pay_info['type'], '')
            amount = f"{pay_info['amount']:,}"
            conditions.append(f"급여: {pay_unit} {amount}원")
        elif pay_info.get('type') == 'negotiable':
            conditions.append("급여: 면접 시 협의")
        
        sections.append("근무조건:\n" + "\n".join([f"• {cond}" for cond in conditions]))
        
        # 자격요건
        requirements_list = []
        if job_data.get('requirements'):
            requirements_list.append(job_data['requirements'])
        
        if job_data.get('training_provided'):
            requirements_list.append("경력무관 (교육제공)")
        
        if requirements_list:
            sections.append("자격요건:\n" + "\n".join([f"• {req}" for req in requirements_list]))
        
        # 복리후생 섹션
        benefits_list = []
        if job_data.get('benefits'):
            benefits_list.append(job_data['benefits'])
        
        if job_data.get('training_provided'):
            benefits_list.append("체계적인 업무 교육")
        
        if job_data.get('flexible_time'):
            benefits_list.append("근무시간 조정 가능")
        
        if benefits_list:
            sections.append("복리후생:\n" + "\n".join([f"• {benefit}" for benefit in benefits_list]))
        
        # 지원방법
        apply_info = job_data.get('apply', '플랫폼 내 지원')
        deadline = job_data.get('deadline', '채용 시 마감')
        sections.append(f"지원방법: {apply_info}")
        sections.append(f"마감일: {deadline}")
        
        return "\n\n".join(sections)

    def _generate_hashtags(self, job_data: Dict) -> List[str]:
        """해시태그 생성"""
        hashtags = []
        
        # 직무 관련
        title_words = job_data['title'].split()
        for word in title_words:
            if len(word) > 1:
                hashtags.append(f"#{word}")
        
        # 고용형태
        hashtags.append(f"#{job_data['employment_type']}")
        
        # 지역
        location_parts = job_data['location'].split()
        for part in location_parts[:2]:
            if len(part) > 1:
                hashtags.append(f"#{part}")
        
        # 추가 옵션
        if job_data.get('training_provided'):
            hashtags.append("#교육제공")
        
        if job_data.get('flexible_time'):
            hashtags.append("#시간조정가능")
        
        # 중복 제거 및 최대 5개로 제한
        unique_hashtags = list(dict.fromkeys(hashtags))[:5]
        return unique_hashtags

    def _apply_discrimination_filter(self, content: Dict) -> Dict:
        """차별 표현 필터링"""
        filtered_content = {}
        
        for key, text in content.items():
            if isinstance(text, str):
                filtered_text = text
                
                # 차별적 키워드 제거/대체
                for category, keywords in self.discriminatory_keywords.items():
                    for keyword in keywords:
                        if keyword in filtered_text:
                            # 맥락에 따른 대체
                            if category == '나이':
                                filtered_text = re.sub(rf'\b{keyword}\b.*?[우선|선호|환영]', '경력무관', filtered_text)
                            elif category == '성별':
                                filtered_text = re.sub(rf'\b{keyword}\b.*?[우선|선호|환영]', '성별무관', filtered_text)
                
                # 시니어 친화 표현으로 대체
                for old_phrase, new_phrase in self.senior_friendly_replacements.items():
                    filtered_text = filtered_text.replace(old_phrase, new_phrase)
                
                filtered_content[key] = filtered_text
            elif isinstance(text, list):
                filtered_content[key] = text
        
        return filtered_content

    def _generate_general_title(self, job_data: Dict) -> str:
        """일반 공고용 제목 생성 (시니어 친화적)"""
        location = job_data.get('location', '').split()[0] if job_data.get('location') else ''
        title = job_data['title']
        employment_type = job_data['employment_type']
        
        # 급여 정보 처리
        pay_info = job_data.get('pay', {})
        pay_text = ""
        if pay_info.get('amount') and pay_info.get('type') != 'negotiable':
            pay_unit = self.pay_units.get(pay_info['type'], '')
            amount = f"{pay_info['amount']:,}"
            pay_text = f" ({pay_unit} {amount}원)"
        elif job_data.get('salary'):
            pay_text = f" ({job_data['salary']})"
        
        # 시니어 친화적 표현 추가
        senior_text = ""
        if job_data.get('senior_friendly'):
            if job_data.get('easy_work'):
                senior_text = " - 쉬운 업무"
            elif job_data.get('training_provided'):
                senior_text = " - 교육 제공"
            else:
                senior_text = " - 시니어 환영"
        
        # 제목 조합
        if location:
            base_title = f"[{location}] {title} {employment_type}"
        else:
            base_title = f"{title} {employment_type}"
        
        return f"{base_title}{pay_text}{senior_text}"

    def _generate_general_summary(self, job_data: Dict) -> str:
        """일반 공고용 핵심 요약 (깔끔하고 전문적으로)"""
        lines = []
        
        # 업무 소개
        duties = job_data['duties']
        lines.append(f"업무내용: {duties}")
        
        # 근무 조건 정보
        schedule_parts = []
        
        # 근무 요일 정보
        schedule = job_data.get('schedule', {})
        if schedule.get('days'):
            schedule_parts.append(f"{schedule['days']}")
        elif job_data.get('work_days'):
            schedule_parts.append(f"{job_data['work_days']}")
        
        # 근무 시간 정보
        if schedule.get('start') and schedule.get('end'):
            schedule_parts.append(f"{schedule['start']}~{schedule['end']}")
        elif schedule.get('time'):
            schedule_parts.append(f"{schedule['time']}")
        elif job_data.get('work_time'):
            schedule_parts.append(f"{job_data['work_time']}")
        
        # 급여 정보
        pay_info = job_data.get('pay', {})
        if pay_info.get('amount'):
            pay_unit = self.pay_units.get(pay_info['type'], '')
            amount = f"{pay_info['amount']:,}"
            schedule_parts.append(f"{pay_unit} {amount}원")
        elif job_data.get('salary'):
            schedule_parts.append(f"{job_data['salary']}")
        
        if schedule_parts:
            lines.append("근무조건: " + " / ".join(schedule_parts))
        
        # 자격요건 및 우대사항
        requirements_parts = []
        if job_data.get('requirements'):
            requirements_parts.append(job_data['requirements'])
        
        if job_data.get('senior_friendly') or job_data.get('training_provided'):
            requirements_parts.append("경력무관")
        
        if job_data.get('training_provided'):
            requirements_parts.append("교육제공")
        
        if requirements_parts:
            lines.append("자격요건: " + " / ".join(requirements_parts))
        else:
            lines.append("자격요건: 성실하고 책임감 있는 분")
        
        return "\n".join(lines)

    def _generate_general_description(self, job_data: Dict) -> str:
        """일반 공고용 상세 설명 (깔끔하고 전문적으로)"""
        sections = []
        
        # 업무 내용
        duties = job_data['duties']
        
        # 업무에 상세한 추가 설명
        additional_info = []
        if any(word in duties for word in ['서빙', '카페', '음료']):
            additional_info.extend([
                "고객 응대 및 서비스 제공",
                "음료 제조 및 매장 관리",
                "기본 교육 제공으로 처음이어도 가능"
            ])
        elif any(word in duties for word in ['계산', '마트', '편의점']):
            additional_info.extend([
                "계산 업무 및 고객 응대",
                "상품 진열 및 매장 정리",
                "POS 시스템 사용법 교육 제공"
            ])
        elif any(word in duties for word in ['청소', '정리']):
            additional_info.extend([
                "시설 청소 및 환경 정리",
                "안전하고 체계적인 작업 환경",
                "개인 페이스에 맞춘 업무 진행"
            ])
        else:
            additional_info.extend([
                "체계적인 업무 교육 제공",
                "안정적인 근무 환경"
            ])
        
        duties_section = f"주요 업무:\n{duties}"
        if additional_info:
            duties_section += "\n" + "\n".join([f"• {info}" for info in additional_info])
        
        sections.append(duties_section)
        
        # 근무 조건
        conditions = []
        conditions.append(f"고용형태: {job_data['employment_type']}")
        conditions.append(f"근무지: {job_data['location']}")
        
        # 근무 시간 정보
        schedule = job_data.get('schedule', {})
        if schedule.get('days'):
            conditions.append(f"근무요일: {schedule['days']}")
        elif job_data.get('work_days'):
            conditions.append(f"근무요일: {job_data['work_days']}")
        
        if schedule.get('start') and schedule.get('end'):
            conditions.append(f"근무시간: {schedule['start']} ~ {schedule['end']}")
        elif schedule.get('time'):
            conditions.append(f"근무시간: {schedule['time']}")
        elif job_data.get('work_time'):
            conditions.append(f"근무시간: {job_data['work_time']}")
        
        # 급여 정보
        pay_info = job_data.get('pay', {})
        if pay_info.get('amount'):
            pay_unit = self.pay_units.get(pay_info['type'], '')
            amount = f"{pay_info['amount']:,}"
            conditions.append(f"급여: {pay_unit} {amount}원")
        elif pay_info.get('type') == 'negotiable':
            conditions.append("급여: 면접 시 협의")
        elif job_data.get('salary'):
            conditions.append(f"급여: {job_data['salary']}")
        
        # 모집 인원 정보
        if job_data.get('recruitment_count'):
            conditions.append(f"모집인원: {job_data['recruitment_count']}명")
        
        sections.append("근무조건:\n" + "\n".join([f"• {cond}" for cond in conditions]))
        
        # 자격요건 및 우대사항
        requirements_list = []
        if job_data.get('requirements'):
            requirements_list.append(job_data['requirements'])
        
        # 기본 자격요건 추가
        requirements_list.extend([
            "성실하고 책임감 있는 분",
            "원활한 의사소통 가능한 분"
        ])
        
        # 경력 관련
        if job_data.get('senior_friendly') or job_data.get('training_provided'):
            requirements_list.append("경력 무관 (신입 환영)")
        
        if requirements_list:
            sections.append("자격요건:\n" + "\n".join([f"• {req}" for req in requirements_list]))
        
        # 복리후생
        benefits_list = []
        if job_data.get('benefits'):
            benefits_list.append(job_data['benefits'])
        
        # 기본 복리후생 추가
        if job_data.get('training_provided'):
            benefits_list.append("체계적인 업무 교육")
        
        if job_data.get('flexible_time'):
            benefits_list.append("근무시간 조정 가능")
        
        # 업무 특성에 따른 추가 혜택
        duties_lower = job_data['duties'].lower()
        if '카페' in duties_lower or '서빙' in duties_lower:
            benefits_list.append("직원 음료 할인")
        elif '마트' in duties_lower or '편의점' in duties_lower:
            benefits_list.append("직원 구매 할인")
        
        if benefits_list:
            sections.append("복리후생:\n" + "\n".join([f"• {benefit}" for benefit in benefits_list]))
        
        # 지원방법
        apply_method = job_data.get('apply', '플랫폼 내 지원')
        deadline = job_data.get('deadline', '채용 시 마감')
        sections.append(f"지원방법: {apply_method}")
        sections.append(f"마감일: {deadline}")
        
        return "\n\n".join(sections)

    def _generate_general_hashtags(self, job_data: Dict) -> List[str]:
        """일반 공고용 해시태그 (깔끔하고 검색 최적화)"""
        hashtags = []
        
        # 직무 관련
        title_words = job_data['title'].split()
        for word in title_words:
            if len(word) > 1:
                hashtags.append(f"#{word}")
        
        # 고용형태
        hashtags.append(f"#{job_data['employment_type']}")
        
        # 지역
        location_parts = job_data['location'].split()
        for part in location_parts[:2]:
            if len(part) > 1:
                hashtags.append(f"#{part}")
        
        # 경력 관련
        if job_data.get('senior_friendly') or job_data.get('training_provided'):
            hashtags.append("#경력무관")
        
        if job_data.get('training_provided'):
            hashtags.append("#교육제공")
        
        if job_data.get('flexible_time'):
            hashtags.append("#시간조정가능")
        
        # 중복 제거 및 최대 5개로 제한
        unique_hashtags = list(dict.fromkeys(hashtags))[:5]
        return unique_hashtags

    def _generate_fallback_template(self, job_data: Dict) -> str:
        """AI 실패 시 기본 템플릿"""
        title = job_data.get('title', '채용공고')
        company = job_data.get('company', '회사명')
        location = job_data.get('location', '근무지')
        
        return f"""
{title} 채용

{company}에서 {title} 직무를 담당하실 분을 모집합니다.

근무지: {location}
고용형태: {job_data.get('employment_type', '정규직')}

많은 지원 바랍니다.
        """.strip()

# 전역 인스턴스
job_assistant = JobWritingAssistant()