let currentStep = 1;
const totalSteps = 8;
const formData = {};

// 지도 관련 변수
let companyMap = null;
let companyMarker = null;
let companyGeocoder = null;
let selectedCompanyLocation = null;

// 뒤로가기
function goBack() {
  if (currentStep === 1) {
    window.location.href = FIRST_LOGIN_URL;
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
          document
            .getElementById("password-error")
            .classList.remove("hidden");
        } else {
          document
            .getElementById("password-error")
            .classList.add("hidden");
        }
      } else {
        document
          .getElementById("confirm-password-container")
          .classList.add("hidden");
        isValid = false;
      }
      break;
    case 3:
      isValid =
        document.getElementById("company-name").value.trim() !== "";
      break;
    case 4:
      isValid =
        document.getElementById("manager-name").value.trim() !== "";
      break;
    case 5:
      const email = document.getElementById("email").value.trim();
      // 이메일 형식 체크
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      isValid = email !== "" && emailRegex.test(email);
      break;
    case 6:
      // 지도에서 선택한 주소가 있는지 확인
      isValid =
        selectedCompanyLocation !== null &&
        document.getElementById("company-sido").value !== "" &&
        document.getElementById("company-sigungu").value !== "" &&
        document.getElementById("company-dong").value !== "";
      break;
    case 7:
      // 파일이 선택되었는지 확인
      const fileInput = document.getElementById("business_registration");
      isValid = fileInput.files.length > 0;
      break;
  }

  if (isValid) {
    button.disabled = false;
    button.classList.remove("bg-gray-300", "text-gray-500");
    button.classList.add(
      "bg-blue-900",
      "text-white",
      "hover:bg-blue-800"
    );
  } else {
    button.disabled = true;
    button.classList.add("bg-gray-300", "text-gray-500");
    button.classList.remove(
      "bg-blue-900",
      "text-white",
      "hover:bg-blue-800"
    );
  }
}

// 다음 단계로
function nextStep() {
  // 현재 단계 데이터 저장
  switch (currentStep) {
    case 1:
      formData.username = document.getElementById("username").value;
      break;
    case 2:
      formData.password = document.getElementById("password").value;
      formData.confirmPassword =
        document.getElementById("confirm-password").value;
      break;
    case 3:
      formData.companyName =
        document.getElementById("company-name").value;
      break;
    case 4:
      formData.managerName =
        document.getElementById("manager-name").value;
      break;
    case 5:
      formData.email = document.getElementById("email").value;
      break;
    case 6:
      formData.companySido =
        document.getElementById("company-sido").value;
      formData.companySigungu =
        document.getElementById("company-sigungu").value;
      formData.companyDong =
        document.getElementById("company-dong").value;
      formData.companyFullAddress = document.getElementById(
        "company-full-address"
      ).value;
      break;
    case 7:
      // 모든 데이터를 hidden input에 저장하고 폼 제출
      document.getElementById("final-username").value = formData.username;
      document.getElementById("final-password").value = formData.password;
      document.getElementById("final-confirm-password").value =
        formData.confirmPassword;
      document.getElementById("final-nickname").value =
        formData.companyName;
      document.getElementById("final-name").value = formData.managerName;
      document.getElementById("final-email").value = formData.email;
      document.getElementById("final-company-sido").value =
        formData.companySido;
      document.getElementById("final-company-sigungu").value =
        formData.companySigungu;
      document.getElementById("final-company-dong").value =
        formData.companyDong;
      document.getElementById("final-company-full-address").value =
        formData.companyFullAddress;

      currentStep++;
      showStep(currentStep);
      document.getElementById("next-button-container").style.display =
        "none";

      // 폼 제출
      setTimeout(() => {
        document.getElementById("company-register-form").submit();
      }, 2000);
      return;
  }

  if (currentStep < totalSteps) {
    currentStep++;
    showStep(currentStep);
  }
}

// ===== 지도 관련 함수들 =====

// 회사 주소 지도 모달 열기
function openCompanyMapModal() {
  document.getElementById("company-map-modal").classList.remove("hidden");

  // 지도가 아직 초기화되지 않았으면 초기화
  if (!companyMap) {
    initCompanyMap();
  } else {
    // 이미 초기화된 경우 지도 크기 재조정
    setTimeout(function () {
      companyMap.relayout();
    }, 100);
  }
}

// 회사 주소 지도 모달 닫기
function closeCompanyMapModal() {
  document.getElementById("company-map-modal").classList.add("hidden");
}

