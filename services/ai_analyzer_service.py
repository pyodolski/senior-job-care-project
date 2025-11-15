"""AI 기반 공고 및 이력서 분석 서비스"""
import json
import os
from openai import OpenAI
from config import Config

# OpenAI 클라이언트 초기화
client = None
if Config.OPENAI_API_KEY:
    client = OpenAI(api_key=Config.OPENAI_API_KEY)
else:
    print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다. AI 분석 기능이 제한됩니다.")


class AIAnalyzerService:
    """OpenAI를 사용한 공고 및 이력서 분석"""
    
    @staticmethod
    def analyze_job_post(title, description, company=None):
        """공고를 AI로 분석하여 카테고리, 키워드, 스킬, 난이도 추출"""
        # OpenAI 클라이언트가 없으면 기본값 반환
        if not client:
            return {
                'category': '기타',
                'keywords': [],
                'skills': [],
                'summary': title[:50],
                'difficulty': '중급'
            }
        
        try:
            prompt = f"""
다음 일자리 공고를 분석해주세요.

제목: {title}
회사: {company or '정보 없음'}
설명: {description[:500]}

다음 형식의 JSON으로 응답해주세요:
{{
    "category": "카테고리 (예: 의료/복지, 사무직, 서비스직, 생산/기술직, 시설관리, 교육, 운전/배송, 기타)",
    "keywords": ["핵심", "키워드", "3-5개"],
    "skills": ["필요한", "스킬", "3-5개"],
    "summary": "공고를 한 문장으로 요약 (50자 이내)",
    "difficulty": "초급/중급/고급 중 하나"
}}

시니어(노인) 일자리 관점에서 분석해주세요.
"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 시니어 일자리 분석 전문가입니다. JSON 형식으로만 응답하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 파싱
            # 코드 블록 제거
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            
            result = json.loads(content.strip())
            
            return {
                'category': result.get('category', '기타'),
                'keywords': result.get('keywords', []),
                'skills': result.get('skills', []),
                'summary': result.get('summary', title[:50]),
                'difficulty': result.get('difficulty', '중급')
            }
            
        except Exception as e:
            print(f"❌ AI 분석 실패: {e}")
            # 실패 시 기본값 반환
            return {
                'category': '기타',
                'keywords': [],
                'skills': [],
                'summary': title[:50],
                'difficulty': '중급'
            }
    
    @staticmethod
    def analyze_resume(experience, strengths, desired_categories=None):
        """이력서를 AI로 분석하여 키워드, 스킬, 경력 레벨 추출"""
        # OpenAI 클라이언트가 없으면 기본값 반환
        if not client:
            return {
                'keywords': [],
                'skills': [],
                'career_level': '경력'
            }
        
        try:
            prompt = f"""
다음 이력서를 분석해주세요.

경력: {experience or '정보 없음'}
강점: {strengths or '정보 없음'}
희망 직종: {desired_categories or '정보 없음'}

다음 형식의 JSON으로 응답해주세요:
{{
    "keywords": ["핵심", "키워드", "3-5개"],
    "skills": ["보유", "스킬", "3-5개"],
    "career_level": "신입/경력/전문가 중 하나"
}}

시니어(노인) 구직자 관점에서 분석해주세요.
"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 시니어 이력서 분석 전문가입니다. JSON 형식으로만 응답하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 파싱
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            
            result = json.loads(content.strip())
            
            return {
                'keywords': result.get('keywords', []),
                'skills': result.get('skills', []),
                'career_level': result.get('career_level', '경력')
            }
            
        except Exception as e:
            print(f"❌ AI 분석 실패: {e}")
            return {
                'keywords': [],
                'skills': [],
                'career_level': '경력'
            }
    
    @staticmethod
    def calculate_similarity(job_keywords, job_skills, resume_keywords, resume_skills):
        """공고와 이력서의 유사도 계산 (0-100점)"""
        if not job_keywords and not job_skills:
            return 50.0  # 기본 점수
        
        # 키워드 매칭
        job_kw_set = set(kw.lower() for kw in job_keywords)
        resume_kw_set = set(kw.lower() for kw in resume_keywords)
        keyword_match = len(job_kw_set & resume_kw_set) / max(len(job_kw_set), 1) * 100
        
        # 스킬 매칭
        job_skill_set = set(skill.lower() for skill in job_skills)
        resume_skill_set = set(skill.lower() for skill in resume_skills)
        skill_match = len(job_skill_set & resume_skill_set) / max(len(job_skill_set), 1) * 100
        
        # 가중 평균 (키워드 60%, 스킬 40%)
        similarity = keyword_match * 0.6 + skill_match * 0.4
        
        return min(similarity, 100.0)
