let currentStep = 1;
const totalSteps = 5;
const formData = {};
let birthData = { year: "", month: "", day: "" };

// 지도 관련 변수
let map = null;
let marker = null;
let geocoder = null;
let selectedLocation = null;

// 생년월일 선택기 초기화
function initBirthPickers() {
  const currentYear = new Date().getFullYear();
  const yearPicker = document.getElementById("year-picker");
  for (let year = currentYear; year >= 1940; year--) {
    const option = document.createElement("div");
    option.className = "px-4 py-2 hover:bg-blue-100 cursor-pointer text-center";
    option.textContent = year + "년";
    option.onclick = () => selectYear(year);
    yearPicker.appendChild(option);
  }

  const monthPicker = document.getElementById("month-picker");
  for (let month = 1; month <= 12; month++) {
    const option = document.createElement("div");
    option.className = "px-4 py-2 hover:bg-blue-100 cursor-pointer text-center";
    option.textContent = month + "월";
    option.onclick = () => selectMonth(month);
    monthPicker.appendChild(option);
  }

  updateDayPicker();
}

function updateDayPicker() {
  const dayPicker = document.getElementById("day-picker");
  dayPicker.innerHTML = "";

  let maxDays = 31;
  if (birthData.year && birthData.month) {
    maxDays = new Date(birthData.year, birthData.month, 0).getDate();
  } else if (birthData.month) {
    const tempYear = 2024;
    maxDays = new Date(tempYear, birthData.month, 0).getDate();
  }

  for (let day = 1; day <= maxDays; day++) {
    const option = document.createElement("div");
    option.className = "px-4 py-2 hover:bg-blue-100 cursor-pointer text-center";
    option.textContent = day + "일";
    option.onclick = () => selectDay(day);
    dayPicker.appendChild(option);
  }
}

function selectYear(year) {
  birthData.year = year;
  document.getElementById("year-text").textContent = year + "년";
  document.getElementById("year-text").classList.remove("text-gray-400");
  document.getElementById("year-text").classList.add("text-gray-800");
  document.getElementById("birth-year").value = year;
  document.getElementById("year-picker").classList.add("hidden");
  updateDayPicker();
  updateNextButton();
}

function selectMonth(month) {
  birthData.month = month;
  document.getElementById("month-text").textContent = month + "월";
  document.getElementById("month-text").classList.remove("text-gray-400");
  document.getElementById("month-text").classList.add("text-gray-800");
  document.getElementById("birth-month").value = month;
  document.getElementById("month-picker").classList.add("hidden");
  updateDayPicker();
  updateNextButton();
}

function selectDay(day) {
  birthData.day = day;
  document.getElementById("day-text").textContent = day + "일";
  document.getElementById("day-text").classList.remove("text-gray-400");
  document.getElementById("day-text").classList.add("text-gray-800");
  document.getElementById("birth-day").value = day;
  document.getElementById("day-picker").classList.add("hidden");
  updateNextButton();
}

function togglePicker(type) {
  ["year", "month", "day"].forEach((t) => {
    if (t !== type) {
      document.getElementById(t + "-picker").classList.add("hidden");
    }
  });

  const picker = document.getElementById(type + "-picker");
  picker.classList.toggle("hidden");
}

document.addEventListener("click", function (e) {
  if (
    !e.target.closest("#year-display") &&
    !e.target.closest("#year-picker")
  ) {
    document.getElementById("year-picker").classList.add("hidden");
  }
  if (
    !e.target.closest("#month-display") &&
    !e.target.closest("#month-picker")
  ) {
    document.getElementById("month-picker").classList.add("hidden");
  }
  if (
    !e.target.closest("#day-display") &&
    !e.target.closest("#day-picker")
  ) {
    document.getElementById("day-picker").classList.add("hidden");
  }
});

document.addEventListener("DOMContentLoaded", function () {
  initBirthPickers();
});

// ===== 지도 관련 함수들 =====

function openMapModal() {
  document.getElementById("map-modal").classList.remove("hidden");

  if (!map) {
    initMap();
  } else {
    setTimeout(function() {
      map.relayout();
    }, 100);
  }
}

function closeMapModal() {
  document.getElementById("map-modal").classList.add("hidden");
}

function initMap() {
  const container = document.getElementById("map");

  const defaultPosition = new kakao.maps.LatLng(37.5665, 126.978);
  const options = {
    center: defaultPosition,
    level: 3
  };

  map = new kakao.maps.Map(container, options);
  geocoder = new kakao.maps.services.Geocoder();

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function (position) {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        const locPosition = new kakao.maps.LatLng(lat, lng);

        map.setCenter(locPosition);

        setTimeout(function() {
          map.relayout();
        }, 100);

        if (!marker) {
          marker = new kakao.maps.Marker({
            position: locPosition,
            map: map
          });
        } else {
          marker.setPosition(locPosition);
        }

        getAddressFromCoords(lat, lng);
      },
      function (error) {
        console.log("현재 위치를 가져올 수 없습니다:", error);
        marker = new kakao.maps.Marker({
          position: defaultPosition,
          map: map
        });
        getAddressFromCoords(37.5665, 126.978);
      }
    );
  } else {
    marker = new kakao.maps.Marker({
      position: defaultPosition,
      map: map
    });
    getAddressFromCoords(37.5665, 126.978);
  }

  kakao.maps.event.addListener(map, "click", function (mouseEvent) {
    const latlng = mouseEvent.latLng;
    const lat = latlng.getLat();
    const lng = latlng.getLng();

    if (!marker) {
      marker = new kakao.maps.Marker({
        position: latlng,
        map: map
      });
    } else {
      marker.setPosition(latlng);
    }

    getAddressFromCoords(lat, lng);
  });
}

