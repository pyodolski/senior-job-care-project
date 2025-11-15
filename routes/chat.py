"""채팅 관련 라우트 """

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.chat_service import ChatService
from services.application_service import ApplicationService
from utils.files_handler import generate_presigned_get_url

# 채팅 관련 블루프린트 생성
chat_bp = Blueprint("chat", __name__)


@chat_bp.app_template_global()
def generate_url(key):
    """템플릿에서 파일 경로(key)를 Presigned URL로 변환하는 함수"""
    if not key:
        return None
    return generate_presigned_get_url(key)

@chat_bp.route("/chat")
@login_required
def chat_list():
    """채팅방 목록 페이지"""
    
    # 사용자의 채팅방 목록 조회
    chat_rooms = ChatService.get_user_chat_rooms(current_user.id)
    
    # 전체 읽지 않은 메시지 수
    unread_total = ChatService.get_unread_message_count(current_user.id)
    
    return render_template("chat/chat_list.html", 
                         chat_rooms=chat_rooms, 
                         unread_total=unread_total)

@chat_bp.route("/chat/<int:room_id>")
@login_required
def chat_room(room_id):
    """채팅방 화면"""
    
    # 메시지 목록 조회
    messages_pagination = ChatService.get_chat_messages(room_id, current_user.id)
    
    # 채팅방 정보 조회
    from models import ChatRoom
    room = ChatRoom.query.filter_by(id=room_id).first_or_404()
    
    # 상대방 정보
    other_user = room.employer if room.applicant_id == current_user.id else room.applicant

    # 메시지를 읽음으로 표시
    ChatService.mark_messages_as_read(room_id, current_user.id)
    
    return render_template("chat/chat_room.html", 
                         room=room, 
                         messages_pagination=messages_pagination,
                         other_user=other_user,
                         job=room.job)

@chat_bp.route("/chat/<int:room_id>/send", methods=["POST"])
@login_required
def send_message(room_id):
    """메시지 전송   """
    
    try:
        data = request.get_json()
        message_content = data.get('message', '').strip()
        message_type = data.get('message_type', 'text')

        if not message_content:
            return jsonify({
                'success': False,
                'message': '메시지 내용을 입력해주세요.'
            }), 400
        
        # 메시지 전송
        message = ChatService.send_message(
            room_id=room_id,
            sender_id=current_user.id,
            message=message_content,
            message_type=message_type
        )
        
        return jsonify({
            'success': True,
            'message': '메시지가 전송되었습니다.',
            'message_data': {
                'id': message.id,
                'message': message.message,
                'sender_id': message.sender_id,
                'sender_name': current_user.nickname,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'message_type': message.message_type
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '메시지 전송 중 오류가 발생했습니다.'
        }), 500

@chat_bp.route("/chat/<int:room_id>/messages")
@login_required
def get_messages(room_id):
    """메시지 목록 조회"""
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # 메시지 목록 조회
        messages_pagination = ChatService.get_chat_messages(
            room_id, current_user.id, page, per_page
        )
        
        messages_data = []
        for message in messages_pagination.items:
            messages_data.append({
                'id': message.id,
                'message': message.message,
                'sender_id': message.sender_id,
                'sender_name': message.sender.nickname,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'message_type': message.message_type,
                'is_read': message.is_read
            })
        
        return jsonify({
            'success': True,
            'messages': messages_data,
            'has_more': messages_pagination.has_next
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '메시지 조회 중 오류가 발생했습니다.'
        }), 500

@chat_bp.route("/chat/<int:room_id>/leave", methods=["POST"])
@login_required
def leave_chat_room(room_id):
    """채팅방 나가기"""
    
    try:
        ChatService.deactivate_chat_room(room_id, current_user.id)
        flash("채팅방을 나갔습니다.", "success")
        return redirect(url_for("chat.chat_list"))
        
    except Exception as e:
        flash("채팅방 나가기 중 오류가 발생했습니다.", "error")
        return redirect(url_for("chat.chat_room", room_id=room_id))

@chat_bp.route("/chat/find-room/<int:job_id>")
@login_required
def find_chat_room(job_id):
    """공고 ID로 채팅방 찾기"""
    
    try:
        from models import ChatRoom
        
        # 현재 사용자가 지원자 또는 고용주로 참여한 채팅방 찾기 (나간 사용자도 포함)
        room = ChatRoom.query.filter(
            ChatRoom.job_id == job_id,
            (ChatRoom.applicant_id == current_user.id) | 
            (ChatRoom.employer_id == current_user.id)
        ).first()
        
        if room:
            return jsonify({
                'success': True,
                'room_id': room.id,
                'message': '채팅방을 찾았습니다.'
            })
        else:
            return jsonify({
                'success': False,
                'message': '채팅방을 찾을 수 없습니다.'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '채팅방 검색 중 오류가 발생했습니다.'
        }), 500