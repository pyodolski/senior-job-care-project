function confirmWithdrawal() {
  if (
    confirm(
      "정말로 회원탈퇴를 하시겠습니까?\n탈퇴 후에는 계정을 복구할 수 없습니다."
    )
  ) {
    // 회원탈퇴 API 호출
    fetch('/withdraw', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert(data.message);
        // 홈 페이지로 리다이렉트
        window.location.href = '/';
      } else {
        alert(data.message || '회원탈퇴에 실패했습니다.');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('회원탈퇴 처리 중 오류가 발생했습니다.');
    });
  }
}
