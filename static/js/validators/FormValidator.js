import { calculateAge, debounce } from "../utils/helpers.js";

/**
 * 폼 검증 관리 클래스
 */
export class FormValidator {
  constructor(onboardingFlow) {
    this.onboardingFlow = onboardingFlow;
    this.nicknameCheckTimeout = null;
    this.nicknameCheckController = null;
  }

  /**
   * 현재 단계 데이터 검증
   */
  async validateCurrentStep() {
    this.onboardingFlow.isValidating = true;
    let isValid = true;
    let errorMessage = "";

    try {
      switch (this.onboardingFlow.currentStep) {
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
              const isDuplicate =
                await this.onboardingFlow.networkManager.checkNicknameDuplicate(
                  nickname
                );
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
          const gender = this.onboardingFlow.formData.gender;
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
            const age = calculateAge(birthDate);
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
      this.onboardingFlow.uiManager.showValidationMessage(
        errorMessage,
        !isValid
      );
    } catch (error) {
      console.error("Validation error:", error);
      this.onboardingFlow.uiManager.showValidationMessage(
        "검증 중 오류가 발생했습니다.",
        true
      );
      isValid = false;
    } finally {
      this.onboardingFlow.isValidating = false;
    }

    return isValid;
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

      const isDuplicate =
        await this.onboardingFlow.networkManager.checkNicknameDuplicate(
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
  }
}
