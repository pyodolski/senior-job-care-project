// edit_job_company.js

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
  workPeriod: "",
  recruitmentEndDate: "",
  selectedDates: [],
  days: [],
  startTime: "",
  endTime: "",
  salaryType: "",
  salaryAmount: 0,
  recruitmentCount: 0,
  description: "",
  location: "",
  detailAddress: "",
  phone: "",
  latitude: null,
  longitude: null
};

const MIN_HOURLY_WAGE = 10030;
let geocodeResult = null;
let currentCalendarDate = new Date();
const today = new Date();


function syncSelectedDataToForm() {
    const form = document.getElementById('editJobForm');
    if (!form) return false;

    const updateHiddenField = (name, value) => {
        let input = form.querySelector(`input[name="${name}"]`);
        if (!input) {
            input = document.createElement('input');
            input.type = 'hidden';
            input.name = name;
            form.appendChild(input);
        }
        input.value = value || '';
    };

    updateHiddenField('job_category', selectedData.category);
    updateHiddenField('recruitment_type', selectedData.category);

    form.querySelector('input[name="title"]').value = selectedData.title;

    updateHiddenField('work_period', selectedData.workPeriod);
    form.querySelector('select[name="work_start_time"]').value = selectedData.startTime;
    form.querySelector('select[name="work_end_time"]').value = selectedData.endTime;

    const isFlexibleDays = selectedData.days.includes("협의");
    updateHiddenField('work_monday', isFlexibleDays || selectedData.days.includes("월") ? "true" : "false");
    updateHiddenField('work_tuesday', isFlexibleDays || selectedData.days.includes("화") ? "true" : "false");
    updateHiddenField('work_wednesday', isFlexibleDays || selectedData.days.includes("수") ? "true" : "false");
    updateHiddenField('work_thursday', isFlexibleDays || selectedData.days.includes("목") ? "true" : "false");
    updateHiddenField('work_friday', isFlexibleDays || selectedData.days.includes("금") ? "true" : "false");
    updateHiddenField('work_saturday', isFlexibleDays || selectedData.days.includes("토") ? "true" : "false");
    updateHiddenField('work_sunday', isFlexibleDays || selectedData.days.includes("일") ? "true" : "false");

    form.querySelector('input[name="recruitment_end_date"]').value = selectedData.recruitmentEndDate;

    if (selectedData.salaryType === '협의' || selectedData.salaryAmount === 0) {
        updateHiddenField('salary', '급여 협의');
    } else {
        const formattedAmount = selectedData.salaryAmount.toLocaleString();
        updateHiddenField('salary', `${selectedData.salaryType} ${formattedAmount}원`);
    }

    form.querySelector('input[name="recruitment_count"]').value = selectedData.recruitmentCount;

    form.querySelector('textarea[name="description"]').value = selectedData.description;

    form.querySelector('input[name="region"]').value = selectedData.location;
    form.querySelector('input[name="detail_address"]').value = selectedData.detailAddress;

    updateHiddenField('latitude', selectedData.latitude || (window.geocodeResult ? window.geocodeResult.lat : ''));
    updateHiddenField('longitude', selectedData.longitude || (window.geocodeResult ? window.geocodeResult.lng : ''));

    if (window.geocodeResult) {
        updateHiddenField('region_1depth_name', window.geocodeResult.region1 || '');
        updateHiddenField('region_2depth_name', window.geocodeResult.region2 || '');
        updateHiddenField('region_3depth_name', window.geocodeResult.region3 || '');
    }

    form.querySelector('input[name="contact_phone"]').value = selectedData.phone;

    if (selectedData.workPeriod === "단기" && selectedData.selectedDates.length > 0) {
        const sortedDates = selectedData.selectedDates.sort();
        updateHiddenField("recruitment_start_date", sortedDates[0]);
        updateHiddenField(
          "recruitment_end_date",
          sortedDates[sortedDates.length - 1]
        );
    }

    return true;
}


