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

async function changeCategory(category) {
  currentQuery = category;
  currentPage = 1;
  updateActiveCategory(category);

  // 뉴스 목록 로드
  const response = await fetch(
    `/news?q=${encodeURIComponent(category)}&page=1`
  );
  const html = await response.text();

  // HTML 파싱하여 뉴스 목록만 추출
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, "text/html");
  const newArticles = doc.querySelectorAll("article");

  // 기존 뉴스 목록 교체
  const newsContainer = document.querySelector(".space-y-6");
  newsContainer.innerHTML = "";
  newArticles.forEach((article) => {
    newsContainer.appendChild(article);
  });
}

async function loadMoreNews() {
  currentPage += 1;
  const response = await fetch(
    `/news?q=${encodeURIComponent(currentQuery)}&page=${currentPage}`
  );
  const html = await response.text();

  // HTML 파싱하여 뉴스 목록만 추출
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, "text/html");
  const newArticles = doc.querySelectorAll("article");

  // 기존 뉴스 목록에 추가
  const newsContainer = document.querySelector(".space-y-6");
  newArticles.forEach((article) => {
    newsContainer.appendChild(article);
  });
}
