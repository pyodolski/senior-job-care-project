from flask import Flask
from config import Config
from models import db, User
from flask_login import LoginManager
from flask_session import Session
from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.user_auth import user_auth_bp
from routes.onboarding import onboarding_bp
from routes.social_oauth import social_oauth_bp
from routes.user_session import user_session_bp
from routes.google_oauth import google_bp
from routes.naver_oauth import naver_bp
from routes.kakao_oauth import kakao_bp
from routes.areas import areas_bp
from routes.community import community_bp
from routes.components import components_bp

app = Flask(__name__)
app.config.from_object(Config)

Session(app)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.home"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 블루프린트 등록
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(user_auth_bp)
app.register_blueprint(onboarding_bp)
app.register_blueprint(social_oauth_bp)  # 새로 생성한 소셜 OAuth 블루프린트
app.register_blueprint(user_session_bp)  # 새로 생성한 사용자 세션 블루프린트
app.register_blueprint(google_bp, url_prefix="/login")
app.register_blueprint(naver_bp)
app.register_blueprint(kakao_bp, url_prefix="/login")
app.register_blueprint(community_bp)


app.register_blueprint(areas_bp)
app.register_blueprint(components_bp)  # 컴포넌트 API 블루프린트

# 초기 DB 설정
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(port=5002, debug=True)
