// 회원가입 페이지 JavaScript

let currentStep = 1;
const totalSteps = 9;
const formData = {};
let birthData = { year: "", month: "", day: "" };

// 지도 관련 변수
let map = null;
let marker = null;
let geocoder = null;
let selectedLocation = null;

// 생년월일 선택기 초기화
function initBirthPickers() {
  // 년도 옵션 생성 (1940 ~ 현재 년도)
  const currentYear = new Date().getFullYear();
  const yearPicker = document.getElementById("year-picker");
  for (let year = currentYear; year >= 1940; year--) {
    const option = document.createElement("div");
    option.className = "px-4 py-2 hover:bg-blue-100 cursor-pointer text-center";
    option.textContent = year + "년";
    option.onclick = () => selectYear(year);
    yearPicker.appendChild(option);
  }

  // 월 옵션 생성 (1 ~ 12)
  const monthPicker = document.getElementById("month-picker");
  for (let month = 1; month <= 12; month++) {
    const option = document.createElement("div");
    option.className = "px-4 py-2 hover:bg-blue-100 cursor-pointer text-center";
    option.textContent = month + "월";
    option.onclick = () => selectMonth(month);
    monthPicker.appendChild(option);
  }

  // 일 옵션 생성 (1 ~ 31)
  updateDayPicker();
}

// 월과 년도에 따라 일 옵션 업데이트
function updateDayPicker() {
  const dayPicker = document.getElementById("day-picker");
  dayPicker.innerHTML = "";

  let maxDays = 31;
  if (birthData.year && birthData.month) {
    // 해당 월의 마지막 날짜 계산
    maxDays = new Date(birthData.year, birthData.month, 0).getDate();
  } else if (birthData.month) {
    // 년도가 없으면 기본값으로 계산
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

// 년도 선택
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

// 월 선택
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

// 일 선택
function selectDay(day) {
  birthData.day = day;
  document.getElementById("day-text").textContent = day + "일";
  document.getElementById("day-text").classList.remove("text-gray-400");
  document.getElementById("day-text").classList.add("text-gray-800");
  document.getElementById("birth-day").value = day;
  document.getElementById("day-picker").classList.add("hidden");
  updateNextButton();
}

// 선택기 토글
function togglePicker(type) {
  // 다른 선택기들 닫기
  ["year", "month", "day"].forEach((t) => {
    if (t !== type) {
      document.getElementById(t + "-picker").classList.add("hidden");
    }
  });

  // 선택한 선택기 토글
  const picker = document.getElementById(type + "-picker");
  picker.classList.toggle("hidden");
}

// 선택기 외부 클릭시 닫기
document.addEventListener("click", function (e) {
  if (!e.target.closest("#year-display") && !e.target.closest("#year-picker")) {
    document.getElementById("year-picker").classList.add("hidden");
  }
  if (
    !e.target.closest("#month-display") &&
    !e.target.closest("#month-picker")
  ) {
    document.getElementById("month-picker").classList.add("hidden");
  }
  if (!e.target.closest("#day-display") && !e.target.closest("#day-picker")) {
    document.getElementById("day-picker").classList.add("hidden");
  }
});

// 페이지 로드시 생년월일 선택기 초기화
document.addEventListener("DOMContentLoaded", function () {
  initBirthPickers();
});

// ===== 지도 관련 함수들 =====

// 지도 모달 열기
function openMapModal() {
  document.getElementById("map-modal").classList.remove("hidden");

  // 지도가 아직 초기화되지 않았으면 초기화
  if (!map) {
    initMap();
  } else {
    // 이미 초기화된 경우 지도 크기 재조정
    setTimeout(function () {
      map.relayout();
    }, 100);
  }
}

// 지도 모달 닫기
function closeMapModal() {
  document.getElementById("map-modal").classList.add("hidden");
}

// 지도 초기화
function initMap() {
  const container = document.getElementById("map");

  // 먼저 기본 위치로 지도 생성
  const defaultPosition = new kakao.maps.LatLng(37.5665, 126.978); // 서울 시청
  const options = {
    center: defaultPosition,
    level: 3,
  };

  map = new kakao.maps.Map(container, options);
  geocoder = new kakao.maps.services.Geocoder();

  // 현재 위치 가져오기
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function (position) {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        const locPosition = new kakao.maps.LatLng(lat, lng);

        // 지도 중심을 현재 위치로 이동
        map.setCenter(locPosition);

        // 지도 크기 재설정 (위치 이동 후)
        setTimeout(function () {
          map.relayout();
        }, 100);

        // 마커 생성
        if (!marker) {
          marker = new kakao.maps.Marker({
            position: locPosition,
            map: map,
          });
        } else {
          marker.setPosition(locPosition);
        }

        // 현재 위치의 주소 가져오기
        getAddressFromCoords(lat, lng);
      },
      function (error) {
        console.log("현재 위치를 가져올 수 없습니다:", error);
        // 기본 위치(서울 시청)에 마커 표시
        marker = new kakao.maps.Marker({
          position: defaultPosition,
          map: map,
        });
        getAddressFromCoords(37.5665, 126.978);
      }
    );
  } else {
    // Geolocation을 지원하지 않는 경우 기본 위치 사용
    marker = new kakao.maps.Marker({
      position: defaultPosition,
      map: map,
    });
    getAddressFromCoords(37.5665, 126.978);
  }

  // 지도 클릭 이벤트
  kakao.maps.event.addListener(map, "click", function (mouseEvent) {
    const latlng = mouseEvent.latLng;
    const lat = latlng.getLat();
    const lng = latlng.getLng();

    // 마커 이동
    if (!marker) {
      marker = new kakao.maps.Marker({
        position: latlng,
        map: map,
      });
    } else {
      marker.setPosition(latlng);
    }

    // 주소 가져오기
    getAddressFromCoords(lat, lng);
  });
}

