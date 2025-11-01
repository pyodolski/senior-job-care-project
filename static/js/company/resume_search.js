function filterResumes(type) {
  // 모든 필터 버튼 초기화
  document.querySelectorAll('[id^="filter-"]').forEach((btn) => {
    btn.classList.remove("bg-blue-600", "text-white");
    btn.classList.add("border", "border-gray-300", "text-gray-700");
  });

  // 선택된 필터 버튼 활성화
  const activeBtn = document.getElementById("filter-" + type);
  activeBtn.classList.remove(
    "border",
    "border-gray-300",
    "text-gray-700"
  );
  activeBtn.classList.add("bg-blue-600", "text-white");

  // 이력서 카드 필터링
  const resumeCards = document.querySelectorAll(".resume-card");
  resumeCards.forEach((card) => {
    if (type === "all") {
      card.style.display = "block";
    } else if (type === "시간협의") {
      const isTimeNegotiable = card.dataset.timeNegotiable === "true";
      card.style.display = isTimeNegotiable ? "block" : "none";
    } else {
      const workType = card.dataset.workType;
      card.style.display = workType === type ? "block" : "none";
    }
  });
}
