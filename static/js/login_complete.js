// Login Complete Page JavaScript

// Enhanced page state management system
const pageState = {
  currentPage: "jobs",
  previousPage: null,
  isTransitioning: false,
  transitionDuration: 300,
  pages: {
    profile: {
      title: "내 정보",
      active: false,
      loaded: false,
      requiresAuth: true,
      redirectUrl: "/profile",
      icon: "👤",
    },
    jobs: {
      title: "구인구직",
      active: true,
      loaded: false,
      requiresAuth: false,
      icon: "💼",
    },
    community: {
      title: "커뮤니티",
      active: false,
      loaded: false,
      requiresAuth: false,
      icon: "💬",
    },
  },
  history: ["jobs"],
  maxHistoryLength: 10,
};

// Page state management functions
const stateManager = {
  // Get current page state
  getCurrentPage() {
    return pageState.pages[pageState.currentPage];
  },

  // Update page state
  updatePageState(pageId, updates) {
    if (pageState.pages[pageId]) {
      Object.assign(pageState.pages[pageId], updates);
      this.notifyStateChange(pageId, updates);
    }
  },

  // Set current page
  setCurrentPage(pageId) {
    if (pageState.pages[pageId] && !pageState.isTransitioning) {
      pageState.previousPage = pageState.currentPage;
      pageState.currentPage = pageId;

      // Update history
      if (pageState.history[pageState.history.length - 1] !== pageId) {
        pageState.history.push(pageId);
        if (pageState.history.length > pageState.maxHistoryLength) {
          pageState.history.shift();
        }
      }

      // Update all page states
      Object.keys(pageState.pages).forEach((key) => {
        pageState.pages[key].active = key === pageId;
      });

      this.notifyStateChange(pageId, { active: true });
      return true;
    }
    return false;
  },

  // Check if page can be accessed
  canAccessPage(pageId) {
    const page = pageState.pages[pageId];
    if (!page) return false;

    // Add authentication check here if needed
    if (page.requiresAuth) {
      // For now, assume user is authenticated
      return true;
    }

    return true;
  },

  // Get page history
  getHistory() {
    return [...pageState.history];
  },

  // Go back to previous page
  goBack() {
    if (pageState.history.length > 1) {
      pageState.history.pop(); // Remove current page
      const previousPageId = pageState.history[pageState.history.length - 1];
      return this.setCurrentPage(previousPageId);
    }
    return false;
  },

  // State change notification (for debugging and extensions)
  notifyStateChange(pageId, changes) {
    console.log(`Page state changed: ${pageId}`, changes);

    // Dispatch custom event for other components to listen
    window.dispatchEvent(
      new CustomEvent("pageStateChange", {
        detail: { pageId, changes, currentState: pageState },
      })
    );
  },

  // Reset state to initial
  reset() {
    pageState.currentPage = "jobs";
    pageState.previousPage = null;
    pageState.isTransitioning = false;
    pageState.history = ["jobs"];

    Object.keys(pageState.pages).forEach((key) => {
      pageState.pages[key].active = key === "jobs";
    });
  },
};

// Enhanced navigation handling with smooth transitions
function handleNavigation(pageId) {
  try {
    // Check if page can be accessed
    if (!stateManager.canAccessPage(pageId)) {
      console.warn(`Access denied to page: ${pageId}`);
      showErrorMessage("페이지에 접근할 수 없습니다.");
      return;
    }

    // Handle profile page redirect
    if (pageId === "profile") {
      redirectToProfile();
      return;
    }

    // Prevent navigation during transition
    if (pageState.isTransitioning) {
      console.log("Navigation blocked: transition in progress");
      return;
    }

    // Load content dynamically if not loaded yet
    if (!pageState.pages[pageId].loaded) {
      loadPageContent(pageId);
    } else {
      // Switch to the selected page with animation
      switchPage(pageId);
    }
  } catch (error) {
    console.error("Navigation error:", error);
    showErrorMessage("페이지 이동 중 오류가 발생했습니다.");
    showDefaultPage();
  }
}

