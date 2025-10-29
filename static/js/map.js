// 지도 페이지 JavaScript

// DOM
const container = document.getElementById("map");

// 상태
let map = null;
const markers = [];
let clusterer = null; // 클러스터러
let currentLocationMarker = null; // 현재 위치 마커
let currentFilter = "all"; // 현재 필터 상태
const infoWindow = new kakao.maps.InfoWindow({ removable: true }); // 단일 재사용

// 유틸: 안전 숫자 변환
const toNumber = (v) => {
  const n = Number(v);
  return Number.isFinite(n) ? n : NaN;
};

// 유틸: 인포윈도우 내부 onclick 파라미터에 넣을 문자열 이스케이프
const escapeForAttr = (s) => String(s ?? "").replace(/'/g, "\\'");

// 마커 생성 (파란색 위치 핀)
function createMarker(position, title) {
  const imageSrc =
    "data:image/svg+xml;base64," +
    btoa(`
    <svg width="24" height="30" viewBox="0 0 24 30" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 0C5.7 0 0.6 5.1 0.6 11.4C0.6 19.2 12 30 12 30C12 30 23.4 19.2 23.4 11.4C23.4 5.1 18.3 0 12 0Z" fill="#023591" stroke="white" stroke-width="1.2"/>
      <circle cx="12" cy="11.4" r="4.8" fill="white"/>
    </svg>
  `);
  const imageSize = new kakao.maps.Size(24, 30);
  const imageOption = { offset: new kakao.maps.Point(12, 30) };
  const markerImage = new kakao.maps.MarkerImage(
    imageSrc,
    imageSize,
    imageOption
  );

  return new kakao.maps.Marker({
    position,
    map,
    title: title ?? "",
    image: markerImage,
  });
}

// 현재 위치 마커 생성
function createCurrentLocationMarker(position) {
  // 현재 위치 마커용 커스텀 이미지 생성 (파스텔 톤 파란색 핀)
  const imageSrc =
    "data:image/svg+xml;base64," +
    btoa(`
    <svg width="24" height="30" viewBox="0 0 24 30" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 0C5.7 0 0.6 5.1 0.6 11.4C0.6 19.2 12 30 12 30C12 30 23.4 19.2 23.4 11.4C23.4 5.1 18.3 0 12 0Z" fill="#4A9EFF" stroke="white" stroke-width="1.2"/>
      <circle cx="12" cy="11.4" r="4.8" fill="white"/>
    </svg>
  `);
  const imageSize = new kakao.maps.Size(24, 30);
  const imageOption = { offset: new kakao.maps.Point(12, 30) };
  const markerImage = new kakao.maps.MarkerImage(
    imageSrc,
    imageSize,
    imageOption
  );

  return new kakao.maps.Marker({
    position,
    map,
    title: "📍 내 현재 위치",
    image: markerImage,
  });
}

// 현재 위치 마커 업데이트 (정확도 정보 포함)
function updateCurrentLocation(position, accuracy = null) {
  if (currentLocationMarker) {
    currentLocationMarker.setMap(null);
  }
  currentLocationMarker = createCurrentLocationMarker(position);

  // 현재 위치 마커 클릭 시 인포윈도우 (정확도 정보 포함)
  kakao.maps.event.addListener(currentLocationMarker, "click", () => {
    const accuracyText = accuracy ? `${Math.round(accuracy)}m` : "측정 중...";
    const statusColor =
      accuracy < 50 ? "#4CAF50" : accuracy < 100 ? "#FF9800" : "#F44336";
    const statusText =
      accuracy < 50
        ? "🟢 매우 정확"
        : accuracy < 100
        ? "🟡 보통 정확"
        : "🔴 정확도 낮음";

    const content = `
      <div class="info-window">
        <div class="title">📍 내 현재 위치</div>
        <div class="details">
          <strong>📌 상태</strong>
          <span>현재 있는 위치입니다</span>
        </div>
        <div class="details">
          <strong>📏 정확도</strong>
          <span style="color: ${statusColor}; font-weight: 600;">${accuracyText}</span>
        </div>
        <div class="details">
          <strong>✅ 신뢰도</strong>
          <span style="font-size: 12px;">${statusText}</span>
        </div>
      </div>
    `;
    infoWindow.setContent(content);
    infoWindow.open(map, currentLocationMarker);
  });
}

// 네비게이션 호출(모바일: 카카오내비, PC: 카카오맵 길찾기)
function navigateTo(lat, lng, name) {
  const safeName = encodeURIComponent(name ?? "");
  const isMobile = /Mobi/i.test(navigator.userAgent);

  if (isMobile) {
    const url = `kakaonavi-sdk://navigate?destination=${safeName}&x=${lng}&y=${lat}&coord_type=wgs84`;
    window.location.href = url;
  } else {
    const url = `https://map.kakao.com/link/to/${safeName},${lat},${lng}`;
    window.open(url, "_blank", "noopener,noreferrer");
  }
}
window.navigateTo = navigateTo; // 인포윈도우 버튼에서 호출

// 채팅방으로 이동하는 함수
async function goToChat(jobId) {
  try {
    const response = await fetch(`/chat/find-room/${jobId}`, {
      method: "GET",
    });
    const data = await response.json();
    if (data.success && data.room_id) {
      window.location.href = `/chat/${data.room_id}`;
    } else {
      alert("채팅방을 찾을 수 없습니다.");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("채팅방 이동 중 오류가 발생했습니다.");
  }
}
window.goToChat = goToChat; // 전역으로 노출

// 공고 지원하기 함수
async function applyJob(jobId) {
  if (
    !confirm(
      "이 공고에 지원하시겠습니까?\n지원하면 자동으로 채팅방이 생성됩니다."
    )
  ) {
    return;
  }
  try {
    const response = await fetch(`/jobs/${jobId}/apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "" }),
    });
    const data = await response.json();
    if (data.success) {
      alert(data.message);
      if (data.chat_room_id && confirm("채팅방으로 이동하시겠습니까?")) {
        window.location.href = `/chat/${data.chat_room_id}`;
      } else {
        location.reload();
      }
    } else {
      alert(data.message || "지원 중 오류가 발생했습니다.");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("지원 중 오류가 발생했습니다.");
  }
}
window.applyJob = applyJob; // 전역으로 노출

// 찜하기 토글 함수
async function toggleBookmark(jobId, button) {
  try {
    const response = await fetch(`/jobs/${jobId}/bookmark`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await response.json();

    if (data.success) {
      const svg = button.querySelector("svg");
      if (data.bookmarked) {
        // 찜 추가됨
        button.classList.remove("text-gray-400");
        button.classList.add("text-red-500");
        svg.setAttribute("fill", "currentColor");
      } else {
        // 찜 제거됨
        button.classList.remove("text-red-500");
        button.classList.add("text-gray-400");
        svg.setAttribute("fill", "none");
      }
    } else {
      alert(data.message || "찜하기 중 오류가 발생했습니다.");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("찜하기 중 오류가 발생했습니다.");
  }
}
window.toggleBookmark = toggleBookmark; // 전역으로 노출

// 기존 마커 제거 (현재 위치 마커는 유지)
function clearMarkers() {
  if (clusterer) {
    clusterer.clear();
  }
  for (const m of markers) m.setMap(null);
  markers.length = 0;
}

// 인포윈도우 템플릿
function buildInfoContent(job) {
  const title = job.title ?? "";
  const company = job.company || "정보 없음";
  const salary =
    typeof job.salary === "number"
      ? job.salary.toLocaleString("ko-KR") + "원"
      : job.salary || "협의";

  const lat = toNumber(job.lat);
  const lng = toNumber(job.lng);

  // 이모지 아이콘 추가
  const companyIcon = "🏢";
  const salaryIcon = "💰";
  const navIcon = "🧭";

  return `
    <div class="info-window">
      <div class="title">${title}</div>
      <div class="details">
        <strong>${companyIcon} 회사</strong>
        <span>${company}</span>
      </div>
      <div class="details">
        <strong>${salaryIcon} 급여</strong>
        <span class="salary">${salary}</span>
      </div>
      <button onclick="navigateTo(${lat}, ${lng}, '${escapeForAttr(
    title
  )}')">${navIcon} 길찾기</button>
    </div>
  `;
}

// 필터 변경 함수
function filterJobs(type) {
  currentFilter = type;

  // 버튼 활성화 상태 변경
  document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.classList.remove("active");
  });
  document
    .getElementById(`filter${type.charAt(0).toUpperCase() + type.slice(1)}`)
    .classList.add("active");

  // 데이터 다시 로드
  loadAllJobs();
}
window.filterJobs = filterJobs; // 전역으로 노출

// 전역 변수로 모든 공고 데이터 저장
let allJobs = [];
let searchQuery = ""; // 검색어 저장

// 검색 기능
function searchJobs(query) {
  searchQuery = query.toLowerCase().trim();

  if (!searchQuery) {
    // 검색어가 없으면 현재 보이는 영역의 공고 표시
    updateVisibleJobList();
    return;
  }

  // 전체 공고에서 검색
  const searchResults = allJobs.filter((job) => {
    const title = (job.title || "").toLowerCase();
    const company = (job.company || "").toLowerCase();
    const nickname = (job.author?.nickname || "").toLowerCase();

    return (
      title.includes(searchQuery) ||
      company.includes(searchQuery) ||
      nickname.includes(searchQuery)
    );
  });

  // 검색 결과 표시
  updateJobList(searchResults);

  // 검색 결과가 있으면 첫 번째 결과로 지도 이동
  if (
    searchResults.length > 0 &&
    searchResults[0].lat &&
    searchResults[0].lng
  ) {
    const firstResult = searchResults[0];
    const position = new kakao.maps.LatLng(firstResult.lat, firstResult.lng);
    map.setCenter(position);
    map.setLevel(5); // 줌 레벨 조정
  }
}

// 검색 입력 필드 이벤트 리스너 설정
function initSearchInput() {
  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    // 입력할 때마다 검색 (디바운싱 적용)
    let searchTimeout;
    searchInput.addEventListener("input", (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        searchJobs(e.target.value);
      }, 300); // 300ms 대기 후 검색
    });

    // Enter 키 누르면 즉시 검색
    searchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        clearTimeout(searchTimeout);
        searchJobs(e.target.value);
      }
    });
  }
}

// 데이터 로드 및 마커 렌더링
async function loadAllJobs() {
  try {
    const res = await fetch(`/jobs_all?type=${currentFilter}`, {
      credentials: "same-origin",
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    clearMarkers();
    infoWindow.close();

    const jobs = Array.isArray(data?.jobs) ? data.jobs : [];
    allJobs = jobs; // 전역 변수에 저장

    if (jobs.length === 0) {
      console.log("표시할 일자리가 없습니다.");
      updateJobList([]);
      return;
    }

    for (const job of jobs) {
      const lat = toNumber(job.lat);
      const lng = toNumber(job.lng);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) continue;

      const pos = new kakao.maps.LatLng(lat, lng);
      const marker = createMarker(pos, job.title);

      // 마커에 job 데이터 저장
      marker.jobData = job;

      kakao.maps.event.addListener(marker, "click", () => {
        infoWindow.setContent(buildInfoContent(job));
        infoWindow.open(map, marker);
      });

      markers.push(marker);
    }

    // 초기 공고 목록 업데이트
    updateVisibleJobList();

    // 클러스터러 생성 및 마커 추가
    if (clusterer) {
      clusterer.clear();
    }

    clusterer = new kakao.maps.MarkerClusterer({
      map: map,
      markers: markers,
      gridSize: 60,
      averageCenter: true,
      minLevel: 6,
      disableClickZoom: false,
      calculator: [10, 30, 50],
      styles: [
        {
          width: "40px",
          height: "40px",
          background: "#023591",
          borderRadius: "50%",
          color: "#fff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "12px",
          fontWeight: "bold",
          border: "3px solid white",
          boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
        },
        {
          width: "50px",
          height: "50px",
          background: "#2D71EB",
          borderRadius: "50%",
          color: "#fff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "14px",
          fontWeight: "bold",
          border: "3px solid white",
          boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
        },
        {
          width: "60px",
          height: "60px",
          background: "#1d4ed8",
          borderRadius: "50%",
          color: "#fff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "16px",
          fontWeight: "bold",
          border: "3px solid white",
          boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
        },
      ],
    });

    const filterText =
      currentFilter === "all"
        ? "전체"
        : currentFilter === "company"
        ? "기업 이음"
        : "사람 이음";
    console.log(
      `${filterText}: ${markers.length}개의 일자리 마커가 표시되었습니다.`
    );
  } catch (err) {
    console.error("일자리 데이터 불러오기 실패:", err);
    alert("일자리를 불러오는 중 오류가 발생했습니다.");
  }
}

// 지도 생성 공통
function createMapAndLoad(center, userLocation = null, accuracy = null) {
  map = new kakao.maps.Map(container, { center, level: 7 });

  // 지도 이동/줌 이벤트 리스너 추가
  kakao.maps.event.addListener(map, "idle", () => {
    updateVisibleJobList();
  });

  loadAllJobs();

  if (userLocation) {
    updateCurrentLocation(userLocation, accuracy);
    startLocationTracking();
  }
}

// 위치 추적 시작
function startLocationTracking() {
  if (!navigator.geolocation) {
    console.warn("브라우저가 위치 서비스를 지원하지 않습니다.");
    return;
  }

  if (navigator.permissions) {
    navigator.permissions.query({ name: "geolocation" }).then((result) => {
      console.log("위치 권한 상태:", result.state);
    });
  }

  const watchId = navigator.geolocation.watchPosition(
    (pos) => {
      const accuracy = pos.coords.accuracy;
      const speed = pos.coords.speed;
      const timestamp = new Date(pos.timestamp);

      console.log(
        `위치 업데이트: 정확도 ${Math.round(
          accuracy
        )}m, 시간 ${timestamp.toLocaleTimeString()}`
      );
      if (speed !== null) {
        console.log(`이동 속도: ${Math.round(speed * 3.6)}km/h`);
      }

      if (accuracy > 1000) {
        console.warn("위치 정확도가 낮아 업데이트를 건너뜁니다.");
        return;
      }

      const position = new kakao.maps.LatLng(
        pos.coords.latitude,
        pos.coords.longitude
      );
      updateCurrentLocation(position, accuracy);

      if ((accuracy < 200 && map) || !currentLocationMarker) {
        map.setCenter(position);
      }
    },
    (err) => {
      console.error("위치 추적 오류:", err);
      let errorMsg = "";
      switch (err.code) {
        case err.PERMISSION_DENIED:
          errorMsg =
            "위치 액세스가 거부되었습니다. 브라우저 설정에서 위치 권한을 허용해주세요.";
          break;
        case err.POSITION_UNAVAILABLE:
          errorMsg = "위치 정보를 사용할 수 없습니다.";
          break;
        case err.TIMEOUT:
          errorMsg = "위치 정보 요청 시간이 초과되었습니다.";
          break;
      }
      console.warn(errorMsg);
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 1000,
    }
  );

  window.addEventListener("beforeunload", () => {
    navigator.geolocation.clearWatch(watchId);
  });
}

// 위치 권한 요청
async function requestLocationPermission() {
  if (!navigator.geolocation) {
    console.warn("브라우저가 위치 서비스를 지원하지 않습니다.");
    return false;
  }

  if (navigator.permissions) {
    try {
      const permission = await navigator.permissions.query({
        name: "geolocation",
      });
      console.log("현재 위치 권한 상태:", permission.state);

      if (permission.state === "denied") {
        alert(
          "위치 서비스가 차단되어 있습니다.\n브라우저 주소창 왼쪽의 자물쇠 아이콘을 클릭하여 위치 권한을 허용해주세요."
        );
        return false;
      }
    } catch (e) {
      console.log("권한 API 지원하지 않음");
    }
  }

  return true;
}

// 초기화
async function initMap() {
  const fallback = new kakao.maps.LatLng(37.5665, 126.978);

  const hasLocationPermission = await requestLocationPermission();
  if (!hasLocationPermission) {
    createMapAndLoad(fallback);
    return;
  }

  console.log("정확한 위치 정보를 위해 위치 권한을 허용해주세요.");

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const accuracy = pos.coords.accuracy;
      console.log(`초기 위치 정확도: ${accuracy}m`);
      console.log(
        `위도: ${pos.coords.latitude}, 경도: ${pos.coords.longitude}`
      );

      const center = new kakao.maps.LatLng(
        pos.coords.latitude,
        pos.coords.longitude
      );
      createMapAndLoad(center, center, accuracy);

      if (accuracy > 100) {
        console.warn(
          `위치 정확도가 낮습니다 (${accuracy}m). WiFi나 GPS를 활성화하면 더 정확한 위치를 얻을 수 있습니다.`
        );
      }
    },
    (err) => {
      console.error("초기 위치 정보 오류:", err);
      let errorMsg = "위치 정보를 가져올 수 없어 서울 시청으로 설정합니다.";

      switch (err.code) {
        case err.PERMISSION_DENIED:
          errorMsg =
            "위치 액세스가 거부되었습니다. 브라우저 설정에서 위치 권한을 허용하고 페이지를 새로고침해주세요.";
          alert(errorMsg);
          break;
        case err.POSITION_UNAVAILABLE:
          errorMsg =
            "위치 정보를 사용할 수 없습니다. GPS나 WiFi를 확인해주세요.";
          break;
        case err.TIMEOUT:
          errorMsg =
            "위치 정보 요청 시간이 초과되었습니다. 네트워크 연결을 확인해주세요.";
          break;
      }
      console.warn(errorMsg);
      createMapAndLoad(fallback);
    },
    {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 0,
    }
  );
}

// 부트스트랩
initMap();
initSearchInput();

// 얼굴 토글 스위치
let isToggleActive = false;

function updateToggleTheme() {
  const toggle = document.getElementById("face-toggle");
  const body = document.body;
  const container = document.getElementById("toggleContainer");

  if (toggle.checked) {
    body.classList.add("toggle-active");
    container.classList.add("active");
    isToggleActive = true;

    setTimeout(() => {
      window.location.href = "/toggle-page";
    }, 1000);
  } else {
    body.classList.remove("toggle-active");
    container.classList.remove("active");
    isToggleActive = false;
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.getElementById("face-toggle");
  const urlParams = new URLSearchParams(window.location.search);

  if (urlParams.get("reset_toggle") === "true") {
    toggle.checked = false;
    updateToggleTheme();
  }

  toggle.addEventListener("change", updateToggleTheme);
  updateToggleTheme();
});

// 지도의 보이는 영역 내의 공고만 필터링
function updateVisibleJobList() {
  if (!map) return;

  // 검색 중이면 검색 결과 유지
  if (searchQuery) {
    return;
  }

  const bounds = map.getBounds();
  const visibleJobs = [];

  for (const marker of markers) {
    const position = marker.getPosition();
    if (bounds.contain(position)) {
      visibleJobs.push(marker.jobData);
    }
  }

  updateJobList(visibleJobs);
}

// 공고 목록 패널 관련 함수
function updateJobList(jobs) {
  const jobList = document.getElementById("jobList");
  const jobCount = document.getElementById("jobCount");

  if (!jobs || jobs.length === 0) {
    jobList.innerHTML =
      '<p class="text-gray-500 text-center py-8">표시할 공고가 없습니다.</p>';
    jobCount.textContent = "0";
    return;
  }

  jobCount.textContent = jobs.length;

  jobList.innerHTML = jobs
    .map((job) => {
      // 기업 이음인지 사람 이음인지 구분
      const isCompany =
        job.type === "company" || job.author?.user_type === 1 || job.company;
      const company = job.company || job.author?.nickname || "정보 없음";
      const companyInitial = company[0] || (isCompany ? "기" : "사");

      // 급여 표시 (main.html과 동일)
      const salary = isCompany
        ? "월급 " + (job.salary || "3,000,000원")
        : job.salary || "50,000원";

      // 날짜/시간 표시 (main.html과 동일)
      let dateStr = "";

      if (isCompany) {
        // 기업 이음: 마감일 표시 (recruitment_end_date 또는 created_at 사용)
        const endDate = job.recruitment_end_date
          ? new Date(job.recruitment_end_date)
          : job.created_at
          ? new Date(job.created_at)
          : null;
        if (endDate && !isNaN(endDate.getTime())) {
          const month = String(endDate.getMonth() + 1).padStart(2, "0");
          const day = String(endDate.getDate()).padStart(2, "0");
          const dayNames = ["일", "월", "화", "수", "목", "금", "토"];
          const dayName = dayNames[endDate.getDay()];
          dateStr = `~${month}/${day} (${dayName})`;
        }
      } else {
        // 사람 이음: 상대 시간 표시 (calculate_time_ago와 동일한 로직)
        if (job.created_at) {
          const date = new Date(job.created_at);
          if (!isNaN(date.getTime())) {
            const now = new Date();
            const diff = Math.floor((now - date) / 1000);
            if (diff < 60) dateStr = "방금 전";
            else if (diff < 3600) dateStr = `${Math.floor(diff / 60)}분 전`;
            else if (diff < 86400)
              dateStr = `${Math.floor(diff / 3600)}시간 전`;
            else dateStr = `${Math.floor(diff / 86400)}일 전`;
          }
        }
      }

      // 상세 페이지 URL (main.html과 동일)
      const detailUrl = isCompany ? `/company/${job.id}` : `/jobs/${job.id}`;

      // 북마크 상태 (main.html과 동일)
      const bookmarkClass = job.bookmarked ? "text-red-500" : "text-gray-400";
      const bookmarkFill = job.bookmarked ? "currentColor" : "none";

      return `
        <div class="bg-white rounded-2xl p-4 shadow-sm border mb-3 cursor-pointer" onclick="location.href='${detailUrl}'">
          <!-- 행[0]: 프로필사진, 회사명/작성자명, 날짜 -->
          <div class="flex items-center justify-between mb-1">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 text-sm font-bold">
                ${companyInitial}
              </div>
              <p class="text-sm text-gray-600">${company}</p>
            </div>
            <p class="text-xs text-gray-500">${dateStr}</p>
          </div>

          <!-- 행[1]: 공고명, 하트 버튼 -->
          <div class="flex items-center justify-between mb-1">
            <h3 class="font-bold text-lg">${job.title || "제목 없음"}</h3>
            <button class="${bookmarkClass} hover:text-red-500" onclick="event.stopPropagation(); toggleBookmark(${
        job.id
      }, this);">
              <svg class="w-6 h-6" fill="${bookmarkFill}" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/>
              </svg>
            </button>
          </div>

          <!-- 행[2]: 급여 -->
          <div class="mb-2">
            <p class="text-blue-600 font-bold">${salary}</p>
          </div>

          <!-- 행[3]: 카테고리, 지원하기 버튼 -->
          <div class="flex items-center justify-between">
            <div class="flex space-x-2">
              ${
                isCompany
                  ? `<span class="bg-gray-100 text-gray-700 text-sm px-3 py-1 rounded-full">${
                      job.recruitment_type || "정직원"
                    }</span>
                     <span class="bg-gray-100 text-gray-700 text-sm px-3 py-1 rounded-full">${
                       job.work_period || "상주직"
                     }</span>`
                  : `<span class="bg-gray-100 text-gray-700 text-sm px-3 py-1 rounded-full">오늘</span>
                     <span class="bg-gray-100 text-gray-700 text-sm px-3 py-1 rounded-full">${
                       job.work_period || "시간대별"
                     }</span>`
              }
            </div>
            ${
              job.applied
                ? `<button class="bg-green-500 text-white font-bold py-2 px-4 rounded-full text-sm" onclick="event.stopPropagation(); goToChat(${job.id})">
                     채팅하기
                   </button>`
                : `<button class="text-white font-bold py-2 px-4 rounded-full text-sm" style="background-color: #023591" onclick="event.stopPropagation(); applyJob(${job.id})">
                     지원하기
                   </button>`
            }
          </div>
        </div>
      `;
    })
    .join("");
}

// 공고 상세 보기는 HTML onclick에서 직접 처리

// 패널 드래그 기능
let startY = 0;
let startHeight = 0;
let isDragging = false;

const panel = document.getElementById("jobListPanel");
const dragHandle = panel?.querySelector(".drag-handle");

if (dragHandle) {
  dragHandle.addEventListener("mousedown", startDrag);
  dragHandle.addEventListener("touchstart", startDrag);
}

function startDrag(e) {
  isDragging = true;
  startY = e.type === "touchstart" ? e.touches[0].clientY : e.clientY;
  startHeight = panel.offsetHeight;

  document.addEventListener("mousemove", onDrag);
  document.addEventListener("mouseup", stopDrag);
  document.addEventListener("touchmove", onDrag);
  document.addEventListener("touchend", stopDrag);
}

function onDrag(e) {
  if (!isDragging) return;

  const currentY = e.type === "touchmove" ? e.touches[0].clientY : e.clientY;
  const diff = startY - currentY;
  const newHeight = startHeight + diff;

  const minHeight = window.innerHeight * 0.2;
  const maxHeight = window.innerHeight * 0.7;

  if (newHeight >= minHeight && newHeight <= maxHeight) {
    panel.style.maxHeight = `${newHeight}px`;
  }
}

function stopDrag() {
  isDragging = false;
  document.removeEventListener("mousemove", onDrag);
  document.removeEventListener("mouseup", stopDrag);
  document.removeEventListener("touchmove", onDrag);
  document.removeEventListener("touchend", stopDrag);
}
