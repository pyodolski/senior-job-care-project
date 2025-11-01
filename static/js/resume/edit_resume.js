let currentStep = 1;
const totalSteps = 6;

function showStep(step) {
  document
    .querySelectorAll(".step-container")
    .forEach((el) => (el.style.display = "none"));

  const stepId =
    typeof step === "string" ? `step-${step}` : `step-${step}`;
  const stepElement = document.getElementById(stepId);

  if (stepElement) {
    stepElement.style.display = "block";
    currentStep = step;
    updateFooterButton();
  }
}

function updateFooterButton() {
  const footerBtn = document.getElementById("footer-next-btn");
  const isLastStep = currentStep === 7 || currentStep === "7";

  if (isLastStep) {
    footerBtn.textContent = "제출하기";
    footerBtn.classList.remove("bg-blue-600", "hover:bg-blue-700");
    footerBtn.classList.add("bg-green-600", "hover:bg-green-700");
  } else {
    footerBtn.textContent = "다음";
    footerBtn.classList.remove("bg-green-600", "hover:bg-green-700");
    footerBtn.classList.add("bg-blue-600", "hover:bg-blue-700");
  }
}

function handleFooterNext() {
  if (currentStep === 7 || currentStep === "7") {
    // 마지막 단계(미리보기)에서는 form submit
    document.querySelector("form").submit();
  } else {
    // 다음 단계로 이동
    let nextStepValue;
    if (currentStep === 1) nextStepValue = 2;
    else if (currentStep === 2) nextStepValue = 3;
    else if (currentStep === 3) nextStepValue = 4;
    else if (currentStep === 4) nextStepValue = 5;
    else if (currentStep === 5) nextStepValue = "5-2";
    else if (currentStep === "5-2") nextStepValue = "5-3";
    else if (currentStep === "5-3") nextStepValue = 6;
    else if (currentStep === 6) nextStepValue = 7;
    else nextStepValue = currentStep + 1;

    nextStep(nextStepValue);
  }
}

// 미리보기 표시
function showPreview() {
  updatePreview();
  nextStep(7);
}

// 특정 단계 수정
function editStep(step) {
  prevStep(step);
}

