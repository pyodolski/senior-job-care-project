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

    // Initialize page-specific functionality
    if (pageId === "jobs") {
      // Initialize jobs page functionality after content is loaded
      setTimeout(() => {
        initializeJobsPage();
      }, 100); // Small delay to ensure DOM is ready
    }

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

// ===== 구인구직 페이지 JavaScript 기능 시작 =====

// 구인구직 페이지 상태 관리
const jobsPageState = {
  currentView: "list", // 'list', 'form', 'detail'
  currentPage: 1,
  totalPages: 1,
  totalJobs: 0,
  editingJobId: null,
  viewingJobId: null,
  filters: {
    keyword: "",
    region: "",
    seniorOnly: false,
    ageMin: "",
    ageMax: "",
  },
  isLoading: false,
  hasUnsavedChanges: false,
};

// 구인구직 페이지가 로드된 후 호출되는 초기화 함수
function initializeJobsPage() {
  console.log("Initializing jobs page functionality");

  // 이벤트 리스너 설정
  setupJobsPageEventListeners();

  // 초기 공고 목록 로드
  loadJobsList();

  // 폼 검증 설정
  setupJobFormValidation();

  console.log("Jobs page initialized successfully");
}

// 구인구직 페이지 이벤트 리스너 설정
function setupJobsPageEventListeners() {
  const jobsContainer = document.getElementById("content-jobs");
  if (!jobsContainer) return;

  // 이벤트 위임을 사용하여 동적으로 생성되는 요소들의 이벤트 처리
  jobsContainer.addEventListener("click", function (e) {
    const target = e.target;

    // 새 공고 작성 버튼
    if (
      target.matches("#create-job-btn") ||
      target.closest("#create-job-btn")
    ) {
      e.preventDefault();
      showJobForm();
    }

    // 공고 목록 새로고침 버튼
    if (
      target.matches("#refresh-jobs-btn") ||
      target.closest("#refresh-jobs-btn")
    ) {
      e.preventDefault();
      refreshJobsList();
    }

    // 공고 상세 보기
    if (target.matches(".job-card") || target.closest(".job-card")) {
      e.preventDefault();
      const jobCard = target.closest(".job-card");
      const jobId = jobCard.getAttribute("data-job-id");
      if (jobId) {
        showJobDetail(jobId);
      }
    }

    // 공고 수정 버튼
    if (target.matches(".edit-job-btn") || target.closest(".edit-job-btn")) {
      e.preventDefault();
      const jobId = target.closest("[data-job-id]").getAttribute("data-job-id");
      editJob(jobId);
    }

    // 공고 삭제 버튼
    if (
      target.matches(".delete-job-btn") ||
      target.closest(".delete-job-btn")
    ) {
      e.preventDefault();
      const jobId = target.closest("[data-job-id]").getAttribute("data-job-id");
      deleteJob(jobId);
    }

    // 폼 제출 버튼
    if (
      target.matches("#submit-job-btn") ||
      target.closest("#submit-job-btn")
    ) {
      e.preventDefault();
      submitJobForm();
    }

    // 폼 취소 버튼
    if (
      target.matches("#cancel-job-btn") ||
      target.closest("#cancel-job-btn")
    ) {
      e.preventDefault();
      cancelJobForm();
    }

    // 목록으로 돌아가기 버튼
    if (
      target.matches("#back-to-list-btn") ||
      target.closest("#back-to-list-btn")
    ) {
      e.preventDefault();
      showJobsList();
    }

    // 페이지네이션 버튼
    if (
      target.matches(".pagination-btn") ||
      target.closest(".pagination-btn")
    ) {
      e.preventDefault();
      const page = parseInt(target.getAttribute("data-page"));
      if (page && page !== jobsPageState.currentPage) {
        loadJobsList(page);
      }
    }

    // 삭제 확인 모달의 버튼들
    if (target.matches("#confirm-delete-btn")) {
      e.preventDefault();
      confirmDeleteJob();
    }

    if (
      target.matches("#cancel-delete-btn") ||
      target.closest(".close-modal")
    ) {
      e.preventDefault();
      hideDeleteModal();
    }
  });

  // 검색 및 필터 이벤트
  jobsContainer.addEventListener("input", function (e) {
    const target = e.target;

    // 검색어 입력
    if (target.matches("#job-search-input")) {
      clearTimeout(target.searchTimeout);
      target.searchTimeout = setTimeout(() => {
        jobsPageState.filters.keyword = target.value.trim();
        loadJobsList(1); // 검색 시 첫 페이지로
      }, 500);
    }

    // 필터 변경
    if (target.matches("#region-filter")) {
      jobsPageState.filters.region = target.value;
      loadJobsList(1);
    }

    if (target.matches("#age-min-filter")) {
      jobsPageState.filters.ageMin = target.value;
      loadJobsList(1);
    }

    if (target.matches("#age-max-filter")) {
      jobsPageState.filters.ageMax = target.value;
      loadJobsList(1);
    }
  });

  // 체크박스 변경 이벤트
  jobsContainer.addEventListener("change", function (e) {
    const target = e.target;

    if (target.matches("#senior-only-filter")) {
      jobsPageState.filters.seniorOnly = target.checked;
      loadJobsList(1);
    }
  });

  // 폼 입력 변경 감지 (미저장 변경사항 경고용)
  jobsContainer.addEventListener("input", function (e) {
    if (e.target.closest("#job-form")) {
      jobsPageState.hasUnsavedChanges = true;
    }
  });
}

