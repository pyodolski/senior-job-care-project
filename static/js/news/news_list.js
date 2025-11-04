let currentPage = 1;
let currentQuery = window.initialQuery;

// 페이지 로드시 초기 카테고리 활성화
document.addEventListener("DOMContentLoaded", function () {
  updateActiveCategory(currentQuery);
});

function updateActiveCategory(category) {
  const buttons = document.querySelectorAll(".category-btn");
  buttons.forEach((btn) => {
    if (btn.dataset.category === category) {
      btn.classList.add("bg-blue-600", "text-white");
      btn.classList.remove("bg-gray-100", "text-gray-700");
    } else {
      btn.classList.add("bg-gray-100", "text-gray-700");
      btn.classList.remove("bg-blue-600", "text-white");
    }
  });
}

function changeCategory(category) {
  // 페이지 새로고침 방식으로 변경 (배포 서버 호환성)
  window.location.href = `/news?q=${encodeURIComponent(category)}&page=1`;
}

async function loadMoreNews() {
  const button = event.target.closest("button");
  const originalText = button.innerHTML;

  try {
    // 로딩 상태 표시
    button.disabled = true;
    button.innerHTML = "<span>로딩 중...</span>";

    currentPage += 1;
    const response = await fetch(
      `/news?q=${encodeURIComponent(currentQuery)}&page=${currentPage}`,
      {
        method: "GET",
        credentials: "same-origin",
        headers: {
          Accept: "text/html",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const html = await response.text();

    // HTML 파싱하여 뉴스 목록만 추출
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const newArticles = doc.querySelectorAll("article");

    if (newArticles.length === 0) {
      button.innerHTML = "<span>더 이상 뉴스가 없습니다</span>";
      return;
    }

    // 기존 뉴스 목록에 추가
    const newsContainer = document.querySelector(".space-y-6");
    newArticles.forEach((article) => {
      newsContainer.appendChild(article);
    });

    // 버튼 원래대로 복구
    button.disabled = false;
    button.innerHTML = originalText;
  } catch (error) {
    console.error("뉴스 로딩 오류:", error);
    alert("뉴스를 불러오는데 실패했습니다. 다시 시도해주세요.");
    button.disabled = false;
    button.innerHTML = originalText;
    currentPage -= 1; // 페이지 번호 복구
  }
}