// 좌표로 주소 가져오기
function getAddressFromCoords(lat, lng) {
  geocoder.coord2Address(lng, lat, function (result, status) {
    if (status === kakao.maps.services.Status.OK) {
      const address = result[0].address;
      const roadAddress = result[0].road_address;

      // 주소 파싱 (읍/면/동까지만)
      const sido = address.region_1depth_name; // 시/도
      const sigungu = address.region_2depth_name; // 시/군/구
      let dong = address.region_3depth_name; // 읍/면/동

      // dong이 없는 경우 (예: 세종특별자치시)
      if (!dong || dong === "") {
        dong = address.region_3depth_h_name || sigungu;
      }

      // 읍/면/동까지만 포함된 주소 생성
      let displayAddress = sido + " " + sigungu;
      if (dong && dong !== sigungu) {
        displayAddress += " " + dong;
      }

      // 전체 주소는 화면 표시용
      const fullAddress = address.address_name;

      // 선택된 위치 정보 저장
      selectedLocation = {
        lat: lat,
        lng: lng,
        fullAddress: fullAddress,
        displayAddress: displayAddress, // 읍/면/동까지만
        sido: sido,
        sigungu: sigungu,
        dong: dong,
      };

      // 화면에 표시 (읍/면/동까지만)
      document.getElementById("selected-address").textContent = displayAddress;

      // 확인 버튼 활성화
      const confirmBtn = document.getElementById("confirm-location-btn");
      confirmBtn.disabled = false;
      confirmBtn.classList.remove("bg-gray-300", "text-gray-500");
      confirmBtn.classList.add(
        "bg-blue-900",
        "text-white",
        "hover:bg-blue-800"
      );
    }
  });
}

// 위치 확인 버튼 클릭
function confirmLocation() {
  if (selectedLocation) {
    // 주소 정보를 hidden input에 저장 (읍/면/동까지만)
    document.getElementById("sido").value = selectedLocation.sido;
    document.getElementById("sigungu").value = selectedLocation.sigungu;
    document.getElementById("dong").value = selectedLocation.dong;

    // 화면에 표시 (읍/면/동까지만)
    document.getElementById("address-search").value =
      selectedLocation.displayAddress;
    document.getElementById("full-address").textContent =
      selectedLocation.displayAddress;
    document.getElementById("address-display").classList.remove("hidden");

    // 모달 닫기
    closeMapModal();

    // 다음 버튼 활성화 체크
    updateNextButton();
  }
}

