/**
 * auth.js
 * Production-grade authentication handler, password visibility toggler,
 * caps lock detection, and institutional access modal manager.
 */

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  const loginAlert = document.getElementById("loginAlert");
  const usernameInput = document.getElementById("username");
  const passwordInput = document.getElementById("password");
  const togglePasswordBtn = document.getElementById("togglePasswordBtn");
  const eyeIcon = document.getElementById("eyeIcon");
  const capsWarning = document.getElementById("capsWarning");
  const rememberCheckbox = document.getElementById("rememberWorkstation");

  // Pre-fill remembered username if previously stored
  if (usernameInput && rememberCheckbox) {
    const savedUsername = localStorage.getItem("shms_remembered_username");
    if (savedUsername) {
      usernameInput.value = savedUsername;
      rememberCheckbox.checked = true;
      if (passwordInput) passwordInput.focus();
    }
  }

  // Password Visibility Toggle
  if (togglePasswordBtn && passwordInput && eyeIcon) {
    togglePasswordBtn.addEventListener("click", () => {
      const isPassword = passwordInput.type === "password";
      passwordInput.type = isPassword ? "text" : "password";

      if (isPassword) {
        // Eye-off SVG
        eyeIcon.innerHTML = `
          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
          <line x1="1" y1="1" x2="23" y2="23"></line>
        `;
      } else {
        // Regular eye SVG
        eyeIcon.innerHTML = `
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
          <circle cx="12" cy="12" r="3"></circle>
        `;
      }
    });
  }

  // Caps Lock Detection
  if (passwordInput && capsWarning) {
    const checkCapsLock = (e) => {
      if (e.getModifierState && e.getModifierState("CapsLock")) {
        capsWarning.style.display = "flex";
      } else {
        capsWarning.style.display = "none";
      }
    };
    passwordInput.addEventListener("keydown", checkCapsLock);
    passwordInput.addEventListener("keyup", checkCapsLock);
  }

  // Form Submission
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const submitBtn = document.getElementById("submitBtn");
      const originalHTML = submitBtn.innerHTML;

      submitBtn.innerHTML = `
        <svg class="spinner" width="18" height="18" viewBox="0 0 50 50" style="animation: spin 0.8s linear infinite;">
          <circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="5" stroke-dasharray="80" stroke-dashoffset="60"></circle>
        </svg>
        <span>Verifying Credentials...</span>
      `;
      submitBtn.disabled = true;

      const username = usernameInput.value.trim();
      const password = passwordInput.value;

      try {
        const response = await fetch("/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password })
        });
        const data = await response.json();

        if (response.ok && data.success) {
          // Handle Remember Workstation
          if (rememberCheckbox && rememberCheckbox.checked) {
            localStorage.setItem("shms_remembered_username", username);
          } else {
            localStorage.removeItem("shms_remembered_username");
          }

          if (loginAlert) {
            loginAlert.className = "auth-alert-box auth-alert-success";
            loginAlert.style.display = "block";
            loginAlert.innerHTML = `✓ Authenticated successfully. Directing to your workspace...`;
          }

          setTimeout(() => {
            window.location.href = data.redirect_url || "/dashboard";
          }, 350);
        } else {
          if (loginAlert) {
            loginAlert.className = "auth-alert-box auth-alert-danger";
            loginAlert.style.display = "block";
            loginAlert.innerHTML = `⚠️ ${data.message || "Invalid username or password. Please try again."}`;
          }
          submitBtn.innerHTML = originalHTML;
          submitBtn.disabled = false;
          if (passwordInput) {
            passwordInput.value = "";
            passwordInput.focus();
          }
        }
      } catch (err) {
        console.error("Authentication request failed:", err);
        if (loginAlert) {
          loginAlert.className = "auth-alert-box auth-alert-danger";
          loginAlert.style.display = "block";
          loginAlert.innerHTML = "⚠️ Network connectivity error. Unable to contact clinical auth node.";
        }
        submitBtn.innerHTML = originalHTML;
        submitBtn.disabled = false;
      }
    });
  }
});

// Modal helpers for IT Support Dialog
function openSupportModal() {
  const modal = document.getElementById("supportModal");
  if (modal) modal.classList.add("active");
}

function closeSupportModal() {
  const modal = document.getElementById("supportModal");
  if (modal) modal.classList.remove("active");
}

// User Logout Handler
async function handleLogout() {
  try {
    await fetch("/api/logout", { method: "POST" });
  } catch (e) {
    console.warn("Logout ping failed", e);
  } finally {
    window.location.href = "/login";
  }
}
