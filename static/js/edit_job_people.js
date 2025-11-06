// edit_job_people.js

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

let selectedData = {
  category: "",
  title: "",
  categories: [],
  workPeriod: "",
  selectedDates: [],
  longTermStartDate: "",
  longTermEndDate: "",
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

const MIN_HOURLY_WAGE = 10030;
let geocodeResult = null;
let currentCalendarDate = new Date();
const today = new Date();

function goBack() {
  window.location.href = window.DETAIL_URL;
}

function isAllFieldsValid() {
    let isValid = true;

    if (selectedData.category.length === 0) isValid = false;

    if (selectedData.title.length === 0 || selectedData.categories.length === 0) isValid = false;

    if (selectedData.workPeriod === "단기") {
        if (selectedData.selectedDates.length === 0) isValid = false;
    } else if (selectedData.workPeriod !== "") {
        const flexibleDays = document.getElementById("flexibleDays")?.checked;
        const flexibleTime = document.getElementById("flexibleTime")?.checked;
        const hasDays = flexibleDays || selectedData.days.length > 0;
        const hasTime = flexibleTime || (selectedData.startTime && selectedData.endTime);
        if (!(hasDays && hasTime)) isValid = false;
    } else {
        isValid = false;
    }

    if (!(selectedData.salaryType !== "" && selectedData.salaryAmount > 0)) isValid = false;

    if (selectedData.description.length === 0) isValid = false;

    if (selectedData.location.length === 0) isValid = false;

    if (selectedData.phone.length < 10) isValid = false;

    return isValid;
}

function updateNextButton() {
  const nextBtn = document.getElementById("nextBtn");
  const agreeTerms = document.getElementById("agreeTerms")?.checked;

  const isFormValid = isAllFieldsValid() && agreeTerms;

  nextBtn.disabled = !isFormValid;
  nextBtn.textContent = "수정 완료";
}

function initializeEditForm(jobData) {
    if (!jobData || !jobData.id) return;

    selectedData.category = jobData.category;
    selectedData.title = jobData.title;
    selectedData.workPeriod = jobData.workPeriod;
    selectedData.longTermStartDate = jobData.recruitmentStartDate;
    selectedData.longTermEndDate = jobData.recruitmentEndDate;
    selectedData.description = jobData.description;
    selectedData.location = jobData.location;
    selectedData.detailAddress = jobData.detailAddress;
    selectedData.phone = jobData.phone.replace(/-/g, '') || "";
    selectedData.days = jobData.workDays.includes('협의') ? ['협의'] : jobData.workDays.filter(d => d.trim() !== '');
    selectedData.startTime = jobData.startTime;
    selectedData.endTime = jobData.endTime;

    selectedData.categories = jobData.recruitmentType.split(',').map(c => c.trim()).filter(c => c);

    const salaryMatch = jobData.salary.match(/^(시급|일급|월급|건당|협의)\s*([\d,]+)?/);
    if (salaryMatch) {
        selectedData.salaryType = salaryMatch[1];
        selectedData.salaryAmount = parseInt((salaryMatch[2] || '0').replace(/,/g, '')) || 0;
    } else {
        selectedData.salaryType = jobData.salary.includes('협의') ? '협의' : '';
        selectedData.salaryAmount = 0;
    }

    document.querySelectorAll('#step1 .radio-option').forEach(opt => {
        if (opt.dataset.value === selectedData.category) {
            opt.classList.add('selected');
            opt.querySelector('.radio-dot').classList.remove('hidden');
        }
    });

    selectedData.categories.forEach(cat => {
        const btn = document.querySelector(`.category-btn[data-category="${cat}"]`);
        if (btn) btn.classList.add('option-selected');
    });

    document.querySelectorAll('.period-btn').forEach(btn => {
        if (btn.dataset.period === selectedData.workPeriod) {
            btn.classList.add('option-selected');
            if (selectedData.workPeriod !== '단기') {
                document.getElementById('longTermSchedule')?.classList.remove('hidden');
                document.getElementById('shortTermCalendar')?.classList.add('hidden');
            } else {
                 document.getElementById('shortTermCalendar')?.classList.remove('hidden');
                 document.getElementById('longTermSchedule')?.classList.add('hidden');
                 generateCalendar();
            }
        }
    });

    selectedData.days.forEach(day => {
        const btn = document.querySelector(`.day-btn[data-day="${day}"]`);
        if (btn) btn.classList.add('option-selected');
    });

    const flexibleDays = document.getElementById('flexibleDays');
    if (flexibleDays) {
        flexibleDays.checked = selectedData.days.includes('협의');
        if (flexibleDays.checked) {
            document.querySelectorAll(".day-btn").forEach((btn) => {
                btn.classList.add("disabled", "opacity-50", "cursor-not-allowed");
            });
        }
    }

    const flexibleTime = document.getElementById('flexibleTime');
    const startTimeSelect = document.getElementById('startTimeSelect');
    const endTimeSelect = document.getElementById('endTimeSelect');
    if (flexibleTime) {
        flexibleTime.checked = selectedData.startTime === '협의';
        if (flexibleTime.checked) {
             if (startTimeSelect) startTimeSelect.disabled = true;
             if (endTimeSelect) endTimeSelect.disabled = true;
        }
    }
    if (startTimeSelect) startTimeSelect.value = selectedData.startTime;
    if (endTimeSelect) endTimeSelect.value = selectedData.endTime;


    document.querySelectorAll('.salary-type-btn').forEach(btn => {
        if (btn.dataset.type === selectedData.salaryType) {
            btn.classList.add('option-selected');
        }
    });
    // ★★★ 수정: selectedData.salaryAmount가 0이 아니면 입력 필드에 표시
    if (selectedData.salaryAmount > 0) {
        document.getElementById('salaryAmount').value = selectedData.salaryAmount.toLocaleString();
    }
    calculateMinimumSalary();

    window.geocodeResult = {
        lat: parseFloat(document.getElementById('latitude').value) || null,
        lng: parseFloat(document.getElementById('longitude').value) || null,
        region1: document.getElementById('region_1depth_name').value,
        region2: document.getElementById('region_2depth_name').value,
        region3: document.getElementById('region_3depth_name').value,
    };
    selectedData.latitude = window.geocodeResult.lat;
    selectedData.longitude = window.geocodeResult.lng;

    document.getElementById('contactPhone').value = selectedData.phone.replace(/(\d{3})(\d{4})(\d{4})/, '$1-$2-$3');

    updateNextButton();
}

function submitJobForm() {
    const agreeTerms = document.getElementById("agreeTerms")?.checked;

    if (!isAllFieldsValid()) {
        alert("모든 필수 필드를 입력해주세요.");
        return false;
    }

    if (!agreeTerms) {
        alert("사람 이음 준수사항에 동의해야 합니다.");
        return false;
    }

    document.getElementById("peopleCategoryHidden").value = selectedData.category;
    document.getElementById("recruitmentTypeHidden").value = selectedData.categories.join(", ");

    const isFlexibleDays = selectedData.days.includes("협의");
    document.getElementById('work_monday_hidden').value = isFlexibleDays || selectedData.days.includes("월") ? "true" : "false";
    document.getElementById('work_tuesday_hidden').value = isFlexibleDays || selectedData.days.includes("화") ? "true" : "false";
    document.getElementById('work_wednesday_hidden').value = isFlexibleDays || selectedData.days.includes("수") ? "true" : "false";
    document.getElementById('work_thursday_hidden').value = isFlexibleDays || selectedData.days.includes("목") ? "true" : "false";
    document.getElementById('work_friday_hidden').value = isFlexibleDays || selectedData.days.includes("금") ? "true" : "false";
    document.getElementById('work_saturday_hidden').value = isFlexibleDays || selectedData.days.includes("토") ? "true" : "false";
    document.getElementById('work_sunday_hidden').value = isFlexibleDays || selectedData.days.includes("일") ? "true" : "false";

    // ★★★ 수정: salaryHidden 필드에 최종 문자열 저장
    if (selectedData.salaryType === '협의' || selectedData.salaryAmount === 0) {
        document.getElementById('salaryHidden').value = '급여 협의';
    } else {
        const formattedAmount = selectedData.salaryAmount.toLocaleString();
        document.getElementById('salaryHidden').value = `${selectedData.salaryType} ${formattedAmount}원`;
    }

    if (selectedData.workPeriod === "단기" && selectedData.selectedDates.length > 0) {
        const sortedDates = selectedData.selectedDates.sort();
        document.querySelector('input[name="recruitment_start_date"]').value = sortedDates[0];
        document.querySelector('input[name="recruitment_end_date"]').value = sortedDates[sortedDates.length - 1];
    }

    return true;
}


function calculateMinimumSalary() {
  const calculationText = document.getElementById("salaryCalculation");
  if (!calculationText || !selectedData.salaryType) {
    if (calculationText) calculationText.textContent = "조건을 선택하면 최소 급여를 계산해드려요";
    return;
  }

  let minimumSalary = 0;
  let salaryTypeText = selectedData.salaryType;

  if (selectedData.salaryType === "시급") {
    minimumSalary = MIN_HOURLY_WAGE;
  } else if (selectedData.salaryType === "일급") {
    minimumSalary = MIN_HOURLY_WAGE * 8;
  } else if (selectedData.salaryType === "월급") {
    minimumSalary = MIN_HOURLY_WAGE * 209;
  } else if (selectedData.salaryType === "건당") {
    calculationText.textContent = "건당 급여는 업무 내용에 따라 협의해주세요";
    return;
  }

  calculationText.textContent = `이 조건으로 근무할 경우 최소 ${salaryTypeText}은 ${minimumSalary.toLocaleString()}원이에요`;
}

function toggleCategories() {
  const container = document.getElementById("categoryContainer");
  const toggleIcon = document.getElementById("categoryToggleIcon");

  if (container.classList.contains("expanded")) {
    container.classList.remove("expanded");
    toggleIcon.style.transform = "rotate(0deg)";
  } else {
    container.classList.add("expanded");
    toggleIcon.style.transform = "rotate(180deg)";
  }
}
window.toggleCategories = toggleCategories;

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
  if (!calendarGrid) return;
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
      if (dayOfWeek === 0) dateCell.classList.add("text-red-500");
      else if (dayOfWeek === 6) dateCell.classList.add("text-blue-500");
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
    if (dayOfWeek === 0) element.classList.add("text-red-500");
    else if (dayOfWeek === 6) element.classList.add("text-blue-500");
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
  const selectedDatesCount = document.getElementById("selectedDatesCount");
  const selectedDatesDisplay = document.getElementById("selectedDatesDisplay");

  if (!selectedDatesCount || !selectedDatesDisplay) return;

  selectedDatesCount.textContent = count;
  if (count > 0) {
    const sortedDates = selectedData.selectedDates.sort();
    const firstDate = sortedDates[0].replace(/-/g, ".");
    const lastDate = sortedDates[sortedDates.length - 1].replace(/-/g, ".");
    if (count === 1) {
      selectedDatesDisplay.textContent = firstDate;
    } else {
      selectedDatesDisplay.textContent = `${firstDate} - ${lastDate}`;
    }
  } else {
    selectedDatesDisplay.textContent =
      "날짜를 선택해주세요";
  }
}

