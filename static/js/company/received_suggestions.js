function acceptSuggestion(suggestionId, event) {
  event.stopPropagation();

  const card = document.getElementById(`suggestion-card-${suggestionId}`);
  const button = card.querySelector("button.bg-blue-600");
  button.disabled = true;
  button.textContent = "처리 중...";
  fetch(`/api/suggestions/${suggestionId}/accept`, { method: "POST", headers: { "Content-Type": "application/json" } })
    .then((response) => response.json())
    .then((data) => {
      if (data.success && data.chat_room_id) {
        window.location.href = `/chat/${data.chat_room_id}`;
      } else {
        alert(data.message || "오류가 발생했습니다.");
        button.disabled = false;
        button.textContent = "수락";
      }
    })
    .catch((error) => {
      alert("네트워크 오류가 발생했습니다.");
      button.disabled = false;
      button.textContent = "수락";
    });
}

function rejectSuggestion(suggestionId, event) {
  event.stopPropagation();

  const card = document.getElementById(`suggestion-card-${suggestionId}`);
  const buttons = card.querySelectorAll("button");
  buttons.forEach((btn) => (btn.disabled = true));
  fetch(`/api/suggestions/${suggestionId}/reject`, { method: "POST", headers: { "Content-Type": "application/json" } })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        card.remove(); // 화면에서 즉시 제거
      } else {
        alert(data.message || "거절 처리 중 오류가 발생했습니다.");
        buttons.forEach((btn) => (btn.disabled = false));
      }
    })
    .catch((error) => {
      alert("네트워크 오류가 발생했습니다.");
      buttons.forEach((btn) => (btn.disabled = false));
    });
}
