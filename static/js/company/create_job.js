// AI 어시스턴트 함수
function openAIAssistant() {
  const title = document.getElementById("jobTitle").value;
  const description = document.getElementById("jobDescription").value;

  document.getElementById("aiTitle").value = title;
  document.getElementById("aiJobContent").value = description.substring(0, 100);

  document.getElementById("aiModal").classList.remove("hidden");
  document.getElementById("aiPreview").classList.add("hidden");
  document.getElementById("aiApplyBtn").classList.add("hidden");
}

function closeAIModal() {
  document.getElementById("aiModal").classList.add("hidden");
  document.getElementById("aiPreview").classList.add("hidden");
  document.getElementById("aiLoading").classList.add("hidden");
  document.getElementById("aiApplyBtn").classList.add("hidden");
}

async function generateWithAI() {
  const title = document.getElementById("aiTitle").value.trim();
  const salary = document.getElementById("aiSalary").value.trim();
  const jobContent = document.getElementById("aiJobContent").value.trim();
  const requirements = document.getElementById("aiRequirements").value.trim();

  if (!title || !jobContent) {
    alert("제목과 직무 내용은 필수입니다.");
    return;
  }

  document.getElementById("aiLoading").classList.remove("hidden");
  document.getElementById("aiPreview").classList.add("hidden");

  try {
    const response = await fetch(window.AI_GENERATE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        salary,
        job_content: jobContent,
        requirements,
      }),
    });

    if (!response.ok) throw new Error("AI 생성 실패");

    const data = await response.json();
    const generatedText = data.description;

    document.getElementById("aiPreviewContent").textContent = generatedText;
    document.getElementById("aiPreview").classList.remove("hidden");
    document.getElementById("aiApplyBtn").classList.remove("hidden");

    window.aiGeneratedText = generatedText;
  } catch (error) {
    console.error("Error:", error);
    alert("AI 작성 중 오류가 발생했습니다: " + error.message);
  } finally {
    document.getElementById("aiLoading").classList.add("hidden");
  }
}

function applyAIText() {
  if (window.aiGeneratedText) {
    document.getElementById("jobDescription").value = window.aiGeneratedText;
    selectedData.description = window.aiGeneratedText;
    alert("내용이 적용되었습니다.");
    closeAIModal();
    updateNextButton();
  }
}

let currentStep = 1;
let maxStep = 6;
let selectedData = {
  category: "",
  title: "",
  workPeriod: "",
  selectedDates: [],
  days: [],
  startTime: "",
  endTime: "",
  salaryType: "",
  salaryAmount: "",
  location: "",
  detailAddress: "",
  phone: "",
  description: "",
};

let currentCalendarDate = new Date();
const today = new Date();

function goToNextStep() {
  if (currentStep < maxStep) {
    const currentSection = document.getElementById(`step${currentStep}`);
    if (currentSection) {
      currentSection.classList.add("completed");

      if (currentStep === 1) {
        document
          .querySelectorAll("#step1 .radio-option")
          .forEach((opt) => opt.classList.add("disabled"));
      }

      const inputs = currentSection.querySelectorAll(
        "input:not([type='checkbox']):not([type='radio']), textarea, select"
      );
      inputs.forEach((input) => {
        input.readOnly = true;
        input.disabled = true;
      });

      const buttons = currentSection.querySelectorAll("button:not(#nextBtn)");
      buttons.forEach((btn) => (btn.disabled = true));
    }

    currentStep++;
    const nextSection = document.getElementById(`step${currentStep}`);
    if (nextSection) {
      nextSection.classList.add("visible");
      document.getElementById("nextBtn").disabled = true;

      setTimeout(() => {
        nextSection.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }, 100);

      updateNextButton();
    }
  } else {
    submitJob();
  }
}

function goBack() {
  if (currentStep > 1) {
    currentStep--;
    const prevSection = document.getElementById(`step${currentStep}`);
    if (prevSection) {
      prevSection.scrollIntoView({ behavior: "smooth" });
      updateNextButton();
    }
  } else {
    window.location.href = window.COMPANY_LIST_URL;
  }
}

