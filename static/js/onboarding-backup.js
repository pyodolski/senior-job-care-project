/**
 * OnboardingFlow 클래스 - 단계별 온보딩 프로세스 관리
 */
class OnboardingFlow {
  constructor() {
    this.currentStep = 1;
    this.maxStep = 4;
    this.formData = {};
    this.isValidating = false;

    // 초기 상태 설정
    this.isOnline = navigator.onLine;
    this.lastSaveTime = null;
    this.lastServerSync = null;
    this.inputTimeout = null;
    this.nicknameCheckTimeout = null;
    this.nicknameCheckController = null;

    // DOM 요소 참조
    this.stepContainers = document.querySelectorAll(".step-container");
    this.progressBar = document.querySelector(".progress-bar");
    this.nextBtn = document.querySelector("#next-btn");
    this.prevBtn = document.querySelector("#prev-btn");
    this.submitBtn = document.querySelector("#submit-btn");

    this.init();
  }

  /**
   * 초기화 메서드
   */
  init() {
    // 이벤트 바인딩 및 UI 초기화
    this.bindEvents();
    this.updateUI();

    // 닉네임 검증 설정
    this.setupNicknameValidation();

    // 네트워크 상태 감지 시작
    this.handleNetworkStatus();

    // 저장된 진행 상황 로드 (비동기)
    this.loadSavedProgress();

    // 저장 상태 표시 요소 생성
    this.createSaveStatusElement();

    // 자동 저장 간격 설정 (5분마다)
    this.setupAutoSaveInterval();
  }

