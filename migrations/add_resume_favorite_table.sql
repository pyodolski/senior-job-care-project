-- 이력서 좋아요 테이블 생성
CREATE TABLE IF NOT EXISTS resume_favorite (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    resume_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (resume_id) REFERENCES resume(id) ON DELETE CASCADE,
    UNIQUE KEY uq_user_resume_favorite (user_id, resume_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 인덱스 추가
CREATE INDEX idx_resume_favorite_user_id ON resume_favorite(user_id);
CREATE INDEX idx_resume_favorite_resume_id ON resume_favorite(resume_id);
