// 메인 페이지 JavaScript

// 검색 폼 제출 처리
document.addEventListener("DOMContentLoaded", function () {
  const searchForm = document.getElementById("searchForm");
  if (searchForm) {
    searchForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const searchType = document.querySelector(
        'input[name="searchType"]:checked'
      ).value;
      const searchQuery = document.getElementById("searchInput").value;

      if (searchType === "company") {
        window.location.href = `/company?q=${encodeURIComponent(searchQuery)}`;
      } else {
        window.location.href = `/jobs?q=${encodeURIComponent(searchQuery)}`;
      }
    });
  }
});

// 공고 지원하기 함수
async function applyJob(jobId, source) {
  // 공공데이터 공고(K-Senior)인 경우 상세 페이지로 이동하면서 모달 자동 열기
  if (source === "K-Senior") {
    window.location.href = `/company/${jobId}?showContact=true`;
    return;
  }

  // 일반 공고인 경우 기존 로직 실행
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

// 이력서 좋아요 토글 함수
async function toggleResumeFavorite(resumeId, button) {
  try {
    const response = await fetch(`/api/resume/${resumeId}/favorite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await response.json();

    if (data.success) {
      const svg = button.querySelector("svg");
      if (data.favorited) {
        // 좋아요 추가됨
        button.classList.remove("text-gray-400");
        button.classList.add("text-red-500");
        svg.setAttribute("fill", "currentColor");
      } else {
        // 좋아요 제거됨
        button.classList.remove("text-red-500");
        button.classList.add("text-gray-400");
        svg.setAttribute("fill", "none");
      }
    } else {
      alert(data.message || "좋아요 중 오류가 발생했습니다.");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("좋아요 중 오류가 발생했습니다.");
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

// ==================== 음성 검색 기능 ====================

// 음성 인식 지원 확인
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

function startVoiceSearch() {
  if (!SpeechRecognition) {
    alert(
      "죄송합니다. 이 브라우저는 음성 인식을 지원하지 않습니다.\nChrome 또는 Edge 브라우저를 사용해주세요."
    );
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = "ko-KR";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  const voiceBtn = document.getElementById("voiceBtn");

  // 음성 인식 시작
  recognition.start();

  // 버튼 상태 변경 (듣는 중)
  voiceBtn.style.opacity = "0.5";
  voiceBtn.style.animation = "pulse 1s infinite";

  // 음성 인식 성공
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    console.log("인식된 음성:", transcript);

    // 음성 피드백
    speak("검색 중입니다");

    // 기업이음 공고 검색 페이지로 이동 (파라미터: q)
    window.location.href = `/company?q=${encodeURIComponent(transcript)}`;
  };

  // 음성 인식 종료
  recognition.onend = () => {
    voiceBtn.style.opacity = "1";
    voiceBtn.style.animation = "";
  };

  // 음성 인식 오류
  recognition.onerror = (event) => {
    console.error("음성 인식 오류:", event.error);
    voiceBtn.style.opacity = "1";
    voiceBtn.style.animation = "";

    let errorMsg = "음성 인식에 실패했습니다.";

    switch (event.error) {
      case "no-speech":
        errorMsg = "음성이 감지되지 않았습니다. 다시 시도해주세요.";
        break;
      case "audio-capture":
        errorMsg = "마이크를 찾을 수 없습니다.";
        break;
      case "not-allowed":
        errorMsg =
          "마이크 권한이 필요합니다. 브라우저 설정에서 마이크 권한을 허용해주세요.";
        break;
    }

    alert(errorMsg);
  };

  // 음성 인식 시작 알림
  speak("말씀해주세요");
}

// 음성 합성 (TTS)
function speak(text) {
  if ("speechSynthesis" in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "ko-KR";
    utterance.rate = 0.9;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  }
}

// 펄스 애니메이션 추가
const style = document.createElement("style");
style.textContent = `
  @keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
  }
`;
document.head.appendChild(style);

// ==================== 관리자 전용: 공공데이터 동기화 ====================

async function syncPublicData() {
  const btn = document.getElementById("syncBtn");
  const result = document.getElementById("syncResult");

  if (!btn || !result) return;

  btn.disabled = true;
  btn.textContent = "⏳ 수집 중...";
  result.innerHTML =
    '<div class="text-white text-center">공공데이터를 가져오는 중입니다...</div>';

  try {
    const response = await fetch("/admin/fetch-senior-jobs", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (data.success) {
      result.innerHTML =
        '<div class="text-white text-center font-bold">✅ ' +
        data.message +
        "</div>";

      // 3초 후 페이지 새로고침
      setTimeout(() => {
        location.reload();
      }, 3000);
    } else {
      result.innerHTML =
        '<div class="text-red-200 text-center">❌ ' + data.message + "</div>";
    }
  } catch (error) {
    result.innerHTML =
      '<div class="text-red-200 text-center">❌ 오류: ' +
      error.message +
      "</div>";
  } finally {
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = "🔄 공공데이터 최신화";
    }, 3000);
  }
}

// ==================== 검색창 토글 ====================

function toggleSearchBar() {
  const searchBar = document.getElementById("searchBar");
  const searchInput = document.getElementById("searchInput");

  if (searchBar) {
    if (searchBar.classList.contains("hidden")) {
      searchBar.classList.remove("hidden");
      // 검색창이 나타나면 입력창에 포커스
      if (searchInput) {
        setTimeout(() => searchInput.focus(), 100);
      }
    } else {
      searchBar.classList.add("hidden");
    }
  }
}
