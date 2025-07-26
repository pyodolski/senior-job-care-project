import { getCsrfToken, retryOperation } from "../utils/helpers.js";

/**
 * 네트워크 관리 클래스
 */
export class NetworkManager {
  constructor(onboardingFlow) {
    this.onboardingFlow = onboardingFlow;
    this.isOnline = navigator.onLine;
  }

  /**
   * 온라인/오프라인 상태 감지 및 처리
   */
  handleNetworkStatus() {
    // 온라인 복구 시 처리
    window.addEventListener("online", () => {
      console.log("Network restored");
      this.onboardingFlow.showSaveStatus(
        "네트워크가 복구되었습니다.",
        "success"
      );

      // 현재 진행 상황 자동 저장
      if (Object.keys(this.onboardingFlow.formData).length > 0) {
        this.onboardingFlow.dataManager.autoSave();
      }
    });

    // 오프라인 시 처리
    window.addEventListener("offline", () => {
      console.log("Network lost");
      this.onboardingFlow.showSaveStatus(
        "네트워크 연결이 끊어졌습니다. 로컬에 임시 저장됩니다.",
        "warning"
      );
    });

    // 페이지 언로드 시 현재 상태 백업
    window.addEventListener("beforeunload", () => {
      if (Object.keys(this.onboardingFlow.formData).length > 0) {
        this.onboardingFlow.dataManager.saveToLocalStorage();
      }
    });
  }

  /**
   * 닉네임 중복 검사 API 호출
   */
  async checkNicknameDuplicate(nickname, signal = null) {
    try {
      const result = await retryOperation(
        async () => {
          const fetchOptions = {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({ nickname }),
          };

          // AbortController 신호 추가
          if (signal) {
            fetchOptions.signal = signal;
          }

          const response = await fetch(
            "/onboarding/check-nickname",
            fetchOptions
          );

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }

          return await response.json();
        },
        2,
        500
      );

      if (result.success) {
        return !result.available; // available이 false면 중복(duplicate)
      } else {
        // 서버에서 오류가 발생한 경우, 사용자에게 알리고 재시도 요청
        console.warn("Nickname check server error:", result.error);
        throw new Error(result.error || "Server validation error");
      }
    } catch (error) {
      // AbortError는 그대로 전파
      if (error.name === "AbortError") {
        throw error;
      }

      console.error("Nickname check error:", error);
      // 네트워크 오류나 서버 오류 시 예외를 던져서 상위에서 처리
      throw error;
    }
  }

  /**
   * 진행 상황 저장 API 호출
   */
  async saveProgress(step, data) {
    const response = await fetch("/onboarding/save-progress", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({
        step: step,
        data: data,
        timestamp: new Date().toISOString(),
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * 진행 상황 로드 API 호출
   */
  async loadProgress() {
    const response = await fetch("/onboarding/get-progress");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  }

  /**
   * 폼 제출 API 호출
   */
  async submitForm(formData) {
    const response = await fetch("/onboarding", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("서버 응답 오류");
    }

    return response;
  }
}
