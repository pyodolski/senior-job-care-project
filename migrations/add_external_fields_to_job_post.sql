-- JobPost 테이블에 외부 데이터 연동 필드 추가

-- source 컬럼 추가 (데이터 출처)
ALTER TABLE job_post ADD COLUMN source VARCHAR(50) NULL;
ALTER TABLE job_post ADD INDEX idx_job_post_source (source);

-- external_id 컬럼 추가 (외부 API의 공고 ID)
ALTER TABLE job_post ADD COLUMN external_id VARCHAR(100) NULL;
ALTER TABLE job_post ADD UNIQUE INDEX idx_job_post_external_id (external_id);

-- application_method 컬럼 추가 (지원 방법)
ALTER TABLE job_post ADD COLUMN application_method VARCHAR(50) NULL;

-- homepage_url 컬럼 추가 (홈페이지 URL)
ALTER TABLE job_post ADD COLUMN homepage_url VARCHAR(500) NULL;

-- full_address 컬럼 추가 (전체 주소)
ALTER TABLE job_post ADD COLUMN full_address VARCHAR(500) NULL;

-- contact_name 컬럼 추가 (담당자 이름)
ALTER TABLE job_post ADD COLUMN contact_name VARCHAR(100) NULL;
