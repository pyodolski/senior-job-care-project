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

// 💡 8단계 구조에 맞게 maxStep과 selectedData 수정
let currentStep = 1;
let maxStep = 9;
let selectedData = {
  category: "", // 1단계: 직무 분야 (job_category)
  title: "",    // 2단계: 제목
  categories: [], // (사용되지 않음 - HTML에서 카테고리 버튼 제거됨)
  workPeriod: "", // 3단계: 근무 기간
  recruitmentEndDate: "", // 4단계: 모집 마감 기한
  selectedDates: [], // 3단계: 단기 근무일
  days: [], // 3단계: 근무 요일
  startTime: "", // 3단계: 시작 시간
  endTime: "", // 3단계: 종료 시간
  salaryType: "", // 5단계: 급여 타입
  salaryAmount: 0, // 5단계: 급여 금액
  recruitmentCount: 0,
  description: "", // 6단계: 상세 설명
  location: "", // 7단계: 주소 (위치)
  detailAddress: "", // 7단계: 상세 주소
  phone: "", // 8단계: 연락처
  latitude: null, // 지오코딩 결과
  longitude: null // 지오코딩 결과
};

const MIN_HOURLY_WAGE = 10030; // 2025년 최저시급 (최소 금액 계산용)

let geocodeResult = null;

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
        // 급여 금액 필드는 예외적으로 비활성화하지 않음 (스크롤 시 계속 표시)
        if (input.id !== 'salaryAmount') {
          input.readOnly = true;
          input.disabled = true;
        }
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
    // 💡 기업이음 목록으로 리다이렉션 (window.COMPANY_LIST_URL 사용)
    window.location.href = window.COMPANY_LIST_URL;
  }
}

function updateNextButton() {
  const nextBtn = document.getElementById("nextBtn");
  let isValid = false;

  switch (currentStep) {
    case 1: // 직무 분야
      // '기타' 필드 처리 포함하여 선택 여부만 확인
      isValid = selectedData.category !== "";
      break;
    case 2: // 제목
      // 기업이음은 2단계에 카테고리 버튼이 없으므로 제목만 확인
      isValid = selectedData.title.length > 0;
      break;
    case 3: // 근무 조건 (기간, 요일, 시간)
      if (selectedData.workPeriod === "단기") {
        isValid = selectedData.selectedDates.length > 0;
      } else if (selectedData.workPeriod !== "") {
        const flexibleDays = document.getElementById("flexibleDays")?.checked;
        const flexibleTime = document.getElementById("flexibleTime")?.checked;
        const hasDays = flexibleDays || selectedData.days.length > 0;
        const hasTime = flexibleTime || (selectedData.startTime && selectedData.endTime);
        isValid = hasDays && hasTime;
      } else {
        isValid = false;
      }
      break;
    case 4: // 💡 모집 마감 기한 (선택 사항)
      // 선택 사항이므로 항상 유효
      isValid = true;
      break;
    case 5: // 💡 급여 정보
      // 급여 타입이 선택되었고, 금액이 0보다 커야 유효
      isValid = selectedData.salaryType !== "" && selectedData.salaryAmount > 0;
      break;
    case 6: // 💡 모집 인원 (새로 추가)
      // 모집 인원은 1명 이상이어야 유효
      isValid = selectedData.recruitmentCount > 0;
      break;
    case 7: // 💡 상세 설명 (기존 6)
      isValid = selectedData.description.length > 0;
      break;
    case 8: // 💡 위치 (기존 7)
      isValid = selectedData.location.length > 0;
      break;
    case 9: // 💡 연락처 및 동의 (기존 8)
      const agreeTerms = document.getElementById("agreeTerms")?.checked;
      isValid = selectedData.phone.length > 0 && agreeTerms;
      nextBtn.textContent = "공고 등록하기";
      break;
  }

  nextBtn.disabled = !isValid;
}

