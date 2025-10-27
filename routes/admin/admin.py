from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models import User, db
from flask import send_from_directory, current_app
from urllib.parse import urlparse
from utils.files_handler import generate_presigned_get_url

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# 권한 검사 데코레이터
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.user_type != 2:
            flash("관리자 권한이 필요합니다.")
            return redirect(url_for('auth.home'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route("/pending_companies")
@admin_required
def pending_companies():
    users = User.query.filter_by(user_type=1, is_verified=False).all()
    return render_template("admin/pending_companies.html", users=users)

@admin_bp.route("/approve_company/<int:user_id>", methods=["POST"])
@admin_required
def approve_company(user_id):
    user = User.query.get_or_404(user_id)
    user.is_verified = True
    db.session.commit()
    flash(f"{user.nickname}님의 승인 완료!")
    return redirect(url_for("admin.pending_companies"))

@admin_bp.route("/reject_company/<int:user_id>", methods=["POST"])
@admin_required
def reject_company(user_id):
    user = User.query.get_or_404(user_id)
    user.user_type = 0
    user.is_verified = False
    db.session.commit()
    flash(f"{user.nickname}님의 승인 거부!")
    return redirect(url_for("admin.pending_companies"))



@admin_bp.route("/download_business_file/<int:user_id>")
@admin_required
def download_business_file(user_id):
    user = User.query.get_or_404(user_id)
    s3_url = user.business_registration_file

    if not s3_url:
        flash("업로드된 사업자등록증 파일이 없습니다.", "error")
        return redirect(url_for("admin.pending_companies"))

    try:
        file_key = urlparse(s3_url).path.lstrip('/')

        original_filename = user.business_registration_original

        presigned_url = generate_presigned_get_url(
            key=file_key,
            expires=300,
            download_name=original_filename
        )

        if presigned_url:
            return redirect(presigned_url)
        else:
            return redirect(url_for("admin.pending_companies"))

    except Exception as e:
        flash(f"파일을 불러오는 중 오류가 발생했습니다: {e}", "error")
        return redirect(url_for("admin.pending_companies"))