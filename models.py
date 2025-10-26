from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta
from sqlalchemy import Float
import enum

db = SQLAlchemy()

# 한국 시간대 (UTC+9)
KST = timezone(timedelta(hours=9))

def get_kst_now():
    """한국 시간(KST)으로 현재 시간을 반환"""
    return datetime.now(KST)

class WorkType(enum.Enum):
    LONG_TERM = "장기"
    SHORT_TERM = "단기"
    PART_TIME = "파트타임"

class Category(enum.Enum):
    SAFETY_MANAGEMENT = "안전·관리"
    SERVICE_STORE = "서비스·매장"
    LIVING_CARE = "생활·돌봄 지원"
    DRIVING_DELIVERY = "운전·배송"
    SOCIAL_PUBLIC = "사회·공공"
    ETC = "기타"

class Strength(enum.Enum):
    SINCERE = "성실한"
    RESPONSIBLE = "책임감 있는"
    METICULOUS = "꼼꼼한"
    ACHIEVEMENT_ORIENTED = "성취지향적인"
    PROACTIVE = "적극적인"
    CHALLENGING = "도전적인"
    PASSIONATE = "열정적인"
    DRIVING_FORCE = "추진력 있는"
    SOCIABLE = "친화력 좋은"
    COMMUNICATIVE = "소통력 있는"
    CREATIVE = "창의적인"
    FLEXIBLE = "유연한"
    ANALYTICAL = "분석적인"
    STRATEGIC = "전략적인"
    ADAPTIVE = "적응력 좋은"
    CALM = "차분한"
    PRACTICAL = "실무중심적인"
    POSITIVE = "긍정적인"

class User(db.Model):
    __tablename__ = 'user'

    # 사용자 고유 ID
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # 기본 정보
    name = db.Column(db.String(100), nullable=True)           # 이름
    nickname = db.Column(db.String(50), nullable=False)       # 닉네임
    gender = db.Column(db.String(10), nullable=True)          # 성별 (male, female 등)
    birth_date = db.Column(db.Date, nullable=True)            # 생년월일
    sido = db.Column(db.String(30), nullable=True)            # 시/도
    sigungu = db.Column(db.String(30), nullable=True)         # 시/군/구
    dong = db.Column(db.String(40), nullable=True)            # 동

    # 일반 로그인용
    username = db.Column(db.String(50), unique=True, nullable=True)  # 일반 로그인용 ID
    password = db.Column(db.String(255), nullable=True)       # 비밀번호 (해시로 저장)

    # 사용자 유형: 0 - 일반, 1 - 기업, 2 - 관리자
    user_type = db.Column(db.Integer, default=0)

    is_verified = db.Column(db.Boolean, default=False)  # 관리자 승인 여부 (False=대기, True=승인)
    business_registration_file = db.Column(db.String(255), nullable=True)  # 사업자 등록증 파일 경로
    business_registration_original = db.Column(db.String(255))  # 사용자 원본 파일명

    # 소셜 로그인 정보
    social_type = db.Column(db.String(20), nullable=True)     # 소셜 로그인 타입 (google, kakao 등)
    social_id = db.Column(db.String(255), nullable=True)      # 소셜 로그인 ID

    # 추가 정보
    email = db.Column(db.String(255), nullable=True)          # 이메일
    phone = db.Column(db.String(20), nullable=True)           # 전화번호
    trust_score = db.Column(db.Float, default=0.0)            # 신뢰점수
    profile_image = db.Column(db.String(255), nullable=True)  # 프로필 사진

    # 시간 정보
    created_at = db.Column(db.DateTime, default=get_kst_now)  # 가입일
    updated_at = db.Column(db.DateTime, default=get_kst_now, onupdate=get_kst_now)  # 수정일

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

    def __repr__(self):
        return f"<User id={self.id} type={self.user_type} username={self.username}>"