function updateNextButton() {
  const nextBtn = document.getElementById("nextBtn");
  let isValid = false;

  switch (currentStep) {
    case 1:
      const hasSelection =
        document.querySelectorAll("#step1 .radio-option.selected").length > 0;
      const customOption = document.querySelector(
        '#step1 .radio-option[data-value="기타"].selected'
      );
      if (customOption) {
        const customValue = document
          .getElementById("customCategory")
          ?.value.trim();
        isValid = hasSelection && customValue !== "";
      } else {
        isValid = hasSelection;
      }
      break;
    case 2:
      isValid = selectedData.title.length > 0;
      break;
    case 3:
      if (selectedData.workPeriod === "단기") {
        isValid = selectedData.selectedDates.length > 0;
      } else {
        isValid = selectedData.workPeriod !== "";
      }
      break;
    case 4:
      isValid = selectedData.description.length > 0;
      break;
    case 5:
      isValid = selectedData.location.length > 0;
      break;
    case 6:
      const agreeTerms = document.getElementById("agreeTerms")?.checked;
      isValid = selectedData.phone.length > 0 && agreeTerms;
      nextBtn.textContent = "AI가 작성한 공고 보기";
      break;
  }

  nextBtn.disabled = !isValid;
}

// 1단계: 직무분야 선택
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("#step1 .radio-option").forEach((option) => {
    option.addEventListener("click", function () {
      this.classList.toggle("selected");
      const radioDot = this.querySelector(".radio-dot");
      radioDot.classList.toggle("hidden");

      if (this.dataset.value === "기타") {
        const customInput = document.getElementById("customCategory");
        if (this.classList.contains("selected")) {
          customInput.classList.remove("hidden");
        } else {
          customInput.classList.add("hidden");
          customInput.value = "";
        }
      }

      const selectedCategories = [];
      document
        .querySelectorAll("#step1 .radio-option.selected")
        .forEach((opt) => {
          if (opt.dataset.value === "기타") {
            const customValue = document
              .getElementById("customCategory")
              .value.trim();
            if (customValue) {
              selectedCategories.push(customValue);
            }
          } else {
            selectedCategories.push(opt.dataset.value);
          }
        });

      selectedData.category = selectedCategories.join(", ");
      updateNextButton();
    });
  });

  document
    .getElementById("customCategory")
    ?.addEventListener("input", function () {
      const selectedCategories = [];
      document
        .querySelectorAll("#step1 .radio-option.selected")
        .forEach((opt) => {
          if (opt.dataset.value === "기타") {
            const customValue = this.value.trim();
            if (customValue) {
              selectedCategories.push(customValue);
            }
          } else {
            selectedCategories.push(opt.dataset.value);
          }
        });

      selectedData.category = selectedCategories.join(", ");
      updateNextButton();
    });

  // 2단계: 제목 입력
  document.getElementById("jobTitle")?.addEventListener("input", function () {
    selectedData.title = this.value;
    updateNextButton();
  });

  // 3단계: 근무 기간 선택
  document.querySelectorAll(".period-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      document
        .querySelectorAll(".period-btn")
        .forEach((b) => b.classList.remove("option-selected"));
      this.classList.add("option-selected");
      selectedData.workPeriod = this.dataset.period;

      const calendar = document.getElementById("shortTermCalendar");
      const schedule = document.getElementById("longTermSchedule");

      if (this.dataset.period === "단기") {
        calendar.classList.remove("hidden");
        schedule.classList.add("hidden");
        generateCalendar();
      } else {
        calendar.classList.add("hidden");
        schedule.classList.remove("hidden");
      }

      updateNextButton();
    });
  });

  // 요일 선택
  document.querySelectorAll(".day-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      this.classList.toggle("option-selected");

      const selectedDays = [];
      document.querySelectorAll(".day-btn.option-selected").forEach((b) => {
        selectedDays.push(b.dataset.day);
      });
      selectedData.days = selectedDays;
    });
  });

  // 상세 주소 입력
  document
    .getElementById("detailAddress")
    .addEventListener("input", function () {
      selectedData.detailAddress = this.value;
    });

  // 연락처 입력
  document
    .getElementById("contactPhone")
    .addEventListener("input", function (e) {
      let value = e.target.value.replace(/[^0-9]/g, "");
      if (value.length > 3 && value.length <= 7) {
        value = value.slice(0, 3) + "-" + value.slice(3);
      } else if (value.length > 7) {
        value =
          value.slice(0, 3) +
          "-" +
          value.slice(3, 7) +
          "-" +
          value.slice(7, 11);
      }
      e.target.value = value;
      selectedData.phone = value;
      updateNextButton();
    });

  // 동의 체크박스
  document
    .getElementById("agreeTerms")
    ?.addEventListener("change", function () {
      updateNextButton();
    });

  // 설명 입력
  document
    .getElementById("jobDescription")
    .addEventListener("input", function () {
      selectedData.description = this.value;
      updateNextButton();
    });

  updateNextButton();
});

