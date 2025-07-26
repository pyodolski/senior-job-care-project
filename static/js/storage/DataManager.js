import { getCurrentUserId, retryOperation } from "../utils/helpers.js";

/**
 * 데이터 저장 및 복원 관리 클래스
 */
export class DataManager {
  constructor(onboardingFlow) {
    this.onboardingFlow = onboardingFlow;
    this.lastSaveTime = null;
    this.lastServerSync = null;
  }

  /**
   * 자동 저장 기능 (AJAX) - 네트워크 오류 처리 및 재시도 포함
   */
  async autoSave() {
    // 네트워크 오프라인 상태 확인
    if (!navigator.onLine) {
      console.log("Offline - auto-save skipped");
      this.onboardingFlow.showSaveStatus(
        "오프라인 상태입니다. 온라인 복구 시 자동 저장됩니다.",
        "warning"
      );
      return;
    }

    try {
      // 재시도 로직과 함께 저장 실행
      const result = await retryOperation(
        async () => {
          return await this.onboardingFlow.networkManager.saveProgress(
            this.onboardingFlow.currentStep,
            this.onboardingFlow.formData
          );
        },
        3,
        1000
      );

      if (result.success) {
        this.onboardingFlow.showSaveStatus("자동 저장됨", "success");
        this.lastSaveTime = new Date();
      } else {
        console.warn("Auto-save warning:", result.error);
        this.onboardingFlow.showSaveStatus(
          "저장 중 문제가 발생했습니다.",
          "warning"
        );
      }
    } catch (error) {
      console.error("Auto-save error:", error);
      this.onboardingFlow.showSaveStatus(
        "저장 실패 - 다시 시도 중...",
        "error"
      );

      // 실패한 데이터를 로컬 스토리지에 임시 저장
      this.saveToLocalStorage();
    }
  }

  /**
   * 로컬 스토리지에 임시 저장
   */
  saveToLocalStorage() {
    try {
      const backupData = {
        step: this.onboardingFlow.currentStep,
        data: this.onboardingFlow.formData,
        timestamp: new Date().toISOString(),
        userId: getCurrentUserId(),
      };

      localStorage.setItem("onboarding_backup", JSON.stringify(backupData));
      console.log("Data backed up to localStorage");
    } catch (error) {
      console.error("localStorage backup failed:", error);
    }
  }

  /**
   * 저장된 진행 상황 로드 - 네트워크 오류 처리 포함
   */
  async loadSavedProgress() {
    try {
      // 재시도 로직과 함께 진행 상황 로드
      const result = await retryOperation(
        async () => {
          return await this.onboardingFlow.networkManager.loadProgress();
        },
        3,
        1000
      );

      if (result.success) {
        this.lastServerSync = new Date();

        // 서버에서 저장된 진행 상황이 있는 경우
        if (result.saved_progress && result.progress_data) {
          this.restoreProgress({
            step: result.current_step,
            data: result.progress_data,
            timestamp: result.timestamp,
          });
          this.onboardingFlow.showSaveStatus(
            "서버에서 진행 상황을 복원했습니다.",
            "success"
          );
        }
      } else {
        throw new Error(result.error || "Failed to load progress");
      }
    } catch (error) {
      console.error("Load progress error:", error);
      // 진행 상황 로드 실패는 조용히 처리 (처음 사용자일 수 있음)
    }
  }

  /**
   * 진행 상황 복원
   */
  restoreProgress(savedData) {
    if (!savedData) return;

    // 저장된 데이터 복원
    this.onboardingFlow.formData = { ...savedData.data };
    this.onboardingFlow.currentStep = savedData.step || 1;

    // UI에 데이터 반영
    this.populateFormFields();
    this.onboardingFlow.uiManager.updateUI();
  }

  /**
   * 폼 필드에 저장된 데이터 채우기
   */
  populateFormFields() {
    // 이름 필드
    if (this.onboardingFlow.formData.name) {
      const nameInput = document.getElementById("name");
      if (nameInput) nameInput.value = this.onboardingFlow.formData.name;
    }

    // 닉네임 필드
    if (this.onboardingFlow.formData.nickname) {
      const nicknameInput = document.getElementById("nickname");
      if (nicknameInput)
        nicknameInput.value = this.onboardingFlow.formData.nickname;
    }

    // 성별 선택
    if (this.onboardingFlow.formData.gender) {
      const genderBtn = document.querySelector(
        `[data-value="${this.onboardingFlow.formData.gender}"]`
      );
      if (genderBtn) {
        genderBtn.classList.add("selected");
      }
    }

    // 생년월일 필드
    if (this.onboardingFlow.formData.birth_date) {
      const birthInput = document.getElementById("birth_date");
      if (birthInput)
        birthInput.value = this.onboardingFlow.formData.birth_date;
    }
  }

  /**
   * 자동 저장 간격 설정
   */
  setupAutoSaveInterval() {
    // 5분마다 자동 저장 (사용자가 입력 중이 아닐 때만)
    setInterval(() => {
      if (
        Object.keys(this.onboardingFlow.formData).length > 0 &&
        !this.onboardingFlow.isValidating
      ) {
        this.autoSave();
      }
    }, 5 * 60 * 1000); // 5분
  }
}
