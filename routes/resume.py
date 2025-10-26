from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.resume_service import ResumeService
from models import Category, WorkType, Strength
from datetime import time

resumes_bp = Blueprint("resumes", __name__)


# ==================== 내 이력서 목록 ====================
@resumes_bp.route("/my-resumes")
@login_required
def my_view_resume():
    """
    현재 로그인한 사용자의 모든 이력서 목록을 보여주는 페이지
    """
    resumes = ResumeService.get_resumes_by_user(current_user.id)

    return render_template(
        "resume/my_view_resume.html",
        resumes=resumes
    )


# ==================== 내 이력서 상세보기 ====================
@resumes_bp.route("/my-resume/<int:resume_id>")
@login_required
def my_resume_detail(resume_id):
    """
    현재 로그인한 사용자 본인의 이력서 상세보기
    """
    resume, is_owner = ResumeService.get_resume_permission_check(
        resume_id,
        current_user.id
    )

    if not resume:
        flash("이력서를 찾을 수 없습니다.", "error")
        return redirect(url_for('resumes.my_view_resume'))

    if not is_owner:
        flash("접근 권한이 없습니다.", "error")
        return redirect(url_for('resumes.my_view_resume'))

    return render_template('resume/my_resume_detail.html', resume=resume, WorkType=WorkType)


# ==================== 이력서 작성 ====================
@resumes_bp.route("/resume/create", methods=["GET", "POST"])
@login_required
def create_resume():
    """
    새로운 이력서를 작성하는 페이지 (여러 개 작성 가능)
    """
    if request.method == "POST":
        # 시간 파싱 헬퍼 함수
        def parse_time(time_str):
            if not time_str:
                return None
            try:
                hour, minute = map(int, time_str.split(':'))
                return time(hour, minute)
            except ValueError:
                return None

        # 폼 데이터 수집
        resume_data = {
            'is_public': 'is_public' in request.form,
            'desired_categories': ",".join(request.form.getlist('categories')),
            'desired_work_type': request.form.get('desired_work_type'),
            'work_monday': 'work_monday' in request.form,
            'work_tuesday': 'work_tuesday' in request.form,
            'work_wednesday': 'work_wednesday' in request.form,
            'work_thursday': 'work_thursday' in request.form,
            'work_friday': 'work_friday' in request.form,
            'work_saturday': 'work_saturday' in request.form,
            'work_sunday': 'work_sunday' in request.form,
            'is_time_negotiable': 'is_time_negotiable' in request.form,
            'desired_start_time': parse_time(request.form.get('start_time')),
            'desired_end_time': parse_time(request.form.get('end_time')),
            'experience': request.form.get('experience'),
            'self_introduction': request.form.get('self_introduction'),
            'strengths': ",".join(request.form.getlist('strengths')),
            'commute_time': request.form.get('commute_time', type=int),
            'walkable_minutes': request.form.get('walkable_minutes', type=int),
            'physical_notes': request.form.get('physical_notes'),
        }

        certificate_names = request.form.getlist('certificate_names')
        certificate_images = request.files.getlist('certificate_images')

        resume = ResumeService.create_resume(
            user_id=current_user.id,
            resume_data=resume_data,
            certificate_names=certificate_names,
            certificate_images=certificate_images
        )

        if resume:
            return redirect(url_for('resumes.my_view_resume'))
        else:
            flash("이력서 작성 중 오류가 발생했습니다.", "error")

    # GET 요청: 빈 폼 렌더링
    return render_template(
        "resume/edit_resume.html",
        resume=None,
        all_categories=list(Category),
        all_work_types=list(WorkType),
        all_strengths=list(Strength)
    )


# ==================== 이력서 수정 ====================
@resumes_bp.route("/resume/<int:resume_id>/edit", methods=["GET", "POST"])
@login_required
def edit_resume(resume_id):
    """
    기존 이력서를 수정하는 페이지 (특정 resume_id 기준)
    """
    # 본인의 이력서인지 확인
    resume, is_owner = ResumeService.get_resume_permission_check(resume_id, current_user.id)

    if not resume:
        flash("이력서를 찾을 수 없습니다.", "error")
        return redirect(url_for('resumes.my_view_resume'))

    if not is_owner:
        flash("수정 권한이 없습니다.", "error")
        return redirect(url_for('resumes.my_view_resume'))

    if request.method == "POST":
        # 시간 파싱 헬퍼 함수
        def parse_time(time_str):
            if not time_str:
                return None
            try:
                hour, minute = map(int, time_str.split(':'))
                return time(hour, minute)
            except ValueError:
                return None

        # 폼 데이터 수집
        resume_data = {
            'is_public': 'is_public' in request.form,
            'desired_categories': ",".join(request.form.getlist('categories')),
            'desired_work_type': request.form.get('desired_work_type'),
            'work_monday': 'work_monday' in request.form,
            'work_tuesday': 'work_tuesday' in request.form,
            'work_wednesday': 'work_wednesday' in request.form,
            'work_thursday': 'work_thursday' in request.form,
            'work_friday': 'work_friday' in request.form,
            'work_saturday': 'work_saturday' in request.form,
            'work_sunday': 'work_sunday' in request.form,
            'is_time_negotiable': 'is_time_negotiable' in request.form,
            'desired_start_time': parse_time(request.form.get('start_time')),
            'desired_end_time': parse_time(request.form.get('end_time')),
            'experience': request.form.get('experience'),
            'self_introduction': request.form.get('self_introduction'),
            'strengths': ",".join(request.form.getlist('strengths')),
            'commute_time': request.form.get('commute_time', type=int),
            'walkable_minutes': request.form.get('walkable_minutes', type=int),
            'physical_notes': request.form.get('physical_notes'),
        }

        certificate_names = request.form.getlist('certificate_names')
        certificate_images = request.files.getlist('certificate_images')

        updated_resume = ResumeService.update_resume(
            resume_id=resume_id,
            user_id=current_user.id,
            resume_data=resume_data,
            certificate_names=certificate_names,
            certificate_images=certificate_images
        )

        if updated_resume:
            return redirect(url_for('resumes.my_resume_detail', resume_id=resume_id))
        else:
            flash("이력서 수정 중 오류가 발생했습니다.", "error")

    # GET 요청: 데이터가 채워진 폼 렌더링
    return render_template(
        "resume/edit_resume.html",
        resume=resume,
        all_categories=list(Category),
        all_work_types=list(WorkType),
        all_strengths=list(Strength)
    )


