# 시니어 소셜 로그인 온보딩 시스템

Flask 기반의 시니어 친화적 소셜 로그인 및 온보딩 시스템입니다.

## 🚀 주요 기능

### **소셜 로그인**

- **Google**, **네이버**, **카카오** 3가지 소셜 플랫폼 지원
- 원클릭 간편 로그인
- 최소한의 개인정보 수집 (이름, 이메일만)

### **단계별 온보딩**

- **4단계 가이드**: 이름 → 닉네임 → 성별 → 생년월일
- **진행 상황 저장**: 중간에 나가도 이어서 진행 가능
- **실시간 검증**: 각 단계별 즉시 검증 및 피드백
- **재개 기능**: 미완료 온보딩 자동 재개

### **사용자 친화적 UI/UX**

- **시니어 최적화**: 큰 글씨, 명확한 버튼, 간단한 인터페이스
- **반응형 디자인**: PC/모바일 모든 기기 지원
- **접근성**: 스크린 리더, 키보드 네비게이션 지원
- **애니메이션**: 부드러운 전환 효과

## 🏗️ 시스템 아키텍처

### **기술 스택**

- **Backend**: Flask 3.0+
- **Database**: MySQL (SQLAlchemy ORM)
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **Authentication**: Flask-Login + Flask-Dance
- **Session**: Flask-Session

### **프로젝트 구조**

```
senior_git/
├── app.py                    # Flask 애플리케이션 진입점
├── config.py                 # 설정 파일
├── models.py                 # 데이터베이스 모델
├── requirements.txt          # Python 의존성
│
├── routes/                   # 라우트 모듈
│   ├── auth.py              # 기본 인증 (홈페이지)
│   ├── social_oauth.py      # 소셜 로그인 콜백
│   ├── user_session.py      # 사용자 세션 관리
│   ├── onboarding.py        # 온보딩 프로세스
│   ├── profile.py           # 사용자 프로필
│   ├── google_oauth.py      # Google OAuth
│   ├── naver_oauth.py       # 네이버 OAuth
│   └── kakao_oauth.py       # 카카오 OAuth
│
├── services/                 # 비즈니스 로직 서비스
│   ├── onboarding.py        # 온보딩 서비스
│   ├── social_login_helper.py # 소셜 로그인 헬퍼
│   ├── validation.py        # 데이터 검증
│   ├── error_handlers.py    # 오류 처리 데코레이터
│   ├── exceptions.py        # 커스텀 예외
│   └── db_utils.py          # 데이터베이스 유틸리티
│
├── templates/               # Jinja2 템플릿
│   ├── home.html           # 홈페이지
│   ├── login.html          # 로그인 페이지
│   ├── profile.html        # 프로필 페이지
│   ├── onboarding/         # 온보딩 템플릿
│   │   ├── step_by_step.html # 단계별 온보딩
│   │   └── resume.html     # 온보딩 재개
│   └── success/            # 성공 페이지
│       └── login_complete.html # 로그인 완료
│
└── static/                 # 정적 파일
    └── js/                 # JavaScript 모듈
        ├── core/           # 핵심 로직
        ├── network/        # 네트워크 관리
        ├── storage/        # 데이터 관리
        ├── ui/             # UI 관리
        ├── validators/     # 폼 검증
        └── utils/          # 유틸리티
```

## 📋 온보딩 플로우

### **1. 소셜 로그인**

```
사용자 클릭 → OAuth 인증 → 콜백 처리 → 사용자 상태 확인
```

### **2. 사용자 분기**

- **신규 사용자**: 온보딩 시작
- **기존 사용자 (미완료)**: 온보딩 재개
- **기존 사용자 (완료)**: 로그인 완료 페이지

### **3. 온보딩 단계**

1. **이름 입력** - 실명 입력 (한글/영문)
2. **닉네임 설정** - 중복 검사, 2-20자
3. **성별 선택** - 남성/여성 선택
4. **생년월일** - 만 14세 이상 검증

### **4. 완료 처리**

```
모든 정보 입력 → 검증 → DB 저장 → 온보딩 상태 'completed' → 로그인 완료
```

