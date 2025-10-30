-- JobPost에 AI 분석 필드 추가
ALTER TABLE job_post ADD COLUMN ai_category VARCHAR(100);
ALTER TABLE job_post ADD COLUMN ai_keywords TEXT;  -- JSON 배열로 저장
ALTER TABLE job_post ADD COLUMN ai_skills TEXT;    -- JSON 배열로 저장
ALTER TABLE job_post ADD COLUMN ai_summary VARCHAR(500);
ALTER TABLE job_post ADD COLUMN ai_difficulty VARCHAR(20);  -- 초급, 중급, 고급
ALTER TABLE job_post ADD COLUMN ai_analyzed_at TIMESTAMP NULL;

-- Resume에 AI 분석 필드 추가
ALTER TABLE resume ADD COLUMN ai_keywords TEXT;  -- JSON 배열로 저장
ALTER TABLE resume ADD COLUMN ai_skills TEXT;    -- JSON 배열로 저장
ALTER TABLE resume ADD COLUMN ai_career_level VARCHAR(20);  -- 신입, 경력, 전문가
ALTER TABLE resume ADD COLUMN ai_analyzed_at TIMESTAMP NULL;

-- 인덱스 추가 (검색 성능 향상)
CREATE INDEX idx_job_post_ai_category ON job_post(ai_category);
CREATE INDEX idx_job_post_ai_analyzed ON job_post(ai_analyzed_at);
CREATE INDEX idx_resume_ai_analyzed ON resume(ai_analyzed_at);