// 미리보기 업데이트
function updatePreview() {
  // 1. 희망 직무분야
  const category = document.querySelector(
    'input[name="categories"]:checked'
  );
  document.getElementById("preview-category").textContent = category
    ? category.value
    : "미선택";

  // 2. 희망 근무 형태
  const workType = document.querySelector(
    'input[name="desired_work_type"]:checked'
  );
  document.getElementById("preview-work-type").textContent = workType
    ? workType.nextElementSibling.textContent
    : "미선택";

  // 3. 희망 근무 요일
  const dayNegotiable = document.getElementById("day_negotiable").checked;
  if (dayNegotiable) {
    document.getElementById("preview-days").textContent = "요일 협의 가능";
  } else {
    const days = [];
    const dayNames = {
      monday: "월",
      tuesday: "화",
      wednesday: "수",
      thursday: "목",
      friday: "금",
      saturday: "토",
      sunday: "일",
    };
    for (let day in dayNames) {
      const checkbox = document.querySelector(`input[name="work_${day}"]`);
      if (checkbox && checkbox.checked) {
        days.push(dayNames[day]);
      }
    }
    document.getElementById("preview-days").textContent =
      days.length > 0 ? days.join(", ") : "미선택";
  }

  // 4. 희망 근무 시간
  const timeNegotiable =
    document.getElementById("time_negotiable").checked;
  if (timeNegotiable) {
    document.getElementById("preview-time").textContent = "시간 협의 가능";
  } else {
    const startTime = document.getElementById("start_time").value;
    const endTime = document.getElementById("end_time").value;
    let timeText = "";
    if (startTime && endTime) {
      const startPeriod =
        parseInt(startTime.split(":")[0]) < 12 ? "오전" : "오후";
      const endPeriod =
        parseInt(endTime.split(":")[0]) < 12 ? "오전" : "오후";
      timeText = `${startPeriod} ${startTime} ~ ${endPeriod} ${endTime}`;
    }
    document.getElementById("preview-time").textContent =
      timeText || "미설정";
  }

  // 5. 경력 및 경험
  const experienceContainer =
    document.getElementById("preview-experience");
  experienceContainer.innerHTML = "";
  if (experienceItems.length > 0) {
    experienceItems.forEach((item) => {
      const p = document.createElement("p");
      p.textContent = "• " + item;
      experienceContainer.appendChild(p);
    });
  } else {
    experienceContainer.textContent = "등록된 경력이 없습니다";
  }

  // 6. 보유 기술 및 재능
  const certsContainer = document.getElementById("preview-certificates");
  certsContainer.innerHTML = "";
  const existingCerts = document.querySelectorAll(
    "#existing-certificates-list .border-blue-600"
  );
  const newCerts = document.querySelectorAll(
    "#certificates-container .certificate-entry"
  );
  const totalCerts = existingCerts.length + newCerts.length;

  if (totalCerts > 0) {
    existingCerts.forEach((cert) => {
      const p = document.createElement("p");
      p.textContent = "• " + cert.querySelector("span").textContent;
      certsContainer.appendChild(p);
    });
    newCerts.forEach((cert) => {
      const p = document.createElement("p");
      p.textContent = "• " + cert.querySelector("span").textContent;
      certsContainer.appendChild(p);
    });
  } else {
    certsContainer.textContent = "등록된 자격증이 없습니다";
  }

  // 7. 성격 및 강점
  const strengths = [];
  document
    .querySelectorAll('input[name="strengths"]:checked')
    .forEach((input) => {
      strengths.push(input.value);
    });
  document.getElementById("preview-strengths").textContent =
    strengths.length > 0 ? strengths.join(", ") : "미선택";

  // 8. 신체적 활동 가능 범위
  const walkableMinutes =
    document.getElementById("walkable-slider").value;
  let walkableText = "";
  if (walkableMinutes == 0) walkableText = "못함";
  else if (walkableMinutes <= 20) walkableText = "20분";
  else if (walkableMinutes <= 40) walkableText = "40분";
  else walkableText = "1시간";
  document.getElementById(
    "preview-walkable"
  ).textContent = `쉬지 않고 걸을 수 있는 시간: ${walkableText}`;

  const physicalContainer = document.getElementById("preview-physical");
  physicalContainer.innerHTML = "";
  if (physicalNotes.length > 0) {
    physicalNotes.forEach((item) => {
      const p = document.createElement("p");
      p.textContent = "• " + item;
      physicalContainer.appendChild(p);
    });
  }

  // 9. 이동 가능 범위
  const commuteNegotiable = document.getElementById("commute-negotiable").checked;
  if (commuteNegotiable) {
    document.getElementById(
      "preview-commute"
    ).textContent = "교통 수단 불가";
  } else {
    const commuteTime = document.getElementById("commute-slider").value;
    let commuteText = "";
    if (commuteTime == 0) commuteText = "집";
    else if (commuteTime <= 20) commuteText = "20분";
    else if (commuteTime <= 40) commuteText = "40분";
    else commuteText = "1시간";
    document.getElementById(
      "preview-commute"
    ).textContent = `대중교통 또는 자차로 가능한 이동시간: ${commuteText}`;
  }

  // 10. 자기소개
  const introduction = document.querySelector(
    'textarea[name="self_introduction"]'
  ).value;
  document.getElementById("preview-introduction").textContent =
    introduction || "작성되지 않았습니다";

  // 11. 통화가능 시간
  const callTime = document.querySelector(
    'input[name="call_available_time"]'
  ).value;
  document.getElementById("preview-call-time").textContent =
    callTime || "미설정";

  // 12. 개인정보 제3자 제공동의
  const privacyConsent = document.querySelector(
    'input[name="privacy_consent"]'
  ).checked;
  document.getElementById("preview-privacy").textContent = privacyConsent
    ? "동의함"
    : "미동의";

  // 13. 이력서 공개 설정
  const isPublic = document.querySelector(
    'input[name="is_public"]'
  ).checked;
  document.getElementById("preview-public").textContent = isPublic
    ? "기업에게 공개됨"
    : "비공개";
}

function handleBackButton() {
  if (currentStep === 1) {
    // 첫 단계에서는 프로필 페이지로 이동
    window.location.href = profileUrl;
  } else {
    // 이전 단계로 이동
    let prevStepValue;
    if (currentStep === 2) prevStepValue = 1;
    else if (currentStep === 3) prevStepValue = 2;
    else if (currentStep === 4) prevStepValue = 3;
    else if (currentStep === 5) prevStepValue = 4;
    else if (currentStep === "5-2") prevStepValue = 5;
    else if (currentStep === "5-3") prevStepValue = "5-2";
    else if (currentStep === 6) prevStepValue = "5-3";
    else if (currentStep === 7) prevStepValue = 6;
    else prevStepValue = currentStep - 1;

    prevStep(prevStepValue);
  }
}

