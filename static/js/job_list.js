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

// 즐겨찾기 토글 함수
async function toggleBookmark(jobId, buttonElement) {
  try {
    const isBookmarked = buttonElement.dataset.bookmarked === "true";
    const response = await fetch(`/jobs/${jobId}/bookmark`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await response.json();

    if (data.success) {
      const svg = buttonElement.querySelector("svg");
      if (isBookmarked) {
        // 북마크 해제
        svg.classList.remove("text-red-500");
        svg.classList.add("text-gray-400");
        svg.setAttribute("fill", "none");
        buttonElement.dataset.bookmarked = "false";
      } else {
        // 북마크 추가
        svg.classList.remove("text-gray-400");
        svg.classList.add("text-red-500");
        svg.setAttribute("fill", "currentColor");
        buttonElement.dataset.bookmarked = "true";
      }
    } else {
      alert(data.message || "즐겨찾기 처리 중 오류가 발생했습니다.");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("즐겨찾기 처리 중 오류가 발생했습니다.");
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

// --- 필터 및 정렬 관련 스크립트 ---
const filterModal = document.getElementById("filterModal");
const filterForm = document.getElementById("filterForm");

function openFilterModal() {
  filterModal.classList.add("show");
}
function closeFilterModal() {
  filterModal.classList.remove("show");
}

// 필터 초기화 함수
function resetFilters() {
  const currentUrl = new URL(window.location.href);
  currentUrl.searchParams.delete("region1");
  currentUrl.searchParams.delete("region2");
  currentUrl.searchParams.delete("region3");
  window.location.href =
    currentUrl.pathname + "?" + currentUrl.searchParams.toString();
}

// 필터 적용 폼 제출 이벤트
filterForm.addEventListener("submit", function (event) {
  event.preventDefault();

  const formData = new FormData(filterForm);
  const currentUrl = new URL(window.location.href);
  const params = currentUrl.searchParams;

  ["region1", "region2", "region3"].forEach((key) => {
    const value = formData.get(key).trim();
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
  });

  window.location.href = currentUrl.pathname + "?" + params.toString();
});
