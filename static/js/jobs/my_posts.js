// 공고 수정
function editPost(jobId) {
  window.location.href = `/jobs/${jobId}/edit`;
}

// 공고 삭제
async function deletePost(jobId) {
  if (
    !confirm(
      "정말로 이 글을 삭제하시겠습니까?\n삭제된 글은 복구할 수 없습니다."
    )
  ) {
    return;
  }

  try {
    const response = await fetch(`/jobs/${jobId}/delete`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (data.success) {
      alert("글이 삭제되었습니다.");
      const cardToRemove = document.querySelector(
        `[data-job-id="${jobId}"]`
      );
      if (cardToRemove) {
        cardToRemove.remove();
      } else {
        location.reload();
      }
    } else {
      alert(data.message || "글 삭제 중 오류가 발생했습니다.");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("글 삭제 중 오류가 발생했습니다.");
  }
}

// 검색 기능
document
  .getElementById("searchInput")
  ?.addEventListener("input", function (e) {
    const searchTerm = e.target.value.toLowerCase();
    const jobCards = document.querySelectorAll("[data-job-id]");
    let visibleCount = 0;

    jobCards.forEach((card) => {
      const title = card.querySelector("h3").textContent.toLowerCase();
      if (title.includes(searchTerm)) {
        card.style.display = "block";
        visibleCount++;
      } else {
        card.style.display = "none";
      }
    });

    // 검색 결과 개수 업데이트
    const displayCountElement = document.getElementById("displayCount");
    if (displayCountElement) {
      displayCountElement.textContent = visibleCount;
    }
  });