// 주소 검색 기능
function searchAddress() {
  const keyword = document.getElementById("map-search-input").value.trim();

  if (!keyword) {
    alert("검색할 주소를 입력해주세요.");
    return;
  }

  // 카카오 주소 검색 서비스
  const ps = new kakao.maps.services.Places();

  ps.keywordSearch(keyword, function (result, status) {
    if (status === kakao.maps.services.Status.OK) {
      // 첫 번째 검색 결과로 이동
      const place = result[0];
      const moveLatLon = new kakao.maps.LatLng(place.y, place.x);

      // 지도 중심 이동
      map.setCenter(moveLatLon);

      // 마커 이동
      if (!marker) {
        marker = new kakao.maps.Marker({
          position: moveLatLon,
          map: map,
        });
      } else {
        marker.setPosition(moveLatLon);
      }

      // 주소 정보 가져오기
      getAddressFromCoords(place.y, place.x);
    } else if (status === kakao.maps.services.Status.ZERO_RESULT) {
      alert("검색 결과가 없습니다.");
    } else {
      alert("검색 중 오류가 발생했습니다.");
    }
  });
}

// 뒤로가기
function goBack() {
  if (currentStep === 1) {
    window.location.href = document.body.dataset.firstLoginUrl;
  } else {
    currentStep--;
    showStep(currentStep);
  }
}

// 스텝 표시
function showStep(step) {
  document
    .querySelectorAll(".step-content")
    .forEach((el) => el.classList.remove("active"));
  document
    .querySelector(`.step-content[data-step="${step}"]`)
    .classList.add("active");

  // 진행바 업데이트
  const progress = (step / totalSteps) * 100;
  document.getElementById("progress-bar").style.width = progress + "%";

  // 다음 버튼 상태 초기화
  updateNextButton();
}

// 다음 버튼 상태 업데이트
function updateNextButton() {
  const button = document.getElementById("next-button");
  let isValid = false;

  switch (currentStep) {
    case 1:
      isValid = document.getElementById("username").value.trim() !== "";
      break;
    case 2:
      const password = document.getElementById("password").value.trim();
      const confirmPassword = document
        .getElementById("confirm-password")
        .value.trim();

      // 비밀번호가 입력되면 확인 필드 표시
      if (password !== "") {
        document
          .getElementById("confirm-password-container")
          .classList.remove("hidden");
        // 두 비밀번호가 모두 입력되고 일치해야 다음 버튼 활성화
        isValid = confirmPassword !== "" && password === confirmPassword;

        // 비밀번호 불일치 에러 메시지
        if (confirmPassword !== "" && password !== confirmPassword) {
          document.getElementById("password-error").classList.remove("hidden");
        } else {
          document.getElementById("password-error").classList.add("hidden");
        }
      } else {
        document
          .getElementById("confirm-password-container")
          .classList.add("hidden");
        isValid = false;
      }
      break;
    case 3:
      isValid = document.getElementById("name").value.trim() !== "";
      break;
    case 4:
      isValid =
        document.getElementById("birth-year").value.trim() !== "" &&
        document.getElementById("birth-month").value.trim() !== "" &&
        document.getElementById("birth-day").value.trim() !== "";
      break;
    case 5:
      isValid = formData.gender !== undefined;
      break;
    case 6:
      isValid = document.getElementById("nickname").value.trim() !== "";
      break;
    case 7:
      const phone = document.getElementById("phone").value.trim();
      // 전화번호 형식 체크 (10자리 이상)
      isValid = phone !== "" && phone.replace(/[^0-9]/g, "").length >= 10;
      break;
    case 8:
      // 지도에서 선택한 주소가 있는지 확인
      isValid =
        selectedLocation !== null &&
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

// 성별 선택
function selectGender(gender, element) {
  document
    .querySelectorAll(".gender-button")
    .forEach((el) => el.classList.remove("selected"));
  element.classList.add("selected");
  formData.gender = gender;
  updateNextButton();
}

// 내 이름으로 하기
function useMyName(event) {
  event.preventDefault();
  const name = formData.name || document.getElementById("name").value;
  if (name) {
    document.getElementById("nickname").value = name;
    updateNextButton();
  }
}

async function nextStep() {
  switch (currentStep) {
    case 1:
      const username = document.getElementById("username").value;
      const errorEl = document.getElementById("username-error");
      const button = document.getElementById("next-button");

      if (!username || username.trim() === "") {
        errorEl.textContent = "아이디를 입력해주세요.";
        errorEl.classList.remove("hidden", "text-green-500");
        errorEl.classList.add("text-red-500");
        return;
      }

      button.disabled = true;
      button.textContent = "확인 중...";

      try {
        const checkUrl = document.body.dataset.checkUsernameUrl;

        const response = await fetch(checkUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: username }),
        });

        const data = await response.json();

        if (data.available) {
          errorEl.textContent = data.message;
          errorEl.classList.remove("hidden", "text-red-500");
          errorEl.classList.add("text-green-500");

          formData.username = username;

          setTimeout(() => {
            currentStep++;
            showStep(currentStep);
            errorEl.classList.add("hidden");
            button.textContent = "다음";
          }, 1000);
        } else {
          // 아이디 중복 또는 오류
          errorEl.textContent = data.message;
          errorEl.classList.remove("hidden", "text-green-500");
          errorEl.classList.add("text-red-500");
          button.disabled = false;
          button.textContent = "다음";
        }
      } catch (error) {
        console.error("아이디 확인 중 오류:", error);
        errorEl.textContent = "아이디 확인 중 오류가 발생했습니다.";
        errorEl.classList.remove("hidden", "text-green-500");
        errorEl.classList.add("text-red-500");
        button.disabled = false;
        button.textContent = "다음";
      }

      return;
    case 2:
      formData.password = document.getElementById("password").value;
      formData.confirmPassword =
        document.getElementById("confirm-password").value;
      break;
    case 3:
      formData.name = document.getElementById("name").value;
      break;
    case 4:
      const year = document.getElementById("birth-year").value;
      const month = document
        .getElementById("birth-month")
        .value.padStart(2, "0");
      const day = document.getElementById("birth-day").value.padStart(2, "0");
      formData.birthDate = `${year}-${month}-${day}`;
      break;
    case 6:
      formData.nickname = document.getElementById("nickname").value;
      break;
    case 7:
      formData.phone = document.getElementById("phone").value;
      break;
    case 8:
      formData.sido = document.getElementById("sido").value;
      formData.sigungu = document.getElementById("sigungu").value;
      formData.dong = document.getElementById("dong").value;

      // 모든 데이터를 hidden input에 저장하고 폼 제출
      document.getElementById("final-username").value = formData.username;
      document.getElementById("final-password").value = formData.password;
      document.getElementById("final-confirm-password").value =
        formData.confirmPassword;
      document.getElementById("final-name").value = formData.name;
      document.getElementById("final-birth-date").value = formData.birthDate;
      document.getElementById("final-gender").value = formData.gender;
      document.getElementById("final-nickname").value = formData.nickname;
      document.getElementById("final-phone").value = formData.phone;
      document.getElementById("final-sido").value = formData.sido;
      document.getElementById("final-sigungu").value = formData.sigungu;
      document.getElementById("final-dong").value = formData.dong;

      currentStep++;
      showStep(currentStep);
      document.getElementById("next-button-container").style.display = "none";

      // 폼 제출
      setTimeout(() => {
        document.getElementById("register-form").submit();
      }, 2000);
      return;
  }

  if (currentStep < totalSteps) {
    currentStep++;
    showStep(currentStep);
  }
}