// 캘린더 생성 함수
function generateCalendar() {
  const year = currentCalendarDate.getFullYear();
  const month = currentCalendarDate.getMonth();

  document.getElementById("currentMonth").textContent = `${year}년 ${
    month + 1
  }월`;

  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startDayOfWeek = firstDay.getDay();

  const calendarGrid = document.getElementById("calendarGrid");
  calendarGrid.innerHTML = "";

  for (let i = 0; i < startDayOfWeek; i++) {
    const emptyCell = document.createElement("div");
    emptyCell.className = "text-center py-2";
    calendarGrid.appendChild(emptyCell);
  }

  for (let day = 1; day <= lastDay.getDate(); day++) {
    const dateCell = document.createElement("button");
    const currentDate = new Date(year, month, day);
    const dateString = `${year}-${String(month + 1).padStart(2, "0")}-${String(
      day
    ).padStart(2, "0")}`;

    const dayOfWeek = (startDayOfWeek + day - 1) % 7;

    dateCell.className =
      "text-center py-2 rounded-full hover:bg-gray-100 transition-colors text-sm font-medium w-9 h-9 flex items-center justify-center mx-auto";
    dateCell.textContent = day;
    dateCell.type = "button";
    dateCell.onclick = () => toggleDateSelection(dateString, dateCell);

    if (currentDate.toDateString() === today.toDateString()) {
      dateCell.classList.add("font-bold", "border", "border-blue-500");
    }

    if (selectedData.selectedDates.includes(dateString)) {
      dateCell.classList.add("bg-blue-600", "text-white", "font-bold");
      dateCell.classList.remove("hover:bg-gray-100");
    } else {
      if (dayOfWeek === 0) {
        dateCell.classList.add("text-red-500");
      } else if (dayOfWeek === 6) {
        dateCell.classList.add("text-blue-500");
      }
    }

    calendarGrid.appendChild(dateCell);
  }

  updateSelectedDatesDisplay();
}

function toggleDateSelection(dateString, element) {
  const index = selectedData.selectedDates.indexOf(dateString);

  if (index > -1) {
    selectedData.selectedDates.splice(index, 1);
    element.classList.remove("bg-blue-600", "text-white", "font-bold");
    element.classList.add("hover:bg-gray-100");

    const date = new Date(dateString);
    const dayOfWeek = date.getDay();
    if (dayOfWeek === 0) {
      element.classList.add("text-red-500");
    } else if (dayOfWeek === 6) {
      element.classList.add("text-blue-500");
    }
  } else {
    selectedData.selectedDates.push(dateString);
    element.classList.add("bg-blue-600", "text-white", "font-bold");
    element.classList.remove(
      "hover:bg-gray-100",
      "text-red-500",
      "text-blue-500"
    );
  }

  updateSelectedDatesDisplay();
  updateNextButton();
}

function updateSelectedDatesDisplay() {
  const count = selectedData.selectedDates.length;
  document.getElementById("selectedDatesCount").textContent = count;

  if (count > 0) {
    const sortedDates = selectedData.selectedDates.sort();
    const firstDate = sortedDates[0].replace(/-/g, ".");
    const lastDate = sortedDates[sortedDates.length - 1].replace(/-/g, ".");

    if (count === 1) {
      document.getElementById("selectedDatesDisplay").textContent = firstDate;
    } else {
      document.getElementById(
        "selectedDatesDisplay"
      ).textContent = `${firstDate} - ${lastDate}`;
    }
  } else {
    document.getElementById("selectedDatesDisplay").textContent =
      "날짜를 선택해주세요";
  }
}

function changeMonth(delta) {
  currentCalendarDate.setMonth(currentCalendarDate.getMonth() + delta);
  generateCalendar();
}
window.changeMonth = changeMonth;

