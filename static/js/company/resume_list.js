// 좋아요 토글
function toggleFavorite(resumeId, button) {
  fetch(`/api/resume/${resumeId}/favorite`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        if (data.favorited) {
          button.classList.remove("text-gray-400");
          button.classList.add("text-red-500");
        } else {
          button.classList.remove("text-red-500");
          button.classList.add("text-gray-400");
        }
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("좋아요 처리 중 오류가 발생했습니다.");
    });
}

// 필터 토글
function toggleFilter(filterType) {
  const filterId = "filter-" + filterType;
  const filterEl = document.getElementById(filterId);

  // 다른 필터들 닫기
  ["category", "days", "physical", "distance"].forEach((type) => {
    if (type !== filterType) {
      document.getElementById("filter-" + type).classList.add("hidden");
    }
  });

  // 현재 필터 토글
  filterEl.classList.toggle("hidden");
}

// 필터 적용
function applyFilters() {
  const resumeCards = document.querySelectorAll(".resume-card");

  // 선택된 직무 분야
  const selectedCategories = Array.from(
    document.querySelectorAll("#filter-category input:checked")
  ).map((cb) => cb.value);

  // 선택된 근무 요일
  const selectedDays = Array.from(
    document.querySelectorAll("#filter-days input:checked")
  ).map((cb) => cb.value);

  // 선택된 신체 능력
  const selectedPhysical = document.querySelector(
    'input[name="physical"]:checked'
  )?.value;

  // 선택된 이동 거리
  const selectedDistance = document.querySelector(
    'input[name="distance"]:checked'
  )?.value;

  resumeCards.forEach((card) => {
    let show = true;

    // 직무 분야 필터
    if (selectedCategories.length > 0) {
      const cardCategories = card.dataset.categories
        .split(",")
        .map((c) => c.trim());
      const hasMatch = selectedCategories.some((cat) =>
        cardCategories.includes(cat)
      );
      if (!hasMatch) show = false;
    }

    // 근무 요일 필터
    if (selectedDays.length > 0) {
      const dayMap = {
        월: "monday",
        화: "tuesday",
        수: "wednesday",
        목: "thursday",
        금: "friday",
        토: "saturday",
        일: "sunday",
      };

      const hasMatch = selectedDays.some((day) => {
        const dayKey = dayMap[day];
        return card.dataset[dayKey] === "true";
      });

      if (!hasMatch) show = false;
    }

    // 신체 능력 필터
    if (selectedPhysical && selectedPhysical !== "all") {
      const walkable = parseInt(card.dataset.walkable) || 0;
      const minWalkable = parseInt(selectedPhysical);
      if (walkable < minWalkable) show = false;
    }

    // 이동 거리 필터
    if (selectedDistance && selectedDistance !== "all") {
      const commute = parseInt(card.dataset.commute) || 0;
      const maxCommute = parseInt(selectedDistance);
      if (commute > maxCommute) show = false;
    }

    card.style.display = show ? "block" : "none";
  });
}
