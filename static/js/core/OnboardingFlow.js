import { NetworkManager } from "../network/NetworkManager.js";
import { DataManager } from "../storage/DataManager.js";
import { UIManager } from "../ui/UIManager.js";
import { FormValidator } from "../validators/FormValidator.js";
import { getCsrfToken } from "../utils/helpers.js";

/**
 * OnboardingFlow 메인 클래스 - 단계별 온보딩 프로세스 관리
 */
export class OnboardingFlow {
  constructor() {
    this.currentStep = 1;
    this.maxStep = 4;
    this.formData = {};
    this.isValidating = false;
    this.inputTimeout = null;

    // DOM 요소 참조
    this.stepContainers = document.querySelectorAll(".step-container");
    this.progressBar = document.querySelector(".progress-bar");
    this.nextBtn = document.querySelector("#next-btn");
    this.prevBtn = document.querySelector("#prev-btn");
    this.submitBtn = document.querySelector("#submit-btn");

    // 관리자 클래스들 초기화
    this.networkManager = new NetworkManager(this);
    this.dataManager = new DataManager(this);
    this.uiManager = new UIManager(this);
    this.formValidator = new FormValidator(this);

    this.init();
  }

  /**
   * 초기화 메서드
   */
  init() {
    // 이벤트 바인딩 및 UI 초기화
    this.bindEvents();
    this.uiManager.updateUI();

    // 닉네임 검증 설정
    this.formValidator.setupNicknameValidation();

    // 네트워크 상태 감지 시작
    this.networkManager.handleNetworkStatus();

    // 저장된 진행 상황 로드 (비동기)
    this.dataManager.loadSavedProgress();

    // 저장 상태 표시 요소 생성
    this.uiManager.createSaveStatusElement();

    // 자동 저장 간격 설정 (5분마다)
    this.dataManager.setupAutoSaveInterval();
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
    const isValid = await this.formValidator.validateCurrentStep();
    if (!isValid) return;

    // 현재 단계 데이터 저장
    this.saveCurrentStepData();

    // 진행 상황 서버에 저장
    await this.dataManager.autoSave();

    // 다음 단계로 이동
    if (this.currentStep < this.maxStep) {
      this.currentStep++;
      this.uiManager.updateUI();
      this.uiManager.focusCurrentInput();
    }
  }

  /**
   * 이전 단계로 이동
   */
  prevStep() {
    if (this.currentStep > 1) {
      this.currentStep--;
      this.uiManager.updateUI();
      this.uiManager.focusCurrentInput();
    }
  }

  /**
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
      this.dataManager.autoSave();
    }
  }

  /**
   * 특정 단계로 이동
   */
  goToStep(step) {
    if (step >= 1 && step <= this.maxStep && step < this.currentStep) {
      this.currentStep = step;
      this.uiManager.updateUI();
      this.uiManager.focusCurrentInput();
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
        this.formValidator.debouncedNicknameCheck(input.value.trim());
      }
    }, 500);
  }

  /**
   * 폼 제출 - HTML 폼 데이터 형식으로 수정
   */
  async submitForm() {
    // 최종 검증
    const isValid = await this.formValidator.validateCurrentStep();
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
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        formData.append("csrf_token", csrfToken);
      }

      const response = await this.networkManager.submitForm(formData);

      if (response.ok) {
        // 성공 시 페이지 리로드 (서버에서 리다이렉트 처리)
        window.location.reload();
      }
    } catch (error) {
      console.error("Submit error:", error);
      this.uiManager.showValidationMessage(
        "제출 중 오류가 발생했습니다. 다시 시도해주세요.",
        true
      );
    }
  }

  /**
   * 저장 상태 표시 (UIManager로 위임)
   */
  showSaveStatus(message, type = "info") {
    this.uiManager.showSaveStatus(message, type);
  }
}
