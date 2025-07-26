from flask import Blueprint, render_template
from flask_login import login_required, current_user

# 프로필 관련 라우트를 담당하는 블루프린트 생성
profile_bp = Blueprint("profile", __name__)

# 로그인한 사용자의 프로필 페이지
@profile_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)