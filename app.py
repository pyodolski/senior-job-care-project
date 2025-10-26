from flask import Flask, render_template
from config import Config
from models import db, User
from flask_login import LoginManager, current_user
from utils.files_handler import generate_presigned_get_url
from flask_session import Session
from routes.auth import auth_bp
from routes.google_oauth import google_bp
from routes.naver_oauth import naver_bp
from routes.kakao_oauth import kakao_bp
from routes.areas import areas_bp
from routes.jobs import jobs_bp
from routes.chat import chat_bp
from routes.company import company_bp
from routes.resume import resumes_bp
from routes.job_assistant import job_assistant_bp
from utils.helpers import format_date, format_datetime, format_salary, get_work_days, calculate_time_ago
from cli import register_cli  # ⬅ cli.py에서 만든 함수 import
from routes.admin.admin import admin_bp
from routes.map import map_bp
from routes.news import news_bp
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*", manage_session=False)
app = Flask(__name__)
app.config.from_object(Config)

Session(app)
db.init_app(app)

# Railway 환경에서는 데이터베이스 초기화를 지연시킴
print("🚀 애플리케이션이 시작되었습니다. 데이터베이스는 첫 요청 시 초기화됩니다.")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.home"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# SocketIO를 앱에 초기화 (Session 이후)
socketio.init_app(app)  # 확장 시 message_queue='redis://localhost:6379/0' 가능[web:31]

# 데이터베이스 초기화 상태 추적
db_initialized = False

def ensure_db_initialized():
    global db_initialized
    if not db_initialized:
        try:
            # 데이터베이스 연결 테스트
            with app.app_context():
                from sqlalchemy import text
                # 간단한 쿼리로 연결 테스트
                db.session.execute(text('SELECT 1'))
                # 테이블 생성 (이미 존재하면 무시됨)
                db.create_all()
                
                # people_category 컬럼 마이그레이션 자동 실행
                try:
                    check_query = text("""
                        SELECT COUNT(*) as count
                        FROM information_schema.COLUMNS 
                        WHERE TABLE_SCHEMA = DATABASE()
                        AND TABLE_NAME = 'job_post' 
                        AND COLUMN_NAME = 'people_category'
                    """)
                    result = db.session.execute(check_query).fetchone()
                    
                    if result[0] == 0:
                        print("🔧 people_category 컬럼 마이그레이션 시작...")
                        alter_query = "ALTER TABLE job_post ADD COLUMN people_category VARCHAR(20) AFTER contact_phone"
                        db.session.execute(text(alter_query))
                        db.session.commit()
                        print("✅ people_category 컬럼 마이그레이션 완료")
                    else:
                        print("ℹ️ people_category 컬럼이 이미 존재합니다")
                except Exception as migration_error:
                    print(f"⚠️ 마이그레이션 오류 (무시 가능): {migration_error}")
                    db.session.rollback()
                
                db_initialized = True
                print("✅ 데이터베이스 연결 및 테이블 초기화 완료")
        except Exception as e:
            print(f"⚠️ 데이터베이스 초기화 오류: {e}")
            # Railway 환경에서는 재시도
            import time
            time.sleep(2)
            try:
                with app.app_context():
                    db.create_all()
                    db_initialized = True
                    print("✅ 데이터베이스 재시도 성공")
            except Exception as retry_error:
                print(f"❌ 데이터베이스 재시도 실패: {retry_error}")

# 에러 핸들러 추가
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    print(f"500 에러 발생: {error}")
    return "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", 500

@app.before_request
def before_request():
    """각 요청 전에 데이터베이스 연결 확인"""
    ensure_db_initialized()

# 루트 라우트 - 스플래시 페이지
@app.route('/')
def splash():
    return render_template('splash.html')

# 토글 페이지 라우트
@app.route('/toggle-page')
def toggle_page():
    return render_template('toggle_page.html')


# 템플릿 필터 등록
app.jinja_env.filters['format_date'] = format_date
app.jinja_env.filters['format_datetime'] = format_datetime
app.jinja_env.filters['format_salary'] = format_salary
app.jinja_env.filters['get_work_days'] = get_work_days
app.jinja_env.filters['time_ago'] = calculate_time_ago

# 공통으로 사용할 프로필 이미지 ( 채팅 목록, 프로필 이미지, 채팅방 등등)
@app.context_processor
def inject_profile_url():
    url = None
    try:
        if current_user.is_authenticated and getattr(current_user, 'profile_image', None):
            url = generate_presigned_get_url(current_user.profile_image, expires=900)
    except Exception:
        url = None
    return dict(profile_url=url)

# 블루프린트 등록
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(google_bp, url_prefix="/login")
app.register_blueprint(naver_bp)
app.register_blueprint(kakao_bp, url_prefix="/login")
app.register_blueprint(areas_bp)
app.register_blueprint(jobs_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(company_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(resumes_bp,url_prefix='/')
app.register_blueprint(job_assistant_bp)
app.register_blueprint(news_bp)
app.register_blueprint(map_bp)

# CLI 명령어 등록
register_cli(app)

from routes.chat_events import init_chat_socketio
init_chat_socketio(socketio)



if __name__ == '__main__':
    # 로컬 개발 환경에서 데이터베이스 연결 테스트
    socketio.run(app, port=5002, debug=True)
