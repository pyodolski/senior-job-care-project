from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from services.onboarding import OnboardingService
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 온보딩 관련 라우트를 담당하는 블루프린트 생성
onboarding_bp = Blueprint("onboarding", __name__)

# 온보딩 페이지 - 필수 정보 입력
@onboarding_bp.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    """온보딩 페이지 - 필수 정보 입력"""
    try:
        # 이미 온보딩이 완료된 사용자는 로그인 완료 페이지로 리다이렉트
        if current_user.onboarding_status == 'completed':
            return redirect(url_for("user_session.login_complete"))
        
        if request.method == "GET":
            # 리셋 요청 처리
            if request.args.get('reset') == 'true':
                OnboardingService.reset_onboarding(current_user)
                flash("온보딩을 처음부터 다시 시작합니다.")
            
            # 온보딩 페이지 렌더링
            onboarding_data = OnboardingService.get_onboarding_data(current_user)
            
            # 현재 단계 결정 - 신규 사용자는 1단계부터 시작
            if current_user.onboarding_status == 'pending' and (current_user.onboarding_step is None or current_user.onboarding_step == 0):
                current_step = 1
            else:
                # 저장된 진행 상황이 있으면 해당 단계로, 없으면 1단계
                current_step = max(current_user.onboarding_step or 1, 1)
            
            # 템플릿에 전달할 데이터 준비
            template_data = {
                'user': current_user,
                'current_step': current_step,
                'saved_data': onboarding_data.get('progress', {}),
                'social_type': current_user.social_type
            }
            
            return render_template("onboarding/step_by_step.html", **template_data)
        
        elif request.method == "POST":
            # 필수 정보 입력 처리
            form_data = {}
            
            # 폼 데이터 수집
            logger.info(f"Received form data: {dict(request.form)}")
            
            if request.form.get('name'):
                form_data['name'] = request.form.get('name').strip()
                logger.info(f"Collected name: {form_data['name']}")
            if request.form.get('nickname'):
                form_data['nickname'] = request.form.get('nickname').strip()
                logger.info(f"Collected nickname: {form_data['nickname']}")
            if request.form.get('gender'):
                form_data['gender'] = request.form.get('gender')
                logger.info(f"Collected gender: {form_data['gender']}")
            if request.form.get('birth_date'):
                form_data['birth_date'] = request.form.get('birth_date')
                logger.info(f"Collected birth_date: {form_data['birth_date']} (type: {type(form_data['birth_date'])})")
            
            # 현재 단계 확인
            current_step = int(request.form.get('step', current_user.onboarding_step or 1))
            
            # 4단계에서 모든 필수 정보가 있으면 완료 처리
            # 현재 폼 데이터와 이전에 저장된 데이터를 합쳐서 확인
            onboarding_data = OnboardingService.get_onboarding_data(current_user)
            saved_progress = onboarding_data.get('progress', {})
            
            # 현재 입력 데이터와 저장된 데이터 병합
            combined_data = saved_progress.copy()
            combined_data.update(form_data)
            
            all_required_fields = ['name', 'nickname', 'gender', 'birth_date']
            is_complete = current_step == 4 and all(field in combined_data and combined_data[field] for field in all_required_fields)
            
            # 데이터 검증 - 병합된 데이터로 검증 (본인 제외)
            validation_errors = OnboardingService.validate_onboarding_data(combined_data, current_step, current_user.id)
            
            if validation_errors:
                # 검증 오류가 있는 경우
                onboarding_data = OnboardingService.get_onboarding_data(current_user)
                template_data = {
                    'user': current_user,
                    'current_step': current_step,
                    'progress_data': form_data,  # 입력한 데이터 유지
                    'social_type': current_user.social_type,
                    'errors': validation_errors
                }
                
                return render_template("onboarding/step_by_step.html", **template_data)
            
            # 완료 처리 확인
            if is_complete:
                # 온보딩 완료 처리 - 병합된 데이터 사용
                logger.info(f"Attempting to complete onboarding for user {current_user.id} with data: {combined_data}")
                success = OnboardingService.complete_onboarding(current_user, combined_data)
                
                if success:
                    flash("회원가입이 완료되었습니다!")
                    return redirect(url_for("user_session.login_complete"))
                else:
                    flash("회원가입 처리 중 오류가 발생했습니다. 다시 시도해주세요.")
                    # 완료 처리 실패 시 현재 페이지 다시 렌더링
                    template_data = {
                        'user': current_user,
                        'current_step': current_step,
                        'saved_data': combined_data,
                        'social_type': current_user.social_type
                    }
                    return render_template("onboarding/step_by_step.html", **template_data)
            else:
                # 진행 상황 저장
                success = OnboardingService.save_onboarding_progress(current_user, form_data, current_step)
                
                if success:
                    # 다음 단계로 진행하거나 현재 단계 유지
                    next_step = min(current_step + 1, 4)
                    
                    onboarding_data = OnboardingService.get_onboarding_data(current_user)
                    template_data = {
                        'user': current_user,
                        'current_step': next_step,
                        'progress_data': onboarding_data.get('progress', {}),
                        'social_type': current_user.social_type,
                        'success_message': '정보가 저장되었습니다.'
                    }
                    
                    return render_template("onboarding/step_by_step.html", **template_data)
                else:
                    flash("정보 저장 중 오류가 발생했습니다. 다시 시도해주세요.")
            
            # 오류 발생 시 현재 페이지 다시 렌더링
            onboarding_data = OnboardingService.get_onboarding_data(current_user)
            template_data = {
                'user': current_user,
                'current_step': current_step,
                'progress_data': form_data,
                'social_type': current_user.social_type
            }
            
            return render_template("onboarding/step_by_step.html", **template_data)
            
    except Exception as e:
        logger.error(f"Error in onboarding route: {str(e)}")
        flash("온보딩 처리 중 오류가 발생했습니다. 다시 시도해주세요.")
        return redirect(url_for("auth.home"))