// 공고 목록 로드
async function loadJobsList(page = 1) {
  if (jobsPageState.isLoading) return;

  try {
    jobsPageState.isLoading = true;
    jobsPageState.currentPage = page;

    showJobsLoading();

    // API 요청 파라미터 구성
    const params = new URLSearchParams({
      page: page,
      ...jobsPageState.filters,
    });

    const response = await fetch(`/api/jobs/list?${params}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "same-origin",
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    if (data.success) {
      renderJobsList(data.data);
      updateJobsStats(data.pagination);
      jobsPageState.currentView = "list";
    } else {
      throw new Error(data.error || "공고 목록을 불러올 수 없습니다.");
    }
  } catch (error) {
    console.error("Error loading jobs list:", error);
    showJobsError("공고 목록을 불러오는 중 오류가 발생했습니다.");
  } finally {
    jobsPageState.isLoading = false;
    hideJobsLoading();
  }
}

// 공고 목록 렌더링
function renderJobsList(jobsData) {
  const { jobs, pagination } = jobsData;

  // 상태 업데이트
  jobsPageState.totalPages = pagination.total_pages;
  jobsPageState.totalJobs = pagination.total;

  // 목록 뷰 표시
  showJobsListView();

  // 공고 카드들 렌더링
  const jobsGrid = document.querySelector("#jobs-list-view .jobs-grid");
  if (!jobsGrid) return;

  if (jobs.length === 0) {
    jobsGrid.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📋</div>
        <h3>등록된 공고가 없습니다</h3>
        <p>첫 번째 구인공고를 작성해보세요!</p>
        <button class="create-job-btn" id="create-job-btn">
          <span class="btn-icon">➕</span>
          공고 작성하기
        </button>
      </div>
    `;
    return;
  }

  jobsGrid.innerHTML = jobs
    .map(
      (job) => `
    <div class="job-card" data-job-id="${job.id}" role="article" tabindex="0">
      <div class="job-header">
        <h3 class="job-title">${escapeHtml(job.title)}</h3>
        <div class="job-company">${escapeHtml(job.company)}</div>
      </div>
      <div class="job-content">
        <div class="job-description">${escapeHtml(job.description)}</div>
        <div class="job-details">
          ${
            job.preferred_age_min || job.preferred_age_max
              ? `
            <span class="job-age">
              <span class="detail-icon">👥</span>
              ${job.preferred_age_min || "제한없음"}세 - ${
                  job.preferred_age_max || "제한없음"
                }세
            </span>
          `
              : ""
          }
          ${
            job.region
              ? `
            <span class="job-region">
              <span class="detail-icon">📍</span>
              ${escapeHtml(job.region)}
            </span>
          `
              : ""
          }
          ${
            job.work_hours
              ? `
            <span class="job-hours">
              <span class="detail-icon">🕒</span>
              ${escapeHtml(job.work_hours)}
            </span>
          `
              : ""
          }
        </div>
      </div>
      <div class="job-footer">
        <div class="job-meta">
          <span class="job-date">${formatDate(job.created_at)}</span>
          ${
            job.is_senior_friendly
              ? '<span class="senior-badge">시니어 친화</span>'
              : ""
          }
        </div>
        <div class="job-actions">
          <button class="job-action view-job-btn" aria-label="공고 상세보기">
            자세히 보기
          </button>
        </div>
      </div>
    </div>
  `
    )
    .join("");

  // 페이지네이션 렌더링
  renderJobsPagination(pagination);
}

// 공고 상세 보기
async function showJobDetail(jobId) {
  try {
    jobsPageState.isLoading = true;
    showJobsLoading();

    const response = await fetch(`/api/jobs/${jobId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "same-origin",
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    if (data.success) {
      renderJobDetail(data.data);
      jobsPageState.currentView = "detail";
      jobsPageState.viewingJobId = jobId;
    } else {
      throw new Error(data.error || "공고 정보를 불러올 수 없습니다.");
    }
  } catch (error) {
    console.error("Error loading job detail:", error);
    showJobsError("공고 상세 정보를 불러오는 중 오류가 발생했습니다.");
  } finally {
    jobsPageState.isLoading = false;
    hideJobsLoading();
  }
}

// 공고 상세 정보 렌더링
function renderJobDetail(job) {
  showJobsDetailView();

  const detailContainer = document.querySelector(
    "#jobs-detail-view .job-detail-content"
  );
  if (!detailContainer) return;

  const currentUser = getCurrentUser(); // 현재 사용자 정보 가져오기
  const isAuthor = currentUser && currentUser.id === job.author_id;

  detailContainer.innerHTML = `
    <div class="job-detail-header">
      <h1 class="job-detail-title">${escapeHtml(job.title)}</h1>
      <div class="job-detail-company">${escapeHtml(job.company)}</div>
      ${
        job.is_senior_friendly
          ? '<span class="senior-badge">시니어 친화 기업</span>'
          : ""
      }
    </div>
    
    <div class="job-detail-body">
      <div class="job-detail-section">
        <h3>상세 설명</h3>
        <div class="job-detail-description">${escapeHtml(
          job.description
        ).replace(/\n/g, "<br>")}</div>
      </div>
      
      <div class="job-detail-info">
        <div class="info-grid">
          ${
            job.preferred_age_min || job.preferred_age_max
              ? `
            <div class="info-item">
              <span class="info-label">📊 선호 연령</span>
              <span class="info-value">${
                job.preferred_age_min || "제한없음"
              }세 - ${job.preferred_age_max || "제한없음"}세</span>
            </div>
          `
              : ""
          }
          ${
            job.region
              ? `
            <div class="info-item">
              <span class="info-label">📍 근무 지역</span>
              <span class="info-value">${escapeHtml(job.region)}</span>
            </div>
          `
              : ""
          }
          ${
            job.work_hours
              ? `
            <div class="info-item">
              <span class="info-label">🕒 근무 시간</span>
              <span class="info-value">${escapeHtml(job.work_hours)}</span>
            </div>
          `
              : ""
          }
          ${
            job.contact_phone
              ? `
            <div class="info-item">
              <span class="info-label">📞 연락처</span>
              <span class="info-value">${escapeHtml(job.contact_phone)}</span>
            </div>
          `
              : ""
          }
        </div>
      </div>
      
      <div class="job-detail-meta">
        <div class="meta-item">
          <span class="meta-label">작성일</span>
          <span class="meta-value">${formatDate(job.created_at)}</span>
        </div>
        ${
          job.updated_at !== job.created_at
            ? `
          <div class="meta-item">
            <span class="meta-label">수정일</span>
            <span class="meta-value">${formatDate(job.updated_at)}</span>
          </div>
        `
            : ""
        }
      </div>
    </div>
    
    <div class="job-detail-actions">
      ${
        isAuthor
          ? `
        <button class="btn btn-primary edit-job-btn" data-job-id="${job.id}">
          <span class="btn-icon">✏️</span>
          수정하기
        </button>
        <button class="btn btn-danger delete-job-btn" data-job-id="${job.id}">
          <span class="btn-icon">🗑️</span>
          삭제하기
        </button>
      `
          : ""
      }
      <button class="btn btn-secondary" id="back-to-list-btn">
        <span class="btn-icon">↩️</span>
        목록으로 돌아가기
      </button>
    </div>
  `;
}

// 공고 작성/수정 폼 표시
function showJobForm(jobData = null) {
  showJobsFormView();

  jobsPageState.currentView = "form";
  jobsPageState.editingJobId = jobData ? jobData.id : null;
  jobsPageState.hasUnsavedChanges = false;

  const formContainer = document.querySelector(
    "#jobs-form-view .job-form-content"
  );
  if (!formContainer) return;

  const isEdit = !!jobData;

  formContainer.innerHTML = `
    <div class="form-header">
      <h2>${isEdit ? "공고 수정" : "새 공고 작성"}</h2>
      <p>${
        isEdit ? "공고 정보를 수정해주세요." : "구인공고를 작성해주세요."
      }</p>
    </div>
    
    <form id="job-form" class="job-form">
      <div class="form-group">
        <label for="job-title-input" class="required">공고 제목</label>
        <input 
          type="text" 
          id="job-title-input" 
          name="title" 
          value="${jobData ? escapeHtml(jobData.title) : ""}"
          placeholder="예: 경험 많은 시니어 회계사 모집"
          maxlength="100"
          required
        >
        <div class="char-count">
          <span class="current">${jobData ? jobData.title.length : 0}</span>/100
        </div>
        <div class="error-message" id="title-error"></div>
      </div>
      
      <div class="form-group">
        <label for="job-company-input" class="required">회사명</label>
        <input 
          type="text" 
          id="job-company-input" 
          name="company" 
          value="${jobData ? escapeHtml(jobData.company) : ""}"
          placeholder="회사명을 입력해주세요"
          maxlength="50"
          required
        >
        <div class="char-count">
          <span class="current">${
            jobData ? jobData.company.length : 0
          }</span>/50
        </div>
        <div class="error-message" id="company-error"></div>
      </div>
      
      <div class="form-group">
        <label for="job-description-input" class="required">상세 설명</label>
        <textarea 
          id="job-description-input" 
          name="description" 
          placeholder="업무 내용, 자격 요건, 우대사항 등을 자세히 작성해주세요"
          maxlength="1000"
          rows="6"
          required
        >${jobData ? escapeHtml(jobData.description) : ""}</textarea>
        <div class="char-count">
          <span class="current">${
            jobData ? jobData.description.length : 0
          }</span>/1000
        </div>
        <div class="error-message" id="description-error"></div>
      </div>
      
      <div class="form-row">
        <div class="form-group">
          <label for="age-min-input">선호 최소 연령</label>
          <input 
            type="number" 
            id="age-min-input" 
            name="preferred_age_min" 
            value="${jobData ? jobData.preferred_age_min || "" : ""}"
            placeholder="예: 50"
            min="18"
            max="100"
          >
        </div>
        <div class="form-group">
          <label for="age-max-input">선호 최대 연령</label>
          <input 
            type="number" 
            id="age-max-input" 
            name="preferred_age_max" 
            value="${jobData ? jobData.preferred_age_max || "" : ""}"
            placeholder="예: 70"
            min="18"
            max="100"
          >
        </div>
      </div>
      
      <div class="form-group">
        <label for="job-region-input">근무 지역</label>
        <input 
          type="text" 
          id="job-region-input" 
          name="region" 
          value="${jobData ? escapeHtml(jobData.region || "") : ""}"
          placeholder="예: 서울시 강남구"
          maxlength="50"
        >
      </div>
      
      <div class="form-group">
        <label for="job-hours-input">근무 시간</label>
        <input 
          type="text" 
          id="job-hours-input" 
          name="work_hours" 
          value="${jobData ? escapeHtml(jobData.work_hours || "") : ""}"
          placeholder="예: 월-금 09:00-18:00"
          maxlength="100"
        >
      </div>
      
      <div class="form-group">
        <label for="job-phone-input">연락처</label>
        <input 
          type="tel" 
          id="job-phone-input" 
          name="contact_phone" 
          value="${jobData ? escapeHtml(jobData.contact_phone || "") : ""}"
          placeholder="예: 02-1234-5678"
          maxlength="20"
        >
      </div>
      
      <div class="form-group checkbox-group">
        <label class="checkbox-label">
          <input 
            type="checkbox" 
            id="senior-friendly-input" 
            name="is_senior_friendly" 
            ${jobData && jobData.is_senior_friendly ? "checked" : ""}
          >
          <span class="checkbox-text">시니어 친화적인 환경입니다</span>
        </label>
      </div>
      
      <div class="form-actions">
        <button type="button" class="btn btn-secondary" id="cancel-job-btn">
          취소
        </button>
        <button type="submit" class="btn btn-primary" id="submit-job-btn">
          ${isEdit ? "수정하기" : "등록하기"}
        </button>
      </div>
    </form>
  `;

  // 폼 검증 이벤트 리스너 추가
  setupJobFormValidation();
}

// 공고 폼 검증 설정
function setupJobFormValidation() {
  const form = document.getElementById("job-form");
  if (!form) return;

  // 실시간 문자 수 카운트
  form
    .querySelectorAll("input[maxlength], textarea[maxlength]")
    .forEach((input) => {
      input.addEventListener("input", function () {
        const charCount = this.closest(".form-group").querySelector(
          ".char-count .current"
        );
        if (charCount) {
          charCount.textContent = this.value.length;
        }
      });
    });

  // 폼 제출 검증
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    submitJobForm();
  });
}

// 공고 폼 제출
async function submitJobForm() {
  const form = document.getElementById("job-form");
  if (!form) return;

  try {
    // 폼 검증
    if (!validateJobForm()) {
      return;
    }

    const formData = new FormData(form);
    const jobData = Object.fromEntries(formData.entries());

    // 체크박스 처리
    jobData.is_senior_friendly = document.getElementById(
      "senior-friendly-input"
    ).checked;

    // 숫자 필드 처리
    if (jobData.preferred_age_min) {
      jobData.preferred_age_min = parseInt(jobData.preferred_age_min);
    }
    if (jobData.preferred_age_max) {
      jobData.preferred_age_max = parseInt(jobData.preferred_age_max);
    }

    const isEdit = !!jobsPageState.editingJobId;
    const url = isEdit
      ? `/api/jobs/${jobsPageState.editingJobId}/update`
      : "/api/jobs/create";
    const method = isEdit ? "PUT" : "POST";

    // 로딩 상태 표시
    const submitBtn = document.getElementById("submit-job-btn");
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="loading-spinner"></span> 처리 중...';

    const response = await fetch(url, {
      method: method,
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "same-origin",
      body: JSON.stringify(jobData),
    });

    const result = await response.json();

    if (result.success) {
      jobsPageState.hasUnsavedChanges = false;
      showSuccessMessage(
        isEdit
          ? "공고가 성공적으로 수정되었습니다."
          : "공고가 성공적으로 등록되었습니다."
      );

      // 목록으로 돌아가기
      await loadJobsList();
      showJobsList();
    } else {
      throw new Error(result.error || "공고 처리 중 오류가 발생했습니다.");
    }
  } catch (error) {
    console.error("Error submitting job form:", error);
    showJobsError(error.message);
  } finally {
    // 버튼 상태 복원
    const submitBtn = document.getElementById("submit-job-btn");
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  }
}

// 공고 폼 검증
function validateJobForm() {
  const form = document.getElementById("job-form");
  if (!form) return false;

  let isValid = true;

  // 필수 필드 검증
  const requiredFields = ["title", "company", "description"];
  requiredFields.forEach((fieldName) => {
    const field = form.querySelector(`[name="${fieldName}"]`);
    const errorElement = document.getElementById(`${fieldName}-error`);

    if (!field.value.trim()) {
      showFieldError(errorElement, "이 필드는 필수입니다.");
      isValid = false;
    } else {
      hideFieldError(errorElement);
    }
  });

  // 연령 범위 검증
  const ageMin = form.querySelector('[name="preferred_age_min"]').value;
  const ageMax = form.querySelector('[name="preferred_age_max"]').value;

  if (ageMin && ageMax && parseInt(ageMin) > parseInt(ageMax)) {
    showJobsError("최소 연령이 최대 연령보다 클 수 없습니다.");
    isValid = false;
  }

  return isValid;
}

// 필드 에러 표시
function showFieldError(errorElement, message) {
  if (errorElement) {
    errorElement.textContent = message;
    errorElement.style.display = "block";
  }
}

// 필드 에러 숨기기
function hideFieldError(errorElement) {
  if (errorElement) {
    errorElement.style.display = "none";
  }
}

// 공고 수정
async function editJob(jobId) {
  try {
    const response = await fetch(`/api/jobs/${jobId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "same-origin",
    });

    const result = await response.json();

    if (result.success) {
      showJobForm(result.data);
    } else {
      throw new Error(result.error || "공고 정보를 불러올 수 없습니다.");
    }
  } catch (error) {
    console.error("Error loading job for edit:", error);
    showJobsError("공고 수정을 위한 정보를 불러오는 중 오류가 발생했습니다.");
  }
}

// 공고 삭제
function deleteJob(jobId) {
  showDeleteModal(jobId);
}

// 삭제 확인 모달 표시
function showDeleteModal(jobId) {
  const modal = document.getElementById("delete-job-modal");
  if (!modal) {
    // 모달이 없으면 생성
    createDeleteModal();
  }

  const confirmBtn = document.getElementById("confirm-delete-btn");
  confirmBtn.setAttribute("data-job-id", jobId);

  modal.style.display = "flex";
  setTimeout(() => {
    modal.classList.add("show");
  }, 10);
}

// 삭제 모달 생성
function createDeleteModal() {
  const modal = document.createElement("div");
  modal.id = "delete-job-modal";
  modal.className = "modal-overlay";
  modal.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h3>공고 삭제 확인</h3>
        <button class="close-modal">&times;</button>
      </div>
      <div class="modal-body">
        <p>이 공고를 정말 삭제하시겠습니까?</p>
        <p class="warning-text">삭제된 공고는 복구할 수 없습니다.</p>
      </div>
      <div class="modal-actions">
        <button class="btn btn-secondary" id="cancel-delete-btn">취소</button>
        <button class="btn btn-danger" id="confirm-delete-btn">삭제하기</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
}

// 삭제 확인
async function confirmDeleteJob() {
  const confirmBtn = document.getElementById("confirm-delete-btn");
  const jobId = confirmBtn.getAttribute("data-job-id");

  try {
    const originalText = confirmBtn.textContent;
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<span class="loading-spinner"></span> 삭제 중...';

    const response = await fetch(`/api/jobs/${jobId}/delete`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "same-origin",
    });

    const result = await response.json();

    if (result.success) {
      hideDeleteModal();
      showSuccessMessage("공고가 성공적으로 삭제되었습니다.");

      // 목록으로 돌아가기
      await loadJobsList();
      showJobsList();
    } else {
      throw new Error(result.error || "공고 삭제 중 오류가 발생했습니다.");
    }
  } catch (error) {
    console.error("Error deleting job:", error);
    showJobsError(error.message);
  } finally {
    confirmBtn.disabled = false;
    confirmBtn.textContent = "삭제하기";
  }
}

