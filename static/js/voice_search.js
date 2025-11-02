/**
 * 음성 검색 기능
 * 사람이음, 기업이음 페이지에서 공통으로 사용
 */

// 음성 인식 지원 확인
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

/**
 * 사람이음 음성 검색
 */
function startVoiceSearch() {
  if (!SpeechRecognition) {
    alert(
      "죄송합니다. 이 브라우저는 음성 인식을 지원하지 않습니다.\nChrome 또는 Edge 브라우저를 사용해주세요."
    );
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = "ko-KR";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  const voiceBtn = document.getElementById("voiceBtn");

  // 음성 인식 시작
  recognition.start();

  // 버튼 상태 변경 (듣는 중)
  if (voiceBtn) {
    voiceBtn.style.opacity = "0.5";
    voiceBtn.style.animation = "pulse 1s infinite";
  }

  // 음성 인식 성공
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    console.log("인식된 음성:", transcript);

    // 음성 피드백
    speak("검색 중입니다");

    // 사람이음 공고 검색 페이지로 이동
    window.location.href = `/jobs?q=${encodeURIComponent(transcript)}`;
  };

  // 음성 인식 종료
  recognition.onend = () => {
    if (voiceBtn) {
      voiceBtn.style.opacity = "1";
      voiceBtn.style.animation = "";
    }
  };

  // 음성 인식 오류
  recognition.onerror = (event) => {
    console.error("음성 인식 오류:", event.error);
    if (voiceBtn) {
      voiceBtn.style.opacity = "1";
      voiceBtn.style.animation = "";
    }

    handleVoiceError(event.error);
  };

  // 음성 인식 시작 알림
  speak("말씀해주세요");
}

/**
 * 기업이음 음성 검색
 */
function startVoiceSearchCompany() {
  if (!SpeechRecognition) {
    alert(
      "죄송합니다. 이 브라우저는 음성 인식을 지원하지 않습니다.\nChrome 또는 Edge 브라우저를 사용해주세요."
    );
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = "ko-KR";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  const voiceBtn = document.getElementById("voiceBtn");

  // 음성 인식 시작
  recognition.start();

  // 버튼 상태 변경 (듣는 중)
  if (voiceBtn) {
    voiceBtn.style.opacity = "0.5";
    voiceBtn.style.animation = "pulse 1s infinite";
  }

  // 음성 인식 성공
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    console.log("인식된 음성:", transcript);

    // 음성 피드백
    speak("검색 중입니다");

    // 기업이음 공고 검색 페이지로 이동
    window.location.href = `/company/list?q=${encodeURIComponent(transcript)}`;
  };

  // 음성 인식 종료
  recognition.onend = () => {
    if (voiceBtn) {
      voiceBtn.style.opacity = "1";
      voiceBtn.style.animation = "";
    }
  };

  // 음성 인식 오류
  recognition.onerror = (event) => {
    console.error("음성 인식 오류:", event.error);
    if (voiceBtn) {
      voiceBtn.style.opacity = "1";
      voiceBtn.style.animation = "";
    }

    handleVoiceError(event.error);
  };

  // 음성 인식 시작 알림
  speak("말씀해주세요");
}

/**
 * 음성 합성 (TTS)
 */
function speak(text) {
  if ("speechSynthesis" in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "ko-KR";
    utterance.rate = 0.9;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  }
}

/**
 * 음성 인식 오류 처리
 */
function handleVoiceError(error) {
  let errorMsg = "음성 인식에 실패했습니다.";

  switch (error) {
    case "no-speech":
      errorMsg = "음성이 감지되지 않았습니다. 다시 시도해주세요.";
      break;
    case "audio-capture":
      errorMsg = "마이크를 찾을 수 없습니다.";
      break;
    case "not-allowed":
      errorMsg =
        "마이크 권한이 필요합니다. 브라우저 설정에서 마이크 권한을 허용해주세요.";
      break;
  }

  alert(errorMsg);
}

// 펄스 애니메이션 CSS 추가
if (!document.getElementById("voice-search-style")) {
  const style = document.createElement("style");
  style.id = "voice-search-style";
  style.textContent = `
    @keyframes pulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.1); }
    }
  `;
  document.head.appendChild(style);
}