# AJAX 진행 상황 저장 라우트
@onboarding_bp.route("/onboarding/save-progress", methods=["POST"])
@login_required
def save_onboarding_progress():
    """AJAX로 온보딩 진행 상황 저장"""
    try:
        # JSON 데이터 파싱
        if not request.is_json:
            return {"success": False, "error": "JSON 데이터가 필요합니다."}, 400
        
        data = request.get_json()
        if not data:
            return {"success": False, "error": "데이터가 없습니다."}, 400
        
        # 필수 필드 확인
        step = data.get('step')
        form_data = data.get('data', {})
        
        if step is None:
            return {"success": False, "error": "단계 정보가 필요합니다."}, 400
        
        # 단계 유효성 검사
        try:
            step = int(step)
            if step < 0 or step > 4:
                return {"success": False, "error": "유효하지 않은 단계입니다."}, 400
        except (ValueError, TypeError):
            return {"success": False, "error": "단계는 숫자여야 합니다."}, 400
        
        # 데이터 검증
        validation_errors = OnboardingService.validate_onboarding_data(form_data, step, current_user.id)
        if validation_errors:
            return {
                "success": False, 
                "error": "데이터 검증 실패", 
                "validation_errors": validation_errors
            }, 400
        
        # 진행 상황 저장
        success = OnboardingService.save_onboarding_progress(current_user, form_data, step)
        
        if success:
            return {
                "success": True,
                "message": "진행 상황이 저장되었습니다.",
                "step": step,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"success": False, "error": "저장 중 오류가 발생했습니다."}, 500
            
    except Exception as e:
        logger.error(f"Error in save_onboarding_progress: {str(e)}")
        return {"success": False, "error": "서버 오류가 발생했습니다."}, 500

