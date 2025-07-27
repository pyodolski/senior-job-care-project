from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user, logout_user
from models import db, User
import logging

logger = logging.getLogger(__name__)

# 인증 관련 라우트를 담당하는 블루프린트 생성
auth_bp = Blueprint("auth", __name__)

# 홈 화면 렌더링
@auth_bp.route("/")
def home():
    return render_template("home.html")

# 소셜 로그인 콜백은 social_oauth.py에서 처리됩니다.

# 로그인한 사용자의 프로필 페이지
@auth_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)
import bcrypt
from flask import request, flash

# 회원가입 라우트
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        nickname = request.form["nickname"]
        name = request.form.get("name")
        gender = request.form.get("gender")
        birth_date = request.form.get("birth_date")
        sido = request.form.get("sido")
        sigungu = request.form.get("sigungu")
        dong = request.form.get("dong")

        if password != confirm_password:
            flash("비밀번호가 일치하지 않습니다.")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(username=username).first():
            flash("이미 존재하는 사용자입니다.")
            return redirect(url_for("auth.register"))

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        user = User(
            username=username,
            password=hashed_pw.decode("utf-8"),
            nickname=nickname,
            name=name,
            gender=gender,
            birth_date=birth_date if birth_date else None,
            user_type=0,
            social_type=None,
            social_id=None,
            sido=sido,
            sigungu=sigungu,
            dong=dong
        )
        db.session.add(user)
        db.session.commit()
        flash("회원가입 완료! 로그인 해주세요.")
        return redirect(url_for("auth.home"))

    return render_template("register.html")


# 로그인 라우트
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if not user or not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            flash("로그인 실패. 아이디 또는 비밀번호를 확인하세요.")
            return redirect(url_for("auth.login"))

        login_user(user)
        return redirect(url_for("auth.profile"))

    return render_template("login.html")

# 로그아웃 라우트
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("로그아웃되었습니다.")
    return redirect(url_for("auth.home"))