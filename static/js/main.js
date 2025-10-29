// 메인 페이지 JavaScript

// 공고 지원하기 함수
async function applyJob(jobId) {
  if (
    !confirm(
      "이 공고에 지원하시겠습니까?\n지원하면 자동으로 채팅방이 생성됩니다."
    )
  ) {
    return;
  }
  try {
    const response = await fetch(`/jobs/${jobId}/apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "" }),
    });
    const data = await response.json();
    if (data.success) {
      alert(data.message);
      if (data.chat_room_id && confirm("채팅방으로 이동하시겠습니까?")) {
        window.location.href = `/chat/${data.chat_room_id}`;
      } else {
        location.reload();
      }
    } else {
      alert(data.message || "지원 중 오류가 발생했습니다.");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("지원 중 오류가 발생했습니다.");
  }
}

// 채팅방으로 이동하는 함수
async function goToChat(jobId) {
  try {
    const response = await fetch(`/chat/find-room/${jobId}`, {
      method: "GET",
    });
    const data = await response.json();
    if (data.success && data.room_id) {
      window.location.href = `/chat/${data.room_id}`;
    } else {
      alert("채팅방을 찾을 수 없습니다.");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("채팅방 이동 중 오류가 발생했습니다.");
  }
}

// 찜하기 토글 함수
async function toggleBookmark(jobId, button) {
  try {
    const response = await fetch(`/jobs/${jobId}/bookmark`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await response.json();

    if (data.success) {
      const svg = button.querySelector("svg");
      if (data.bookmarked) {
        // 찜 추가됨
        button.classList.remove("text-gray-400");
        button.classList.add("text-red-500");
        svg.setAttribute("fill", "currentColor");
      } else {
        // 찜 제거됨
        button.classList.remove("text-red-500");
        button.classList.add("text-gray-400");
        svg.setAttribute("fill", "none");
      }
    } else {
      alert(data.message || "찜하기 중 오류가 발생했습니다.");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("찜하기 중 오류가 발생했습니다.");
  }
}

// 얼굴 토글 스위치 상태 관리
let isToggleActive = false;

// 토글 스위치 기능
function updateToggleTheme() {
  const toggle = document.getElementById("face-toggle");
  const body = document.body;
  const container = document.getElementById("toggleContainer");
  const toggleText = document.getElementById("toggleText");

  if (toggle.checked) {
    body.classList.add("toggle-active");
    container.classList.add("active");
    isToggleActive = true;

    // 1초 후에 토글 페이지로 이동 (애니메이션 완료 후)
    setTimeout(() => {
      window.location.href = "/toggle-page";
    }, 1000);
  } else {
    body.classList.remove("toggle-active");
    container.classList.remove("active");
    isToggleActive = false;
  }
}

// 페이지 로드 시 초기화
document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.getElementById("face-toggle");
  const urlParams = new URLSearchParams(window.location.search);

  // reset_toggle 파라미터가 있으면 토글을 비활성화 상태로 설정
  if (urlParams.get("reset_toggle") === "true") {
    toggle.checked = false;
    updateToggleTheme();
  }

  // 토글 변경 이벤트 리스너 추가
  toggle.addEventListener("change", updateToggleTheme);

  // 초기 상태 설정
  updateToggleTheme();
});