# AJAX 진행 상황 조회 라우트
@onboarding_bp.route("/onboarding/get-progress", methods=["GET"])
@login_required
def get_onboarding_progress():
    """AJAX로 온보딩 진행 상황 조회"""
    try:
        # 온보딩 데이터 조회
        onboarding_data = OnboardingService.get_onboarding_data(current_user)
        
        # 응답 데이터 구성
        response_data = {
            "success": True,
            "user_id": current_user.id,
            "onboarding_status": current_user.onboarding_status,
            "current_step": current_user.onboarding_step or 0,
            "progress_data": onboarding_data.get('progress', {}),
            "timestamp": onboarding_data.get('timestamp'),
            "social_type": current_user.social_type,
            "is_profile_complete": current_user.is_profile_complete
        }
        
        # 저장된 진행 상황이 있는지 확인
        if onboarding_data.get('progress'):
            response_data["saved_progress"] = True
        else:
            response_data["saved_progress"] = False
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in get_onboarding_progress: {str(e)}")
        return {"success": False, "error": "진행 상황 조회 중 오류가 발생했습니다."}, 500

# 닉네임 중복 검사 AJAX 라우트
@onboarding_bp.route("/onboarding/check-nickname", methods=["POST"])
@login_required
def check_nickname_availability():
    """AJAX로 닉네임 중복 검사"""
    try:
        # JSON 데이터 파싱
        if not request.is_json:
            return {"success": False, "error": "JSON 데이터가 필요합니다."}, 400
        
        data = request.get_json()
        nickname = data.get('nickname', '').strip()
        
        if not nickname:
            return {"success": False, "error": "닉네임을 입력해주세요."}, 400
        
        # 기본 검증
        if len(nickname) < 2:
            return {
                "success": False, 
                "available": False,
                "error": "닉네임은 2자 이상 입력해주세요."
            }
        
        if len(nickname) > 20:
            return {
                "success": False, 
                "available": False,
                "error": "닉네임은 20자 이하로 입력해주세요."
            }
        
        # 중복 검사 (본인 제외)
        is_available = OnboardingService.check_nickname_availability(nickname, current_user.id)
        
        if is_available:
            return {
                "success": True,
                "available": True,
                "message": "사용 가능한 닉네임입니다."
            }
        else:
            return {
                "success": True,
                "available": False,
                "error": "이미 사용 중인 닉네임입니다."
            }
            
    except Exception as e:
        logger.error(f"Error in check_nickname_availability: {str(e)}")
        return {"success": False, "error": "닉네임 검사 중 오류가 발생했습니다."}, 500

# 온보딩 재개 라우트
@onboarding_bp.route("/onboarding/resume")
@login_required
def resume_onboarding():
    """중단된 온보딩 재개"""
    try:
        # 이미 온보딩이 완료된 사용자는 로그인 완료 페이지로 리다이렉트
        if current_user.onboarding_status == 'completed':
            return redirect(url_for("user_session.login_complete"))
        
        # 온보딩 데이터가 없는 경우 기본 온보딩으로 리다이렉트
        if not current_user.onboarding_data:
            return redirect(url_for("onboarding.onboarding"))
        
        # 중단된 온보딩 데이터 복원
        onboarding_data = OnboardingService.get_onboarding_data(current_user)
        
        # 진행 단계 복원
        saved_step = onboarding_data.get('step', 0)
        progress_data = onboarding_data.get('progress', {})
        
        # 최소 1단계는 보장
        if saved_step < 1:
            saved_step = 1
        
        # 템플릿에 전달할 데이터 준비
        template_data = {
            'user': current_user,
            'current_step': saved_step,
            'progress_data': progress_data,
            'social_type': current_user.social_type,
            'is_resume': True,
            'resume_message': f'{saved_step}단계부터 이어서 진행합니다.'
        }
        
        return render_template("onboarding/resume.html", **template_data)
        
    except Exception as e:
        logger.error(f"Error in resume_onboarding route: {str(e)}")
        flash("온보딩 재개 중 오류가 발생했습니다. 처음부터 다시 시작합니다.")
        return redirect(url_for("onboarding.onboarding"))