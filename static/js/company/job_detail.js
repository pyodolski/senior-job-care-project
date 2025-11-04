const mainContainer = document.querySelector("[data-job-id]");
const jobId = mainContainer ? mainContainer.dataset.jobId : null;

// K-Senior 외부 공고용 모달 함수
if (window.isKSeniorJob) {
  function showContactModal() {
    document.getElementById("contactModal").classList.remove("hidden");
  }
  function closeContactModal() {
    document.getElementById("contactModal").classList.add("hidden");
  }
  // window 객체에 함수 등록
  window.showContactModal = showContactModal;
  window.closeContactModal = closeContactModal;

  // URL 파라미터 확인하여 자동으로 모달 열기
  document.addEventListener("DOMContentLoaded", function () {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("showContact") === "true") {
      showContactModal();
    }
  });
}

function toggleBookmark() {
  if (!jobId) return;
  const bookmarkBtn = document.querySelector(".btn-bookmark svg");

  fetch(`/jobs/${jobId}/bookmark`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        if (data.is_bookmarked) {
          bookmarkBtn.classList.add("text-red-500");
          bookmarkBtn.classList.remove("text-gray-500");
        } else {
          bookmarkBtn.classList.remove("text-red-500");
          bookmarkBtn.classList.add("text-gray-500");
        }

        // 통계 업데이트 (찜 수)
        const currentStats = document.querySelector("section .flex.gap-4");
        if (currentStats && currentStats.children[1]) {
          currentStats.children[1].textContent = `찜 ${data.bookmark_count}`;
        }
      } else {
        alert(data.message || "오류가 발생했습니다.");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("오류가 발생했습니다.");
    });
}

async function applyJob() {
  if (!jobId) return;
  if (
    !confirm(
      "이 공고에 지원하시겠습니까?\n지원하면 자동으로 채팅방이 생성됩니다."
    )
  ) {
    return;
  }

  const applyBtn = document.querySelector(".btn-apply");
  const originalText = applyBtn.textContent;

  try {
    applyBtn.disabled = true;
    applyBtn.textContent = "지원 중...";

    const response = await fetch(`/jobs/${jobId}/apply`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: "",
      }),
    });

    const data = await response.json();

    if (data.success) {
      alert(data.message);

      // 지원 통계 업데이트
      const currentStats = document.querySelector("section .flex.gap-4");
      if (currentStats && currentStats.children[2]) {
        const currentCount = parseInt(
          currentStats.children[2].textContent.match(/\d+/)[0]
        );
        currentStats.children[2].textContent = `지원 ${currentCount + 1}`;
      }

      // 채팅방으로 이동할지 묻기
      if (data.chat_room_id && confirm("채팅방으로 이동하시겠습니까?")) {
        window.location.href = `/chat/${data.chat_room_id}`;
      } else {
        // 지원하기 버튼을 채팅하기 버튼으로 변경
        applyBtn.textContent = "채팅하기";
        applyBtn.className =
          "btn-apply flex-1 bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-4 rounded-lg transition-colors";
        applyBtn.onclick = function () {
          goToChatFromDetail();
        };
      }
    } else {
      alert(data.message || "지원 중 오류가 발생했습니다.");
      applyBtn.disabled = false;
      applyBtn.textContent = originalText;
    }
  } catch (error) {
    console.error("Error:", error);
    alert("지원 중 오류가 발생했습니다.");
    applyBtn.disabled = false;
    applyBtn.textContent = originalText;
  }
}

// 채팅방으로 이동하는 함수 (상세 페이지용)
async function goToChatFromDetail() {
  if (!jobId) return;
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