# ==================== 자격증 삭제 (AJAX) ====================
@resumes_bp.route("/resume/certificate/delete/<int:cert_id>", methods=['DELETE'])
@login_required
def delete_certificate(cert_id):
    """
    특정 자격증 하나를 실시간으로 삭제하는 API
    """
    success = ResumeService.delete_certificate(
        user_id=current_user.id,
        cert_id=cert_id
    )

    if success:
        return jsonify({'success': True, 'message': '자격증이 삭제되었습니다.'})
    else:
        return jsonify({'success': False, 'message': '삭제에 실패했거나 권한이 없습니다.'}), 403


# ==================== 이력서 삭제 (AJAX) ====================
@resumes_bp.route("/resume/<int:resume_id>/delete", methods=["POST"])
@login_required
def delete_resume(resume_id):
    """
    이력서 삭제 API
    - S3에서 자격증 이미지 먼저 삭제
    - DB에서 이력서 삭제
    """
    success = ResumeService.delete_resume(resume_id, current_user.id)

    if success:
        return jsonify({"success": True, "message": "이력서가 삭제되었습니다."})
    else:
        return jsonify({"success": False, "message": "이력서 삭제에 실패했습니다."}), 400


# ==================== 공개/비공개 토글 (AJAX) ====================
@resumes_bp.route("/resume/<int:resume_id>/toggle-public", methods=["POST"])
@login_required
def toggle_public(resume_id):
    """
    이력서 공개/비공개 토글 API
    """
    data = request.get_json()
    is_public = data.get("ispublic", False)

    success = ResumeService.toggle_resume_public(resume_id, current_user.id, is_public)

    if success:
        return jsonify({"success": True, "message": "공개 상태가 변경되었습니다."})
    else:
        return jsonify({"success": False, "message": "상태 변경에 실패했습니다."}), 400


# ==================== 공개 이력서 목록 (기업회원용) ====================
@resumes_bp.route("/list")
@login_required
def resume_list():
    """
    공개된 이력서 목록 (기업회원만 접근 가능)
    """
    if current_user.user_type != 1:
        flash("기업회원만 접근 가능한 페이지입니다.", "error")
        return redirect(url_for('auth.main'))

    page = request.args.get('page', 1, type=int)
    per_page = 5

    pagination = ResumeService.get_public_resumes_paginated(page=page, per_page=per_page)

    return render_template(
        "resume/resume_list.html",
        resumes=pagination.items,
        pagination=pagination
    )


# ==================== 공개 이력서 더보기 API (AJAX) ====================
@resumes_bp.route("/api/resumes")
@login_required
def api_resumes():
    """
    공개 이력서 더보기 API (AJAX)
    """
    if current_user.user_type != 1:
        return jsonify({'success': False, 'message': '권한 없음'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = 5

    pagination = ResumeService.get_public_resumes_paginated(page=page, per_page=per_page)

    resumes_html = render_template(
        "resume/_resume_cards.html",
        resumes=pagination.items
    )

    return jsonify({
        'html': resumes_html,
        'has_next': pagination.has_next
    })


# ==================== 기업회원의 이력서 상세보기 ====================
@resumes_bp.route("/resume/<int:resume_id>/view")
@login_required
def view_resume(resume_id):
    """
    기업 회원이 특정 공개 이력서를 조회하는 페이지
    """
    if current_user.user_type != 1:
        flash("기업회원만 접근 가능합니다.", "error")
        return redirect(url_for('auth.main'))

    resume = ResumeService.get_resume_by_id(resume_id)

    if not resume or not resume.is_public:
        flash("비공개 이력서이거나 존재하지 않는 이력서입니다.", "error")
        return redirect(url_for('resumes.resume_list'))

    return render_template("resume/view_resume.html", resume=resume)