// Load page content dynamically
async function loadPageContent(pageId) {
  try {
    // Show loading state
    const pageElement = document.getElementById(`content-${pageId}`);
    if (!pageElement) {
      throw new Error(`Page element not found: content-${pageId}`);
    }

    // Set loading state
    pageElement.innerHTML = `
      <div class="content-loading">
        <div class="loading-spinner"></div>
        <div class="loading-text">${pageState.pages[pageId].title} 정보를 불러오는 중...</div>
      </div>
    `;

    // Determine API endpoint
    let apiEndpoint;
    switch (pageId) {
      case "jobs":
        apiEndpoint = "/api/components/jobs";
        break;
      case "community":
        apiEndpoint = "/api/components/community";
        break;
      default:
        throw new Error(`Unknown page: ${pageId}`);
    }

    // Fetch content from server
    const response = await fetch(apiEndpoint, {
      method: "GET",
      headers: {
        "Content-Type": "text/html",
      },
      credentials: "same-origin",
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const content = await response.text();

    // Update page content
    pageElement.innerHTML = content;

    // Mark as loaded
    stateManager.updatePageState(pageId, { loaded: true });

    // Enhance accessibility for dynamically loaded content
    enhanceAccessibilityForPage(pageId);

    // Ensure clean page switch
    ensureSinglePageVisibility(pageId);

    // Switch to the page
    switchPage(pageId);

    console.log(`Successfully loaded content for page: ${pageId}`);
  } catch (error) {
    console.error(`Failed to load content for page ${pageId}:`, error);

    // Show error state
    const pageElement = document.getElementById(`content-${pageId}`);
    if (pageElement) {
      pageElement.innerHTML = `
        <div class="content-error">
          <div class="error-icon">⚠️</div>
          <div class="error-message">
            <h3>콘텐츠를 불러올 수 없습니다</h3>
            <p>네트워크 연결을 확인하고 다시 시도해주세요.</p>
            <button class="retry-button" onclick="loadPageContent('${pageId}')">다시 시도</button>
          </div>
        </div>
      `;
    }

    showErrorMessage(
      `${pageState.pages[pageId].title} 페이지를 불러올 수 없습니다.`
    );
  }
}

// Enhanced page switching with smooth animations
function switchPage(pageId) {
  try {
    if (!pageState.pages[pageId]) {
      throw new Error(`Page ${pageId} not found`);
    }

    // Set transition state
    pageState.isTransitioning = true;

    // Ensure only one page is visible - immediate fix for overlapping issue
    ensureSinglePageVisibility(pageId);

    const targetPageElement = document.getElementById(`content-${pageId}`);

    if (!targetPageElement) {
      throw new Error(`Page element not found: content-${pageId}`);
    }

    // Add smooth transition effect
    targetPageElement.classList.add("entering");

    setTimeout(() => {
      targetPageElement.classList.remove("entering");
      pageState.isTransitioning = false;
    }, pageState.transitionDuration);

    // Update navigation active state with animation
    updateNavigationState(pageId);

    // Update page state using state manager
    stateManager.setCurrentPage(pageId);

    // Update document title
    updateDocumentTitle(pageState.pages[pageId].title);
  } catch (error) {
    console.error("Page switching error:", error);
    pageState.isTransitioning = false;
    showDefaultPage();
  }
}

// Update navigation visual state
function updateNavigationState(pageId) {
  document.querySelectorAll(".nav-icon").forEach((icon) => {
    icon.classList.remove("active");

    // Add smooth transition effect
    if (icon.getAttribute("data-page") === pageId) {
      setTimeout(() => {
        icon.classList.add("active");
      }, 50);
    }
  });
}

// Update document title
function updateDocumentTitle(pageTitle) {
  document.title = `${pageTitle} - 메인 페이지`;
}

// Ensure only one page is visible at a time
function ensureSinglePageVisibility(activePageId) {
  // Hide all pages first
  document.querySelectorAll(".content-page").forEach((page) => {
    page.style.display = "none";
    page.classList.remove("active", "entering", "exiting");
  });

  // Show only the active page
  const activePage = document.getElementById(`content-${activePageId}`);
  if (activePage) {
    activePage.style.display = "block";
    activePage.classList.add("active");
  }

  console.log(`Ensured only page ${activePageId} is visible`);
}

// Show error message to user
function showErrorMessage(message) {
  // Create temporary error message element
  const errorDiv = document.createElement("div");
  errorDiv.style.cssText = `
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: #dc3545;
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    font-size: 14px;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    animation: slideDown 0.3s ease;
  `;
  errorDiv.textContent = message;

  document.body.appendChild(errorDiv);

  // Remove after 3 seconds
  setTimeout(() => {
    errorDiv.style.animation = "slideUp 0.3s ease";
    setTimeout(() => {
      if (errorDiv.parentNode) {
        errorDiv.parentNode.removeChild(errorDiv);
      }
    }, 300);
  }, 3000);
}

// Enhanced profile page redirect with error handling
function redirectToProfile() {
  try {
    // Show loading state
    const profileIcon = document.querySelector('[data-page="profile"]');
    if (profileIcon) {
      profileIcon.classList.add("disabled");
      const originalText = profileIcon.querySelector(".label").textContent;
      profileIcon.querySelector(".label").textContent = "이동 중...";

      // Restore original state after timeout
      setTimeout(() => {
        profileIcon.classList.remove("disabled");
        profileIcon.querySelector(".label").textContent = originalText;
      }, 5000);
    }

    // Get profile URL from page state or use default
    const profileUrl = pageState.pages.profile.redirectUrl || "/profile";

    // Add loading indicator
    showLoadingMessage("프로필 페이지로 이동 중...");

    // Attempt redirect with timeout
    const redirectTimeout = setTimeout(() => {
      handleRedirectError("페이지 이동 시간이 초과되었습니다.");
    }, 5000);

    // Check if URL is accessible before redirect
    fetch(profileUrl, { method: "HEAD" })
      .then((response) => {
        clearTimeout(redirectTimeout);
        if (response.ok || response.status === 405) {
          // 405 is acceptable for HEAD requests
          window.location.href = profileUrl;
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
      })
      .catch((error) => {
        clearTimeout(redirectTimeout);
        console.error("Profile URL check failed:", error);
        // Try direct redirect anyway
        window.location.href = profileUrl;
      });
  } catch (error) {
    console.error("Profile redirect error:", error);
    handleRedirectError("프로필 페이지로 이동할 수 없습니다.");
  }
}

// Handle redirect errors
function handleRedirectError(message) {
  // Remove loading message
  hideLoadingMessage();

  // Re-enable profile icon
  const profileIcon = document.querySelector('[data-page="profile"]');
  if (profileIcon) {
    profileIcon.classList.remove("disabled");
    profileIcon.querySelector(".label").textContent = "내 정보";
  }

  // Show error message
  showErrorMessage(message);

  // Offer alternative action
  setTimeout(() => {
    if (confirm(`${message}\n\n다시 시도하시겠습니까?`)) {
      redirectToProfile();
    } else {
      // Return to home page
      handleNavigation("placeholder");
    }
  }, 1000);
}

// Show loading message
function showLoadingMessage(message) {
  const loadingDiv = document.createElement("div");
  loadingDiv.id = "loading-overlay";
  loadingDiv.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
    color: white;
    font-size: 16px;
    flex-direction: column;
    gap: 16px;
  `;

  loadingDiv.innerHTML = `
    <div class="loading-spinner" style="border-color: #f3f3f3; border-top-color: #007bff;"></div>
    <div>${message}</div>
  `;

  document.body.appendChild(loadingDiv);
}

// Hide loading message
function hideLoadingMessage() {
  const loadingDiv = document.getElementById("loading-overlay");
  if (loadingDiv) {
    loadingDiv.remove();
  }
}

// Show default page on error
function showDefaultPage() {
  switchPage("jobs");
}

// Initialize logo display with enhanced fallback logic
function initializeLogo() {
  const logoImage = document.querySelector(".logo-image");
  const logoText = document.querySelector(".logo-text");
  const logoFallback = document.querySelector(".logo-fallback");
  const logoContainer = document.querySelector(".logo-container");
  let logoLoadAttempts = 0;
  const maxAttempts = 3;

  // Hide all logo elements initially
  logoImage.style.display = "none";
  logoText.style.display = "none";
  logoFallback.style.display = "none";

  // Add loading classes for smooth transition
  logoImage.classList.add("loading");
  logoContainer.classList.add("loading");

  // Set up load event listener for successful image loading
  logoImage.addEventListener("load", function () {
    console.log("Logo image loaded successfully");
    this.classList.remove("loading");
    logoContainer.classList.remove("loading");
    this.style.display = "block";
    logoText.style.display = "none";
    logoFallback.style.display = "none";
  });

  // Set up error event listener with multiple format retry logic
  logoImage.addEventListener("error", function () {
    logoLoadAttempts++;
    console.log(
      `Logo image failed to load (attempt ${logoLoadAttempts}/${maxAttempts})`
    );

    // Try different image formats in order: SVG -> PNG -> JPG
    if (logoLoadAttempts === 1 && this.src.includes(".svg")) {
      console.log("SVG failed, trying PNG logo");
      this.src = "/static/images/sample-logo.png";
    } else if (logoLoadAttempts === 2 && this.src.includes(".png")) {
      console.log("PNG failed, trying JPG logo");
      this.src = "/static/images/sample-logo.jpg";
    } else {
      // All image formats failed, show text or icon fallback
      console.log("All logo image formats failed, showing fallback");
      this.style.display = "none";
      this.classList.remove("loading");
      logoContainer.classList.remove("loading");
      showLogoFallback();
    }
  });

  // Set timeout for loading fallback (4 seconds to allow for retries)
  setTimeout(function () {
    if (logoImage.classList.contains("loading")) {
      console.log("Logo image loading timeout, showing fallback");
      logoImage.style.display = "none";
      logoImage.classList.remove("loading");
      logoContainer.classList.remove("loading");
      showLogoFallback();
    }
  }, 4000);

  // Function to show appropriate fallback
  function showLogoFallback() {
    // Check if logo text is available and not empty
    const logoTextContent = logoText.textContent.trim();
    if (logoTextContent && logoTextContent !== "Sample Logo") {
      // Show custom text logo if available
      logoText.style.display = "block";
      logoFallback.style.display = "none";
    } else {
      // Show icon fallback with default text
      logoText.style.display = "none";
      logoFallback.style.display = "flex";
    }
  }

  // Try to load the logo image (start with SVG since it exists)
  logoImage.src = "/static/images/sample-logo.svg";
}

// Initialize region display with API integration
function initializeRegionDisplay() {
  const regionDisplay = document.getElementById("region-display");
  const regionPlaceholder = document.getElementById("region-placeholder");
  const regionStatus = document.getElementById("region-status");

  // Early return if elements don't exist
  if (!regionPlaceholder) {
    console.log("Region placeholder element not found");
    return;
  }

  // Set initial loading state
  regionPlaceholder.textContent = "지역 정보를 불러오는 중...";
  if (regionStatus) {
    regionStatus.classList.add("loading");
    regionStatus.classList.remove("error", "success");
  }

  // Call the API to get user region information
  fetch("/api/user/region", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "same-origin",
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then((data) => {
      console.log("Region API response:", data);

      if (data.success && data.data) {
        // Successfully loaded region information
        const regionName = data.data.display_name || data.data.dong;
        regionPlaceholder.textContent = regionName;

        // Update status to success
        if (regionStatus) {
          regionStatus.classList.remove("loading", "error");
          regionStatus.classList.add("success");
        }

        // Add region info to region display if it exists
        if (regionDisplay) {
          regionDisplay.setAttribute("title", data.data.full_address);
          regionDisplay.setAttribute(
            "aria-label",
            `현재 지역: ${data.data.full_address}`
          );
        }

        console.log(`Successfully loaded region: ${regionName}`);
      } else {
        throw new Error(data.error || "알 수 없는 오류가 발생했습니다.");
      }
    })
    .catch((error) => {
      console.error("Region API error:", error);

      // Handle different error scenarios
      let errorMessage = "지역 정보 없음";
      let shouldRetry = false;

      if (
        error.message.includes("404") ||
        error.message.includes("REGION_NOT_SET")
      ) {
        errorMessage = "지역 미설정";
      } else if (
        error.message.includes("401") ||
        error.message.includes("AUTH_REQUIRED")
      ) {
        errorMessage = "로그인 필요";
      } else if (
        error.message.includes("500") ||
        error.message.includes("INTERNAL_ERROR")
      ) {
        errorMessage = "서버 오류";
        shouldRetry = true;
      } else if (
        error.name === "TypeError" ||
        error.message.includes("Failed to fetch")
      ) {
        errorMessage = "네트워크 오류";
        shouldRetry = true;
      }

      regionPlaceholder.textContent = errorMessage;

      // Update status to error
      if (regionStatus) {
        regionStatus.classList.remove("loading", "success");
        regionStatus.classList.add("error");
      }

      // Add retry functionality for certain errors
      if (shouldRetry) {
        setTimeout(() => {
          console.log("Retrying region display initialization...");
          initializeRegionDisplay();
        }, 5000); // Retry after 5 seconds
      }

      // Announce error to screen readers
      const liveRegion = document.getElementById("live-region");
      if (liveRegion) {
        liveRegion.textContent = `지역 정보 로딩 실패: ${errorMessage}`;
      }
    });
}

// Set up keyboard shortcuts
function setupKeyboardShortcuts() {
  document.addEventListener("keydown", function (e) {
    // Only handle shortcuts when not in input fields
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") {
      return;
    }

    // Number keys 1-3 for quick navigation
    if (e.key >= "1" && e.key <= "3") {
      e.preventDefault();
      const pageIds = ["jobs", "community", "profile"];
      const pageId = pageIds[parseInt(e.key) - 1];
      if (pageId) {
        handleNavigation(pageId);
      }
    }

    // Escape key to go back
    if (e.key === "Escape") {
      e.preventDefault();
      if (stateManager.goBack()) {
        console.log("Navigated back via keyboard");
      }
    }

    // Alt + J for jobs (default page)
    if (e.altKey && e.key === "j") {
      e.preventDefault();
      handleNavigation("jobs");
    }
  });
}

// Enhance accessibility attributes
function enhanceAccessibility() {
  // Add ARIA attributes to job cards
  document.querySelectorAll(".job-card").forEach((card, index) => {
    card.setAttribute("role", "article");
    card.setAttribute("aria-labelledby", `job-title-${index}`);
    card.setAttribute("tabindex", "0");

    const title = card.querySelector(".job-title");
    if (title) {
      title.id = `job-title-${index}`;
    }
  });

  // Add ARIA attributes to community posts
  document.querySelectorAll(".post-card").forEach((card, index) => {
    card.setAttribute("role", "article");
    card.setAttribute("aria-labelledby", `post-title-${index}`);
    card.setAttribute("tabindex", "0");

    const title = card.querySelector(".post-title");
    if (title) {
      title.id = `post-title-${index}`;
    }

    const author = card.querySelector(".post-author");
    if (author) {
      author.setAttribute("aria-label", `작성자: ${author.textContent}`);
    }
  });

  // Add ARIA attributes to post actions
  document.querySelectorAll(".post-action").forEach((action) => {
    const text = action.textContent.trim();
    action.setAttribute("aria-label", `${text} 버튼`);
    action.setAttribute("role", "button");
  });

  // Add live region for dynamic content updates
  const liveRegion = document.createElement("div");
  liveRegion.id = "live-region";
  liveRegion.setAttribute("aria-live", "polite");
  liveRegion.setAttribute("aria-atomic", "true");
  liveRegion.style.cssText =
    "position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden;";
  document.body.appendChild(liveRegion);

  // Announce page changes to screen readers
  window.addEventListener("pageStateChange", function (e) {
    const { pageId } = e.detail;
    const pageTitle = pageState.pages[pageId]?.title;
    if (pageTitle && liveRegion) {
      liveRegion.textContent = `${pageTitle} 페이지로 이동했습니다.`;
    }
  });

  console.log("Accessibility enhancements applied");
}

// Enhance accessibility for dynamically loaded page content
function enhanceAccessibilityForPage(pageId) {
  const pageElement = document.getElementById(`content-${pageId}`);
  if (!pageElement) return;

  if (pageId === "jobs") {
    // Add ARIA attributes to job cards
    pageElement.querySelectorAll(".job-card").forEach((card, index) => {
      card.setAttribute("role", "article");
      card.setAttribute("aria-labelledby", `job-title-${pageId}-${index}`);
      card.setAttribute("tabindex", "0");

      const title = card.querySelector(".job-title");
      if (title) {
        title.id = `job-title-${pageId}-${index}`;
      }
    });
  } else if (pageId === "community") {
    // Add ARIA attributes to community posts
    pageElement.querySelectorAll(".post-card").forEach((card, index) => {
      card.setAttribute("role", "article");
      card.setAttribute("aria-labelledby", `post-title-${pageId}-${index}`);
      card.setAttribute("tabindex", "0");

      const title = card.querySelector(".post-title");
      if (title) {
        title.id = `post-title-${pageId}-${index}`;
      }

      const author = card.querySelector(".post-author");
      if (author) {
        author.setAttribute("aria-label", `작성자: ${author.textContent}`);
      }
    });

    // Add ARIA attributes to post actions
    pageElement.querySelectorAll(".post-action").forEach((action) => {
      const text = action.textContent.trim();
      action.setAttribute("aria-label", `${text} 버튼`);
      action.setAttribute("role", "button");
    });
  }

  console.log(`Accessibility enhancements applied for page: ${pageId}`);
}

// Global error handling
window.addEventListener("error", function (e) {
  console.error("Global error caught:", e.error);
  showErrorMessage("페이지에서 오류가 발생했습니다. 새로고침을 시도해보세요.");

  // Reset to safe state
  setTimeout(() => {
    if (pageState.currentPage !== "placeholder") {
      showDefaultPage();
    }
  }, 3000);
});

window.addEventListener("unhandledrejection", function (e) {
  console.error("Unhandled promise rejection:", e.reason);
  showErrorMessage("네트워크 오류가 발생했습니다.");
  e.preventDefault();
});

// Enhanced error recovery
function recoverFromError() {
  try {
    // Reset page state
    stateManager.reset();

    // Clear any loading states
    hideLoadingMessage();

    // Re-enable all navigation icons
    document.querySelectorAll(".nav-icon").forEach((icon) => {
      icon.classList.remove("disabled");
      const label = icon.querySelector(".label");
      if (label) {
        const pageId = icon.getAttribute("data-page");
        const originalText =
          pageState.pages[pageId]?.title || label.textContent;
        label.textContent = originalText;
      }
    });

    // Show default page
    showDefaultPage();

    console.log("Error recovery completed");
  } catch (recoveryError) {
    console.error("Error during recovery:", recoveryError);
    // Last resort: reload page
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  }
}

// Browser compatibility checks and polyfills
(function () {
  // Check for essential features
  const hasRequiredFeatures =
    "querySelector" in document &&
    "addEventListener" in window &&
    "classList" in document.createElement("div");

  if (!hasRequiredFeatures) {
    // Fallback for very old browsers
    document.body.innerHTML =
      '<div style="padding: 20px; text-align: center; font-family: Arial, sans-serif;"><h2>브라우저 업데이트 필요</h2><p>이 페이지를 정상적으로 이용하려면 최신 브라우저가 필요합니다.</p></div>';
    return;
  }

  // Polyfill for CustomEvent (IE support)
  if (typeof window.CustomEvent !== "function") {
    function CustomEvent(event, params) {
      params = params || {
        bubbles: false,
        cancelable: false,
        detail: undefined,
      };
      var evt = document.createEvent("CustomEvent");
      evt.initCustomEvent(
        event,
        params.bubbles,
        params.cancelable,
        params.detail
      );
      return evt;
    }
    CustomEvent.prototype = window.Event.prototype;
    window.CustomEvent = CustomEvent;
  }

  // Polyfill for Object.assign (IE support)
  if (typeof Object.assign !== "function") {
    Object.assign = function (target) {
      if (target == null) {
        throw new TypeError("Cannot convert undefined or null to object");
      }
      var to = Object(target);
      for (var index = 1; index < arguments.length; index++) {
        var nextSource = arguments[index];
        if (nextSource != null) {
          for (var nextKey in nextSource) {
            if (Object.prototype.hasOwnProperty.call(nextSource, nextKey)) {
              to[nextKey] = nextSource[nextKey];
            }
          }
        }
      }
      return to;
    };
  }

  // Add fallback text for emoji icons
  document.addEventListener("DOMContentLoaded", function () {
    const icons = document.querySelectorAll(".nav-icon .icon");
    icons.forEach(function (icon) {
      const navIcon = icon.closest(".nav-icon");
      const pageId = navIcon.getAttribute("data-page");

      // Add fallback text as data attribute
      switch (pageId) {
        case "profile":
          icon.setAttribute("data-fallback", "[프로필]");
          break;
        case "jobs":
          icon.setAttribute("data-fallback", "[구직]");
          break;
        case "community":
          icon.setAttribute("data-fallback", "[커뮤니티]");
          break;
      }
    });
  });

  console.log("Browser compatibility checks completed");
})();

// Initialize page
document.addEventListener("DOMContentLoaded", function () {
  // Set up navigation event listeners with enhanced interaction
  document.querySelectorAll(".nav-icon").forEach((icon) => {
    // Click event
    icon.addEventListener("click", function (e) {
      e.preventDefault();
      const pageId = this.getAttribute("data-page");
      handleNavigation(pageId);
    });

    // Keyboard support (Enter and Space)
    icon.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        const pageId = this.getAttribute("data-page");
        handleNavigation(pageId);
      }
    });

    // Touch support for mobile
    icon.addEventListener("touchstart", function (e) {
      this.style.transform = "scale(0.95)";
    });

    icon.addEventListener("touchend", function (e) {
      this.style.transform = "";
    });

    // Focus and blur events for better accessibility
    icon.addEventListener("focus", function () {
      this.style.outline = "2px solid #007bff";
      this.style.outlineOffset = "2px";
    });

    icon.addEventListener("blur", function () {
      this.style.outline = "";
      this.style.outlineOffset = "";
    });
  });

  // Initialize logo display logic
  initializeLogo();

  // Initialize region display (placeholder for future implementation)
  initializeRegionDisplay();

  // Set up global keyboard shortcuts
  setupKeyboardShortcuts();

  // Initialize page state
  console.log("Page initialized with state:", pageState);

  // Enhance accessibility
  enhanceAccessibility();

  // Ensure clean initial state
  ensureSinglePageVisibility("jobs");

  // Load initial page content (jobs page)
  loadPageContent("jobs");
});

// Add CSS animations for error messages
const style = document.createElement("style");
style.textContent = `
  @keyframes slideDown {
    from { transform: translateX(-50%) translateY(-20px); opacity: 0; }
    to { transform: translateX(-50%) translateY(0); opacity: 1; }
  }
  @keyframes slideUp {
    from { transform: translateX(-50%) translateY(0); opacity: 1; }
    to { transform: translateX(-50%) translateY(-20px); opacity: 0; }
  }
`;
document.head.appendChild(style);