function nextStep(step) {
  currentStep = step;
  showStep(step);
}

function prevStep(step) {
  currentStep = step;
  showStep(step);
}

// 슬라이더 배경색 업데이트 함수
function updateSliderBackground(slider) {
  const min = slider.min || 0;
  const max = slider.max || 100;
  const value = slider.value;
  const percentage = ((value - min) / (max - min)) * 100;

  slider.style.background = `linear-gradient(to right, #2563eb 0%, #2563eb ${percentage}%, #e5e7eb ${percentage}%, #e5e7eb 100%)`;
}

// 초기화
document.addEventListener("DOMContentLoaded", function () {
  showStep(1);
  initTimeSelectors();
  updateTimeDisplay();
  initExperienceList();
  initPhysicalNotesList();

  // 슬라이더 초기 배경색 설정
  const walkableSlider = document.getElementById("walkable-slider");
  const commuteSlider = document.getElementById("commute-slider");

  if (walkableSlider) {
    updateSliderBackground(walkableSlider);
    walkableSlider.addEventListener("input", function() {
      updateSliderBackground(this);
    });
  }

  if (commuteSlider) {
    updateSliderBackground(commuteSlider);
    commuteSlider.addEventListener("input", function() {
      updateSliderBackground(this);
    });
  }
});

// 신체적 특성 관련 함수
let physicalNotes = [];

function initPhysicalNotesList() {
  const physicalHidden = document.getElementById("physical-notes-hidden");
  const physicalText = physicalHidden.value.trim();

  if (physicalText) {
    physicalNotes = physicalText
      .split("\n")
      .filter((item) => item.trim());
    updatePhysicalNotesDisplay();
  }
}

function addPhysicalNote() {
  const input = document.getElementById("physical-input");
  const value = input.value.trim();

  if (value) {
    physicalNotes.push(value);
    updatePhysicalNotesDisplay();
    updatePhysicalNotesHidden();
    input.value = "";
  }
}

function removePhysicalNote(index) {
  physicalNotes.splice(index, 1);
  updatePhysicalNotesDisplay();
  updatePhysicalNotesHidden();
}

function updatePhysicalNotesDisplay() {
  const list = document.getElementById("physical-notes-list");
  list.innerHTML = "";

  physicalNotes.forEach((item, index) => {
    const div = document.createElement("div");
    div.className =
      "border-2 border-blue-600 rounded-lg px-4 py-3 flex items-center justify-between";
    div.innerHTML = `
      <span class="text-gray-900 flex-1">${item}</span>
      <button
        type="button"
        class="text-gray-400 hover:text-gray-600 ml-2"
        onclick="removePhysicalNote(${index})"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    `;
    list.appendChild(div);
  });
}

function updatePhysicalNotesHidden() {
  const hidden = document.getElementById("physical-notes-hidden");
  hidden.value = physicalNotes.join("\n");
}

// Enter 키로 신체적 특성 추가
document.addEventListener("DOMContentLoaded", function () {
  const physicalInput = document.getElementById("physical-input");
  if (physicalInput) {
    physicalInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        addPhysicalNote();
      }
    });
  }
});

// 경력/경험 관련 함수
let experienceItems = [];

function initExperienceList() {
  const experienceHidden = document.getElementById("experience-hidden");
  const experienceText = experienceHidden.value.trim();

  if (experienceText) {
    // 줄바꿈으로 구분된 경험들을 배열로 변환
    experienceItems = experienceText
      .split("\n")
      .filter((item) => item.trim());
    updateExperienceDisplay();
  }
}

function addExperience() {
  const input = document.getElementById("experience-input");
  const value = input.value.trim();

  if (value) {
    experienceItems.push(value);
    updateExperienceDisplay();
    updateExperienceHidden();
    input.value = "";
  }
}

function removeExperience(index) {
  experienceItems.splice(index, 1);
  updateExperienceDisplay();
  updateExperienceHidden();
}

function updateExperienceDisplay() {
  const list = document.getElementById("experience-list");
  list.innerHTML = "";

  experienceItems.forEach((item, index) => {
    const div = document.createElement("div");
    div.className =
      "border-2 border-blue-600 rounded-lg px-4 py-3 flex items-center justify-between";
    div.innerHTML = `
      <span class="text-gray-900 flex-1">${item}</span>
      <button
        type="button"
        class="text-gray-400 hover:text-gray-600 ml-2"
        onclick="removeExperience(${index})"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    `;
    list.appendChild(div);
  });
}