## 🔧 설치 및 실행

### **1. 환경 설정**

```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt
```

### **2. 데이터베이스 설정**

```bash
# MySQL 설정 후 config.py에서 연결 정보 수정
# 데이터베이스 자동 생성 (첫 실행 시)
python app.py
```

### **3. OAuth 설정**

`config.py`에서 각 플랫폼별 OAuth 설정:

```python
# Google OAuth
GOOGLE_CLIENT_ID = "your_google_client_id"
GOOGLE_CLIENT_SECRET = "your_google_client_secret"

# 네이버 OAuth
NAVER_CLIENT_ID = "your_naver_client_id"
NAVER_CLIENT_SECRET = "your_naver_client_secret"

# 카카오 OAuth
KAKAO_CLIENT_ID = "your_kakao_client_id"
KAKAO_CLIENT_SECRET = "your_kakao_client_secret"
```

### **4. 애플리케이션 실행**

```bash
python app.py
# http://localhost:5002 접속
```

## 🛡️ 보안 및 검증

### **데이터 검증**

- **실시간 검증**: 클라이언트/서버 이중 검증
- **입력 제한**: 길이, 패턴, 선택지 검증
- **XSS 방지**: 입력 데이터 정제
- **중복 검사**: 닉네임 중복 실시간 확인

### **에러 처리**

- **커스텀 예외**: 상세한 오류 분류
- **사용자 친화적 메시지**: 기술적 오류 → 이해하기 쉬운 메시지
- **로깅**: 모든 오류 상세 기록
- **복구 메커니즘**: 오류 발생 시 안전한 복구

### **데이터베이스 안전성**

- **트랜잭션 관리**: 안전한 DB 작업
- **롤백 처리**: 오류 시 자동 롤백
- **무결성 검사**: 데이터 일관성 보장

## 📊 API 엔드포인트

### **인증 관련**

- `GET /` - 홈페이지
- `GET /login/google` - Google 로그인
- `GET /naver_login` - 네이버 로그인
- `GET /login/kakao` - 카카오 로그인

### **온보딩 관련**

- `GET|POST /onboarding` - 온보딩 메인
- `GET /onboarding/resume` - 온보딩 재개
- `POST /onboarding/save-progress` - 진행 상황 저장 (AJAX)
- `GET /onboarding/get-progress` - 진행 상황 조회 (AJAX)
- `POST /onboarding/check-nickname` - 닉네임 중복 검사 (AJAX)

### **사용자 관리**

- `GET /login-complete` - 로그인 완료 페이지
- `POST /logout` - 로그아웃
- `GET /profile` - 사용자 프로필

## 🎯 주요 특징

### **시니어 친화적 설계**

- **직관적 UI**: 복잡하지 않은 단순한 인터페이스
- **명확한 안내**: 각 단계별 상세한 설명
- **오류 방지**: 실시간 검증으로 오류 최소화
- **접근성**: 웹 접근성 가이드라인 준수

### **성능 최적화**

- **코드 리팩토링**: 중복 코드 제거 (65% 축소)
- **모듈화**: 기능별 서비스 분리
- **캐싱**: 세션 기반 진행 상황 저장
- **최적화된 쿼리**: 불필요한 DB 호출 최소화

### **확장성**

- **모듈식 구조**: 새로운 소셜 플랫폼 쉽게 추가 가능
- **플러그인 가능**: 검증 규칙, 오류 처리 커스터마이징
- **다국어 지원**: 템플릿 구조로 다국어 확장 가능

## 🔄 배포 가이드

### **환경 변수 설정**

```bash
export FLASK_ENV=production
export SECRET_KEY=your_secret_key
export DATABASE_URL=mysql://user:password@host:port/database
```

### **프로덕션 설정**

```python
# config.py
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SECRET_KEY = os.environ.get('SECRET_KEY')
```

### **WSGI 서버 배포**

```bash
# Gunicorn 사용 예시
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🤝 기여하기

1. Fork 프로젝트
2. Feature 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 Push (`git push origin feature/amazing-feature`)
5. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해 주세요.

---

**시니어를 위한, 시니어에 의한 로그인 시스템** ❤️
