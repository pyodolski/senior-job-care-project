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

      // 채팅방으로 이동할지 묻기
      if (data.chat_room_id && confirm("채팅방으로 이동하시겠습니까?")) {
        window.location.href = `/chat/${data.chat_room_id}`;
      } else {
        // 페이지 새로고침하여 버튼 상태 업데이트
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
    // 해당 공고와 관련된 채팅방 찾기
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

// 정렬 드롭다운 토글
function toggleSortDropdown() {
  const dropdown = document.getElementById("sortDropdown");
  dropdown.classList.toggle("show");
}

// 정렬 순서 변경
function changeSortOrder(sortBy) {
  const currentUrl = new URL(window.location.href);
  currentUrl.searchParams.set("sort", sortBy);
  // 페이지네이션을 1페이지로 리셋
  currentUrl.searchParams.set("page", 1);
  window.location.href = currentUrl.toString();
}

// 필터 모달 열기
function openFilterModal() {
  const filterModal = document.getElementById('filterModal');
  if (filterModal) {
    filterModal.classList.add('show');
  }
}

// 필터 모달 닫기
function closeFilterModal() {
  const filterModal = document.getElementById('filterModal');
  if (filterModal) {
    filterModal.classList.remove('show');
  }
}

// 필터 초기화 함수
function resetFilters() {
  const currentUrl = new URL(window.location.href);
  currentUrl.searchParams.delete('region1');
  currentUrl.searchParams.delete('region2');
  currentUrl.searchParams.delete('region3');
  currentUrl.searchParams.delete('page'); // 페이지 리셋
  window.location.href = currentUrl.pathname + '?' + currentUrl.searchParams.toString();
}

// DOMContentLoaded 이벤트 핸들러
document.addEventListener("DOMContentLoaded", function () {
  // 필터 모달 초기화
  const filterModal = document.getElementById('filterModal');
  const filterForm = document.getElementById('filterForm');

  if (filterForm) {
    // 필터 적용 폼 제출 이벤트
    filterForm.addEventListener('submit', function(event) {
      event.preventDefault();

      const formData = new FormData(filterForm);
      const currentUrl = new URL(window.location.href);
      const params = currentUrl.searchParams;

      // 지역 필터 파라미터 업데이트
      ['region1', 'region2', 'region3'].forEach(key => {
        const value = formData.get(key).trim();
        if (value) {
          params.set(key, value);
        } else {
          params.delete(key);
        }
      });

      params.set("page", 1); // 필터 적용 시 1페이지로 리셋

      window.location.href = currentUrl.pathname + '?' + params.toString();
    });
  }

  // 외부 클릭 시 드롭다운/모달 닫기
  document.addEventListener("click", function (event) {
    const sortBtn = event.target.closest(".relative");
    const dropdown = document.getElementById("sortDropdown");

    // 정렬 드롭다운 닫기
    if (dropdown && !sortBtn && dropdown.classList.contains("show")) {
      dropdown.classList.remove("show");
    }

    // 모달 외부 클릭 시 닫기 (단, 모달 콘텐츠 내부 클릭은 제외)
    if (filterModal && event.target === filterModal) {
      closeFilterModal();
    }
  });
});