// 삭제 모달 숨기기
function hideDeleteModal() {
  const modal = document.getElementById("delete-job-modal");
  if (modal) {
    modal.classList.remove("show");
    setTimeout(() => {
      modal.style.display = "none";
    }, 300);
  }
}

// 뷰 전환 함수들
function showJobsListView() {
  setJobsViewVisibility("list");
}

function showJobsFormView() {
  setJobsViewVisibility("form");
}

function showJobsDetailView() {
  setJobsViewVisibility("detail");
}

function setJobsViewVisibility(activeView) {
  const views = ["list", "form", "detail"];
  views.forEach((view) => {
    const element = document.getElementById(`jobs-${view}-view`);
    if (element) {
      element.style.display = view === activeView ? "block" : "none";
    }
  });
}

// 목록으로 돌아가기
function showJobsList() {
  if (jobsPageState.hasUnsavedChanges) {
    if (!confirm("저장하지 않은 변경사항이 있습니다. 정말 나가시겠습니까?")) {
      return;
    }
  }

  showJobsListView();
  jobsPageState.currentView = "list";
  jobsPageState.editingJobId = null;
  jobsPageState.viewingJobId = null;
  jobsPageState.hasUnsavedChanges = false;
}

// 공고 폼 취소
function cancelJobForm() {
  if (jobsPageState.hasUnsavedChanges) {
    if (!confirm("저장하지 않은 변경사항이 있습니다. 정말 취소하시겠습니까?")) {
      return;
    }
  }

  showJobsList();
}

