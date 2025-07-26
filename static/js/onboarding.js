import { OnboardingFlow } from "./core/OnboardingFlow.js";
import { onboardingStyles } from "./styles/onboarding-styles.js";

// 스타일 추가
document.head.insertAdjacentHTML("beforeend", onboardingStyles);

// 전역 변수로 인스턴스 생성
let onboardingFlow;

// DOM 로드 완료 시 초기화
document.addEventListener("DOMContentLoaded", function () {
  onboardingFlow = new OnboardingFlow();

  // 전역 스코프에 노출 (템플릿에서 사용하기 위해)
  window.onboardingFlow = onboardingFlow;
});
