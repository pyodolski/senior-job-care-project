"""채팅 서비스 """

from models import db, ChatRoom, ChatMessage, JobPost, User, JobApplication
from sqlalchemy import select,or_, and_, desc, func, case
from datetime import datetime
from sqlalchemy.orm import aliased, joinedload
from utils.files_handler import generate_presigned_get_url

class ChatService:
    
    @staticmethod
    def create_or_get_chat_room(job_id, applicant_id, employer_id):
        """채팅방 생성 또는 기존 채팅방 조회"""
        # 기존 채팅방 확인
        existing_room = ChatRoom.query.filter_by(
            job_id=job_id,
            applicant_id=applicant_id,
            employer_id=employer_id
        ).first()
        
        if existing_room:
            # 비활성화된 채팅방이면 다시 활성화
            if not existing_room.is_active:
                existing_room.is_active = True
                existing_room.updated_at = datetime.utcnow()
                
            # 나간 사용자가 다시 참여하는 경우 복귀 처리
            if existing_room.applicant_id == applicant_id and existing_room.applicant_left:
                existing_room.applicant_left = False
                existing_room.updated_at = datetime.utcnow()
            elif existing_room.employer_id == employer_id and existing_room.employer_left:
                existing_room.employer_left = False
                existing_room.updated_at = datetime.utcnow()
                
            db.session.commit()
            return existing_room
        
        # 새 채팅방 생성
        new_room = ChatRoom(
            job_id=job_id,
            applicant_id=applicant_id,
            employer_id=employer_id
        )
        
        db.session.add(new_room)
        db.session.commit()
        
        # 시스템 메시지 추가 (채팅방 생성 알림)
        job = JobPost.query.get(job_id)
        applicant = User.query.get(applicant_id)
        
        system_message = ChatMessage(
            room_id=new_room.id,
            sender_id=applicant_id,
            message=f"{applicant.nickname}님이 '{job.title}' 공고에 지원하여 채팅방이 생성되었습니다.",
            message_type='system'
        )
        
        db.session.add(system_message)
        db.session.commit()
        
        return new_room
    
    @staticmethod
    def send_message(room_id, sender_id, message, message_type='text'):
        """메시지 전송"""
        # 채팅방 존재 확인
        room = ChatRoom.query.get_or_404(room_id)
        
        # 메시지 생성
        new_message = ChatMessage(
            room_id=room_id,
            sender_id=sender_id,
            message=message,
            message_type=message_type
        )
        
        db.session.add(new_message)
        
        # 채팅방 업데이트 시간 갱신
        room.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return new_message
    
    @staticmethod
    def get_user_chat_rooms(user_id):
        """사용자의 채팅방 목록 조회 (나간 채팅방 제외)  """
        # 별칭설정
        other_user_alias = aliased(User)

        # 채팅방별 안 읽은 메시지 수 계산
        unread_counts_subquery = (
            select(
                ChatMessage.room_id,
                func.count(ChatMessage.id).label("unread_count"),
            )
            .where(ChatMessage.sender_id != user_id, ChatMessage.is_read == False)
            .group_by(ChatMessage.room_id)
            .subquery("unread_counts")
        )

        # 채팅방별 마지막 메시지 ID 계산
        last_message_subquery = (
            select(
                ChatMessage.id,
                ChatMessage.room_id,
                func.row_number()
                .over(partition_by=ChatMessage.room_id, order_by=desc(ChatMessage.created_at))
                .label("rn"),
            )
            .subquery("last_message_rn")
        )

        #가장 최신 메시지의 ID만 선택
        last_message_id_subquery = (
            select(
                last_message_subquery.c.id.label("message_id"),
                last_message_subquery.c.room_id,
            )
            .where(last_message_subquery.c.rn == 1)
            .subquery("last_message_ids")
        )

        # 한 번에 가져오기
        results = (
            db.session.query(
                ChatRoom,
                other_user_alias.nickname.label("other_user_nickname"),
                other_user_alias.profile_image.label("other_user_profile_img"),
                ChatMessage,
                unread_counts_subquery.c.unread_count.label("unread_count"),
            )
            .filter(
                or_(ChatRoom.applicant_id == user_id, ChatRoom.employer_id == user_id),
            )
            .outerjoin(
                unread_counts_subquery,
                ChatRoom.id == unread_counts_subquery.c.room_id,
            )
            .outerjoin(
                last_message_id_subquery,
                ChatRoom.id == last_message_id_subquery.c.room_id,
            )
            .outerjoin(
                ChatMessage, ChatMessage.id == last_message_id_subquery.c.message_id
            )
            .join(
                other_user_alias,
                case(
                    (ChatRoom.applicant_id == user_id, other_user_alias.id == ChatRoom.employer_id),
                    (ChatRoom.employer_id == user_id, other_user_alias.id == ChatRoom.applicant_id),
                ),
            )
            .order_by(desc(ChatRoom.updated_at))
            .all()
        )

        room_data = []
        for room, other_nickname, other_profile, last_message, unread_count in results:

            profile_image_url = None
            if other_profile:
                profile_image_url = generate_presigned_get_url(other_profile)

            other_user_info = {
                'nickname': other_nickname,
                'profile_image_url': profile_image_url
            }

            room_data.append({
                "room": room,
                "other_user": other_user_info,
                "last_message": last_message,
                "unread_count": unread_count or 0,
            })

        return room_data
    
    @staticmethod
    def get_chat_messages(room_id, user_id, page=1, per_page=50):
        """채팅방의 메시지 목록 조회 """
        room = ChatRoom.query.filter(
            and_(
                ChatRoom.id == room_id,
                or_(
                    ChatRoom.applicant_id == user_id,
                    ChatRoom.employer_id == user_id
                )
            )
        ).first_or_404()

        # 메시지 조회 (최신 순)
        pagination = ChatMessage.query.filter_by(room_id=room_id) \
            .options(joinedload(ChatMessage.sender)) \
            .order_by(desc(ChatMessage.created_at))\
            .paginate(page=page, per_page=per_page, error_out=False)
        return pagination

    @staticmethod
    def mark_messages_as_read(room_id, user_id):
        """메시지를 읽음으로 표시"""
        ChatMessage.query.filter_by(room_id=room_id, is_read=False)\
                        .filter(ChatMessage.sender_id != user_id)\
                        .update({'is_read': True})
        
        db.session.commit()
    
    @staticmethod
    def get_unread_message_count(user_id):
        """사용자의 전체 읽지 않은 메시지 수 조회"""
        user_rooms = ChatRoom.query.filter(
            or_(
                ChatRoom.applicant_id == user_id,
                ChatRoom.employer_id == user_id
            )
        ).all()
        
        room_ids = [room.id for room in user_rooms]
        
        if not room_ids:
            return 0
        
        # 읽지 않은 메시지 수
        unread_count = ChatMessage.query.filter(
            and_(
                ChatMessage.room_id.in_(room_ids),
                ChatMessage.sender_id != user_id,
                ChatMessage.is_read == False
            )
        ).count()
        
        return unread_count
    
    @staticmethod
    def deactivate_chat_room(room_id, user_id):
        """채팅방 나가기 (개별 사용자별)"""
        room = ChatRoom.query.filter(
            and_(
                ChatRoom.id == room_id,
                or_(
                    ChatRoom.applicant_id == user_id,
                    ChatRoom.employer_id == user_id
                )
            )
        ).first_or_404()

        if room.applicant_id == user_id:
            room.applicant_left = True
        elif room.employer_id == user_id:
            room.employer_left = True
        
        # 두 사용자 모두 나간 경우에만 채팅방 비활성화
        if room.applicant_left and room.employer_left:
            room.is_active = False
        
        room.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return True