// 최저임금 계산 함수
function calculateMinimumWage() {
  const minHourlyWage = 10030;
  const salaryType = selectedData.salaryType;
  const startTime = document.getElementById("startTimeSelect")?.value;
  const endTime = document.getElementById("endTimeSelect")?.value;

  let minWageText = "";

  if (salaryType === "시급") {
    if (startTime && endTime) {
      const start = parseInt(startTime.split(":")[0]);
      const end = parseInt(endTime.split(":")[0]);
      const hours = end > start ? end - start : 24 - start + end;
      const dailyWage = minHourlyWage * hours;
      minWageText = `이 조건으로 근무할 경우 최소 일급은 <strong>${dailyWage.toLocaleString()}원</strong>이에요`;
    } else {
      minWageText = `이 조건으로 근무할 경우 최소 일급은 <strong>70,210원</strong>이에요 (7시간 기준)`;
    }
  } else if (salaryType === "일급") {
    minWageText = `최저시급 기준 7시간 근무 시 최소 일급은 <strong>70,210원</strong>이에요`;
  } else if (salaryType === "월급") {
    const daysCount = selectedData.days.length || 5;
    const monthlyWage = minHourlyWage * 7 * daysCount * 4;
    minWageText = `주 ${daysCount}일 근무 시 최소 월급은 <strong>${monthlyWage.toLocaleString()}원</strong>이에요`;
  } else if (salaryType === "건당") {
    minWageText = `건당 급여는 작업 내용에 따라 협의하여 결정해주세요`;
  }

  document.getElementById("minimumWageInfo").innerHTML = minWageText;
}

// 지도 관련 변수
let addressMap = null;
let addressMarker = null;
let selectedAddress = null;

function openAddressSearch() {
  document.getElementById("addressModal").classList.remove("hidden");

  if (!addressMap) {
    setTimeout(function () {
      initAddressMap();
    }, 100);
  } else {
    setTimeout(function () {
      addressMap.relayout();
    }, 100);
  }
}
window.openAddressSearch = openAddressSearch;

function initAddressMap() {
  const container = document.getElementById("addressMap");

  if (typeof kakao === "undefined" || !kakao.maps) {
    console.error("카카오 맵 스크립트가 아직 로드되지 않았습니다.");
    return;
  }

  if (!container) {
    console.error("지도 컨테이너를 찾을 수 없습니다.");
    return;
  }

  const options = {
    center: new kakao.maps.LatLng(35.8242, 128.7569),
    level: 5,
  };

  addressMap = new kakao.maps.Map(container, options);

  setTimeout(function () {
    addressMap.relayout();
  }, 100);

  kakao.maps.event.addListener(addressMap, "click", function (mouseEvent) {
    const latlng = mouseEvent.latLng;

    if (addressMarker) {
      addressMarker.setMap(null);
    }

    addressMarker = new kakao.maps.Marker({
      position: latlng,
      map: addressMap,
    });

    const geocoder = new kakao.maps.services.Geocoder();
    geocoder.coord2Address(
      latlng.getLng(),
      latlng.getLat(),
      function (result, status) {
        if (status === kakao.maps.services.Status.OK) {
          const address = result[0].address;
          const roadAddress = result[0].road_address;

          selectedAddress = {
            address: roadAddress
              ? roadAddress.address_name
              : address.address_name,
            lat: latlng.getLat(),
            lng: latlng.getLng(),
          };

          document.getElementById("selectedAddressText").textContent =
            selectedAddress.address;
          document.getElementById("confirmAddressBtn").disabled = false;
        }
      }
    );
  });
}

function searchAddress() {
  const query = document.getElementById("addressSearch").value.trim();
  if (!query) {
    alert("주소를 입력해주세요");
    return;
  }

  const geocoder = new kakao.maps.services.Geocoder();

  geocoder.addressSearch(query, function (result, status) {
    if (status === kakao.maps.services.Status.OK) {
      const coords = new kakao.maps.LatLng(result[0].y, result[0].x);

      addressMap.setCenter(coords);
      addressMap.setLevel(3);

      if (addressMarker) {
        addressMarker.setMap(null);
      }

      addressMarker = new kakao.maps.Marker({
        position: coords,
        map: addressMap,
      });

      selectedAddress = {
        address: result[0].address_name || result[0].road_address?.address_name,
        lat: parseFloat(result[0].y),
        lng: parseFloat(result[0].x),
      };

      document.getElementById("selectedAddressText").textContent =
        selectedAddress.address;
      document.getElementById("confirmAddressBtn").disabled = false;
    } else {
      alert("주소를 찾을 수 없습니다. 다시 시도해주세요.");
    }
  });
}
window.searchAddress = searchAddress;