document.addEventListener("DOMContentLoaded", function () {
  // 1단계: 직무분야 선택
  document.querySelectorAll("#step1 .radio-option").forEach((option) => {
    option.addEventListener("click", function () {
      // 선택 해제 로직은 기업이음이 다중 선택 가능하도록 설정되어 있으므로 수정
      this.classList.toggle("selected");
      this.querySelector(".radio-dot").classList.toggle("hidden");

      // 기타 입력 필드 표시/숨김
      if (this.dataset.value === "기타") {
        document.getElementById("customCategory")?.classList.toggle("hidden", !this.classList.contains("selected"));
        if (!this.classList.contains("selected")) document.getElementById("customCategory").value = "";
      }

      // 선택된 카테고리를 selectedData.category에 저장 (다중 선택된 경우 콤마로 연결)
      const selectedCategories = [];
      document
        .querySelectorAll("#step1 .radio-option.selected")
        .forEach((opt) => {
          if (opt.dataset.value === "기타") {
            const customValue = document.getElementById("customCategory")?.value.trim();
            if (customValue) selectedCategories.push(customValue);
          } else {
            selectedCategories.push(opt.dataset.value);
          }
        });

      selectedData.category = selectedCategories.join(", ");
      updateNextButton();
    });
  });

  // 기타 입력 필드 로직
  document.getElementById("customCategory")?.addEventListener("input", function () {
    const 기타옵션 = document.querySelector('#step1 .radio-option[data-value="기타"].selected');
    if (기타옵션) {
        selectedData.category = this.value.trim();
    }
    updateNextButton();
  });


  // 2단계: 제목 입력
  const jobTitle = document.getElementById("jobTitle");
  if (jobTitle) {
    jobTitle.addEventListener("input", function () {
      selectedData.title = this.value;
      updateNextButton();
    });
  }

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

  // 💡 4단계: 모집 마감일 입력
  document.getElementById("recruitmentEndDate")?.addEventListener("change", function () {
    selectedData.recruitmentEndDate = this.value;
    updateNextButton();
  });


  // 5단계: 급여 타입 버튼
  document.querySelectorAll(".salary-type-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      document
        .querySelectorAll(".salary-type-btn")
        .forEach((b) => b.classList.remove("option-selected"));
      this.classList.add("option-selected");
      selectedData.salaryType = this.dataset.type;
      calculateMinimumSalary();
      updateNextButton();
    });
  });

  // 5단계: 급여 금액 입력
  const salaryAmount = document.getElementById("salaryAmount");
  if (salaryAmount) {
    salaryAmount.addEventListener("input", function (e) {
      let value = e.target.value.replace(/[^0-9]/g, "");
      if (value) {
        value = parseInt(value).toLocaleString();
      }
      e.target.value = value;
      selectedData.salaryAmount = parseInt(value.replace(/,/g, "")) || 0;
      calculateMinimumSalary();
      updateNextButton();
    });
  }

  const recruitmentCount = document.getElementById("recruitmentCount");
  if (recruitmentCount) {
    recruitmentCount.addEventListener("input", function(e) {
        let value = e.target.value.replace(/[^0-9]/g, "");
        e.target.value = value;
        selectedData.recruitmentCount = parseInt(value) || 0;
        updateNextButton();
    });
  }

  // 7단계: 상세 설명 입력
  const jobDescription = document.getElementById("jobDescription");
  if (jobDescription) {
    jobDescription.addEventListener("input", function () {
      selectedData.description = this.value;
      updateNextButton();
    });
  }


  // 8단계: 상세 주소 입력
  const detailAddress = document.getElementById("detailAddress");
  if (detailAddress) {
    detailAddress.addEventListener("input", function () {
      selectedData.detailAddress = this.value;
    });
  }

  // 9단계: 연락처 입력
  const contactPhone = document.getElementById("contactPhone");
  if (contactPhone) {
    contactPhone.addEventListener("input", function (e) {
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
  }

  // 8단계: 동의 체크박스
  const agreeTerms = document.getElementById("agreeTerms");
  if (agreeTerms) {
    agreeTerms.addEventListener("change", function () {
      updateNextButton();
    });
  }

  // 3단계: 요일/시간 선택 및 협의 로직
  document.querySelectorAll(".day-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      if (!this.classList.contains("disabled")) {
        this.classList.toggle("option-selected");
        const selectedDays = [];
        document
          .querySelectorAll(".day-btn.option-selected")
          .forEach((b) => selectedDays.push(b.dataset.day));
        selectedData.days = selectedDays;
        updateNextButton();
      }
    });
  });

  const flexibleDays = document.getElementById("flexibleDays");
  if (flexibleDays) {
    flexibleDays.addEventListener("change", function () {
      const dayBtns = document.querySelectorAll(".day-btn");
      if (this.checked) {
        dayBtns.forEach((btn) => {
          btn.classList.add("disabled");
          btn.classList.remove("option-selected");
        });
        selectedData.days = ["협의"];
      } else {
        dayBtns.forEach((btn) => {
          btn.classList.remove("disabled");
        });
        selectedData.days = [];
      }
      updateNextButton();
    });
  }

  const flexibleTime = document.getElementById("flexibleTime");
  const startTimeSelect = document.getElementById("startTimeSelect");
  const endTimeSelect = document.getElementById("endTimeSelect");
  if (flexibleTime && startTimeSelect && endTimeSelect) {
    flexibleTime.addEventListener("change", function () {
      if (this.checked) {
        startTimeSelect.disabled = true;
        endTimeSelect.disabled = true;
        startTimeSelect.classList.add("opacity-50", "cursor-not-allowed");
        endTimeSelect.classList.add("opacity-50", "cursor-not-allowed");
        selectedData.startTime = "협의";
        selectedData.endTime = "협의";
      } else {
        startTimeSelect.disabled = false;
        endTimeSelect.disabled = false;
        startTimeSelect.classList.remove("opacity-50", "cursor-not-allowed");
        endTimeSelect.classList.remove("opacity-50", "cursor-not-allowed");
        selectedData.startTime = startTimeSelect.value;
        selectedData.endTime = endTimeSelect.value;
      }
      updateNextButton();
    });

    startTimeSelect.addEventListener("change", function () {
      selectedData.startTime = this.value;
      updateNextButton();
    });

    endTimeSelect.addEventListener("change", function () {
      selectedData.endTime = this.value;
      updateNextButton();
    });
  }

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

