async function deleteResume(url, resumeId) {
  if (!confirm("정말 이력서를 삭제하시겠습니까?")) return;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
    });
    const data = await res.json();

    // 삭제 성공 시 로직
    if (data.success) {
      alert("삭제되었습니다.");
      const cardToRemove = document.querySelector(
        `[data-resume-id="${resumeId}"]`
      );
      if (cardToRemove) {
        cardToRemove.remove(); // 화면에서 해당 카드만 제거
      } else {
        location.reload(); // 만약 카드를 못찾으면 페이지 전체 새로고침
      }
    }
    // 삭제 실패 시 로직
    else {
      alert(data.message || "삭제에 실패했습니다.");
    }
  } catch (e) {
    console.error("Error:", e);
    alert("요청 중 오류가 발생했습니다.");
  }
}

async function togglePublic(url, isPublic, resumeId) {
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
      body: JSON.stringify({ ispublic: isPublic }),
    });
    const data = await res.json();

    if (!data.success) {
      // 실패 시, 스위치를 원래 상태로 되돌림
      alert(data.message || "공개 설정 변경에 실패했습니다.");
      const input = document.querySelector(`#toggle-${resumeId}`);
      if (input) input.checked = !isPublic;
    }
  } catch (e) {
    console.error("Error:", e);
    alert("요청 중 오류가 발생했습니다.");
    const input = document.querySelector(`#toggle-${resumeId}`);
    if (input) input.checked = !isPublic;
  }
}
