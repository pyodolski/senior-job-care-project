async function deleteResume(url) {
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
    if (data.success) {
      alert("삭제되었습니다.");
      location.href = window.myViewResumeUrl;
    } else {
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

    if (data.success) {
      location.reload();
    } else {
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
