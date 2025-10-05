// 채팅 관련 JavaScript 함수들

// 다른 도메인이면: const socket = io("https://api.example.com", { withCredentials: true });
const socket = io({ withCredentials: true }); // 세션 기반 인증 공유[web:17]

// 템플릿에서 주입된 전역 값 사용
const ROOM_ID = window.roomId;
const CURRENT_USER_ID = window.currentUserId;
const CURRENT_USER_NAME = window.currentUserName || "?";
const OTHER_USER_NAME = window.otherUserName || "?";

// 채팅방으로 이동
function goToChatRoom(roomId) {
  navigateTo(`/chat/${roomId}`);
}

// 채팅 목록으로 이동
function goToChatList() {
  navigateTo("/chat");
}

async function sendMessage(roomId) {
  const messageInput = document.getElementById("messageInput");
  const message = (messageInput.value || "").trim();
  if (!message) return;

  const sendBtn = document.getElementById("sendBtn");
  const originalText = sendBtn ? sendBtn.innerHTML : null;

  try {
    if (typeof showLoading === "function" && sendBtn) showLoading(sendBtn);

    // 서버로 소켓 이벤트 전송
    socket.emit("send_message", {
      room_id: roomId,
      message: message,
      message_type: "text",
    });

    // 낙관적 렌더를 원하면 아래 주석 해제(서버 수신 시 실제 id로 중복 방지됨)
    /*
    addMessageToChat({
      id: undefined,
      message,
      sender_id: CURRENT_USER_ID,
      sender_name: CURRENT_USER_NAME,
      created_at: new Date().toISOString().slice(0,19).replace('T',' '),
      message_type: "text"
    }, true);
    */

    // 입력창 비우고 스크롤
    messageInput.value = "";
    scrollToBottom();
  } catch (error) {
    if (typeof showAlert === "function") showAlert("메시지 전송 중 오류가 발생했습니다.");
    console.error(error);
  } finally {
    if (typeof hideLoading === "function" && sendBtn) hideLoading(sendBtn, originalText);
    messageInput.focus();
  }
}

// 채팅창에 메시지 추가
function addMessageToChat(messageData, isOwn = false) {
  const messagesContainer = document.getElementById("chatMessages");
  if (!messagesContainer) return;

  // 이미 동일 ID의 메시지가 존재하면 중복 추가 방지
  if (messageData && typeof messageData.id !== "undefined") {
    const exists = messagesContainer.querySelector(
      `[data-message-id="${messageData.id}"]`
    );
    if (exists) {
      return;
    }
  }

  const messageElement = createMessageElement(messageData, isOwn);
  messagesContainer.appendChild(messageElement);
}

// 메시지 요소 생성
function createMessageElement(messageData, isOwn = false) {
  const messageDiv = document.createElement("div");
  const isSystem = messageData.message_type === "system";
  messageDiv.className = `message ${isOwn ? "own" : ""} ${
    isSystem ? "system" : ""
  }`;

  // 중복 판별을 위한 메시지 ID 저장
  if (typeof messageData.id !== "undefined") {
    messageDiv.dataset.messageId = String(messageData.id);
  }

  const avatarDiv = document.createElement("div");
  avatarDiv.className = "message-avatar";
  const senderName = messageData.sender_name || "?";
  if (!isSystem) {
    avatarDiv.textContent = senderName.charAt(0);
  }

  const contentDiv = document.createElement("div");
  contentDiv.className = "message-content";

  const bubbleDiv = document.createElement("div");
  bubbleDiv.className = "message-bubble";
  bubbleDiv.textContent = messageData.message;

  const timeDiv = document.createElement("div");
  timeDiv.className = "message-time";
  timeDiv.textContent = formatMessageTime(messageData.created_at);

  contentDiv.appendChild(bubbleDiv);
  contentDiv.appendChild(timeDiv);

  if (!isSystem) {
    messageDiv.appendChild(avatarDiv);
  }
  messageDiv.appendChild(contentDiv);

  return messageDiv;
}

// 메시지 시간 포맷팅
function formatMessageTime(timeString) {
  const date = new Date(timeString);
  const now = new Date();

  // 오늘 날짜인지 확인
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString("ko-KR", {
      hour: "2-digit",
      minute: "2-digit",
    });
  } else {
    return date.toLocaleDateString("ko-KR", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
}

// 채팅창 스크롤을 맨 아래로
function scrollToBottom() {
  const messagesContainer = document.getElementById("chatMessages");
  if (messagesContainer) {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
}

// Enter 키로 메시지 전송
function handleMessageKeyPress(event, roomId) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage(roomId);
  }
}

// 채팅방 나가기
async function leaveChatRoom(roomId) {
  if (!showConfirm("정말로 이 채팅방을 나가시겠습니까?")) {
    return;
  }

  try {
    // 서버 응답을 기다리지 않고 바로 리다이렉트 (Flask가 redirect 응답을 보내므로)
    const form = document.createElement("form");
    form.method = "POST";
    form.action = `/chat/${roomId}/leave`;
    document.body.appendChild(form);
    form.submit();
  } catch (error) {
    showAlert("채팅방 나가기 중 오류가 발생했습니다.");
  }
}

// 페이지 로드 시 초기화
document.addEventListener("DOMContentLoaded", function () {
  // 채팅창이 있으면 스크롤을 맨 아래로
  scrollToBottom();

  // 메시지 입력창에 포커스
  const messageInput = document.getElementById("messageInput");
  if (messageInput) {
    messageInput.focus();
  }
});

// 소켓 초기화: join, 초기 읽음, 수신 이벤트
document.addEventListener("DOMContentLoaded", function () {
  // 연결되면 방 참가 + 초기 읽음 처리
  socket.on("connect", () => {
    socket.emit("join", { room_id: ROOM_ID });           // 방 참가[web:17]
    socket.emit("read_messages", { room_id: ROOM_ID });   // 초기 읽음 처리[web:17]
  });

  socket.on("connect_error", (err) => console.error("socket connect_error", err));
  socket.on("error", (err) => console.error("socket error", err));

  // 서버가 방송하는 새 메시지 수신
  socket.on("new_message", (msg) => {
    if (msg.room_id !== ROOM_ID) return;
    const isOwn = msg.sender_id === CURRENT_USER_ID;

    // 기존 addMessageToChat 인터페이스로 매핑
    addMessageToChat({
      id: msg.id,
      message: msg.message,
      sender_id: msg.sender_id,
      sender_name: isOwn ? CURRENT_USER_NAME : OTHER_USER_NAME,
      created_at: msg.created_at,
      message_type: msg.message_type,
    }, isOwn);

    if (!isOwn) {
      // 수신 즉시 읽음 처리
      socket.emit("read_messages", { room_id: ROOM_ID }); // 읽음 브로드캐스트[web:17]
    }
    scrollToBottom();
  });

  // 읽음 처리 방송 수신(배지/UI 훅이 있으면 갱신)
  socket.on("messages_read", (data) => {
    if (data.room_id !== ROOM_ID) return;
    if (typeof updateReadState === "function") updateReadState();
  });

  // 초기 포커스/스크롤
  scrollToBottom();
  const messageInput = document.getElementById("messageInput");
  if (messageInput) messageInput.focus();
});
// 현재 사용자 ID 가져오기 (전역 변수나 데이터 속성에서)
function getCurrentUserId() {
  return window.currentUserId || parseInt(document.body.dataset.userId) || 0;
}
