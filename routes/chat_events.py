# sockets/chat_events.py
from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from models import ChatRoom, ChatMessage, db
from services.chat_service import ChatService

def init_chat_socketio(socketio):
    # 채팅방 룸명
    def _room(room_id: int) -> str:
        return str(room_id)

    # ADD: 사용자 개인 룸 이름
    def _user_room(user_id: int) -> str:
        return f"user:{user_id}"

    # 방 접근 권한 확인
    def _user_in_room(room_id: int, user_id: int) -> bool:
        room = ChatRoom.query.filter_by(id=room_id).first()
        return bool(room and (room.applicant_id == user_id or room.employer_id == user_id))

    # 미읽음 합계 (전체 - 확장용)
    def _calc_unread_total(user_id: int) -> int:
        return ChatService.get_unread_message_count(user_id)

    #특정 방의 미읽음 (사용자 기준: 상대가 보낸 미읽음 수)
    def _calc_room_unread(room_id: int, user_id: int) -> int:
        return ChatMessage.query.filter_by(room_id=room_id, is_read=False)\
            .filter(ChatMessage.sender_id != user_id).count()

    @socketio.on("connect")
    def handle_connect():
        if not current_user.is_authenticated:
            return False
        #  사용자 개인 룸
        join_room(_user_room(current_user.id))
        emit("connected", {"sid": request.sid, "user_id": current_user.id})

    @socketio.on("join")
    def handle_join(data):
        if not current_user.is_authenticated:
            return False
        room_id = int(data.get("room_id", 0))
        if room_id <= 0:
            emit("error", {"code": "BAD_REQUEST", "message": "invalid room_id"})
            return
        if not _user_in_room(room_id, current_user.id):
            emit("error", {"code": "FORBIDDEN", "message": "no permission for room"})
            return
        join_room(_room(room_id))
        emit("joined", {"room_id": room_id}, to=request.sid)

    @socketio.on("leave")
    def handle_leave(data):
        if not current_user.is_authenticated:
            return False
        room_id = int(data.get("room_id", 0))
        if room_id <= 0:
            emit("error", {"code": "BAD_REQUEST", "message": "invalid room_id"})
            return
        leave_room(_room(room_id))
        emit("left", {"room_id": room_id}, to=request.sid)

    @socketio.on("send_message")
    def handle_send_message(data):
        if not current_user.is_authenticated:
            return False
        room_id = int(data.get("room_id", 0))
        content = (data.get("message") or "").strip()
        msg_type = (data.get("message_type") or "text").strip()
        if room_id <= 0 or not content:
            emit("error", {"code": "BAD_REQUEST", "message": "room_id/message required"})
            return
        if not _user_in_room(room_id, current_user.id):
            emit("error", {"code": "FORBIDDEN", "message": "no permission for room"})
            return
        try:
            msg = ChatService.send_message(room_id, current_user.id, content, msg_type)
            payload = {
                "id": msg.id,
                "room_id": room_id,
                "message": msg.message,
                "message_type": msg.message_type,
                "sender_id": msg.sender_id,
                "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "is_read": msg.is_read,
            }
            socketio.emit("new_message", payload, to=_room(room_id))

            # 마지막 메시지 변경 수신자/발신자 개인룸에 전송 (목록 갱신용)
            last_msg_event = {
                "room_id": room_id,
                "message": msg.message,
                "message_type": msg.message_type,
                "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }

            # 수신자 미읽음 방별/ 배지 미읽음 갱신
            room = ChatRoom.query.get(room_id)
            receiver_id = room.employer_id if msg.sender_id == room.applicant_id else room.applicant_id
            # 개인 룸으로 송신: 수신자/발신자 모두에게 보내면 양쪽 목록이 갱신됨
            socketio.emit("last_message_updated", last_msg_event,to=_user_room(receiver_id))  # 수신자 목록 갱신 [web:14][web:72]
            socketio.emit("last_message_updated", last_msg_event,to=_user_room(msg.sender_id))  # 발신자 목록 갱신 [web:14][web:72]
            #전체 미읽음 합계
            unread_total = _calc_unread_total(receiver_id)
            socketio.emit("unread_total", {"count": unread_total}, to=_user_room(receiver_id))

            # 해당 방 미읽음 수
            room_unread = _calc_room_unread(room_id, receiver_id)
            socketio.emit("room_unread_count", {"room_id": room_id, "count": room_unread}, to=_user_room(receiver_id))

        except Exception:
            db.session.rollback()
            emit("error", {"code": "SERVER_ERROR", "message": "failed to send message"})

    @socketio.on("read_messages")
    def handle_read_messages(data):
        if not current_user.is_authenticated:
            return False
        room_id = int(data.get("room_id", 0))
        if room_id <= 0:
            emit("error", {"code": "BAD_REQUEST", "message": "invalid room_id"})
            return
        if not _user_in_room(room_id, current_user.id):
            emit("error", {"code": "FORBIDDEN", "message": "no permission for room"})
            return
        try:
            ChatService.mark_messages_as_read(room_id, current_user.id)
            socketio.emit("messages_read", {"room_id": room_id, "reader_id": current_user.id}, to=_room(room_id))

            # 본인 배지/ 방별 미읽음 갱신
            my_total = _calc_unread_total(current_user.id)
            socketio.emit("unread_total", {"count": my_total}, to=_user_room(current_user.id))

            my_room_unread = _calc_room_unread(room_id, current_user.id)
            socketio.emit("room_unread_count", {"room_id": room_id, "count": my_room_unread}, to=_user_room(current_user.id))

            # 상대방 배지도 영향이 있으면(선택) 상대 갱신
            room = ChatRoom.query.get(room_id)
            other_id = room.employer_id if current_user.id == room.applicant_id else room.applicant_id
            other_total = _calc_unread_total(other_id)
            socketio.emit("unread_total", {"count": other_total}, to=_user_room(other_id))

            other_room_unread = _calc_room_unread(room_id, other_id)
            socketio.emit("room_unread_count", {"room_id": room_id, "count": other_room_unread}, to=_user_room(other_id))

        except Exception:
            db.session.rollback()
            emit("error", {"code": "SERVER_ERROR", "message": "failed to mark as read"})