  /**
   * 이벤트 바인딩
   */
  bindEvents() {
    // 다음 버튼 클릭
    if (this.nextBtn) {
      this.nextBtn.addEventListener("click", () => this.nextStep());
    }

    // 이전 버튼 클릭
    if (this.prevBtn) {
      this.prevBtn.addEventListener("click", () => this.prevStep());
    }

    // 제출 버튼 클릭
    if (this.submitBtn) {
      this.submitBtn.addEventListener("click", () => this.submitForm());
    }

    // Enter 키 처리
    document.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !this.isValidating) {
        e.preventDefault();
        if (this.currentStep < this.maxStep) {
          this.nextStep();
        } else {
          this.submitForm();
        }
      }
    });

    // 입력 필드 변경 시 자동 저장
    document.addEventListener("input", (e) => {
      if (e.target.classList.contains("step-input")) {
        this.handleInputChange(e.target);
      }
    });

    // 성별 버튼 클릭
    document.querySelectorAll(".gender-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        this.selectGender(e.target.dataset.value);
      });
    });
  }

  /**
   * 다음 단계로 이동
   */
  async nextStep() {
    if (this.isValidating) return;

    // 현재 단계 검증
    const isValid = await this.validateCurrentStep();
    if (!isValid) return;

    // 현재 단계 데이터 저장
    this.saveCurrentStepData();

    // 진행 상황 서버에 저장
    await this.autoSave();

    // 다음 단계로 이동
    if (this.currentStep < this.maxStep) {
      this.currentStep++;
      this.updateUI();
      this.focusCurrentInput();
    }
  }

  /**
   * 이전 단계로 이동
   */
  prevStep() {
    if (this.currentStep > 1) {
      this.currentStep--;
      this.updateUI();
      this.focusCurrentInput();
    }
  }

  /**
   * 현재 단계 데이터 검증
   */
  async validateCurrentStep() {
    this.isValidating = true;
    let isValid = true;
    let errorMessage = "";

    try {
      switch (this.currentStep) {
        case 1: // 이름 검증
          const name = document.getElementById("name")?.value?.trim();
          if (!name) {
            errorMessage = "이름을 입력해주세요.";
            isValid = false;
          } else if (name.length < 2) {
            errorMessage = "이름은 2글자 이상 입력해주세요.";
            isValid = false;
          } else if (name.length > 50) {
            errorMessage = "이름은 50글자 이하로 입력해주세요.";
            isValid = false;
          } else if (!/^[가-힣a-zA-Z\s]+$/.test(name)) {
            errorMessage = "이름은 한글, 영문, 공백만 입력 가능합니다.";
            isValid = false;
          }
          break;

        case 2: // 닉네임 검증
          const nickname = document.getElementById("nickname")?.value?.trim();
          if (!nickname) {
            errorMessage = "닉네임을 입력해주세요.";
            isValid = false;
          } else if (nickname.length < 2) {
            errorMessage = "닉네임은 2글자 이상 입력해주세요.";
            isValid = false;
          } else if (nickname.length > 20) {
            errorMessage = "닉네임은 20글자 이하로 입력해주세요.";
            isValid = false;
          } else if (!/^[가-힣a-zA-Z0-9]+$/.test(nickname)) {
            errorMessage = "닉네임은 한글, 영문, 숫자만 사용 가능합니다.";
            isValid = false;
          } else {
            // 닉네임 중복 검사 (실시간) - 오류 처리 개선
            try {
              const isDuplicate = await this.checkNicknameDuplicate(nickname);
              if (isDuplicate) {
                errorMessage = "이미 사용 중인 닉네임입니다.";
                isValid = false;
              }
            } catch (error) {
              console.error("Nickname validation error:", error);
              // 네트워크 오류 시 사용자에게 알리고 재시도 요청
              errorMessage =
                "닉네임 확인 중 오류가 발생했습니다. 네트워크 상태를 확인하고 다시 시도해주세요.";
              isValid = false;
            }
          }
          break;

        case 3: // 성별 검증
          const gender = this.formData.gender;
          if (!gender) {
            errorMessage = "성별을 선택해주세요.";
            isValid = false;
          }
          break;

        case 4: // 생년월일 검증
          const birthDate = document.getElementById("birth_date")?.value;
          if (!birthDate) {
            errorMessage = "생년월일을 입력해주세요.";
            isValid = false;
          } else {
            const age = this.calculateAge(birthDate);
            if (age < 14) {
              errorMessage = "만 14세 이상만 가입 가능합니다.";
              isValid = false;
            } else if (age > 100) {
              errorMessage = "올바른 생년월일을 입력해주세요.";
              isValid = false;
            }
          }
          break;
      }

      // 검증 결과 UI 업데이트
      this.showValidationMessage(errorMessage, !isValid);
    } catch (error) {
      console.error("Validation error:", error);
      this.showValidationMessage("검증 중 오류가 발생했습니다.", true);
      isValid = false;
    } finally {
      this.isValidating = false;
    }

    return isValid;
  } /**
 
  * 현재 단계 데이터 저장
   */
  saveCurrentStepData() {
    switch (this.currentStep) {
      case 1:
        this.formData.name = document.getElementById("name")?.value?.trim();
        break;
      case 2:
        this.formData.nickname = document
          .getElementById("nickname")
          ?.value?.trim();
        break;
      case 3:
        // 성별은 selectGender에서 이미 저장됨
        break;
      case 4:
        this.formData.birth_date = document.getElementById("birth_date")?.value;
        break;
    }
  }

  /**
   * 성별 선택 처리
   */
  selectGender(gender) {
    // 모든 성별 버튼 비활성화
    document.querySelectorAll(".gender-btn").forEach((btn) => {
      btn.classList.remove("selected");
    });

    // 선택된 버튼 활성화
    const selectedBtn = document.querySelector(`[data-value="${gender}"]`);
    if (selectedBtn) {
      selectedBtn.classList.add("selected");
      this.formData.gender = gender;

      // 자동 저장
      this.autoSave();
    }
  }

  /**
   * UI 업데이트
   */
  updateUI() {
    // 단계 컨테이너 표시/숨김
    this.stepContainers.forEach((container, index) => {
      const stepNumber = index + 1;
      if (stepNumber === this.currentStep) {
        container.classList.add("active");
        container.classList.remove("completed", "hidden");
      } else if (stepNumber < this.currentStep) {
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
    if (this.progressBar) {
      const progress = (this.currentStep / this.maxStep) * 100;
      const progressFill = this.progressBar.querySelector(".progress-fill");
      if (progressFill) {
        progressFill.style.width = `${progress}%`;
      }

      // 단계 표시 업데이트
      const stepIndicators =
        this.progressBar.querySelectorAll(".step-indicator");
      stepIndicators.forEach((indicator, index) => {
        const stepNumber = index + 1;
        if (stepNumber <= this.currentStep) {
          indicator.classList.add("completed");
        } else {
          indicator.classList.remove("completed");
        }

        if (stepNumber === this.currentStep) {
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
    if (this.prevBtn) {
      this.prevBtn.style.display = this.currentStep > 1 ? "block" : "none";
    }

    // 다음 버튼
    if (this.nextBtn) {
      this.nextBtn.style.display =
        this.currentStep < this.maxStep ? "block" : "none";
    }

    // 제출 버튼
    if (this.submitBtn) {
      this.submitBtn.style.display =
        this.currentStep === this.maxStep ? "block" : "none";
    }
  }

  /**
   * 완료된 단계 요약 업데이트
   */
  updateCompletedSteps() {
    const summaryContainer = document.querySelector(".completed-steps-summary");
    if (!summaryContainer) return;

    let summaryHTML = "";

    if (this.currentStep > 1 && this.formData.name) {
      summaryHTML += `<div class="summary-item">
                <span class="label">이름:</span>
                <span class="value">${this.formData.name}</span>
                <button class="edit-btn" onclick="onboardingFlow.goToStep(1)">수정</button>
            </div>`;
    }

    if (this.currentStep > 2 && this.formData.nickname) {
      summaryHTML += `<div class="summary-item">
                <span class="label">닉네임:</span>
                <span class="value">${this.formData.nickname}</span>
                <button class="edit-btn" onclick="onboardingFlow.goToStep(2)">수정</button>
            </div>`;
    }

    if (this.currentStep > 3 && this.formData.gender) {
      const genderText = this.formData.gender === "male" ? "남성" : "여성";
      summaryHTML += `<div class="summary-item">
                <span class="label">성별:</span>
                <span class="value">${genderText}</span>
                <button class="edit-btn" onclick="onboardingFlow.goToStep(3)">수정</button>
            </div>`;
    }

    summaryContainer.innerHTML = summaryHTML;
  }

  /**
   * 특정 단계로 이동
   */
  goToStep(step) {
    if (step >= 1 && step <= this.maxStep && step < this.currentStep) {
      this.currentStep = step;
      this.updateUI();
      this.focusCurrentInput();
    }
  }

  /**
   * 현재 입력 필드에 포커스
   */
  focusCurrentInput() {
    setTimeout(() => {
      const currentContainer = document.querySelector(
        `.step-container[data-step="${this.currentStep}"]`
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
   * 나이 계산
   */
  calculateAge(birthDate) {
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();

    if (
      monthDiff < 0 ||
      (monthDiff === 0 && today.getDate() < birth.getDate())
    ) {
      age--;
    }

    return age;
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
   * 입력 변경 처리
   */
  handleInputChange(input) {
    // 실시간 검증 및 저장을 위한 디바운스
    clearTimeout(this.inputTimeout);
    this.inputTimeout = setTimeout(() => {
      this.saveCurrentStepData();

      // 닉네임 실시간 중복 검사
      if (input.id === "nickname") {
        this.debouncedNicknameCheck(input.value.trim());
      }
    }, 500);
  }

  /**
   * 폼 제출 - HTML 폼 데이터 형식으로 수정
   */
  async submitForm() {
    // 최종 검증
    const isValid = await this.validateCurrentStep();
    if (!isValid) return;

    // 모든 데이터 수집
    this.saveCurrentStepData();

    try {
      // HTML 폼 데이터로 전송
      const formData = new FormData();

      // 모든 데이터를 폼 데이터로 추가
      if (this.formData.name) formData.append("name", this.formData.name);
      if (this.formData.nickname)
        formData.append("nickname", this.formData.nickname);
      if (this.formData.gender) formData.append("gender", this.formData.gender);
      if (this.formData.birth_date)
        formData.append("birth_date", this.formData.birth_date);

      // 현재 단계 정보 추가
      formData.append("step", "4");

      // CSRF 토큰 추가
      const csrfToken = this.getCsrfToken();
      if (csrfToken) {
        formData.append("csrf_token", csrfToken);
      }

      const response = await fetch("/onboarding", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        // 성공 시 페이지 리로드 (서버에서 리다이렉트 처리)
        window.location.reload();
      } else {
        throw new Error("서버 응답 오류");
      }
    } catch (error) {
      console.error("Submit error:", error);
      this.showValidationMessage(
        "제출 중 오류가 발생했습니다. 다시 시도해주세요.",
        true
      );
    }
  }

  /**
   * CSRF 토큰 가져오기
   */
  getCsrfToken() {
    const token = document
      .querySelector('meta[name="csrf-token"]')
      ?.getAttribute("content");
    return token || "";
  } /**
   * 
자동 저장 기능 (AJAX) - 네트워크 오류 처리 및 재시도 포함
   */
  async autoSave() {
    // 네트워크 오프라인 상태 확인
    if (!navigator.onLine) {
      console.log("Offline - auto-save skipped");
      this.showSaveStatus(
        "오프라인 상태입니다. 온라인 복구 시 자동 저장됩니다.",
        "warning"
      );
      return;
    }

    try {
      // 재시도 로직과 함께 저장 실행
      const result = await this.retryOperation(
        async () => {
          const response = await fetch("/onboarding/save-progress", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": this.getCsrfToken(),
            },
            body: JSON.stringify({
              step: this.currentStep,
              data: this.formData,
              timestamp: new Date().toISOString(),
            }),
          });

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }

          return await response.json();
        },
        3,
        1000
      );

      if (result.success) {
        this.showSaveStatus("자동 저장됨", "success");
        this.lastSaveTime = new Date();
      } else {
        console.warn("Auto-save warning:", result.error);
        this.showSaveStatus("저장 중 문제가 발생했습니다.", "warning");
      }
    } catch (error) {
      console.error("Auto-save error:", error);
      this.showSaveStatus("저장 실패 - 다시 시도 중...", "error");

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
        step: this.currentStep,
        data: this.formData,
        timestamp: new Date().toISOString(),
        userId: this.getCurrentUserId(),
      };

      localStorage.setItem("onboarding_backup", JSON.stringify(backupData));
      console.log("Data backed up to localStorage");
    } catch (error) {
      console.error("localStorage backup failed:", error);
    }
  }

  /**
   * 현재 사용자 ID 가져오기
   */
  getCurrentUserId() {
    const userIdElement = document.querySelector("[data-user-id]");
    return userIdElement ? userIdElement.dataset.userId : null;
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

  /**
   * 저장된 진행 상황 로드 - 네트워크 오류 처리 포함
   */
  async loadSavedProgress() {
    try {
      // 재시도 로직과 함께 진행 상황 로드
      const result = await this.retryOperation(
        async () => {
          const response = await fetch("/onboarding/get-progress");
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
          return await response.json();
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
          this.showSaveStatus("서버에서 진행 상황을 복원했습니다.", "success");
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
    this.formData = { ...savedData.data };
    this.currentStep = savedData.step || 1;

    // UI에 데이터 반영
    this.populateFormFields();
    this.updateUI();
  }

  /**
   * 폼 필드에 저장된 데이터 채우기
   */
  populateFormFields() {
    // 이름 필드
    if (this.formData.name) {
      const nameInput = document.getElementById("name");
      if (nameInput) nameInput.value = this.formData.name;
    }

    // 닉네임 필드
    if (this.formData.nickname) {
      const nicknameInput = document.getElementById("nickname");
      if (nicknameInput) nicknameInput.value = this.formData.nickname;
    }

    // 성별 선택
    if (this.formData.gender) {
      const genderBtn = document.querySelector(
        `[data-value="${this.formData.gender}"]`
      );
      if (genderBtn) {
        genderBtn.classList.add("selected");
      }
    }

    // 생년월일 필드
    if (this.formData.birth_date) {
      const birthInput = document.getElementById("birth_date");
      if (birthInput) birthInput.value = this.formData.birth_date;
    }
  }
  /*
   *
   * 닉네임 중복 검사 API 호출 - 안전한 오류 처리
   */
  async checkNicknameDuplicate(nickname, signal = null) {
    try {
      const result = await this.retryOperation(
        async () => {
          const fetchOptions = {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": this.getCsrfToken(),
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
   * 닉네임 중복 검사 (실시간) - 향상된 UX
   */
  async checkNicknameRealtime(nickname) {
    const nicknameInput = document.getElementById("nickname");

    // 입력값이 없거나 너무 짧은 경우
    if (!nickname || nickname.length < 2) {
      this.showNicknameValidation("", false);
      this.removeInputValidationClass(nicknameInput);
      return;
    }

    // 길이 제한 검사
    if (nickname.length > 20) {
      this.showNicknameValidation("닉네임은 20자 이하로 입력해주세요.", true);
      this.setInputValidationClass(nicknameInput, "invalid");
      return;
    }

    // 특수문자 검사 (한글, 영문, 숫자만 허용)
    if (!/^[가-힣a-zA-Z0-9]+$/.test(nickname)) {
      this.showNicknameValidation(
        "닉네임은 한글, 영문, 숫자만 사용 가능합니다.",
        true
      );
      this.setInputValidationClass(nicknameInput, "invalid");
      return;
    }

    // 로딩 상태 표시
    this.showNicknameValidation("확인 중...", false, true);
    this.setInputValidationClass(nicknameInput, "checking");

    try {
      // 이전 요청 취소
      if (this.nicknameCheckController) {
        this.nicknameCheckController.abort();
      }

      // 새로운 AbortController 생성
      this.nicknameCheckController = new AbortController();

      const isDuplicate = await this.checkNicknameDuplicate(
        nickname,
        this.nicknameCheckController.signal
      );

      if (isDuplicate) {
        this.showNicknameValidation("이미 사용 중인 닉네임입니다.", true);
        this.setInputValidationClass(nicknameInput, "invalid");
      } else {
        this.showNicknameValidation("사용 가능한 닉네임입니다.", false);
        this.setInputValidationClass(nicknameInput, "valid");
      }
    } catch (error) {
      // AbortError는 무시 (사용자가 계속 입력 중)
      if (error.name === "AbortError") {
        return;
      }

      console.error("Nickname check error:", error);
      // 네트워크 오류 시에는 사용자에게 재시도 안내
      this.showNicknameValidation(
        "네트워크 오류로 확인할 수 없습니다. 잠시 후 다시 시도해주세요.",
        true
      );
      this.setInputValidationClass(nicknameInput, "error");
    }
  }

  /**
   * 입력 필드 검증 상태 클래스 설정
   */
  setInputValidationClass(input, state) {
    if (!input) return;

    // 기존 검증 클래스 제거
    input.classList.remove("valid", "invalid", "checking", "error");

    // 새로운 상태 클래스 추가
    if (state) {
      input.classList.add(state);
    }
  }

  /**
   * 입력 필드 검증 클래스 제거
   */
  removeInputValidationClass(input) {
    if (!input) return;
    input.classList.remove("valid", "invalid", "checking", "error");
  }

  /**
   * 닉네임 검증 메시지 표시 - 향상된 UI 피드백
   */
  showNicknameValidation(message, isError, isLoading = false) {
    const validationElement = document.getElementById("nickname-validation");
    if (!validationElement) return;

    // 메시지 설정
    if (isLoading) {
      validationElement.innerHTML = `
            <span class="loading-spinner"></span>
            <span>${message}</span>
        `;
    } else {
      validationElement.textContent = message;
    }

    // 클래스 설정
    let className = "validation-message";
    if (isLoading) {
      className += " loading";
    } else if (isError) {
      className += " error";
    } else if (message) {
      className += " success";
    }

    validationElement.className = className;
    validationElement.style.display = message ? "block" : "none";

    // 성공 메시지는 3초 후 자동 숨김
    if (!isError && !isLoading && message) {
      setTimeout(() => {
        if (validationElement.textContent === message) {
          validationElement.style.display = "none";
        }
      }, 3000);
    }
  }

  /**
   * 디바운스된 닉네임 검사
   */
  debouncedNicknameCheck(nickname) {
    // 이전 타이머 취소
    if (this.nicknameCheckTimeout) {
      clearTimeout(this.nicknameCheckTimeout);
    }

    // 새로운 타이머 설정 (500ms 지연)
    this.nicknameCheckTimeout = setTimeout(() => {
      this.checkNicknameRealtime(nickname);
    }, 500);
  }

  /**
   * 닉네임 입력 필드 이벤트 핸들러 개선
   */
  setupNicknameValidation() {
    const nicknameInput = document.getElementById("nickname");
    if (!nicknameInput) return;

    // 실시간 입력 이벤트
    nicknameInput.addEventListener("input", (e) => {
      const nickname = e.target.value.trim();

      // 즉시 기본 검증 (길이, 특수문자)
      this.validateNicknameFormat(nickname);

      // 디바운스된 중복 검사
      if (nickname.length >= 2) {
        this.debouncedNicknameCheck(nickname);
      }
    });

    // 포커스 아웃 시 최종 검증
    nicknameInput.addEventListener("blur", (e) => {
      const nickname = e.target.value.trim();
      if (nickname.length >= 2) {
        this.checkNicknameRealtime(nickname);
      }
    });

    // 엔터 키 처리
    nicknameInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const nickname = e.target.value.trim();
        if (nickname.length >= 2) {
          this.checkNicknameRealtime(nickname);
        }
      }
    });
  }

  /**
   * 닉네임 형식 검증 (즉시 피드백)
   */
  validateNicknameFormat(nickname) {
    const nicknameInput = document.getElementById("nickname");

    if (!nickname) {
      this.showNicknameValidation("", false);
      this.removeInputValidationClass(nicknameInput);
      return true;
    }

    if (nickname.length < 2) {
      this.showNicknameValidation("닉네임은 2자 이상 입력해주세요.", true);
      this.setInputValidationClass(nicknameInput, "invalid");
      return false;
    }

    if (nickname.length > 20) {
      this.showNicknameValidation("닉네임은 20자 이하로 입력해주세요.", true);
      this.setInputValidationClass(nicknameInput, "invalid");
      return false;
    }

    if (!/^[가-힣a-zA-Z0-9]+$/.test(nickname)) {
      this.showNicknameValidation(
        "닉네임은 한글, 영문, 숫자만 사용 가능합니다.",
        true
      );
      this.setInputValidationClass(nicknameInput, "invalid");
      return false;
    }

    // 형식이 올바른 경우
    this.removeInputValidationClass(nicknameInput);
    return true;
  } /**

   * 네트워크 오류 처리 및 재시도
   */
  async retryOperation(operation, maxRetries = 3, delay = 1000) {
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

  /**
   * 온라인/오프라인 상태 감지 및 처리
   */
  handleNetworkStatus() {
    // 온라인 복구 시 처리
    window.addEventListener("online", () => {
      console.log("Network restored");
      this.showSaveStatus("네트워크가 복구되었습니다.", "success");

      // 현재 진행 상황 자동 저장
      if (Object.keys(this.formData).length > 0) {
        this.autoSave();
      }
    });

    // 오프라인 시 처리
    window.addEventListener("offline", () => {
      console.log("Network lost");
      this.showSaveStatus(
        "네트워크 연결이 끊어졌습니다. 로컬에 임시 저장됩니다.",
        "warning"
      );
    });

    // 페이지 언로드 시 현재 상태 백업
    window.addEventListener("beforeunload", () => {
      if (Object.keys(this.formData).length > 0) {
        this.saveToLocalStorage();
      }
    });
  }

  /**
   * 자동 저장 간격 설정
   */
  setupAutoSaveInterval() {
    // 5분마다 자동 저장 (사용자가 입력 중이 아닐 때만)
    setInterval(() => {
      if (Object.keys(this.formData).length > 0 && !this.isValidating) {
        this.autoSave();
      }
    }, 5 * 60 * 1000); // 5분
  }
}

// CSS 스타일 추가
const saveStatusStyles = `
<style>
.save-status {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 10px 15px;
    border-radius: 5px;
    font-size: 14px;
    font-weight: 500;
    z-index: 1000;
    display: none;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
}

.save-status.success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.save-status.error {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.save-status.warning {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
}

.save-status.info {
    background-color: #d1ecf1;
    color: #0c5460;
    border: 1px solid #bee5eb;
}

/* 입력 필드 검증 상태 스타일 */
.step-input {
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.step-input.valid {
    border-color: #28a745;
    box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25);
}

.step-input.invalid {
    border-color: #dc3545;
    box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
}

.step-input.checking {
    border-color: #ffc107;
    box-shadow: 0 0 0 0.2rem rgba(255, 193, 7, 0.25);
}

.step-input.error {
    border-color: #dc3545;
    box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
}

/* 검증 메시지 스타일 개선 */
.validation-message {
    margin-top: 8px;
    font-size: 14px;
    padding: 8px 12px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    transition: all 0.3s ease;
}

.validation-message.error {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.validation-message.success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.validation-message.loading {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
}

/* 로딩 스피너 */
.loading-spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid #f3f3f3;
    border-top: 2px solid #856404;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-right: 8px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* 성별 버튼 스타일 */
.gender-btn {
    transition: all 0.3s ease;
    margin: 0 10px;
    padding: 12px 24px;
    border: 2px solid #dee2e6;
    background-color: white;
    border-radius: 8px;
    cursor: pointer;
}

.gender-btn:hover {
    border-color: #007bff;
    background-color: #f8f9fa;
}

.gender-btn.selected {
    background-color: #007bff;
    color: white;
    border-color: #007bff;
    transform: scale(1.05);
}

/* 단계 전환 애니메이션 */
.step-container.hidden {
    display: none;
}

.step-container.active {
    display: block;
    animation: fadeIn 0.3s ease-in-out;
}

.step-container.completed {
    opacity: 0.7;
    transform: scale(0.98);
    transition: all 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* 진행률 바 스타일 */
.progress-fill {
    transition: width 0.5s ease;
    background: linear-gradient(90deg, #007bff, #0056b3);
}

.step-indicator {
    transition: all 0.3s ease;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    border: 2px solid #dee2e6;
    background-color: white;
    color: #6c757d;
}

.step-indicator.completed {
    background-color: #28a745;
    color: white;
    border-color: #28a745;
    transform: scale(1.1);
}

.step-indicator.current {
    background-color: #007bff;
    color: white;
    border-color: #007bff;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(0, 123, 255, 0); }
    100% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0); }
}

/* 완료된 단계 요약 스타일 */
.completed-steps-summary {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 20px;
}

.summary-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #dee2e6;
}

.summary-item:last-child {
    border-bottom: none;
}

.summary-item .label {
    font-weight: 600;
    color: #495057;
}

.summary-item .value {
    color: #007bff;
    font-weight: 500;
}

.edit-btn {
    background: none;
    border: 1px solid #007bff;
    color: #007bff;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.edit-btn:hover {
    background-color: #007bff;
    color: white;
}
</style>
`;

// 스타일 추가
document.head.insertAdjacentHTML("beforeend", saveStatusStyles);

// 전역 변수로 인스턴스 생성
let onboardingFlow;

// DOM 로드 완료 시 초기화
document.addEventListener("DOMContentLoaded", function () {
  onboardingFlow = new OnboardingFlow();
});
