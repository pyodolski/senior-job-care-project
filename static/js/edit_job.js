// AI 어시스턴트 함수
function openAIAssistant() {
  // 현재 입력된 값들을 AI 모달에 미리 채우기
  const title = document.getElementById("title").value;
  const salary = document.getElementById("salary").value;
  const description = document.getElementById("description").value;

  document.getElementById("aiTitle").value = title;
  document.getElementById("aiSalary").value = salary;
  document.getElementById("aiJobContent").value = description.substring(0, 100); // 처음 100글자만

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

  // 로딩 표시
  document.getElementById("aiLoading").classList.remove("hidden");
  document.getElementById("aiPreview").classList.add("hidden");

  try {
    // AI 생성 기능이 현재 사용 불가능한 경우 기본 템플릿 제공
    const generatedText = `【${title}】

📋 주요 업무
${jobContent}

💰 급여 조건
${salary || "협의"}

📌 자격 요건
${requirements || "경력 무관, 성실하고 책임감 있는 분"}

🏢 근무 환경
- 깔끔하고 쾌적한 근무 환경
- 동료들과의 원활한 소통
- 체계적인 업무 시스템

📞 지원 방법
관심 있으신 분은 연락 부탁드립니다.
성실하고 열정적인 분들의 많은 지원 바랍니다.`;

    // 미리보기 표시
    document.getElementById("aiPreviewContent").textContent = generatedText;
    document.getElementById("aiPreview").classList.remove("hidden");
    document.getElementById("aiApplyBtn").classList.remove("hidden");

    // 나중에 사용하기 위해 저장
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
    document.getElementById("description").value = window.aiGeneratedText;
    alert("내용이 적용되었습니다.");
    closeAIModal();
  }
}

// 모집 형태 선택
function selectRecruitmentType(button, value) {
  document
    .querySelectorAll(".btn-option[data-value]")
    .forEach((btn) => btn.classList.remove("active"));
  button.classList.add("active");
  document.getElementById("recruitment_type").value = value;

  const workPeriodGroup = document.getElementById("work_period_group");
  if (value === "일용직") {
    workPeriodGroup.style.display = "block";
    document.getElementById("work_period").required = true;
  } else {
    workPeriodGroup.style.display = "none";
    document.getElementById("work_period").required = false;
    document.getElementById("work_period").value = "";
    document
      .querySelectorAll("#work_period_group .btn-option")
      .forEach((btn) => btn.classList.remove("active"));
  }
}

// 근무 기간 선택
function selectWorkPeriod(button, value) {
  document
    .querySelectorAll("#work_period_group .btn-option")
    .forEach((btn) => btn.classList.remove("active"));
  button.classList.add("active");
  document.getElementById("work_period").value = value;
}

// 요일 선택 토글
function toggleDay(button) {
  button.classList.toggle("option-selected");
  const day = button.getAttribute("data-day");
  const hiddenInput = document.getElementById("work_" + day);
  hiddenInput.value = button.classList.contains("option-selected")
    ? "true"
    : "false";
}

// 전화번호 자동 포맷팅
document.addEventListener("DOMContentLoaded", function () {
  const contactPhone = document.getElementById("contact_phone");
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
    });
  }

  // 폼 제출 전 검증
  const jobForm = document.getElementById("jobForm");
  if (jobForm) {
    jobForm.addEventListener("submit", function (e) {
      const recruitmentType = document.getElementById("recruitment_type").value;
      const workPeriod = document.getElementById("work_period").value;

      if (!recruitmentType) {
        alert("모집 형태를 선택해주세요");
        e.preventDefault();
        return;
      }

      if (recruitmentType === "일용직" && !workPeriod) {
        alert("근무 기간을 선택해주세요");
        e.preventDefault();
        return;
      }
    });
  }
});

// 지도 관련 변수
let addressMap = null;
let addressMarker = null;
let selectedPosition = null;
let geocoder = null;
let ps = null;

// 카카오 맵 초기화 (DOMContentLoaded 후)
document.addEventListener("DOMContentLoaded", function () {
  if (typeof kakao !== "undefined" && kakao.maps) {
    geocoder = new kakao.maps.services.Geocoder();
    ps = new kakao.maps.services.Places();
  }
});