function updateExperienceHidden() {
  const hidden = document.getElementById("experience-hidden");
  hidden.value = experienceItems.join("\n");
}

// Enter 키로 경력 추가
document.addEventListener("DOMContentLoaded", function () {
  const experienceInput = document.getElementById("experience-input");
  if (experienceInput) {
    experienceInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        addExperience();
      }
    });
  }
});

// 자격증 관련 함수 (새 디자인용)
// 파일 선택 시 파일 이름 표시
function updateFileName() {
  const fileInput = document.getElementById("certificate-file");
  const fileNameSpan = document.getElementById("certificate-file-name");

  if (fileInput.files.length > 0) {
    fileNameSpan.textContent = fileInput.files[0].name;
  } else {
    fileNameSpan.textContent = "";
  }
}

function addCertificateWithFile() {
  const input = document.getElementById("certificate-input");
  const fileInput = document.getElementById("certificate-file");
  const certName = input.value.trim();
  const file = fileInput.files[0];

  if (!certName) {
    alert("자격증 이름을 입력해주세요.");
    return;
  }

  // 새 자격증 항목 추가
  const container = document.getElementById("certificates-container");
  const div = document.createElement("div");
  div.className =
    "border-2 border-blue-600 rounded-lg px-4 py-3 flex items-center justify-between certificate-entry mb-2";

  let certDisplayText = certName;
  if (file) {
    certDisplayText += ` <span class="text-xs text-gray-500">(사진 첨부됨)</span>`;
  }

  div.innerHTML = `
    <span class="text-gray-900">${certDisplayText}</span>
    <button
      type="button"
      class="text-gray-400 hover:text-gray-600"
      onclick="this.parentElement.remove()"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
      </svg>
    </button>
    <input type="hidden" name="certificate_names" value="${certName}">
  `;

  container.appendChild(div);

  // 파일이 선택된 경우 파일도 추가
  if (file) {
    const fileContainer = document.createElement("div");
    fileContainer.style.display = "none";
    const fileInputClone = document.createElement("input");
    fileInputClone.type = "file";
    fileInputClone.name = "certificate_images";

    // FileList를 전달하기 위해 DataTransfer 사용
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInputClone.files = dataTransfer.files;

    div.appendChild(fileInputClone);
  }

  // 입력 필드 초기화
  input.value = "";
  fileInput.value = "";
  document.getElementById("certificate-file-name").textContent = "";
}

// Enter 키로 자격증 추가
document.addEventListener("DOMContentLoaded", function () {
  const certInput = document.getElementById("certificate-input");
  if (certInput) {
    certInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        addCertificateWithFile();
      }
    });
  }
});

// 시간 선택 모달 관련 함수
function initTimeSelectors() {
  const startHourSelect = document.getElementById("start-hour");
  const endHourSelect = document.getElementById("end-hour");

  // 시간 옵션 생성 (00:00 ~ 23:30, 30분 단위)
  const timeOptions = [];
  for (let h = 0; h < 24; h++) {
    for (let m = 0; m < 60; m += 30) {
      const hour = String(h).padStart(2, "0");
      const minute = String(m).padStart(2, "0");
      timeOptions.push(`${hour}:${minute}`);
    }
  }

  timeOptions.forEach((time) => {
    const option1 = document.createElement("option");
    option1.value = time;
    option1.textContent = time;
    startHourSelect.appendChild(option1);

    const option2 = document.createElement("option");
    option2.value = time;
    option2.textContent = time;
    endHourSelect.appendChild(option2);
  });
}

function openTimeModal() {
  const modal = document.getElementById("time-modal");
  modal.style.display = "flex";
  modal.classList.remove("hidden");

  // 애니메이션을 위한 약간의 딜레이
  setTimeout(() => {
    modal.classList.add("flex");
  }, 10);

  // 현재 설정된 시간 가져오기
  const startTime =
    document.getElementById("start_time").value || "09:00";
  const endTime = document.getElementById("end_time").value || "18:00";

  // 시작 시간 설정
  const [startHour, startMin] = startTime.split(":");
  const startH = parseInt(startHour);
  document.getElementById("start-period").value =
    startH < 12 ? "오전" : "오후";
  document.getElementById("start-hour").value = startTime;

  // 종료 시간 설정
  const [endHour, endMin] = endTime.split(":");
  const endH = parseInt(endHour);
  document.getElementById("end-period").value =
    endH < 12 ? "오전" : "오후";
  document.getElementById("end-hour").value = endTime;
}

