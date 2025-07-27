from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, login_user, logout_user
from models import db, User
import bcrypt

# 사용자 인증 관련 라우트를 담당하는 블루프린트 생성
user_auth_bp = Blueprint("user_auth", __name__)

# 회원가입 라우트
@user_auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        nickname = request.form["nickname"]
        name = request.form.get("name")
        gender = request.form.get("gender")
        birth_date = request.form.get("birth_date")

        if password != confirm_password:
            flash("비밀번호가 일치하지 않습니다.")
            return redirect(url_for("user_auth.register"))

        if User.query.filter_by(username=username).first():
            flash("이미 존재하는 사용자입니다.")
            return redirect(url_for("user_auth.register"))

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        user = User()
        user.username = username
        user.password = hashed_pw.decode("utf-8")
        user.nickname = nickname
        user.name = name
        user.gender = gender
        user.birth_date = birth_date if birth_date else None
        user.user_type = 0
        user.social_type = None
        user.social_id = None
        user.onboarding_status = 'completed'  # 일반 로그인 사용자는 가입 시 온보딩 완료 처리
        user.is_profile_complete = True  # 프로필 완성 상태로 설정
        db.session.add(user)
        db.session.commit()
        flash("회원가입 완료! 로그인 해주세요.")
        return redirect(url_for("auth.home"))

    return render_template("register.html")


# 로그인 라우트
@user_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if not user or not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            flash("로그인 실패. 아이디 또는 비밀번호를 확인하세요.")
            return redirect(url_for("user_auth.login"))

        # 일반 로그인 사용자의 온보딩 상태 자동 완료 처리
        if user.onboarding_status == 'pending':
            user.onboarding_status = 'completed'
            user.is_profile_complete = True
            db.session.commit()

        login_user(user)
        return redirect(url_for("user_session.login_complete"))

    return render_template("login.html")


# 로그아웃 처리
@user_auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.home"))