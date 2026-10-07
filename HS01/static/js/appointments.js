/**
 * appointments.js
 * Real-time slot availability checker, booking scheduler, token generator, and status manager.
 */

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("appointmentsTableBody")) {
    loadAppointments();
  }

  // Populate doctor dropdown for appointment booking
  loadDoctorsDropdown();

  const doctorSelect = document.getElementById("apt_doctor_select");
  const dateInput = document.getElementById("apt_date_input");

  if (doctorSelect && dateInput) {
    doctorSelect.addEventListener("change", refreshAvailableSlots);
    dateInput.addEventListener("change", refreshAvailableSlots);
  }

  const bookForm = document.getElementById("bookAppointmentForm");
  if (bookForm) {
    bookForm.addEventListener("submit", handleBookAppointment);
  }
});

async function loadAppointments(filterParams = {}) {
  const tbody = document.getElementById("appointmentsTableBody");
  if (!tbody) return;

  try {
    let url = "/api/appointments";
    const query = new URLSearchParams(filterParams).toString();
    if (query) url += `?${query}`;

    const res = await fetch(url);
    const json = await res.json();

    if (!json.success || !json.data) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Failed to load appointments.</td></tr>`;
      return;
    }

    if (json.data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 24px;">No appointments found.</td></tr>`;
      return;
    }

    tbody.innerHTML = json.data.map(a => `
      <tr>
        <td><strong>${escapeHtml(a.appointment_id)}</strong></td>
        <td><span class="badge" style="background:#0284c7; color:white; font-weight:700;">#${a.token_number}</span></td>
        <td>
          <div style="font-weight: 600;">${escapeHtml(a.patient_name)}</div>
          <div style="font-size: 11px; color: var(--text-muted);">ID: ${a.patient_id}</div>
        </td>
        <td>
          <div style="font-weight: 600;">${escapeHtml(a.doctor_name)}</div>
          <div style="font-size: 11px; color: var(--text-muted);">${escapeHtml(a.department)}</div>
        </td>
        <td>
          <div>${a.appointment_date}</div>
          <div style="font-size: 11px; color: var(--primary); font-weight: 600;">${escapeHtml(a.time_slot)}</div>
        </td>
        <td>
          <span class="badge ${a.status === 'Completed' ? 'badge-completed' : a.status === 'Cancelled' ? 'badge-cancelled' : 'badge-scheduled'}">
            ${escapeHtml(a.status)}
          </span>
        </td>
        <td>
          ${a.status === 'Scheduled' ? `
            <button class="btn btn-sm btn-primary" onclick="updateAppointmentStatus('${a.appointment_id}', 'Completed')">Complete</button>
            <button class="btn btn-sm btn-danger" onclick="updateAppointmentStatus('${a.appointment_id}', 'Cancelled')">Cancel</button>
          ` : `
            <span class="text-muted" style="font-size:12px;">--</span>
          `}
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading appointments:", err);
    tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Error loading data.</td></tr>`;
  }
}

async function loadDoctorsDropdown() {
  const select = document.getElementById("apt_doctor_select");
  if (!select) return;

  try {
    const res = await fetch("/api/doctors");
    const json = await res.json();
    if (json.success && json.data) {
      select.innerHTML = `<option value="">-- Choose Doctor --</option>` +
        json.data.map(d => `<option value="${d.doctor_id}">${escapeHtml(d.name)} (${escapeHtml(d.specialization)})</option>`).join("");
    }
  } catch (err) {
    console.error("Error loading doctors dropdown:", err);
  }
}

async function refreshAvailableSlots() {
  const docId = document.getElementById("apt_doctor_select")?.value;
  const dateVal = document.getElementById("apt_date_input")?.value;
  const slotSelect = document.getElementById("apt_slot_select");

  if (!slotSelect) return;
  if (!docId || !dateVal) {
    slotSelect.innerHTML = `<option value="">Select Doctor & Date First</option>`;
    slotSelect.disabled = true;
    return;
  }

  slotSelect.disabled = true;
  slotSelect.innerHTML = `<option value="">Checking schedule...</option>`;

  try {
    const res = await fetch(`/api/doctors/${docId}/availability?date=${dateVal}`);
    const json = await res.json();

    if (json.success && json.available_slots) {
      if (json.available_slots.length === 0) {
        slotSelect.innerHTML = `<option value="">No slots open on this date</option>`;
        slotSelect.disabled = true;
      } else {
        slotSelect.innerHTML = `<option value="">-- Select Time Slot --</option>` +
          json.available_slots.map(s => `<option value="${s}">${s}</option>`).join("");
        slotSelect.disabled = false;
      }
    }
  } catch (err) {
    console.error("Error checking slot availability:", err);
    slotSelect.innerHTML = `<option value="">Error fetching slots</option>`;
  }
}

async function handleBookAppointment(e) {
  e.preventDefault();
  const btn = e.target.querySelector("button[type='submit']");
  btn.disabled = true;

  const payload = {
    patient_id: document.getElementById("apt_patient_id").value.trim(),
    doctor_id: document.getElementById("apt_doctor_select").value,
    appointment_date: document.getElementById("apt_date_input").value,
    time_slot: document.getElementById("apt_slot_select").value,
    purpose: document.getElementById("apt_purpose").value.trim()
  };

  try {
    const res = await fetch("/api/appointments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const json = await res.json();

    if (json.success) {
      alert(`✓ ${json.message}`);
      e.target.reset();
      closeModal("bookAppointmentModal");
      loadAppointments();
    } else {
      alert(`⚠️ ${json.message || "Failed to book appointment."}`);
    }
  } catch (err) {
    console.error("Booking error:", err);
    alert("⚠️ Network error while booking appointment.");
  } finally {
    btn.disabled = false;
  }
}

async function updateAppointmentStatus(aptId, status) {
  if (!confirm(`Confirm status change to ${status}?`)) return;

  try {
    const res = await fetch(`/api/appointments/${aptId}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status })
    });
    const json = await res.json();
    if (json.success) {
      loadAppointments();
    } else {
      alert(json.message);
    }
  } catch (err) {
    console.error("Update appointment status error:", err);
  }
}