function closeTimeModal(event) {
  if (event && event.target.id === "time-modal") {
    const modal = document.getElementById("time-modal");
    modal.classList.remove("flex");
    modal.classList.add("hidden");

    // 애니메이션이 끝난 후 display none 처리
    setTimeout(() => {
      if (modal.classList.contains("hidden")) {
        modal.style.display = "none";
      }
    }, 300);
  }
}

function confirmTime() {
  const startPeriod = document.getElementById("start-period").value;
  const startHour = document.getElementById("start-hour").value;
  const endPeriod = document.getElementById("end-period").value;
  const endHour = document.getElementById("end-hour").value;

  // hidden input에 24시간 형식으로 저장
  document.getElementById("start_time").value = startHour;
  document.getElementById("end_time").value = endHour;

  // 디스플레이 업데이트
  updateTimeDisplay();

  // 모달 닫기 (애니메이션 포함)
  const modal = document.getElementById("time-modal");
  modal.classList.remove("flex");
  modal.classList.add("hidden");

  // 애니메이션이 끝난 후 display none 처리
  setTimeout(() => {
    if (modal.classList.contains("hidden")) {
      modal.style.display = "none";
    }
  }, 300);
}

function updateTimeDisplay() {
  const startTime =
    document.getElementById("start_time").value || "09:00";
  const endTime = document.getElementById("end_time").value || "18:00";

  const startPeriod =
    parseInt(startTime.split(":")[0]) < 12 ? "오전" : "오후";
  const endPeriod =
    parseInt(endTime.split(":")[0]) < 12 ? "오전" : "오후";

  const display = `${startPeriod} ${startTime} ~ ${endPeriod} ${endTime}`;
  document.getElementById("time-display").textContent = display;
}

const timeNegotiable = document.getElementById("time_negotiable"),
  startTime = document.getElementById("start_time"),
  endTime = document.getElementById("end_time"),
  timeSelector = document.getElementById("time-selector"),
  timeDisplay = document.getElementById("time-display");
function toggleTime() {
  const d = timeNegotiable.checked;
  startTime.disabled = d;
  endTime.disabled = d;

  if (d) {
    timeSelector.classList.add("disabled");
    timeDisplay.textContent = "시간 협의 가능";
  } else {
    timeSelector.classList.remove("disabled");
    updateTimeDisplay();
  }
}
timeNegotiable.addEventListener("change", toggleTime);
document.addEventListener("DOMContentLoaded", () => {
  showStep(1);
  toggleTime();
});

// 요일 협의 토글 기능
const dayNegotiable = document.getElementById("day_negotiable");
function toggleDays() {
  const isNegotiable = dayNegotiable.checked;
  const dayLabels = document.querySelectorAll(".day-btn-label");
  const dayCheckboxes = document.querySelectorAll(".day-checkbox");

  dayLabels.forEach((label) => {
    if (isNegotiable) {
      label.classList.add("disabled");
    } else {
      label.classList.remove("disabled");
    }
  });

  dayCheckboxes.forEach((checkbox) => {
    checkbox.disabled = isNegotiable;
  });
}
dayNegotiable.addEventListener("change", toggleDays);
document.addEventListener("DOMContentLoaded", () => {
  toggleDays();
});

// 교통 수단 토글 기능
const commuteNegotiable = document.getElementById("commute-negotiable");
const commuteSlider = document.getElementById("commute-slider");
function toggleCommute() {
  const isImpossible = commuteNegotiable.checked;

  if (isImpossible) {
    commuteSlider.disabled = true;
  } else {
    commuteSlider.disabled = false;
  }
}
commuteNegotiable.addEventListener("change", toggleCommute);
document.addEventListener("DOMContentLoaded", () => {
  toggleCommute();
});
function deleteCertificate(certId, buttonElement) {
  if (!confirm("정말로 이 자격증을 영구적으로 삭제하시겠습니까?")) {
    return;
  }

  fetch(`/resume/certificate/delete/${certId}`, {
    method: "DELETE",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        buttonElement.closest(".existing-cert-item").remove();
        alert("자격증이 성공적으로 삭제되었습니다.");
      } else {
        alert("삭제에 실패했습니다: " + (data.message || "서버 오류"));
      }
    })
    .catch((error) => {
      console.error("삭제 요청 중 오류 발생:", error);
      alert("삭제 처리 중 오류가 발생했습니다.");
    });
}
