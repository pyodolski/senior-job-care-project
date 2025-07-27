/**
 * 유틸리티 함수들
 */

/**
 * 나이 계산
 */
export function calculateAge(birthDate) {
  const today = new Date();
  const birth = new Date(birthDate);
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();

  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }

  return age;
}

/**
 * CSRF 토큰 가져오기
 */
export function getCsrfToken() {
  const token = document
    .querySelector('meta[name="csrf-token"]')
    ?.getAttribute("content");
  return token || "";
}

/**
 * 디바운스 함수
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * 현재 사용자 ID 가져오기
 */
export function getCurrentUserId() {
  const userIdElement = document.querySelector("[data-user-id]");
  return userIdElement ? userIdElement.dataset.userId : null;
}

/**
 * 네트워크 오류 처리 및 재시도
 */
export async function retryOperation(operation, maxRetries = 3, delay = 1000) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      if (i === maxRetries - 1) {
        throw error;
      }

      // 지수 백오프로 재시도 간격 증가
      await new Promise((resolve) =>
        setTimeout(resolve, delay * Math.pow(2, i))
      );
    }
  }
}