function getAddressFromCoords(lat, lng) {
  geocoder.coord2Address(lng, lat, function (result, status) {
    if (status === kakao.maps.services.Status.OK) {
      const address = result[0].address;
      const roadAddress = result[0].road_address;

      const sido = address.region_1depth_name;
      const sigungu = address.region_2depth_name;
      let dong = address.region_3depth_name;

      if (!dong || dong === '') {
        dong = address.region_3depth_h_name || sigungu;
      }

      let displayAddress = sido + ' ' + sigungu;
      if (dong && dong !== sigungu) {
        displayAddress += ' ' + dong;
      }

      const fullAddress = address.address_name;

      selectedLocation = {
        lat: lat,
        lng: lng,
        fullAddress: fullAddress,
        displayAddress: displayAddress,
        sido: sido,
        sigungu: sigungu,
        dong: dong
      };

      document.getElementById("selected-address").textContent = displayAddress;

      const confirmBtn = document.getElementById("confirm-location-btn");
      confirmBtn.disabled = false;
      confirmBtn.classList.remove("bg-gray-300", "text-gray-500");
      confirmBtn.classList.add("bg-blue-900", "text-white", "hover:bg-blue-800");
    }
  });
}

function confirmLocation() {
  if (selectedLocation) {
    document.getElementById("sido").value = selectedLocation.sido;
    document.getElementById("sigungu").value = selectedLocation.sigungu;
    document.getElementById("dong").value = selectedLocation.dong;

    document.getElementById("address-search").value = selectedLocation.displayAddress;
    document.getElementById("full-address").textContent = selectedLocation.displayAddress;
    document.getElementById("address-display").classList.remove("hidden");

    closeMapModal();

    updateNextButton();
  }
}

// 뒤로가기
function goBack() {
  if (currentStep === 1) {
    window.location.href = window.authMainUrl;
  } else {
    currentStep--;
    showStep(currentStep);
  }
}

function showStep(step) {
  document.querySelectorAll('.step-content').forEach(el => el.classList.remove('active'));
  document.querySelector(`.step-content[data-step="${step}"]`).classList.add('active');

  const progress = (step / totalSteps) * 100;
  document.getElementById('progress-bar').style.width = progress + '%';

  updateNextButton();
}

function updateNextButton() {
  const button = document.getElementById("next-button");
  let isValid = false;

  switch(currentStep) {
    case 1:
      isValid = document.getElementById("birth-year").value.trim() !== "" &&
               document.getElementById("birth-month").value.trim() !== "" &&
               document.getElementById("birth-day").value.trim() !== "";
      break;
    case 2:
      isValid = formData.gender !== undefined;
      break;
    case 3:
      const phone = document.getElementById("phone").value.trim();
      isValid = phone !== "" && phone.replace(/[^0-9]/g, "").length >= 10;
      break;
    case 4:
      isValid = selectedLocation !== null &&
        document.getElementById("sido").value !== "" &&
        document.getElementById("sigungu").value !== "" &&
        document.getElementById("dong").value !== "";
      break;
  }

  if (isValid) {
    button.disabled = false;
    button.classList.remove("bg-gray-300", "text-gray-500");
    button.classList.add("bg-blue-900", "text-white", "hover:bg-blue-800");
  } else {
    button.disabled = true;
    button.classList.add("bg-gray-300", "text-gray-500");
    button.classList.remove("bg-blue-900", "text-white", "hover:bg-blue-800");
  }
}

function selectGender(gender, element) {
  document.querySelectorAll('.gender-button').forEach(el => el.classList.remove('selected'));
  element.classList.add('selected');
  formData.gender = gender;
  updateNextButton();
}

function nextStep() {
  switch(currentStep) {
    case 1:
      const year = document.getElementById("birth-year").value;
      const month = document.getElementById("birth-month").value.padStart(2, "0");
      const day = document.getElementById("birth-day").value.padStart(2, "0");
      formData.birthDate = `${year}-${month}-${day}`;
      break;
    case 3:
      formData.phone = document.getElementById("phone").value;
      break;
    case 4:
      formData.sido = document.getElementById("sido").value;
      formData.sigungu = document.getElementById("sigungu").value;
      formData.dong = document.getElementById("dong").value;

      document.getElementById("final-birth-date").value = formData.birthDate;
      document.getElementById("final-gender").value = formData.gender;
      document.getElementById("final-phone").value = formData.phone;
      document.getElementById("final-sido").value = formData.sido;
      document.getElementById("final-sigungu").value = formData.sigungu;
      document.getElementById("final-dong").value = formData.dong;

      currentStep++;
      showStep(currentStep);
      document.getElementById("next-button-container").style.display = "none";

      setTimeout(() => {
        document.getElementById("onboarding-form").submit();
      }, 2000);
      return;
  }

  if (currentStep < totalSteps) {
    currentStep++;
    showStep(currentStep);
  }
}

// 전화번호 자동 포맷팅
document.getElementById("phone").addEventListener("input", function(e) {
  let value = e.target.value.replace(/[^0-9]/g, "");
  let formattedValue = "";

  if (value.length <= 3) {
    formattedValue = value;
  } else if (value.length <= 7) {
    formattedValue = value.slice(0, 3) + "-" + value.slice(3);
  } else {
    formattedValue = value.slice(0, 3) + "-" + value.slice(3, 7) + "-" + value.slice(7, 11);
  }

  e.target.value = formattedValue;
  updateNextButton();
});

document.querySelectorAll("input").forEach(input => {
  input.addEventListener("keypress", function (e) {
    if (e.key === "Enter" && !document.getElementById("next-button").disabled) {
      e.preventDefault();
      nextStep();
    }
  });
});
