/**
 * UI 관리 클래스
 */
export class UIManager {
  constructor(onboardingFlow) {
    this.onboardingFlow = onboardingFlow;
  }

  /**
   * UI 업데이트
   */
  updateUI() {
    // 단계 컨테이너 표시/숨김
    this.onboardingFlow.stepContainers.forEach((container, index) => {
      const stepNumber = index + 1;
      if (stepNumber === this.onboardingFlow.currentStep) {
        container.classList.add("active");
        container.classList.remove("completed", "hidden");
      } else if (stepNumber < this.onboardingFlow.currentStep) {
        container.classList.add("completed");
        container.classList.remove("active", "hidden");
      } else {
        container.classList.add("hidden");
        container.classList.remove("active", "completed");
      }
    });

    // 진행률 바 업데이트
    this.updateProgressBar();

    // 버튼 상태 업데이트
    this.updateButtons();

    // 완료된 단계 요약 업데이트
    this.updateCompletedSteps();
  }

  /**
   * 진행률 바 업데이트
   */
  updateProgressBar() {
    if (this.onboardingFlow.progressBar) {
      const progress =
        (this.onboardingFlow.currentStep / this.onboardingFlow.maxStep) * 100;
      const progressFill =
        this.onboardingFlow.progressBar.querySelector(".progress-fill");
      if (progressFill) {
        progressFill.style.width = `${progress}%`;
      }

      // 단계 표시 업데이트
      const stepIndicators =
        this.onboardingFlow.progressBar.querySelectorAll(".step-indicator");
      stepIndicators.forEach((indicator, index) => {
        const stepNumber = index + 1;
        if (stepNumber <= this.onboardingFlow.currentStep) {
          indicator.classList.add("completed");
        } else {
          indicator.classList.remove("completed");
        }

        if (stepNumber === this.onboardingFlow.currentStep) {
          indicator.classList.add("current");
        } else {
          indicator.classList.remove("current");
        }
      });
    }
  }

  /**
   * 버튼 상태 업데이트
   */
  updateButtons() {
    // 이전 버튼
    if (this.onboardingFlow.prevBtn) {
      this.onboardingFlow.prevBtn.style.display =
        this.onboardingFlow.currentStep > 1 ? "block" : "none";
    }

    // 다음 버튼
    if (this.onboardingFlow.nextBtn) {
      this.onboardingFlow.nextBtn.style.display =
        this.onboardingFlow.currentStep < this.onboardingFlow.maxStep
          ? "block"
          : "none";
    }

    // 제출 버튼
    if (this.onboardingFlow.submitBtn) {
      this.onboardingFlow.submitBtn.style.display =
        this.onboardingFlow.currentStep === this.onboardingFlow.maxStep
          ? "block"
          : "none";
    }
  }

  /**
   * 완료된 단계 요약 업데이트
   */
  updateCompletedSteps() {
    const summaryContainer = document.querySelector(".completed-steps-summary");
    if (!summaryContainer) return;

    let summaryHTML = "";

    if (
      this.onboardingFlow.currentStep > 1 &&
      this.onboardingFlow.formData.name
    ) {
      summaryHTML += `<div class="summary-item">
                <span class="label">이름:</span>
                <span class="value">${this.onboardingFlow.formData.name}</span>
                <button class="edit-btn" onclick="onboardingFlow.goToStep(1)">수정</button>
            </div>`;
    }

    if (
      this.onboardingFlow.currentStep > 2 &&
      this.onboardingFlow.formData.nickname
    ) {
      summaryHTML += `<div class="summary-item">
                <span class="label">닉네임:</span>
                <span class="value">${this.onboardingFlow.formData.nickname}</span>
                <button class="edit-btn" onclick="onboardingFlow.goToStep(2)">수정</button>
            </div>`;
    }

    if (
      this.onboardingFlow.currentStep > 3 &&
      this.onboardingFlow.formData.gender
    ) {
      const genderText =
        this.onboardingFlow.formData.gender === "male" ? "남성" : "여성";
      summaryHTML += `<div class="summary-item">
                <span class="label">성별:</span>
                <span class="value">${genderText}</span>
                <button class="edit-btn" onclick="onboardingFlow.goToStep(3)">수정</button>
            </div>`;
    }

    summaryContainer.innerHTML = summaryHTML;
  }

  /**
   * 현재 입력 필드에 포커스
   */
  focusCurrentInput() {
    setTimeout(() => {
      const currentContainer = document.querySelector(
        `.step-container[data-step="${this.onboardingFlow.currentStep}"]`
      );
      if (currentContainer) {
        const input = currentContainer.querySelector("input, button");
        if (input) {
          input.focus();
        }
      }
    }, 100);
  }

  /**
   * 검증 메시지 표시
   */
  showValidationMessage(message, isError = false) {
    const messageContainer = document.querySelector(".validation-message");
    if (messageContainer) {
      messageContainer.textContent = message;
      messageContainer.className = `validation-message ${
        isError ? "error" : "success"
      }`;
      messageContainer.style.display = message ? "block" : "none";
    }
  }

  /**
   * 저장 상태 표시
   */
  showSaveStatus(message, type = "info") {
    const statusElement =
      document.querySelector(".save-status") || this.createSaveStatusElement();

    statusElement.textContent = message;
    statusElement.className = `save-status ${type}`;
    statusElement.style.display = "block";

    // 성공 메시지는 3초 후 자동 숨김
    if (type === "success") {
      setTimeout(() => {
        statusElement.style.display = "none";
      }, 3000);
    }
  }

  /**
   * 저장 상태 표시 요소 생성
   */
  createSaveStatusElement() {
    const statusElement = document.createElement("div");
    statusElement.className = "save-status";
    statusElement.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 10px 15px;
        border-radius: 5px;
        font-size: 14px;
        z-index: 1000;
        display: none;
    `;

    document.body.appendChild(statusElement);
    return statusElement;
  }
}
