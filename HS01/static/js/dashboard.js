/**
 * dashboard.js
 * Analytics, real-time metrics aggregator, emergency alert monitor, and activity feed.
 */

document.addEventListener("DOMContentLoaded", () => {
  loadDashboardStats();
  // Poll every 30 seconds for live updates
  setInterval(loadDashboardStats, 30000);
});

async function loadDashboardStats() {
  try {
    const res = await fetch("/api/dashboard/stats");
    if (!res.ok) return;
    const json = await res.json();
    if (!json.success) return;

    const stats = json.stats;

    // Update KPI Elements if they exist on the page
    updateText("stat-patients", stats.total_patients);
    updateText("stat-doctors", stats.total_doctors);
    updateText("stat-today-apts", stats.today_appointments);
    updateText("stat-pending-apts", stats.pending_appointments);
    updateText("stat-beds-avail", stats.available_beds);
    updateText("stat-beds-occ", stats.occupied_beds);
    updateText("stat-bed-rate", `${stats.bed_occupancy_rate}%`);
    updateText("stat-emergency", stats.emergency_patients);
    updateText("stat-critical", stats.critical_emergency);
    updateText("stat-lab-pending", stats.pending_lab_tests);
    updateText("stat-med-alert", stats.low_stock_medicines);
    updateText("stat-revenue", `$${stats.total_revenue.toLocaleString()}`);
    updateText("stat-today-rev", `$${stats.today_revenue.toLocaleString()}`);

    // Emergency Alert Banner
    const alertBanner = document.getElementById("emergencyAlertBanner");
    const alertMessage = document.getElementById("emergencyAlertMessage");
    if (alertBanner && alertMessage) {
      if (json.emergency_alert) {
        alertMessage.textContent = json.emergency_alert;
        alertBanner.style.display = "flex";
      } else {
        alertBanner.style.display = "none";
      }
    }

    // Bed Occupancy Progress Bar
    const bedProgressBar = document.getElementById("bedProgressBar");
    if (bedProgressBar) {
      bedProgressBar.style.width = `${stats.bed_occupancy_rate}%`;
      if (stats.bed_occupancy_rate > 85) {
        bedProgressBar.style.backgroundColor = "var(--critical)";
      } else if (stats.bed_occupancy_rate > 65) {
        bedProgressBar.style.backgroundColor = "var(--warning)";
      } else {
        bedProgressBar.style.backgroundColor = "var(--success)";
      }
    }

    // Activity Logs
    renderActivityFeed(json.recent_activity);

    // Department Distribution
    renderDeptDistribution(json.department_distribution);

  } catch (err) {
    console.error("Error loading dashboard stats:", err);
  }
}

function updateText(elementId, value) {
  const el = document.getElementById(elementId);
  if (el) el.textContent = value !== undefined ? value : "--";
}

function renderActivityFeed(activities) {
  const feed = document.getElementById("activityFeed");
  if (!feed || !activities) return;

  if (activities.length === 0) {
    feed.innerHTML = "<p class='text-muted' style='font-size:13px;'>No recent activities logged.</p>";
    return;
  }

  feed.innerHTML = activities.map(act => `
    <li class="activity-item">
      <div class="activity-text"><strong>${escapeHtml(act.role)}:</strong> ${escapeHtml(act.action)}</div>
      <div class="activity-meta">Module: ${escapeHtml(act.module)} • ${escapeHtml(act.date)} ${escapeHtml(act.time)}</div>
    </li>
  `).join("");
}

function renderDeptDistribution(depts) {
  const container = document.getElementById("deptDistribution");
  if (!container || !depts) return;

  const entries = Object.entries(depts);
  if (entries.length === 0) {
    container.innerHTML = "<p class='text-muted' style='font-size:13px;'>No department data available.</p>";
    return;
  }

  container.innerHTML = entries.map(([dept, count]) => `
    <div style="margin-bottom: 12px;">
      <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
        <span style="font-weight: 600;">${escapeHtml(dept)}</span>
        <span class="badge badge-scheduled">${count} Specialist(s)</span>
      </div>
      <div style="background: #e2e8f0; height: 6px; border-radius: 3px; overflow: hidden;">
        <div style="background: var(--primary); height: 100%; width: ${Math.min(100, count * 25)}%;"></div>
      </div>
    </div>
  `).join("");
}

function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("active");
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("active");
}

function escapeHtml(text) {
  if (!text) return "";
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}
