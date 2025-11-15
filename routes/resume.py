from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.resume_service import ResumeService
from models import Category, WorkType, Strength
from datetime import time, datetime
from utils.files_handler import generate_presigned_get_url

resumes_bp = Blueprint("resumes", __name__)


# 내 이력서 목록
@resumes_bp.route("/my-resumes")
@login_required
def my_view_resume():
    """로그인한 사용자의 모든 이력서 목록을 보여주는 페이지"""
    resumes = ResumeService.get_resumes_by_user(current_user.id)

    return render_template(
        "resume/my_view_resume.html",
        resumes=resumes
    )


#  내 이력서 상세보기
@resumes_bp.route("/my-resume/<int:resume_id>")
@login_required
def my_resume_detail(resume_id):
    """현재 로그인한 사용자 본인의 이력서 상세보기"""
    resume, is_owner = ResumeService.get_resume_permission_check(
        resume_id,
        current_user.id
    )

    if not resume:
        return redirect(url_for('resumes.my_view_resume'))

    if not is_owner:
        return redirect(url_for('resumes.my_view_resume'))

    # 프로필 이미지 URL 생성
    profile_url = None
    if resume.user.profile_image:
        profile_url = generate_presigned_get_url(resume.user.profile_image, expires=900)

    return render_template('resume/my_resume_detail.html', resume=resume, now=datetime.now(), profile_url=profile_url)