// 회사 주소 지도 초기화
function initCompanyMap() {
  const container = document.getElementById("company-map");

  // 먼저 기본 위치로 지도 생성
  const defaultPosition = new kakao.maps.LatLng(37.5665, 126.978); // 서울 시청
  const options = {
    center: defaultPosition,
    level: 3,
  };

  companyMap = new kakao.maps.Map(container, options);
  companyGeocoder = new kakao.maps.services.Geocoder();

  // 현재 위치 가져오기
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function (position) {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        const locPosition = new kakao.maps.LatLng(lat, lng);

        // 지도 중심을 현재 위치로 이동
        companyMap.setCenter(locPosition);

        // 지도 크기 재설정 (위치 이동 후)
        setTimeout(function () {
          companyMap.relayout();
        }, 100);

        // 마커 생성
        if (!companyMarker) {
          companyMarker = new kakao.maps.Marker({
            position: locPosition,
            map: companyMap,
          });
        } else {
          companyMarker.setPosition(locPosition);
        }

        // 현재 위치의 주소 가져오기
        getCompanyAddressFromCoords(lat, lng);
      },
      function (error) {
        console.log("현재 위치를 가져올 수 없습니다:", error);
        // 기본 위치(서울 시청)에 마커 표시
        companyMarker = new kakao.maps.Marker({
          position: defaultPosition,
          map: companyMap,
        });
        getCompanyAddressFromCoords(37.5665, 126.978);
      }
    );
  } else {
    // Geolocation을 지원하지 않는 경우 기본 위치 사용
    companyMarker = new kakao.maps.Marker({
      position: defaultPosition,
      map: companyMap,
    });
    getCompanyAddressFromCoords(37.5665, 126.978);
  }

  // 지도 클릭 이벤트
  kakao.maps.event.addListener(
    companyMap,
    "click",
    function (mouseEvent) {
      const latlng = mouseEvent.latLng;
      const lat = latlng.getLat();
      const lng = latlng.getLng();

      // 마커 이동
      if (!companyMarker) {
        companyMarker = new kakao.maps.Marker({
          position: latlng,
          map: companyMap,
        });
      } else {
        companyMarker.setPosition(latlng);
      }

      // 주소 가져오기
      getCompanyAddressFromCoords(lat, lng);
    }
  );
}

// 회사 주소 좌표로 주소 가져오기
function getCompanyAddressFromCoords(lat, lng) {
  companyGeocoder.coord2Address(lng, lat, function (result, status) {
    if (status === kakao.maps.services.Status.OK) {
      const address = result[0].address;
      const roadAddress = result[0].road_address;

      // 주소 파싱
      const sido = address.region_1depth_name; // 시/도
      const sigungu = address.region_2depth_name; // 시/군/구
      let dong = address.region_3depth_name; // 읍/면/동

      // dong이 없는 경우 (예: 세종특별자치시)
      if (!dong || dong === "") {
        dong = address.region_3depth_h_name || sigungu;
      }

      // 전체 주소
      const fullAddress = address.address_name;

      // 표시용 주소 (시/도 시/군/구 읍/면/동)
      let displayAddress = sido + " " + sigungu;
      if (dong && dong !== sigungu) {
        displayAddress += " " + dong;
      }

      // 선택된 위치 정보 저장
      selectedCompanyLocation = {
        lat: lat,
        lng: lng,
        fullAddress: fullAddress,
        displayAddress: displayAddress,
        sido: sido,
        sigungu: sigungu,
        dong: dong,
      };

      // 화면에 표시
      document.getElementById("company-selected-address").textContent =
        fullAddress;

      // 확인 버튼 활성화
      const confirmBtn = document.getElementById(
        "company-confirm-location-btn"
      );
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

// 회사 위치 확인 버튼 클릭
function confirmCompanyLocation() {
  if (selectedCompanyLocation) {
    // 주소 정보를 hidden input에 저장
    document.getElementById("company-sido").value =
      selectedCompanyLocation.sido;
    document.getElementById("company-sigungu").value =
      selectedCompanyLocation.sigungu;
    document.getElementById("company-dong").value =
      selectedCompanyLocation.dong;
    document.getElementById("company-full-address").value =
      selectedCompanyLocation.fullAddress;

    // 화면에 표시
    document.getElementById("company-address-search").value =
      selectedCompanyLocation.displayAddress;

    // 모달 닫기
    closeCompanyMapModal();

    // 다음 버튼 활성화 체크
    updateNextButton();
  }
}

// 입력 이벤트 리스너
document
  .getElementById("username")
  .addEventListener("input", updateNextButton);
document
  .getElementById("password")
  .addEventListener("input", updateNextButton);
document
  .getElementById("confirm-password")
  .addEventListener("input", updateNextButton);
document
  .getElementById("company-name")
  .addEventListener("input", updateNextButton);
document
  .getElementById("manager-name")
  .addEventListener("input", updateNextButton);
document
  .getElementById("email")
  .addEventListener("input", updateNextButton);
document
  .getElementById("business_registration")
  .addEventListener("change", updateNextButton);

// Enter 키로 다음 단계
document.querySelectorAll("input").forEach((input) => {
  input.addEventListener("keypress", function (e) {
    if (
      e.key === "Enter" &&
      !document.getElementById("next-button").disabled
    ) {
      e.preventDefault();
      nextStep();
    }
  });
});