function submitJobForm() {
    const agreeTerms = document.getElementById("agreeTerms")?.checked;

    if (!isAllFieldsValid()) {
        alert("모든 필수 필드를 입력해주세요.");
        return false;
    }

    if (!agreeTerms) {
        alert("기업 이음 준수사항에 동의해야 합니다.");
        return false;
    }

    return syncSelectedDataToForm();
}


function isAllFieldsValid() {
    let isValid = true;

    if (selectedData.category.length === 0) isValid = false;

    if (selectedData.title.length === 0) isValid = false;

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

    if (!(selectedData.recruitmentCount > 0)) isValid = false;

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
}


function initializeEditForm(jobData) {
    if (!jobData || !jobData.id) return;

    selectedData.category = jobData.category;
    selectedData.title = jobData.title;
    selectedData.workPeriod = jobData.workPeriod;
    selectedData.recruitmentEndDate = jobData.recruitmentEndDate;
    selectedData.recruitmentCount = jobData.recruitmentCount;
    selectedData.description = jobData.description;
    selectedData.location = jobData.location;
    selectedData.detailAddress = jobData.detailAddress;
    selectedData.phone = jobData.phone.replace(/-/g, '') || "";
    selectedData.days = jobData.workDays.includes('협의') ? ['협의'] : jobData.workDays.filter(d => d.trim() !== '');
    selectedData.startTime = jobData.startTime;
    selectedData.endTime = jobData.endTime;

    const salaryMatch = jobData.salary.match(/^(시급|일급|월급|건당)\s*([\d,]+)/);
    if (salaryMatch) {
        selectedData.salaryType = salaryMatch[1];
        selectedData.salaryAmount = parseInt(salaryMatch[2].replace(/,/g, '')) || 0;
    } else {
        selectedData.salaryType = jobData.salary.includes('협의') ? '협의' : '';
        selectedData.salaryAmount = 0;
    }

    const initialCategories = selectedData.category.split(',').map(c => c.trim()).filter(c => c);

    document.querySelectorAll('#step1 .radio-option').forEach(opt => {
        const optValue = opt.dataset.value;

        if (initialCategories.includes(optValue)) {
            opt.classList.add('selected');
            opt.querySelector('.radio-dot').classList.remove('hidden');
        } else if (opt.dataset.value === '기타' && selectedData.category && !initialCategories.some(c => document.querySelector(`#step1 .radio-option[data-value="${c}"]`))) {
             opt.classList.add('selected');
             opt.querySelector('.radio-dot').classList.remove('hidden');
             const customInput = document.getElementById('customCategory');
             customInput.classList.remove('hidden');
             customInput.value = selectedData.category;
        }
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
    document.getElementById('salaryAmount').value = selectedData.salaryAmount.toLocaleString();
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
window.initializeEditForm = initializeEditForm;


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
    selectedDatesDisplay.textContent = "날짜를 선택해주세요";
  }
}

function changeMonth(delta) {
  currentCalendarDate.setMonth(currentCalendarDate.getMonth() + delta);
  generateCalendar();
}
window.changeMonth = changeMonth;

function calculateMinimumSalary() {
  const calculationText = document.getElementById("salaryCalculation");
  if (!calculationText || !selectedData.salaryType) {
    if (calculationText) calculationText.textContent = "조건을 선택하면 최소 급여를 계산해드려요";
    return;
  }

  let minimumSalary = 0;

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

let map = null;
let marker = null;
let geocoder = null;
let selectedLocation = null;
const mapListeners = [];

function openAddressSearch() {
  document.getElementById("addressModal")?.classList.remove("hidden");

  setTimeout(() => {
    initMap();
  }, 100);
}
window.openAddressSearch = openAddressSearch;

function initMap() {
  const container = document.getElementById("addressMap");
  if (!container || typeof kakao === 'undefined' || !kakao.maps) return;

  const initialLat = selectedData.latitude || 35.8242;
  const initialLng = selectedData.longitude || 128.7569;
  const initialPos = new kakao.maps.LatLng(initialLat, initialLng);

  if (!map) {
      map = new kakao.maps.Map(container, {
          center: initialPos,
          level: 5,
      });
      geocoder = new kakao.maps.services.Geocoder();

      mapListeners.forEach(listener => kakao.maps.event.removeListener(listener));
      mapListeners.length = 0;

      const clickListener = kakao.maps.event.addListener(map, "click", function (mouseEvent) {
          const latlng = mouseEvent.latLng;
          const lat = latlng.getLat();
          const lng = latlng.getLng();

          if (marker) marker.setMap(null);
          marker = new kakao.maps.Marker({
              position: latlng,
              map: map,
          });

          getAddressFromCoords(lat, lng);
      });
      mapListeners.push(clickListener);
  } else {
      map.relayout();
      map.setCenter(initialPos);
  }

  if (selectedData.location) {
      if (marker) marker.setMap(null);
      marker = new kakao.maps.Marker({
          position: initialPos,
          map: map,
      });
      document.getElementById("selectedAddressText").textContent = selectedData.location;
      document.getElementById("confirmAddressBtn").disabled = false;
      selectedLocation = {
        address: selectedData.location,
        lat: initialLat,
        lng: initialLng,
      };
  }
}
window.initMap = initMap;

function getAddressFromCoords(lat, lng) {
    if (!geocoder) geocoder = new kakao.maps.services.Geocoder();

    geocoder.coord2Address(
        lng,
        lat,
        function (result, status) {
            if (status === kakao.maps.services.Status.OK) {
                const address = result[0].address;
                const roadAddress = result[0].road_address;
                const displayAddress = roadAddress ? roadAddress.address_name : address.address_name;

                selectedLocation = {
                    address: displayAddress,
                    lat: lat,
                    lng: lng,
                    region1: address.region_1depth_name,
                    region2: address.region_2depth_name,
                    region3: address.region_3depth_name,
                };
                document.getElementById("selectedAddressText").textContent = displayAddress;
                document.getElementById("confirmAddressBtn").disabled = false;
            } else {
                console.error("주소 변환 실패:", status);
            }
        }
    );
}


function searchAddress() {
  const query = document.getElementById("addressSearch").value.trim();
  if (!query) {
    alert("주소를 입력해주세요");
    return;
  }
  if (!geocoder) geocoder = new kakao.maps.services.Geocoder();

  geocoder.addressSearch(query, function (result, status) {
    if (status === kakao.maps.services.Status.OK) {
      const coords = new kakao.maps.LatLng(result[0].y, result[0].x);
      map.setCenter(coords);
      map.setLevel(3);

      if (marker) marker.setMap(null);
      marker = new kakao.maps.Marker({
        position: coords,
        map: map,
      });

      const roadAddress = result[0].road_address;
      const address = result[0].address;
      selectedLocation = {
        address: roadAddress ? roadAddress.address_name : address.address_name,
        lat: parseFloat(result[0].y),
        lng: parseFloat(result[0].x),
        region1: address.region_1depth_name,
        region2: address.region_2depth_name,
        region3: address.region_3depth_name,
      };
      document.getElementById("selectedAddressText").textContent =
        selectedLocation.address;
      document.getElementById("confirmAddressBtn").disabled = false;
    } else {
      alert("주소를 찾을 수 없습니다. 다시 시도해주세요.");
    }
  });
}
window.searchAddress = searchAddress;

function closeAddressModal() {
  document.getElementById("addressModal")?.classList.add("hidden");
  if (!selectedLocation) {
    document.getElementById("selectedAddressText").textContent =
      "지도에서 위치를 클릭하거나 검색해주세요";
  } else {
    document.getElementById("selectedAddressText").textContent = selectedLocation.address;
  }
  document.getElementById("confirmAddressBtn").disabled = true;
  document.getElementById("addressSearch").value = "";
}
window.closeAddressModal = closeAddressModal;

async function confirmLocation() {
  if (selectedLocation) {
    document.getElementById("workLocation").value = selectedLocation.address;
    selectedData.location = selectedLocation.address;
    selectedData.latitude = selectedLocation.lat;
    selectedData.longitude = selectedLocation.lng;

    if (selectedLocation.region1) {
        window.geocodeResult = {
            lat: selectedLocation.lat,
            lng: selectedLocation.lng,
            region1: selectedLocation.region1,
            region2: selectedLocation.region2,
            region3: selectedLocation.region3,
        };

        document.getElementById("latitude").value = selectedLocation.lat;
        document.getElementById("longitude").value = selectedLocation.lng;
        document.getElementById("region_1depth_name").value = selectedLocation.region1;
        document.getElementById("region_2depth_name").value = selectedLocation.region2;
        document.getElementById("region_3depth_name").value = selectedLocation.region3;

    } else {
        if (!geocoder) geocoder = new kakao.maps.services.Geocoder();

        try {
            const regionResult = await new Promise((resolve, reject) => {
                geocoder.coord2RegionCode(
                    selectedLocation.lng,
                    selectedLocation.lat,
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

            window.geocodeResult = {
                lat: selectedLocation.lat,
                lng: selectedLocation.lng,
                region1: legalRegion.region_1depth_name,
                region2: legalRegion.region_2depth_name,
                region3: legalRegion.region_3depth_name,
            };

            document.getElementById("latitude").value = selectedLocation.lat;
            document.getElementById("longitude").value = selectedLocation.lng;
            document.getElementById("region_1depth_name").value = legalRegion.region_1depth_name;
            document.getElementById("region_2depth_name").value = legalRegion.region_2depth_name;
            document.getElementById("region_3depth_name").value = legalRegion.region_3depth_name;

        } catch (error) {
            window.geocodeResult = null;
            alert("주소 정보를 가져오는 데 실패했습니다. 다른 위치를 선택해주세요.");
        }
    }

    updateNextButton();
    closeAddressModal();
  }
}
window.confirmLocation = confirmLocation;

document.addEventListener("DOMContentLoaded", function () {
    if (window.INITIAL_JOB_DATA && window.INITIAL_JOB_DATA.id) {
        initializeEditForm(window.INITIAL_JOB_DATA);
    }

    document.querySelectorAll("#step1 .radio-option").forEach((option) => {
        option.addEventListener("click", function () {
            this.classList.toggle("selected");
            this.querySelector(".radio-dot").classList.toggle("hidden");

            if (this.dataset.value === "기타") {
                document.getElementById("customCategory")?.classList.toggle("hidden", !this.classList.contains("selected"));
                if (!this.classList.contains("selected")) document.getElementById("customCategory").value = "";
            }

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

    document.getElementById("customCategory")?.addEventListener("input", function () {
        const 기타옵션 = document.querySelector('#step1 .radio-option[data-value="기타"].selected');
        if (기타옵션) {
            selectedData.category = this.value.trim();
        }
        updateNextButton();
    });


    document.getElementById("jobTitle")?.addEventListener("input", function () {
      selectedData.title = this.value;
      updateNextButton();
    });

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

    document.getElementById("recruitmentEndDate")?.addEventListener("change", function () {
      selectedData.recruitmentEndDate = this.value;
      updateNextButton();
    });


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

    const recruitmentCount = document.getElementById("recruitmentCount");
    if (recruitmentCount) {
      recruitmentCount.addEventListener("input", function(e) {
          let value = e.target.value.replace(/[^0-9]/g, "");
          e.target.value = value;
          selectedData.recruitmentCount = parseInt(value) || 0;
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

    document.querySelectorAll(".day-btn").forEach((btn) => {
        btn.addEventListener("click", function () {
            if (document.getElementById("flexibleDays")?.checked) {
                return;
            }

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
});