// 전화번호 자동 포맷팅
document.getElementById("phone").addEventListener("input", function (e) {
  let value = e.target.value.replace(/[^0-9]/g, "");
  let formattedValue = "";

  if (value.length <= 3) {
    formattedValue = value;
  } else if (value.length <= 7) {
    formattedValue = value.slice(0, 3) + "-" + value.slice(3);
  } else {
    formattedValue =
      value.slice(0, 3) + "-" + value.slice(3, 7) + "-" + value.slice(7, 11);
  }

  e.target.value = formattedValue;
  updateNextButton();
});

// 입력 이벤트 리스너
document.getElementById("username").addEventListener("input", updateNextButton);
document.getElementById("password").addEventListener("input", updateNextButton);
document
  .getElementById("confirm-password")
  .addEventListener("input", updateNextButton);
document.getElementById("name").addEventListener("input", updateNextButton);
document.getElementById("nickname").addEventListener("input", updateNextButton);
document.getElementById("sido").addEventListener("change", updateNextButton);
document.getElementById("sigungu").addEventListener("change", updateNextButton);
document.getElementById("dong").addEventListener("change", updateNextButton);

document.getElementById("username").addEventListener("input", function () {
  const errorEl = document.getElementById("username-error");
  if (errorEl && !errorEl.classList.contains("hidden")) {
    errorEl.classList.add("hidden");
    errorEl.classList.remove("text-green-500", "text-red-500");
  }
});

// Enter 키로 다음 단계
document.querySelectorAll("input").forEach((input) => {
  input.addEventListener("keypress", function (e) {
    if (e.key === "Enter" && !document.getElementById("next-button").disabled) {
      e.preventDefault();
      nextStep();
    }
  });
});