function closeAddressModal() {
  document.getElementById("addressModal").classList.add("hidden");
  selectedAddress = null;
  document.getElementById("selectedAddressText").textContent =
    "지도에서 위치를 클릭하거나 검색해주세요";
  document.getElementById("confirmAddressBtn").disabled = true;
  document.getElementById("addressSearch").value = "";
}
window.closeAddressModal = closeAddressModal;

function confirmAddress() {
  if (selectedAddress) {
    document.getElementById("workLocation").value = selectedAddress.address;
    selectedData.location = selectedAddress.address;
    selectedData.latitude = selectedAddress.lat;
    selectedData.longitude = selectedAddress.lng;
    updateNextButton();
    closeAddressModal();
  }
}
window.confirmAddress = confirmAddress;

// 제출 함수
async function submitJob() {
  console.log("제출 데이터:", selectedData);

  try {
    let geocodeResult = null;
    if (selectedData.latitude && selectedData.longitude) {
      geocodeResult = {
        lat: selectedData.latitude,
        lng: selectedData.longitude,
      };
    } else {
      geocodeResult = await geocodeAddress(selectedData.location);
    }

    const formData = new FormData();

    formData.append("title", selectedData.title);
    formData.append("company", window.CURRENT_USER_NICKNAME);
    formData.append("people_category", selectedData.category);
    formData.append(
      "description",
      selectedData.description || "상세 설명 없음"
    );
    formData.append("work_period", selectedData.workPeriod);

    if (
      selectedData.workPeriod === "단기" &&
      selectedData.startDate &&
      selectedData.endDate
    ) {
      formData.append("recruitment_start_date", selectedData.startDate);
      formData.append("recruitment_end_date", selectedData.endDate);
    }

    formData.append(
      "salary",
      `${selectedData.salaryType} ${selectedData.salaryAmount}원`
    );
    formData.append("region", selectedData.location);

    if (selectedData.detailAddress) {
      formData.append("detail_address", selectedData.detailAddress);
    }

    if (geocodeResult) {
      formData.append("latitude", geocodeResult.lat);
      formData.append("longitude", geocodeResult.lng);
      formData.append("region_1depth_name", geocodeResult.region1 || "");
      formData.append("region_2depth_name", geocodeResult.region2 || "");
      formData.append("region_3depth_name", geocodeResult.region3 || "");
    }

    formData.append("contact_phone", selectedData.phone);

    formData.append(
      "work_monday",
      selectedData.days.includes("월") ? "true" : "false"
    );
    formData.append(
      "work_tuesday",
      selectedData.days.includes("화") ? "true" : "false"
    );
    formData.append(
      "work_wednesday",
      selectedData.days.includes("수") ? "true" : "false"
    );
    formData.append(
      "work_thursday",
      selectedData.days.includes("목") ? "true" : "false"
    );
    formData.append(
      "work_friday",
      selectedData.days.includes("금") ? "true" : "false"
    );
    formData.append(
      "work_saturday",
      selectedData.days.includes("토") ? "true" : "false"
    );
    formData.append(
      "work_sunday",
      selectedData.days.includes("일") ? "true" : "false"
    );

    const startTimeSelect = document.getElementById("startTimeSelect");
    const endTimeSelect = document.getElementById("endTimeSelect");

    if (startTimeSelect && startTimeSelect.value) {
      formData.append("work_start_time", startTimeSelect.value);
    }
    if (endTimeSelect && endTimeSelect.value) {
      formData.append("work_end_time", endTimeSelect.value);
    }

    const response = await fetch(window.CREATE_COMPANY_JOB_URL, {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      alert("공고가 성공적으로 작성되었습니다! 지도에서 확인할 수 있습니다.");
      window.location.href = window.COMPANY_LIST_URL;
    } else {
      const text = await response.text();
      console.error("서버 응답:", text);
      alert("공고 작성 중 오류가 발생했습니다.");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("공고 작성 중 오류가 발생했습니다: " + error.message);
  }
}

async function geocodeAddress(address) {
  try {
    const response = await fetch(
      `/api/address_search?query=${encodeURIComponent(address)}`
    );
    const data = await response.json();

    if (data.documents && data.documents.length > 0) {
      const result = data.documents[0];
      return {
        lat: parseFloat(result.y),
        lng: parseFloat(result.x),
        region1: result.address?.region_1depth_name || "",
        region2: result.address?.region_2depth_name || "",
        region3: result.address?.region_3depth_name || "",
      };
    }
    return null;
  } catch (error) {
    console.error("주소 변환 오류:", error);
    return null;
  }
}