function changeMonth(delta) {
  currentCalendarDate.setMonth(currentCalendarDate.getMonth() + delta);
  generateCalendar();
}
window.changeMonth = changeMonth;

let addressMap = null;
let addressMarker = null;
let selectedAddress = null;

function openAddressSearch() {
  document.getElementById("addressModal").classList.remove("hidden");
  if (!addressMap) {
    setTimeout(() => {
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
  const initialLat = selectedData.latitude || 35.8242;
  const initialLng = selectedData.longitude || 128.7569;
  const initialPos = new kakao.maps.LatLng(initialLat, initialLng);

  const options = {
    center: initialPos,
    level: 5,
  };
  addressMap = new kakao.maps.Map(container, options);

  if (selectedData.location) {
      if (addressMarker) addressMarker.setMap(null);
      addressMarker = new kakao.maps.Marker({
          position: initialPos,
          map: addressMap,
      });
      document.getElementById("selectedAddressText").textContent = selectedData.location;
      document.getElementById("confirmAddressBtn").disabled = false;
      selectedAddress = {
        address: selectedData.location,
        lat: initialLat,
        lng: initialLng,
      };
  }

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
      const address = result[0].address;
      const roadAddress = result[0].road_address;
      selectedAddress = {
        address: roadAddress ? roadAddress.address_name : address.address_name,
        lat: parseFloat(result[0].y),
        lng: parseFloat(result[0].x),
        region1: address.region_1depth_name,
        region2: address.region_2depth_name,
        region3: address.region_3depth_name,
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
  if (!selectedAddress || !selectedAddress.address) {
    document.getElementById("selectedAddressText").textContent =
      "지도에서 위치를 클릭하거나 검색해주세요";
  } else {
     document.getElementById("selectedAddressText").textContent = selectedAddress.address;
  }
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

    if (!selectedAddress.region1) {
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

          selectedAddress.region1 = legalRegion.region_1depth_name;
          selectedAddress.region2 = legalRegion.region_2depth_name;
          selectedAddress.region3 = legalRegion.region_3depth_name;

        } catch (error) {
          console.error("주소 변환 중 오류 발생:", error);
          alert("주소 정보를 가져오는 데 실패했습니다. 다른 위치를 선택해주세요.");
          return;
        }
    }

    geocodeResult = {
        lat: selectedAddress.lat,
        lng: selectedAddress.lng,
        region1: selectedAddress.region1,
        region2: selectedAddress.region2,
        region3: selectedAddress.region3,
    };

    document.getElementById("latitude").value = selectedAddress.lat;
    document.getElementById("longitude").value = selectedAddress.lng;
    document.getElementById("region_1depth_name").value = selectedAddress.region1;
    document.getElementById("region_2depth_name").value = selectedAddress.region2;
    document.getElementById("region_3depth_name").value = selectedAddress.region3;

    updateNextButton();
    closeAddressModal();
  }
}
window.confirmAddress = confirmAddress;


document.addEventListener("DOMContentLoaded", function () {
    if (window.INITIAL_JOB_DATA && window.INITIAL_JOB_DATA.id) {
        initializeEditForm(window.INITIAL_JOB_DATA);
    }

    document.querySelectorAll("#step1 .radio-option").forEach((option) => {
        option.addEventListener("click", function () {
            document.querySelectorAll("#step1 .radio-option").forEach((opt) => {
                opt.classList.remove("selected");
                opt.querySelector(".radio-dot").classList.add("hidden");
            });
            this.classList.add("selected");
            this.querySelector(".radio-dot").classList.remove("hidden");
            selectedData.category = this.dataset.value;
            updateNextButton();
        });
    });

    document.getElementById("jobTitle")?.addEventListener("input", function () {
      selectedData.title = this.value;
      updateNextButton();
    });

    document.querySelectorAll(".category-btn").forEach((btn) => {
        btn.addEventListener("click", function () {
            this.classList.toggle("option-selected");
            const selectedCategories = [];
            document
                .querySelectorAll(".category-btn.option-selected")
                .forEach((b) => selectedCategories.push(b.dataset.category));
            selectedData.categories = selectedCategories;
            updateNextButton();
        });
    });


    document.querySelectorAll(".period-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        document
          .querySelectorAll(".period-btn")
          .forEach((b) => b.classList.remove("option-selected"));
        this.classList.add("option-selected");
        selectedData.workPeriod = this.dataset.period;

        document.getElementById("workPeriodHidden").value = selectedData.workPeriod;

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

    document.querySelectorAll(".day-btn").forEach((btn) => {
        btn.addEventListener("click", function () {
            if (document.getElementById("flexibleDays")?.checked) return;

            this.classList.toggle("option-selected");
            const selectedDays = [];
            document
              .querySelectorAll(".day-btn.option-selected")
              .forEach((b) => selectedDays.push(b.dataset.day));
            selectedData.days = selectedDays;
            updateNextButton();
        });
    });

    const flexibleDays = document.getElementById("flexibleDays");
    if (flexibleDays) {
      flexibleDays.addEventListener("change", function () {
        const dayBtns = document.querySelectorAll(".day-btn");
        if (this.checked) {
          dayBtns.forEach((btn) => {
            btn.classList.add("disabled", "opacity-50", "cursor-not-allowed");
            btn.classList.remove("option-selected");
          });
          selectedData.days = ["협의"];
        } else {
          dayBtns.forEach((btn) => {
            btn.classList.remove("disabled", "opacity-50", "cursor-not-allowed");
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

    const longTermStartDate = document.getElementById("longTermStartDate");
    const longTermEndDate = document.getElementById("longTermEndDate");
    if (longTermStartDate) {
        longTermStartDate.addEventListener("change", function () {
        selectedData.longTermStartDate = this.value;
        });
    }
    if (longTermEndDate) {
        longTermEndDate.addEventListener("change", function () {
        selectedData.longTermEndDate = this.value;
        });
    }

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

    document.getElementById("jobDescription")?.addEventListener("input", function () {
      selectedData.description = this.value;
      updateNextButton();
    });


    document.getElementById("detailAddress")?.addEventListener("input", function () {
      selectedData.detailAddress = this.value;
    });

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

    document.getElementById("agreeTerms")?.addEventListener("change", function () {
      updateNextButton();
    });
});