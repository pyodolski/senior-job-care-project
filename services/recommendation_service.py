"""AI 기반 맞춤 추천 서비스"""
import json
from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt
from models import db, JobPost, Resume, JobBookmark, JobApplication, User
from services.ai_analyzer_service import AIAnalyzerService


class RecommendationService:
    """사용자 맞춤 공고 추천 서비스"""
    
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """두 지점 간의 거리 계산 """
        if not all([lat1, lon1, lat2, lon2]):
            return float('inf')
        
        # 지구 반지름 (km)
        R = 6371
        
        # 라디안으로 변환
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine 공식
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return R * c
    
    @staticmethod
    def get_user_location(user):
        """사용자 위치 정보 가져오기"""
        return None, None  # lat, lng
    
    @staticmethod
    def calculate_location_score(user, job, max_distance=50):
        """위치 기반 점수 계산 (0-30점)"""
        # 같은 시/도면 기본 점수
        score = 0
        
        if user.sido and job.region_1depth_name:
            if user.sido == job.region_1depth_name:
                score += 10
                
                # 같은 시/군/구면 추가 점수
                if user.sigungu and job.region_2depth_name:
                    if user.sigungu == job.region_2depth_name:
                        score += 10
                        
                        # 같은 동이면 최대 점수
                        if user.dong and job.region_3depth_name:
                            if user.dong == job.region_3depth_name:
                                score += 10
        
        return min(score, 30.0)
    
    @staticmethod
    def calculate_category_score(resume, job):
        """카테고리 매칭 점수 (0-25점) """
        score = 0
        
        # 이력서 희망 직종과 공고 카테고리 매칭
        if resume.desired_categories and (job.job_category or job.people_category or job.ai_category):
            desired = resume.desired_categories.lower()
            job_cat = (job.job_category or job.people_category or job.ai_category or '').lower()
            
            if job_cat in desired or desired in job_cat:
                score += 15
        
        # AI 키워드 매칭
        if resume.ai_keywords and job.ai_keywords:
            try:
                resume_kw = json.loads(resume.ai_keywords) if isinstance(resume.ai_keywords, str) else resume.ai_keywords
                job_kw = json.loads(job.ai_keywords) if isinstance(job.ai_keywords, str) else job.ai_keywords
                
                similarity = AIAnalyzerService.calculate_similarity(
                    job_kw, 
                    json.loads(job.ai_skills) if job.ai_skills else [],
                    resume_kw,
                    json.loads(resume.ai_skills) if resume.ai_skills else []
                )
                
                score += (similarity / 100) * 10
            except:
                pass
        
        return min(score, 25.0)
    
    @staticmethod
    def calculate_work_condition_score(resume, job):
        """근무 조건 매칭 점수 (0-20점)"""
        score = 0
        
        # 근무 요일 매칭 (10점)
        resume_days = [
            resume.work_monday, resume.work_tuesday, resume.work_wednesday,
            resume.work_thursday, resume.work_friday, resume.work_saturday, resume.work_sunday
        ]
        job_days = [
            job.work_monday, job.work_tuesday, job.work_wednesday,
            job.work_thursday, job.work_friday, job.work_saturday, job.work_sunday
        ]
        
        if any(resume_days) and any(job_days):
            matching_days = sum(1 for r, j in zip(resume_days, job_days) if r and j)
            total_job_days = sum(job_days)
            if total_job_days > 0:
                score += (matching_days / total_job_days) * 10
        
        # 근무 시간 매칭 (10점)
        if resume.is_time_negotiable:
            score += 10  # 시간 협의 가능하면 만점
        elif resume.desired_start_time and resume.desired_end_time and job.work_start_time and job.work_end_time:
            # 시간대가 겹치는지 확인
            if (resume.desired_start_time <= job.work_start_time <= resume.desired_end_time or
                resume.desired_start_time <= job.work_end_time <= resume.desired_end_time):
                score += 10
        
        return min(score, 20.0)
    
    @staticmethod
    def calculate_behavior_score(user_id, job):
        """사용자 행동 패턴 기반 점수 (0-15점)"""
        score = 0
        
        # 찜한 공고와 유사한지 확인
        bookmarked_jobs = db.session.query(JobPost).join(
            JobBookmark, JobBookmark.job_id == JobPost.id
        ).filter(JobBookmark.user_id == user_id).limit(10).all()
        
        if bookmarked_jobs:
            # 찜한 공고들의 카테고리와 비교
            for bj in bookmarked_jobs:
                if bj.job_category == job.job_category or bj.people_category == job.people_category:
                    score += 3
                    break
            
            # AI 키워드 유사도
            if job.ai_keywords:
                try:
                    job_kw = json.loads(job.ai_keywords) if isinstance(job.ai_keywords, str) else job.ai_keywords
                    for bj in bookmarked_jobs:
                        if bj.ai_keywords:
                            bj_kw = json.loads(bj.ai_keywords) if isinstance(bj.ai_keywords, str) else bj.ai_keywords
                            common = set(job_kw) & set(bj_kw)
                            if common:
                                score += len(common) * 2
                                break
                except:
                    pass
        
        # 지원한 공고와 유사한지 확인
        applied_jobs = db.session.query(JobPost).join(
            JobApplication, JobApplication.job_id == JobPost.id
        ).filter(JobApplication.user_id == user_id).limit(5).all()
        
        if applied_jobs:
            for aj in applied_jobs:
                if aj.job_category == job.job_category or aj.people_category == job.people_category:
                    score += 5
                    break
        
        return min(score, 15.0)
    
    @staticmethod
    def calculate_popularity_score(job):
        """인기도 점수 (0-5점)"""
        # 조회수, 지원수, 찜 수를 종합
        view_score = min(job.view_count / 100, 2)
        app_score = min(job.application_count / 10, 2)
        bookmark_score = min(job.bookmark_count / 10, 1)
        
        return view_score + app_score + bookmark_score
    
    @staticmethod
    def calculate_recency_score(job):
        """최신도 점수 (0-5점)"""
        if not job.created_at:
            return 0
        
        days_old = (datetime.now() - job.created_at.replace(tzinfo=None)).days
        
        if days_old <= 1:
            return 5.0
        elif days_old <= 3:
            return 4.0
        elif days_old <= 7:
            return 3.0
        elif days_old <= 14:
            return 2.0
        elif days_old <= 30:
            return 1.0
        else:
            return 0.5
    
    @staticmethod
    def get_recommendations(user_id, limit=20):
        """사용자 맞춤 추천 공고 가져오기"""
        user = User.query.get(user_id)
        if not user:
            return []
        
        # 이력서 확인
        resume = Resume.query.filter_by(user_id=user_id).first()
        if not resume:
            # 이력서 없으면 인기 공고 반환
            jobs = JobPost.query.order_by(
                JobPost.view_count.desc()
            ).limit(limit).all()
            return [(job, 50.0, ['인기 공고']) for job in jobs]
        
        # 모든 공고 가져오기 (위치 정보 있고 AI 분석된 것만)
        jobs = JobPost.query.filter(
            JobPost.latitude.isnot(None),
            JobPost.longitude.isnot(None),
            JobPost.ai_analyzed_at.isnot(None)  # AI 분석된 공고만
        ).all()
        
        # 각 공고에 대해 점수 계산
        scored_jobs = []
        for job in jobs:
            # 이미 지원한 공고는 제외
            if JobApplication.query.filter_by(user_id=user_id, job_id=job.id).first():
                continue
            
            # 점수 계산
            location_score = RecommendationService.calculate_location_score(user, job)
            category_score = RecommendationService.calculate_category_score(resume, job)
            work_score = RecommendationService.calculate_work_condition_score(resume, job)
            behavior_score = RecommendationService.calculate_behavior_score(user_id, job)
            popularity_score = RecommendationService.calculate_popularity_score(job)
            recency_score = RecommendationService.calculate_recency_score(job)
            
            total_score = (
                location_score +      # 30점
                category_score +      # 25점
                work_score +          # 20점
                behavior_score +      # 15점
                popularity_score +    # 5점
                recency_score         # 5점
            )  # 총 100점
            
            # 추천 이유
            reasons = []
            if location_score >= 20:
                reasons.append('🏠 집에서 가까워요')
            if category_score >= 15:
                reasons.append('💼 희망 직종과 맞아요')
            if work_score >= 15:
                reasons.append('⏰ 근무 조건이 맞아요')
            if behavior_score >= 10:
                reasons.append('❤️ 관심 있는 분야예요')
            if popularity_score >= 3:
                reasons.append('🔥 인기 공고예요')
            if recency_score >= 4:
                reasons.append('🆕 새로운 공고예요')
            
            if not reasons:
                reasons.append('추천 공고')
            
            scored_jobs.append((job, total_score, reasons))
        
        # 점수 순으로 정렬
        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        
        return scored_jobs[:limit]
