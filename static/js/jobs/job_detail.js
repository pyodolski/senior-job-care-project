const mainContainer = document.querySelector("main");
const jobId = window.jobId;

// 지도 초기화
if (window.jobLatitude && window.jobLongitude) {
  window.addEventListener('load', function() {
    const container = document.getElementById('map');
    const options = {
      center: new kakao.maps.LatLng(window.jobLatitude, window.jobLongitude),
      level: 3
    };

    const map = new kakao.maps.Map(container, options);

    // 마커 표시
    const markerPosition = new kakao.maps.LatLng(window.jobLatitude, window.jobLongitude);
    const marker = new kakao.maps.Marker({
      position: markerPosition
    });
    marker.setMap(map);
  });
}

function toggleBookmark() {
  if (!jobId) return;
  const bookmarkBtnContainer = document.querySelector(".btn-bookmark");
  const bookmarkBtn = bookmarkBtnContainer.querySelector("svg");

  fetch(`/jobs/${jobId}/bookmark`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        if (data.is_bookmarked) {
          bookmarkBtn.classList.add("text-red-500");
          bookmarkBtn.classList.remove("text-gray-400");
          bookmarkBtnContainer.classList.add("border-red-500", "bg-red-50");
          bookmarkBtnContainer.classList.remove("border-gray-300", "bg-white");
        } else {
          bookmarkBtn.classList.remove("text-red-500");
          bookmarkBtn.classList.add("text-gray-400");
          bookmarkBtnContainer.classList.remove("border-red-500", "bg-red-50");
          bookmarkBtnContainer.classList.add("border-gray-300", "bg-white");
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

function toggleRelatedBookmark(event, relatedJobId) {
  // 링크 클릭 이벤트 방지
  event.preventDefault();
  event.stopPropagation();

  if (!relatedJobId) return;

  const bookmarkBtn = document.querySelector(`.related-bookmark-btn-${relatedJobId} svg`);

  fetch(`/jobs/${relatedJobId}/bookmark`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        if (data.is_bookmarked) {
          bookmarkBtn.classList.add("text-red-500");
          bookmarkBtn.classList.remove("text-gray-400");
        } else {
          bookmarkBtn.classList.remove("text-red-500");
          bookmarkBtn.classList.add("text-gray-400");
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