class JobPost(db.Model):
    __tablename__ = 'job_post'

    # 공고 고유 ID
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # 기본 공고 정보
    title = db.Column(db.String(200), nullable=False)          # 공고 제목
    company = db.Column(db.String(100), nullable=False)        # 회사 이름
    description = db.Column(db.Text, nullable=False)           # 공고 내용

    # 근무 조건
    work_start_time = db.Column(db.Time, nullable=True)        # 근무 시작 시간
    work_end_time = db.Column(db.Time, nullable=True)          # 근무 종료 시간
    recruitment_count = db.Column(db.Integer, nullable=True)   # 모집 인원
    region = db.Column(db.String(100), nullable=True)          # 근무 지역 (맵 연동)
    latitude = db.Column(Float, nullable=True)  # 위도
    longitude = db.Column(Float, nullable=True)  # 경도
    salary = db.Column(db.String(100), nullable=True)          # 급여

    # 행정구역 정보를 분리하여 저장할 필드 추가
    region_1depth_name = db.Column(db.String(50), index=True)  # 시/도 (예: '서울')
    region_2depth_name = db.Column(db.String(50), index=True)  # 시/군/구 (예: '강남구')
    region_3depth_name = db.Column(db.String(50), index=True)  # 읍/면/동 (예: '역삼동')

    # 근무 요일 (월화수목금토일)
    work_monday = db.Column(db.Boolean, default=False)         # 월요일
    work_tuesday = db.Column(db.Boolean, default=False)        # 화요일
    work_wednesday = db.Column(db.Boolean, default=False)      # 수요일
    work_thursday = db.Column(db.Boolean, default=False)       # 목요일
    work_friday = db.Column(db.Boolean, default=False)         # 금요일
    work_saturday = db.Column(db.Boolean, default=False)       # 토요일
    work_sunday = db.Column(db.Boolean, default=False)         # 일요일

    # 모집 형태 및 기간
    recruitment_type = db.Column(db.String(50), nullable=True) # 모집 형태
    work_period = db.Column(db.String(20), nullable=True)      # 기간 (1개월, 3개월, 6개월, 1년 이상)

    # 연락처
    contact_phone = db.Column(db.String(20), nullable=True)    # 연락처 전화번호

    # 사람 이음 전용 필드
    people_category = db.Column(db.String(20), nullable=True)  # 사람이음 카테고리 (업무, 이웃, 과외, 제능, 문화)

    # 기업 이음 전용 필드들
    job_category = db.Column(db.String(50), nullable=True)     # 직무 내용 (사무직, 생산/기술직, 서비스직, 기타)
    job_category_custom = db.Column(db.String(100), nullable=True)  # 직무 내용 직접입력
    salary_min = db.Column(db.Integer, nullable=True)          # 최소 임금 (만원 단위)
    salary_max = db.Column(db.Integer, nullable=True)          # 최대 임금 (만원 단위)
    salary_negotiable = db.Column(db.Boolean, default=False)   # 임금 협의 여부
    experience_required = db.Column(db.String(20), nullable=True)  # 경력 요구사항 (무관, 경력직)
    
    # 복리후생 (Boolean 필드들)
    benefit_commute_bus = db.Column(db.Boolean, default=False)     # 통근버스
    benefit_lunch = db.Column(db.Boolean, default=False)           # 중식제공
    benefit_uniform = db.Column(db.Boolean, default=False)         # 근무복 제공
    benefit_health_checkup = db.Column(db.Boolean, default=False)  # 정기 건강검진
    benefit_other = db.Column(db.String(200), nullable=True)       # 기타 복리후생
    
    # 장애인용 복지시설 (Boolean 필드들)
    disabled_parking = db.Column(db.Boolean, default=False)        # 장애인용 주차장
    disabled_elevator = db.Column(db.Boolean, default=False)       # 장애인용 승강기
    disabled_ramp = db.Column(db.Boolean, default=False)           # 건물 내부 경사로
    disabled_restroom = db.Column(db.Boolean, default=False)       # 장애인용 화장실
    
    # 모집기간
    recruitment_start_date = db.Column(db.Date, nullable=True)     # 모집 시작일
    recruitment_end_date = db.Column(db.Date, nullable=True)       # 모집 마감일

    # 통계 정보
    application_count = db.Column(db.Integer, default=0)       # 지원횟수
    view_count = db.Column(db.Integer, default=0)              # 조회수
    bookmark_count = db.Column(db.Integer, default=0)          # 찜 횟수

    # 작성자 및 시간 정보
    created_at = db.Column(db.DateTime, default=get_kst_now)  # 공고 작성일
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 작성자 (User ID)

    author = db.relationship('User', backref=db.backref('job_posts', lazy=True))

    def __repr__(self):
        return f"<JobPost id={self.id} title={self.title} company={self.company}>"

class JobBookmark(db.Model):
    __tablename__ = 'job_bookmark'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=get_kst_now)
    
    # 관계 설정
    user = db.relationship('User', backref=db.backref('bookmarks', lazy=True))
    job = db.relationship('JobPost', backref=db.backref('bookmarks', lazy=True))
    
    # 유니크 제약: 한 사용자가 같은 공고를 중복으로 찜할 수 없음
    __table_args__ = (
        db.UniqueConstraint('user_id', 'job_id', name='uq_user_job_bookmark'),
    )
    
    def __repr__(self):
        return f"<JobBookmark user_id={self.user_id} job_id={self.job_id}>"

class JobApplication(db.Model):
    """공고 지원 모델"""
    __tablename__ = 'job_application'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 지원자
    job_id = db.Column(db.Integer, db.ForeignKey('job_post.id'), nullable=False)  # 지원한 공고
    status = db.Column(db.String(20), default='pending')  # 지원 상태: pending, accepted, rejected
    message = db.Column(db.Text, nullable=True)  # 지원 메시지
    created_at = db.Column(db.DateTime, default=get_kst_now)
    updated_at = db.Column(db.DateTime, default=get_kst_now, onupdate=get_kst_now)
    
    # 관계 설정
    user = db.relationship('User', backref=db.backref('applications', lazy=True))
    job = db.relationship('JobPost', backref=db.backref('applications', lazy=True))
    
    # 유니크 제약: 한 사용자가 같은 공고에 중복 지원 불가
    __table_args__ = (
        db.UniqueConstraint('user_id', 'job_id', name='uq_user_job_application'),
    )
    
    def __repr__(self):
        return f"<JobApplication user_id={self.user_id} job_id={self.job_id} status={self.status}>"

