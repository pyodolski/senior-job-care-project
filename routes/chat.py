"""
채팅 관련 라우트 모듈
===================

채팅방 목록, 채팅 화면, 메시지 전송 등의 웹 라우트를 처리합니다.

주요 기능:
- 채팅방 목록 조회
- 채팅 화면 표시
- 메시지 전송 (AJAX)
- 읽지 않은 메시지 관리

작성자: [팀명]
최종 수정일: 2025-01-09
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.chat_service import ChatService
from services.application_service import ApplicationService

# 채팅 관련 블루프린트 생성
chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat")
@login_required
def chat_list():
    """
    채팅방 목록 페이지
    =================
    
    기능:
    - 사용자가 참여한 모든 채팅방 목록 표시
    - 각 채팅방의 상대방 정보, 마지막 메시지, 읽지 않은 메시지 수 표시
    - 최근 활동순으로 정렬
    
    URL: GET /chat
    템플릿: chat/chat_list.html
    
    반환값:
    - chat_rooms: 채팅방 목록 (상대방 정보, 마지막 메시지 등 포함)
    - unread_total: 전체 읽지 않은 메시지 수
    """
    
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
    """
    채팅방 화면
    ===========
    
    기능:
    - 특정 채팅방의 메시지 목록 표시
    - 메시지 전송 폼 제공
    - 실시간 메시지 업데이트 (JavaScript)
    - 메시지 읽음 처리
    
    URL: GET /chat/<room_id>
    템플릿: chat/chat_room.html
    
    매개변수:
    - room_id: 채팅방 ID
    
    반환값:
    - room: 채팅방 정보
    - messages: 메시지 목록
    - other_user: 상대방 정보
    - job: 관련 공고 정보
    """
    
    # 메시지 목록 조회 (권한 확인 포함)
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
    """
    메시지 전송 (AJAX)
    ==================
    
    기능:
    - 채팅방에 새 메시지 전송
    - JSON 형태로 결과 반환
    - 실시간 업데이트를 위한 메시지 정보 반환
    
    URL: POST /chat/<room_id>/send
    
    매개변수:
    - room_id: 채팅방 ID
    
    요청 데이터:
    - message: 메시지 내용 (필수)
    - message_type: 메시지 타입 (기본값: 'text')
    
    반환값 (JSON):
    - success: 성공 여부
    - message: 결과 메시지
    - message_data: 전송된 메시지 정보 (성공 시)
    """
    
    try:
        # 요청 데이터 추출
        data = request.get_json()
        message_content = data.get('message', '').strip()
        message_type = data.get('message_type', 'text')
        
        # 메시지 내용 검증
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
    """
    메시지 목록 조회 (AJAX)
    ======================
    
    기능:
    - 채팅방의 메시지 목록을 JSON으로 반환
    - 페이지네이션 지원
    - 실시간 업데이트용
    
    URL: GET /chat/<room_id>/messages
    
    매개변수:
    - room_id: 채팅방 ID
    
    쿼리 파라미터:
    - page: 페이지 번호 (기본값: 1)
    - per_page: 페이지당 메시지 수 (기본값: 50)
    
    반환값 (JSON):
    - success: 성공 여부
    - messages: 메시지 목록
    - has_more: 더 많은 메시지 존재 여부
    """
    
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
    """
    채팅방 나가기
    ============
    
    기능:
    - 채팅방을 비활성화하여 목록에서 제거
    - 상대방은 계속 채팅방을 볼 수 있음
    
    URL: POST /chat/<room_id>/leave
    
    매개변수:
    - room_id: 채팅방 ID
    
    반환값:
    - 성공 시: 채팅 목록 페이지로 리다이렉트
    - 실패 시: 에러 메시지와 함께 채팅방으로 리다이렉트
    """
    
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
    """
    공고 ID로 채팅방 찾기
    ====================
    
    기능:
    - 특정 공고와 관련된 사용자의 채팅방 찾기
    - 지원자 또는 고용주로서 참여한 채팅방 조회
    
    URL: GET /chat/find-room/<job_id>
    
    매개변수:
    - job_id: 공고 ID
    
    반환값 (JSON):
    - success: 성공 여부
    - room_id: 채팅방 ID (찾은 경우)
    - message: 결과 메시지
    """
    
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