// 공고 목록 새로고침
function refreshJobsList() {
  loadJobsList(jobsPageState.currentPage);
}

// 페이지네이션 렌더링
function renderJobsPagination(pagination) {
  const paginationContainer = document.querySelector(
    "#jobs-list-view .pagination-container"
  );
  if (!paginationContainer) return;

  const { current_page, total_pages, has_prev, has_next } = pagination;

  if (total_pages <= 1) {
    paginationContainer.innerHTML = "";
    return;
  }

  let paginationHTML = '<div class="pagination">';

  // 이전 페이지 버튼
  if (has_prev) {
    paginationHTML += `<button class="pagination-btn" data-page="${
      current_page - 1
    }">이전</button>`;
  }

  // 페이지 번호들
  const startPage = Math.max(1, current_page - 2);
  const endPage = Math.min(total_pages, current_page + 2);

  for (let i = startPage; i <= endPage; i++) {
    paginationHTML += `
      <button class="pagination-btn ${
        i === current_page ? "active" : ""
      }" data-page="${i}">
        ${i}
      </button>
    `;
  }

  // 다음 페이지 버튼
  if (has_next) {
    paginationHTML += `<button class="pagination-btn" data-page="${
      current_page + 1
    }">다음</button>`;
  }

  paginationHTML += "</div>";
  paginationContainer.innerHTML = paginationHTML;
}

