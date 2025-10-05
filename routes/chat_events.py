# sockets/chat_events.py
from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from models import ChatRoom, db
from services.chat_service import ChatService

def init_chat_socketio(socketio):
    def _room(room_id: int) -> str:
        return str(room_id)

    def _user_in_room(room_id: int, user_id: int) -> bool:
        room = ChatRoom.query.filter_by(id=room_id).first()
        return bool(room and (room.applicant_id == user_id or room.employer_id == user_id))

    @socketio.on("connect")
    def handle_connect():
        if not current_user.is_authenticated:
            return False
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
        except Exception:
            db.session.rollback()
            emit("error", {"code": "SERVER_ERROR", "message": "failed to mark as read"})
