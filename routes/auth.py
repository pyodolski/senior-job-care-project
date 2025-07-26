from flask import Blueprint, render_template
import logging

logger = logging.getLogger(__name__)

# 인증 관련 라우트를 담당하는 블루프린트 생성
auth_bp = Blueprint("auth", __name__)

# 홈 화면 렌더링
@auth_bp.route("/")
def home():
    return render_template("home.html")