class ChatRoom(db.Model):
    """채팅방 모델"""
    __tablename__ = 'chat_room'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_post.id'), nullable=False)  # 관련 공고
    applicant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 지원자
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 고용주
    is_active = db.Column(db.Boolean, default=True)  # 채팅방 활성 상태
    applicant_left = db.Column(db.Boolean, default=False)  # 지원자가 나갔는지 여부
    employer_left = db.Column(db.Boolean, default=False)  # 고용주가 나갔는지 여부
    created_at = db.Column(db.DateTime, default=get_kst_now)
    updated_at = db.Column(db.DateTime, default=get_kst_now, onupdate=get_kst_now)
    
    # 관계 설정
    job = db.relationship('JobPost', backref=db.backref('chat_rooms', lazy=True))
    applicant = db.relationship('User', foreign_keys=[applicant_id], backref=db.backref('applicant_chats', lazy=True))
    employer = db.relationship('User', foreign_keys=[employer_id], backref=db.backref('employer_chats', lazy=True))
    
    # 유니크 제약: 같은 공고에 대해 같은 지원자와 고용주 간 채팅방은 하나만
    __table_args__ = (
        db.UniqueConstraint('job_id', 'applicant_id', 'employer_id', name='uq_chat_room'),
    )
    
    def __repr__(self):
        return f"<ChatRoom id={self.id} job_id={self.job_id} applicant_id={self.applicant_id} employer_id={self.employer_id}>"

class ChatMessage(db.Model):
    """채팅 메시지 모델"""
    __tablename__ = 'chat_message'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)  # 채팅방
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 발신자
    message = db.Column(db.Text, nullable=False)  # 메시지 내용
    message_type = db.Column(db.String(20), default='text')  # 메시지 타입: text, image, file
    is_read = db.Column(db.Boolean, default=False)  # 읽음 여부
    created_at = db.Column(db.DateTime, default=get_kst_now)
    
    # 관계 설정
    room = db.relationship('ChatRoom', backref=db.backref('messages', lazy=True, order_by='ChatMessage.created_at'))
    sender = db.relationship('User', backref=db.backref('sent_messages', lazy=True))
    
    def __repr__(self):
        return f"<ChatMessage id={self.id} room_id={self.room_id} sender_id={self.sender_id}>"


class Resume(db.Model):
    __tablename__ = 'resume'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # --- 공개 여부 ---
    is_public = db.Column(db.Boolean, default=False, nullable=False)

    # --- 희망 근무 조건 ---
    desired_categories = db.Column(db.String(255), nullable=True)
    desired_work_type = db.Column(db.Enum(WorkType), nullable=True)

    work_monday = db.Column(db.Boolean, default=False)
    work_tuesday = db.Column(db.Boolean, default=False)
    work_wednesday = db.Column(db.Boolean, default=False)
    work_thursday = db.Column(db.Boolean, default=False)
    work_friday = db.Column(db.Boolean, default=False)
    work_saturday = db.Column(db.Boolean, default=False)
    work_sunday = db.Column(db.Boolean, default=False)

    desired_start_time = db.Column(db.Time, nullable=True)
    desired_end_time = db.Column(db.Time, nullable=True)
    # --- '시간 협의 가능' 필드 (체크박스)---
    is_time_negotiable = db.Column(db.Boolean, default=False, nullable=False)

    # --- 경력, 자기소개 ---
    experience = db.Column(db.Text, nullable=True)
    self_introduction = db.Column(db.Text, nullable=True)

    # --- 개인 특성 ---
    strengths = db.Column(db.Text, nullable=True)
    commute_time = db.Column(db.Integer, nullable=True)

    # --- 신체 관련 필드 ---
    walkable_minutes = db.Column(db.Integer, nullable=True)  # 쉬지 않고 걸을 수 있는 시간 (분 단위)
    physical_notes = db.Column(db.Text, nullable=True)  # 신체적 특징

    created_at = db.Column(db.DateTime, default=get_kst_now)
    updated_at = db.Column(db.DateTime, default=get_kst_now, onupdate=get_kst_now)

    # --- 관계 설정 ---
    user = db.relationship('User', backref=db.backref('resume', lazy=True))

    # Certificate 모델과의 1:N 관계 설정
    certificates = db.relationship('Certificate', backref='resume', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Resume {self.id} for User {self.user_id}>'


class Certificate(db.Model):
    __tablename__ = 'certificate'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)

    # Resume 모델과의 관계를 위한 외래 키
    resume_id = db.Column(db.Integer, db.ForeignKey('resume.id'), nullable=False)

    def __repr__(self):
        return f'<Certificate {self.name}>'