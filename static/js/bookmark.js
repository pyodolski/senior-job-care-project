// 찜 목록 페이지 JavaScript

let currentCategory = "people"; // 기본값: 사람 이음

// 페이지 로드시 초기 카테고리 활성화
document.addEventListener("DOMContentLoaded", function () {
  const urlParams = new URLSearchParams(window.location.search);
  const category = urlParams.get("category") || "people";
  currentCategory = category;
  updateActiveTab(category);
});

function updateActiveTab(category) {
  const tabs = document.querySelectorAll(".bookmark-tab");

  tabs.forEach((tab, index) => {
    if (tab.dataset.category === category) {
      tab.classList.add("bg-blue-900", "text-white");
      tab.classList.remove("bg-gray-200", "text-gray-500");
      // 선택된 탭은 하단 패딩을 4px 더 줘서 파란색 선을 덮음
      tab.style.paddingBottom = "16px";
    } else {
      tab.classList.add("bg-gray-200", "text-gray-500");
      tab.classList.remove("bg-blue-900", "text-white");
      // 선택되지 않은 탭은 하단 패딩을 줄여서 파란색 선이 보이게 함
      tab.style.paddingBottom = "12px";
    }
  });
}

function changeBookmarkCategory(category) {
  currentCategory = category;
  const currentUrl = new URL(window.location.href);
  currentUrl.searchParams.set("category", category);
  window.location.href = currentUrl.toString();
}

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

// 정렬 드롭다운 토글
function toggleSortDropdown() {
  const dropdown = document.getElementById("sortDropdown");
  dropdown.classList.toggle("show");
}

// 정렬 순서 변경
function changeSortOrder(sortBy) {
  const currentUrl = new URL(window.location.href);
  currentUrl.searchParams.set("sort", sortBy);
  window.location.href = currentUrl.toString();
}

// 외부 클릭 시 드롭다운 닫기
document.addEventListener("click", function (event) {
  const sortBtn = event.target.closest(".relative");
  const dropdown = document.getElementById("sortDropdown");
  if (dropdown && !sortBtn && dropdown.classList.contains("show")) {
    dropdown.classList.remove("show");
  }
});

// 찜 목록에서 찜 해제 함수
async function toggleBookmarkInList(jobId, button) {
  try {
    const response = await fetch(`/jobs/${jobId}/bookmark`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await response.json();

    if (data.success) {
      // 찜 해제되면 해당 카드를 페이지에서 제거
      const card = button.closest(".bg-white");
      card.style.transition = "opacity 0.3s";
      card.style.opacity = "0";
      setTimeout(() => {
        card.remove();
        // 남은 공고가 없으면 페이지 새로고침
        const remainingCards = document.querySelectorAll(
          ".bg-white.rounded-2xl"
        );
        if (remainingCards.length === 0) {
          location.reload();
        }
      }, 300);
    }
  } catch (error) {
    console.error("Error:", error);
  }
}
