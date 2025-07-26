from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # 기본 정보
    name = db.Column(db.String(100), nullable=True)
    nickname = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=True)         # 'male', 'female' 등
    birth_date = db.Column(db.Date, nullable=True)

    # 일반 로그인용
    username = db.Column(db.String(50), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)       # 비밀번호는 해시 저장

    # 사용자 유형: 0 - 일반, 1 - 기업, 2 - 관리자
    user_type = db.Column(db.Integer, default=0)

    # 소셜 로그인 정보
    social_type = db.Column(db.String(20), nullable=True)     # 'google', 'kakao', 'naver'
    social_id = db.Column(db.String(255), nullable=True)

    # 가입일
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 온보딩 상태 관리
    onboarding_status = db.Column(db.String(20), default='pending')  # 'pending', 'completed'
    onboarding_data = db.Column(db.Text, nullable=True)  # JSON 형태로 임시 데이터 저장
    onboarding_step = db.Column(db.Integer, default=0)   # 현재 진행 단계
    is_profile_complete = db.Column(db.Boolean, default=False)  # 필수 정보 완성도

    # 유니크 제약: 동일 소셜 타입과 ID는 중복 불가
    __table_args__ = (
        db.UniqueConstraint('social_type', 'social_id', name='uq_social_login'),
    )

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    @property
    def age(self):
        """생년월일로부터 나이 계산"""
        if self.birth_date:
            from datetime import date
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None

    def is_required_info_complete(self):
        """필수 정보 완성도 체크"""
        required_fields = [self.name, self.nickname, self.gender, self.birth_date]
        return all(field is not None and str(field).strip() != '' for field in required_fields)

    def update_profile_complete_status(self):
        """프로필 완성 상태 업데이트"""
        self.is_profile_complete = self.is_required_info_complete()

    def __repr__(self):
        return f"<User id={self.id} type={self.user_type} username={self.username}>"
