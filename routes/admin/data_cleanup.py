from flask import Blueprint, render_template, flash, redirect, url_for  # render_template 임포트 추가
from flask_login import login_required, current_user
from functools import wraps
from scripts.scheduler_service import delete_expired_job_posts

data_cleanup_bp = Blueprint('data_cleanup', __name__)


def admin_required(f):
    """관리자 권한 확인 데코레이터"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != 2:
            flash('관리자만 접근할 수 있습니다.', 'error')
            return redirect(url_for('auth.home'))
        return f(*args, **kwargs)

    return decorated_function



@data_cleanup_bp.route('/admin/data-cleanup')
@login_required
@admin_required
def data_cleanup_page():
    return render_template('admin/data_cleanup.html')




# --- 만료된 공고 삭제 ---
@data_cleanup_bp.route('/admin/delete-expired-jobs', methods=['POST'])
@login_required
@admin_required
def delete_expired_jobs_manual():
    """만료된 공고 수동 삭제 (POST 액션)"""
    print(f"관리자(ID:{current_user.id}) 만료 공고 수동 삭제 시작 (data_cleanup)")
    try:
        delete_expired_job_posts()
        print("만료 공고 수동 삭제 완료 (data_cleanup)")

        return redirect(url_for('data_cleanup.data_cleanup_page'))

    except Exception as e:
        print(f"만료 공고 수동 삭제 오류 (data_cleanup): {e}")
        return redirect(url_for('data_cleanup.data_cleanup_page'))