// 통계 정보 업데이트
function updateJobsStats(pagination) {
  const statsElement = document.querySelector("#jobs-list-view .jobs-stats");
  if (statsElement) {
    statsElement.textContent = `총 ${pagination.total}개의 공고`;
  }
}

// 로딩 상태 표시/숨기기
function showJobsLoading() {
  const loadingOverlay = document.getElementById("jobs-loading-overlay");
  if (loadingOverlay) {
    loadingOverlay.style.display = "flex";
  }
}

function hideJobsLoading() {
  const loadingOverlay = document.getElementById("jobs-loading-overlay");
  if (loadingOverlay) {
    loadingOverlay.style.display = "none";
  }
}

// 에러 메시지 표시
function showJobsError(message) {
  showErrorMessage(message);
}

// 성공 메시지 표시
function showSuccessMessage(message) {
  const successDiv = document.createElement("div");
  successDiv.style.cssText = `
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: #28a745;
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    font-size: 14px;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    animation: slideDown 0.3s ease;
  `;
  successDiv.textContent = message;

  document.body.appendChild(successDiv);

  setTimeout(() => {
    successDiv.style.animation = "slideUp 0.3s ease";
    setTimeout(() => {
      if (successDiv.parentNode) {
        successDiv.parentNode.removeChild(successDiv);
      }
    }, 300);
  }, 3000);
}

// 유틸리티 함수들
function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function formatDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now - date);
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 1) {
    return "오늘";
  } else if (diffDays <= 7) {
    return `${diffDays - 1}일 전`;
  } else {
    return date.toLocaleDateString("ko-KR");
  }
}

function getCurrentUser() {
  // 현재 사용자 정보 반환 (실제 구현에서는 서버에서 받아온 데이터 사용)
  // 임시로 null 반환
  return null;
}

// ===== 구인구직 페이지 JavaScript 기능 끝 =====