// 💡 최저임금 계산 함수
function calculateMinimumSalary() {
  const calculationText = document.getElementById("salaryCalculation");
  if (!calculationText || !selectedData.salaryType) {
    return;
  }

  let minimumSalary = 0;
  let salaryTypeText = selectedData.salaryType;

  // 근무 조건에 따른 최소 급여 계산
  if (selectedData.salaryType === "시급") {
    minimumSalary = MIN_HOURLY_WAGE;
    calculationText.textContent = `최소 시급은 ${minimumSalary.toLocaleString()}원이에요`;
  } else if (selectedData.salaryType === "일급") {
    minimumSalary = MIN_HOURLY_WAGE * 8;
    calculationText.textContent = `최저시급 기준 8시간 근무 시 최소 일급은 ${minimumSalary.toLocaleString()}원이에요`;
  } else if (selectedData.salaryType === "월급") {
    minimumSalary = Math.floor(MIN_HOURLY_WAGE * 209);
    calculationText.textContent = `주 40시간 근무 시 최소 월급은 ${minimumSalary.toLocaleString()}원이에요`;
  } else if (selectedData.salaryType === "건당") {
    calculationText.textContent = "건당 급여는 업무 내용에 따라 협의해주세요";
    return;
  }
}
window.calculateMinimumSalary = calculateMinimumSalary;

// 지도 관련 변수
let addressMap = null;
let addressMarker = null;
let selectedAddress = null;

function openAddressSearch() {
  document.getElementById("addressModal").classList.remove("hidden");
  if (!addressMap) {
    setTimeout(() => {
      initAddressMap();
    }, 100);
  }
}
window.openAddressSearch = openAddressSearch;

