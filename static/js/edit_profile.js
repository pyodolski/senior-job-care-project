// 지도 관련 변수
let map = null;
let marker = null;
let geocoder = null;
let selectedLocation = null;

// 페이지 로드 시 초기 주소 표시
document.addEventListener("DOMContentLoaded", function () {
  const sido = document.getElementById("sido").value;
  const sigungu = document.getElementById("sigungu").value;
  const dong = document.getElementById("dong").value;

  if (sido && sigungu && dong) {
    document.getElementById("address-search").value = `${sido} ${sigungu} ${dong}`;
    document.getElementById("full-address").textContent = `${sido} ${sigungu} ${dong}`;

    // Hidden input에도 설정
    document.getElementById("final-sido").value = sido;
    document.getElementById("final-sigungu").value = sigungu;
    document.getElementById("final-dong").value = dong;
  }
});

// 뒤로가기
function goBack() {
  window.location.href = window.authProfileUrl;
}

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

      // 선택된 위치 정보 저장
      selectedLocation = {
        lat: lat,
        lng: lng,
        displayAddress: displayAddress, // 읍/면/동까지만
        sido: sido,
        sigungu: sigungu,
        dong: dong,
      };

      // 화면에 표시 (읍/면/동까지만)
      document.getElementById("selected-address").textContent =
        displayAddress;

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

    document.getElementById("final-sido").value = selectedLocation.sido;
    document.getElementById("final-sigungu").value = selectedLocation.sigungu;
    document.getElementById("final-dong").value = selectedLocation.dong;

    // 화면에 표시 (읍/면/동까지만)
    document.getElementById("address-search").value =
      selectedLocation.displayAddress;
    document.getElementById("full-address").textContent =
      selectedLocation.displayAddress;

    // 모달 닫기
    closeMapModal();
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
      value.slice(0, 3) +
      "-" +
      value.slice(3, 7) +
      "-" +
      value.slice(7, 11);
  }

  e.target.value = formattedValue;
});