# 이력서 작성
@resumes_bp.route("/resume/create", methods=["GET", "POST"])
@login_required
def create_resume():
    """새로운 이력서를 작성하는 페이지 """
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

        # 요일 협의 가능 여부 확인
        is_day_negotiable = 'is_day_negotiable' in request.form
        
        # 폼 데이터 수집
        resume_data = {
            'is_public': 'is_public' in request.form,
            'desired_categories': ",".join(request.form.getlist('categories')),
            'desired_work_type': request.form.get('desired_work_type'),
            'work_monday': 'work_monday' in request.form or is_day_negotiable,
            'work_tuesday': 'work_tuesday' in request.form or is_day_negotiable,
            'work_wednesday': 'work_wednesday' in request.form or is_day_negotiable,
            'work_thursday': 'work_thursday' in request.form or is_day_negotiable,
            'work_friday': 'work_friday' in request.form or is_day_negotiable,
            'work_saturday': 'work_saturday' in request.form or is_day_negotiable,
            'work_sunday': 'work_sunday' in request.form or is_day_negotiable,
            'is_time_negotiable': 'is_time_negotiable' in request.form,
            'desired_start_time': parse_time(request.form.get('start_time')),
            'desired_end_time': parse_time(request.form.get('end_time')),
            'experience': request.form.get('experience'),
            'self_introduction': request.form.get('self_introduction'),
            'call_available_time': request.form.get('call_available_time'),
            'privacy_consent': 'privacy_consent' in request.form,
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

    # GET
    return render_template(
        "resume/edit_resume.html",
        resume=None,
        all_categories=list(Category),
        all_work_types=list(WorkType),
        all_strengths=list(Strength),
        submit_url=url_for('resumes.resume_preview')
    )


#  이력서 수정
@resumes_bp.route("/resume/<int:resume_id>/edit", methods=["GET", "POST"])
@login_required
def edit_resume(resume_id):
    """기존 이력서를 수정하는 페이지 """
    resume, is_owner = ResumeService.get_resume_permission_check(resume_id, current_user.id)

    if not resume:
        return redirect(url_for('resumes.my_view_resume'))

    if not is_owner:
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

        # 요일 협의 가능 여부 확인
        is_day_negotiable = 'is_day_negotiable' in request.form
        
        # 폼 데이터 수집
        resume_data = {
            'is_public': 'is_public' in request.form,
            'desired_categories': ",".join(request.form.getlist('categories')),
            'desired_work_type': request.form.get('desired_work_type'),
            'work_monday': 'work_monday' in request.form or is_day_negotiable,
            'work_tuesday': 'work_tuesday' in request.form or is_day_negotiable,
            'work_wednesday': 'work_wednesday' in request.form or is_day_negotiable,
            'work_thursday': 'work_thursday' in request.form or is_day_negotiable,
            'work_friday': 'work_friday' in request.form or is_day_negotiable,
            'work_saturday': 'work_saturday' in request.form or is_day_negotiable,
            'work_sunday': 'work_sunday' in request.form or is_day_negotiable,
            'is_time_negotiable': 'is_time_negotiable' in request.form,
            'desired_start_time': parse_time(request.form.get('start_time')),
            'desired_end_time': parse_time(request.form.get('end_time')),
            'experience': request.form.get('experience'),
            'self_introduction': request.form.get('self_introduction'),
            'call_available_time': request.form.get('call_available_time'),
            'privacy_consent': 'privacy_consent' in request.form,
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

    # GET
    return render_template(
        "resume/edit_resume.html",
        resume=resume,
        all_categories=list(Category),
        all_work_types=list(WorkType),
        all_strengths=list(Strength),
        submit_url=url_for('resumes.edit_resume', resume_id=resume_id)
    )


# 이력서 미리보기
@resumes_bp.route("/resume/preview", methods=["POST"])
@login_required
def resume_preview():
    """이력서 작성 완료 후 미리보기 페이지"""
    import json
    from flask import session

    form_data = request.form.to_dict(flat=False)
    session['resume_draft'] = json.dumps(form_data)
    

    print("=== 폼 데이터 ===")
    for key, value in request.form.items():
        print(f"{key}: {value}")
    print("================")

    is_day_negotiable = request.form.get('is_day_negotiable') == 'on'
    
    if is_day_negotiable:
        days_text = '요일 협의 가능'
    else:
        work_days = []
        if request.form.get('work_monday'): work_days.append('월')
        if request.form.get('work_tuesday'): work_days.append('화')
        if request.form.get('work_wednesday'): work_days.append('수')
        if request.form.get('work_thursday'): work_days.append('목')
        if request.form.get('work_friday'): work_days.append('금')
        if request.form.get('work_saturday'): work_days.append('토')
        if request.form.get('work_sunday'): work_days.append('일')
        days_text = ', '.join(work_days) if work_days else '미설정'
    time_text = '시간 협의 가능' if request.form.get('is_time_negotiable') else f"{request.form.get('start_time', '09:00')} ~ {request.form.get('end_time', '18:00')}"
    
    # 미리보기 데이터 생성
    preview_data = {
        'category': request.form.get('categories', '선택 안 함'),
        'work_type': request.form.get('desired_work_type', '선택 안 함'),
        'days': days_text,
        'time': time_text,
        'experience': [exp.strip() for exp in request.form.get('experience', '').split('\n') if exp.strip()] or ['작성 안 함'],
        'certificates': request.form.getlist('certificate_names') or ['없음'],
        'strengths': ', '.join(request.form.getlist('strengths')) or '선택 안 함',
        'walkable': f"{request.form.get('walkable_minutes', '0')}분",
        'physical': [note.strip() for note in request.form.get('physical_notes', '').split('\n') if note.strip()] or ['작성 안 함'],
        'commute': f"{request.form.get('commute_time', '0')}분",
        'introduction': request.form.get('self_introduction', '작성 안 함'),
        'call_time': request.form.get('call_available_time', '언제든지'),
        'privacy': '동의함' if request.form.get('privacy_consent') else '미동의',
        'public': '공개' if request.form.get('is_public') else '비공개'
    }

    
    return render_template(
        "resume/resume_preview.html",
        preview_data=preview_data,
        resume_data_json=session.get('resume_draft', '{}')
    )


# 이력서 제출
@resumes_bp.route("/resume/submit", methods=["POST"])
@login_required
def submit_resume():
    """미리보기에서 제출하기 버튼 클릭 시 실제 저장"""
    import json
    from flask import session
    
    # 세션에서 저장된 데이터 가져오기
    resume_draft = session.get('resume_draft')
    if not resume_draft:
        flash("세션이 만료되었습니다. 다시 작성해주세요.", "error")
        return redirect(url_for('resumes.create_resume'))
    
    form_data = json.loads(resume_draft)
    
    # 시간 파싱 헬퍼 함수
    def parse_time(time_str):
        if not time_str:
            return None
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        except ValueError:
            return None
    
    # 요일 협의 가능 여부 확인
    is_day_negotiable = 'is_day_negotiable' in form_data
    
    # 데이터 변환
    resume_data = {
        'is_public': 'is_public' in form_data,
        'desired_categories': ",".join(form_data.get('categories', [])),
        'desired_work_type': form_data.get('desired_work_type', [None])[0],
        'work_monday': 'work_monday' in form_data or is_day_negotiable,
        'work_tuesday': 'work_tuesday' in form_data or is_day_negotiable,
        'work_wednesday': 'work_wednesday' in form_data or is_day_negotiable,
        'work_thursday': 'work_thursday' in form_data or is_day_negotiable,
        'work_friday': 'work_friday' in form_data or is_day_negotiable,
        'work_saturday': 'work_saturday' in form_data or is_day_negotiable,
        'work_sunday': 'work_sunday' in form_data or is_day_negotiable,
        'is_time_negotiable': 'is_time_negotiable' in form_data,
        'desired_start_time': parse_time(form_data.get('start_time', [None])[0]),
        'desired_end_time': parse_time(form_data.get('end_time', [None])[0]),
        'experience': form_data.get('experience', [None])[0],
        'self_introduction': form_data.get('self_introduction', [None])[0],
        'call_available_time': form_data.get('call_available_time', [None])[0],
        'privacy_consent': 'privacy_consent' in form_data,
        'strengths': ",".join(form_data.get('strengths', [])),
        'commute_time': int(form_data.get('commute_time', [0])[0]) if form_data.get('commute_time') else None,
        'walkable_minutes': int(form_data.get('walkable_minutes', [0])[0]) if form_data.get('walkable_minutes') else None,
        'physical_notes': form_data.get('physical_notes', [None])[0],
    }
    
    # 이력서 생성
    new_resume = ResumeService.create_resume(
        user_id=current_user.id,
        resume_data=resume_data,
        certificate_names=form_data.get('certificate_names', []),
        certificate_images=[]  # 파일은 세션에 저장할 수 없으므로 빈 리스트
    )
    
    if new_resume:
        session.pop('resume_draft', None)
        return redirect(url_for('resumes.my_view_resume'))
    else:
        return redirect(url_for('resumes.create_resume'))


# 자격증 삭제
@resumes_bp.route("/resume/certificate/delete/<int:cert_id>", methods=['DELETE'])
@login_required
def delete_certificate(cert_id):
    """특정 자격증 하나 삭제 """
    success = ResumeService.delete_certificate(
        user_id=current_user.id,
        cert_id=cert_id
    )

    if success:
        return jsonify({'success': True, 'message': '자격증이 삭제되었습니다.'})
    else:
        return jsonify({'success': False, 'message': '삭제에 실패했거나 권한이 없습니다.'}), 403


# 이력서 삭제
@resumes_bp.route("/resume/<int:resume_id>/delete", methods=["POST"])
@login_required
def delete_resume(resume_id):
    """이력서 삭제 API"""
    success = ResumeService.delete_resume(resume_id, current_user.id)

    if success:
        return jsonify({"success": True, "message": "이력서가 삭제되었습니다."})
    else:
        return jsonify({"success": False, "message": "이력서 삭제에 실패했습니다."}), 400


#  공개/비공개 토글
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


# 공개 이력서 목록 (기업회원용)
@resumes_bp.route("/list")
@login_required
def resume_list():
    """좋아요한 이력서 목록 (기업회원만 접근 가능)"""
    if current_user.user_type != 1:
        return redirect(url_for('auth.main'))

    page = request.args.get('page', 1, type=int)
    per_page = 5

    # 좋아요한 이력서만 조회
    from models import ResumeFavorite, Resume, User
    
    favorites = ResumeFavorite.query.filter_by(user_id=current_user.id).all()
    resume_ids = [fav.resume_id for fav in favorites]
    
    # 좋아요한 이력서 목록 조회
    pagination = Resume.query.join(User).filter(
        Resume.id.in_(resume_ids),
        Resume.is_public == True
    ).order_by(Resume.updated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "resume/resume_list.html",
        resumes=pagination.items,
        pagination=pagination
    )


#  공개 이력서 더보기
@resumes_bp.route("/api/resumes")
@login_required
def api_resumes():
    """공개 이력서 더보기 """
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


# 기업회원의 이력서 상세보기
@resumes_bp.route("/resume/<int:resume_id>/view")
@login_required
def view_resume(resume_id):
    """기업 회원이 특정 공개 이력서를 조회하는 페이지"""
    if current_user.user_type != 1:
        return redirect(url_for('auth.main'))

    resume = ResumeService.get_resume_by_id(resume_id)

    if not resume or not resume.is_public:
        return redirect(url_for('resumes.resume_list'))

    return render_template("resume/view_resume.html", resume=resume)



#  이력서 좋아요 토글
@resumes_bp.route("/api/resume/<int:resume_id>/favorite", methods=["POST"])
@login_required
def toggle_resume_favorite(resume_id):
    """이력서 좋아요 토글 (기업회원만 가능)"""
    if current_user.user_type != 1:
        return jsonify({"success": False, "message": "기업회원만 가능합니다."}), 403
    
    from models import ResumeFavorite, Resume, db
    
    # 이력서 존재 확인
    resume = Resume.query.get_or_404(resume_id)
    
    # 이미 좋아요했는지 확인
    favorite = ResumeFavorite.query.filter_by(
        user_id=current_user.id,
        resume_id=resume_id
    ).first()
    
    if favorite:
        # 좋아요 취소
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({"success": True, "favorited": False, "message": "좋아요가 취소되었습니다."})
    else:
        # 좋아요 추가
        new_favorite = ResumeFavorite(
            user_id=current_user.id,
            resume_id=resume_id
        )
        db.session.add(new_favorite)
        db.session.commit()
        return jsonify({"success": True, "favorited": True, "message": "좋아요가 추가되었습니다."})