function initAddressMap() {
  const container = document.getElementById("addressMap");
  const options = {
    center: new kakao.maps.LatLng(35.8242, 128.7569),
    level: 5,
  };
  addressMap = new kakao.maps.Map(container, options);
  kakao.maps.event.addListener(addressMap, "click", function (mouseEvent) {
    const latlng = mouseEvent.latLng;
    if (addressMarker) addressMarker.setMap(null);
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
      if (addressMarker) addressMarker.setMap(null);
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

async function confirmAddress() {
  if (selectedAddress) {
    document.getElementById("workLocation").value = selectedAddress.address;
    selectedData.location = selectedAddress.address;
    selectedData.latitude = selectedAddress.lat;
    selectedData.longitude = selectedAddress.lng;

    // 지오코딩을 통해 행정 구역 정보 가져오기
    const geocoder = new kakao.maps.services.Geocoder();
    try {
      const regionResult = await new Promise((resolve, reject) => {
        geocoder.coord2RegionCode(
          selectedAddress.lng,
          selectedAddress.lat,
          (result, status) => {
            if (status === kakao.maps.services.Status.OK) {
              resolve(result);
            } else {
              reject(new Error("주소 변환 실패"));
            }
          }
        );
      });

      const legalRegion =
        regionResult.find((r) => r.region_type === "B") || regionResult[0];

      // 전역 geocodeResult 변수에 행정 구역 정보 저장
      geocodeResult = {
        lat: selectedAddress.lat,
        lng: selectedAddress.lng,
        region1: legalRegion.region_1depth_name,
        region2: legalRegion.region_2depth_name,
        region3: legalRegion.region_3depth_name,
      };

      // Hidden field에 값 설정 (HTML에 해당 필드가 있다고 가정)
      document.getElementById("latitude").value = selectedAddress.lat;
      document.getElementById("longitude").value = selectedAddress.lng;
      document.getElementById("region_1depth_name").value = legalRegion.region_1depth_name;
      document.getElementById("region_2depth_name").value = legalRegion.region_2depth_name;
      document.getElementById("region_3depth_name").value = legalRegion.region_3depth_name;

    } catch (error) {
      console.error("주소 변환 중 오류 발생:", error);
      geocodeResult = null;
      alert("주소 정보를 가져오는 데 실패했습니다. 다른 위치를 선택해주세요.");
    } finally {
      updateNextButton();
      closeAddressModal();
    }
  }
}
window.confirmAddress = confirmAddress;

let isSubmitting = false; // 중복 제출 방지 플래그

async function submitJob() {
  if (isSubmitting) {
    console.log("이미 제출 중입니다.");
    return;
  }

  isSubmitting = true;

  const nextBtn = document.getElementById("nextBtn");
  if (nextBtn) {
    nextBtn.disabled = true;
    nextBtn.classList.add("bg-gray-400", "cursor-not-allowed");
    nextBtn.classList.remove("bg-blue-600", "hover:bg-blue-700");
    nextBtn.textContent = "제출 중...";
  }

  console.log("제출 데이터:", selectedData);
  try {
    const formData = new FormData();
    formData.append("title", selectedData.title);
    formData.append("company", window.CURRENT_USER_NICKNAME);

    // 💡 기업이음: job_category와 recruitment_type에 1단계 선택 값 사용
    formData.append("job_category", selectedData.category);
    formData.append("recruitment_type", selectedData.category);

    formData.append(
      "description",
      selectedData.description || "상세 설명 없음"
    );
    formData.append("work_period", selectedData.workPeriod);

    // 💡 모집 마감 기한 추가 (4단계)
    if (selectedData.recruitmentEndDate) {
        formData.append("recruitment_end_date", selectedData.recruitmentEndDate);
    }

    // 💡 모집 인원 추가
    if (selectedData.recruitmentCount > 0) {
        formData.append("recruitment_count", selectedData.recruitmentCount);
    } else {

        formData.append("recruitment_count", 1);
    }

    // 단기 근무일 경우 선택된 날짜 전송 (시작일/종료일)
    if (
      selectedData.workPeriod === "단기" &&
      selectedData.selectedDates.length > 0
    ) {
      const sortedDates = selectedData.selectedDates.sort();
      formData.append("recruitment_start_date", sortedDates[0]);
      formData.append(
        "recruitment_end_date",
        sortedDates[sortedDates.length - 1]
      );
    }

    // 💡 급여 정보 전송 (5단계)
    if (selectedData.salaryType && selectedData.salaryAmount > 0) {
      formData.append(
        "salary",
        `${
          selectedData.salaryType
        } ${selectedData.salaryAmount.toLocaleString()}원`
      );
    } else {
      formData.append("salary", "급여 협의");
    }

    formData.append("region", selectedData.location);
    formData.append("contact_phone", selectedData.phone);
    if (selectedData.detailAddress) {
      formData.append("detail_address", selectedData.detailAddress);
    }

    // 지오코딩 결과 전송
    if (geocodeResult && geocodeResult.lat && geocodeResult.lng) {
      formData.append("latitude", geocodeResult.lat);
      formData.append("longitude", geocodeResult.lng);
      formData.append("region_1depth_name", geocodeResult.region1 || "");
      formData.append("region_2depth_name", geocodeResult.region2 || "");
      formData.append("region_3depth_name", geocodeResult.region3 || "");
    }

    // 근무 요일 (협의 포함)
    formData.append(
      "work_monday",
      selectedData.days.includes("월") || selectedData.days.includes("협의") ? "true" : "false"
    );
    formData.append(
      "work_tuesday",
      selectedData.days.includes("화") || selectedData.days.includes("협의") ? "true" : "false"
    );
    formData.append(
      "work_wednesday",
      selectedData.days.includes("수") || selectedData.days.includes("협의") ? "true" : "false"
    );
    formData.append(
      "work_thursday",
      selectedData.days.includes("목") || selectedData.days.includes("협의") ? "true" : "false"
    );
    formData.append(
      "work_friday",
      selectedData.days.includes("금") || selectedData.days.includes("협의") ? "true" : "false"
    );
    formData.append(
      "work_saturday",
      selectedData.days.includes("토") || selectedData.days.includes("협의") ? "true" : "false"
    );
    formData.append(
      "work_sunday",
      selectedData.days.includes("일") || selectedData.days.includes("협의") ? "true" : "false"
    );

    // 근무 시간 (협의 제외)
    const startTimeSelect = document.getElementById("startTimeSelect");
    const endTimeSelect = document.getElementById("endTimeSelect");

    if (startTimeSelect && startTimeSelect.value && selectedData.startTime !== "협의") {
      formData.append("work_start_time", startTimeSelect.value);
    }
    if (endTimeSelect && endTimeSelect.value && selectedData.endTime !== "협의") {
      formData.append("work_end_time", endTimeSelect.value);
    }

    // 💡 기업이음 공고 작성 URL 사용
    const response = await fetch(window.CREATE_COMPANY_JOB_URL, {
      method: "POST",
      body: formData,
    });

    if (response.ok) {
      alert("공고가 성공적으로 작성되었습니다!");
      window.location.href = window.COMPANY_LIST_URL; // 💡 기업이음 목록으로 리다이렉션
    } else {
      const text = await response.text();
      console.error("서버 응답:", text);
      alert("공고 작성 중 오류가 발생했습니다.");

      // 오류 발생 시 버튼 다시 활성화
      isSubmitting = false;
      if (nextBtn) {
        nextBtn.disabled = false;
        nextBtn.classList.remove("bg-gray-400", "cursor-not-allowed");
        nextBtn.classList.add("bg-blue-600", "hover:bg-blue-700");
        nextBtn.textContent = currentStep === maxStep ? "공고 등록하기" : "다음";
      }
    }
  } catch (error) {
    console.error("Error:", error);
    alert("공고 작성 중 오류가 발생했습니다: " + error.message);

    // 오류 발생 시 버튼 다시 활성화
    isSubmitting = false;
    if (nextBtn) {
      nextBtn.disabled = false;
      nextBtn.classList.remove("bg-gray-400", "cursor-not-allowed");
      nextBtn.classList.add("bg-blue-600", "hover:bg-blue-700");
      nextBtn.textContent = currentStep === maxStep ? "공고 등록하기" : "다음";
    }
  }
}