// 주소 검색 모달 열기
function openAddressModal() {
  document.getElementById("addressModal").classList.remove("hidden");
  if (!addressMap) {
    setTimeout(() => {
      initAddressMap();
    }, 100);
  }
}

// 지도 초기화
function initAddressMap() {
  const container = document.getElementById("addressMap");
  const options = {
    center: new kakao.maps.LatLng(35.8242, 128.7569),
    level: 5,
  };

  addressMap = new kakao.maps.Map(container, options);

  addressMarker = new kakao.maps.Marker({
    position: addressMap.getCenter(),
    map: addressMap,
  });
  selectedPosition = addressMap.getCenter();

  kakao.maps.event.addListener(addressMap, "click", function (mouseEvent) {
    const latlng = mouseEvent.latLng;
    addressMarker.setPosition(latlng);
    selectedPosition = latlng;

    // 좌표로 주소 검색
    geocoder.coord2Address(
      latlng.getLng(),
      latlng.getLat(),
      function (result, status) {
        if (status === kakao.maps.services.Status.OK) {
          const address =
            result[0].road_address?.address_name ||
            result[0].address?.address_name;
          document.getElementById("selectedAddressText").textContent = address;
          document.getElementById("confirmAddressBtn").disabled = false;
        }
      }
    );
  });
}

// 주소 검색
function searchAddress() {
  const keyword = document.getElementById("addressSearchKeyword").value.trim();
  if (!keyword) {
    alert("검색어를 입력해주세요");
    return;
  }

  ps.keywordSearch(keyword, function (data, status) {
    if (status === kakao.maps.services.Status.OK) {
      const firstItem = data[0];
      const moveLatLon = new kakao.maps.LatLng(firstItem.y, firstItem.x);

      addressMap.setCenter(moveLatLon);
      addressMarker.setPosition(moveLatLon);
      selectedPosition = moveLatLon;

      document.getElementById("selectedAddressText").textContent =
        firstItem.address_name;
      document.getElementById("confirmAddressBtn").disabled = false;
    } else {
      alert("검색 결과가 없습니다");
    }
  });
}

// 주소 선택 완료
async function selectAddress() {
  if (!selectedPosition) {
    alert("지도에서 위치를 선택해주세요");
    return;
  }

  const lat = selectedPosition.getLat();
  const lng = selectedPosition.getLng();

  document.getElementById("latitude").value = lat;
  document.getElementById("longitude").value = lng;

  try {
    const addrResult = await new Promise((resolve, reject) => {
      geocoder.coord2Address(lng, lat, (result, status) => {
        status === kakao.maps.services.Status.OK ? resolve(result) : reject();
      });
    });

    const regionResult = await new Promise((resolve, reject) => {
      geocoder.coord2RegionCode(lng, lat, (result, status) => {
        status === kakao.maps.services.Status.OK ? resolve(result) : reject();
      });
    });

    const roadAddr = addrResult[0].road_address?.address_name || "";
    const jibunAddr = addrResult[0].address?.address_name || "";
    const selectedAddr = roadAddr || jibunAddr;

    // 주소 입력 필드에 값 설정
    const regionInput = document.getElementById("region");
    regionInput.value = selectedAddr;

    // 입력 필드가 업데이트되었음을 시각적으로 표시
    regionInput.classList.add("bg-blue-50");
    setTimeout(() => {
      regionInput.classList.remove("bg-blue-50");
    }, 500);

    const legalRegion =
      regionResult.find((r) => r.region_type === "B") || regionResult[0];
    document.getElementById("region_1depth_name").value =
      legalRegion.region_1depth_name;
    document.getElementById("region_2depth_name").value =
      legalRegion.region_2depth_name;
    document.getElementById("region_3depth_name").value =
      legalRegion.region_3depth_name;

    closeAddressModal();
  } catch (error) {
    console.error("주소 변환 중 오류 발생:", error);
    alert("주소 정보를 가져오는 데 실패했습니다");
  }
}

// 주소 검색 모달 닫기
function closeAddressModal() {
  document.getElementById("addressModal").classList.add("hidden");
}
