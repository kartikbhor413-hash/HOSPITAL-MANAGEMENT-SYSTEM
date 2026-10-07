/**
 * patients.js
 * Patient management, live search, new registration modal, and comprehensive profile viewer.
 */

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("patientsTableBody")) {
    loadPatients();
  }

  const searchInput = document.getElementById("patientSearchInput");
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener("input", (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        loadPatients(e.target.value.trim());
      }, 300);
    });
  }

  const patientForm = document.getElementById("newPatientForm");
  if (patientForm) {
    patientForm.addEventListener("submit", handleCreatePatient);
  }
});

async function loadPatients(query = "") {
  const tbody = document.getElementById("patientsTableBody");
  if (!tbody) return;

  try {
    const url = query ? `/api/patients?query=${encodeURIComponent(query)}` : "/api/patients";
    const res = await fetch(url);
    const json = await res.json();

    if (!json.success || !json.data) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Failed to load patients.</td></tr>`;
      return;
    }

    if (json.data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 24px;">No patients found matching your search.</td></tr>`;
      return;
    }

    tbody.innerHTML = json.data.map(p => `
      <tr>
        <td><strong>${escapeHtml(p.patient_id)}</strong></td>
        <td>
          <div style="font-weight: 600;">${escapeHtml(p.name)}</div>
          <div style="font-size: 11.5px; color: var(--text-muted);">${escapeHtml(p.email || 'No email')}</div>
        </td>
        <td>${p.age || '--'} yrs / ${escapeHtml(p.gender || '--')}</td>
        <td><span class="badge" style="background: #f1f5f9; font-weight:700;">${escapeHtml(p.blood_group || 'Unknown')}</span></td>
        <td>${escapeHtml(p.phone)}</td>
        <td>
          <span class="badge ${p.status === 'Inpatient' ? 'badge-critical' : p.status === 'Discharged' ? 'badge-medium' : 'badge-low'}">
            ${escapeHtml(p.status || 'Outpatient')}
          </span>
        </td>
        <td>
          <button class="btn btn-sm btn-secondary" onclick="viewPatientProfile('${p.patient_id}')">View Profile</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error fetching patients:", err);
    tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Error connecting to server.</td></tr>`;
  }
}

async function handleCreatePatient(e) {
  e.preventDefault();
  const form = e.target;
  const btn = form.querySelector("button[type='submit']");
  btn.disabled = true;

  const payload = {
    name: document.getElementById("pat_name").value.trim(),
    age: document.getElementById("pat_age").value,
    gender: document.getElementById("pat_gender").value,
    blood_group: document.getElementById("pat_blood").value,
    phone: document.getElementById("pat_phone").value.trim(),
    email: document.getElementById("pat_email").value.trim(),
    address: document.getElementById("pat_address").value.trim(),
    emergency_contact: document.getElementById("pat_emergency").value.trim(),
    allergies: document.getElementById("pat_allergies").value.trim(),
    chronic_conditions: document.getElementById("pat_chronic").value.trim()
  };

  try {
    const res = await fetch("/api/patients", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const json = await res.json();

    if (json.success) {
      alert(`✓ Patient registered successfully! Assigned ID: ${json.data.patient_id}`);
      form.reset();
      closeModal("newPatientModal");
      loadPatients();
    } else {
      alert(`⚠️ ${json.message || "Registration failed."}`);
    }
  } catch (err) {
    console.error("Error creating patient:", err);
    alert("⚠️ Failed to register patient due to network error.");
  } finally {
    btn.disabled = false;
  }
}

async function viewPatientProfile(patientId) {
  try {
    const res = await fetch(`/api/patients/${patientId}`);
    const json = await res.json();
    if (!json.success) {
      alert("Patient profile not found.");
      return;
    }

    const p = json.patient;
    const history = json.history;

    const modalBody = document.getElementById("patientProfileBody");
    if (!modalBody) return;

    modalBody.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); padding-bottom: 16px;">
        <div>
          <h3 style="font-size: 18px; font-weight: 700;">${escapeHtml(p.name)}</h3>
          <div style="font-size: 12px; color: var(--text-muted);">
            ID: <strong>${p.patient_id}</strong> • Registered: ${p.registration_date} • Status: <span class="badge ${p.status === 'Inpatient' ? 'badge-critical' : 'badge-low'}">${p.status}</span>
          </div>
        </div>
        <div style="text-align: right;">
          <span class="badge" style="background:#dbeafe; color:#1e40af; font-size: 13px; font-weight:700;">Blood: ${p.blood_group}</span>
        </div>
      </div>

      <div class="form-row" style="margin-bottom: 16px; font-size: 13px;">
        <div><strong>Age / Gender:</strong> ${p.age} yrs / ${p.gender}</div>
        <div><strong>Phone:</strong> ${p.phone}</div>
        <div><strong>Email:</strong> ${p.email || 'None'}</div>
        <div><strong>Emergency Contact:</strong> ${p.emergency_contact || 'None'}</div>
      </div>

      <div style="background: #f8fafc; padding: 12px; border-radius: var(--radius-sm); margin-bottom: 20px; font-size: 12.5px;">
        <div><strong>Allergies:</strong> ${p.allergies && p.allergies.length ? p.allergies.join(", ") : 'None documented'}</div>
        <div style="margin-top: 4px;"><strong>Chronic Conditions:</strong> ${p.chronic_conditions && p.chronic_conditions.length ? p.chronic_conditions.join(", ") : 'None documented'}</div>
        <div style="margin-top: 4px;"><strong>Address:</strong> ${p.address || 'N/A'}</div>
      </div>

      <h4 style="font-size: 14px; font-weight: 700; margin-bottom: 8px;">Clinical Consultations & Diagnoses (${history.medical_records.length})</h4>
      ${history.medical_records.length === 0 ? '<p class="text-muted" style="font-size:12px;">No consultation history on record.</p>' : `
        <div style="display:flex; flex-direction:column; gap:8px; margin-bottom: 16px;">
          ${history.medical_records.map(m => `
            <div style="border:1px solid var(--border-color); padding:10px; border-radius:var(--radius-sm); font-size:12.5px;">
              <div style="display:flex; justify-content:space-between; font-weight:600;">
                <span>Diagnosis: ${escapeHtml(m.diagnosis)}</span>
                <span class="text-muted">${m.date}</span>
              </div>
              <div style="color:var(--text-muted); margin-top:4px;">Notes: ${escapeHtml(m.doctor_notes || 'N/A')}</div>
            </div>
          `).join("")}
        </div>
      `}

      <h4 style="font-size: 14px; font-weight: 700; margin-bottom: 8px;">Active Prescriptions (${history.prescriptions.length})</h4>
      ${history.prescriptions.length === 0 ? '<p class="text-muted" style="font-size:12px;">No prescriptions found.</p>' : `
        <div style="display:flex; flex-direction:column; gap:8px; margin-bottom: 16px;">
          ${history.prescriptions.map(rx => `
            <div style="border:1px solid var(--border-color); padding:10px; border-radius:var(--radius-sm); font-size:12.5px;">
              <div style="display:flex; justify-content:space-between; font-weight:600;">
                <span>Rx ID: ${rx.prescription_id} (${rx.dispense_status})</span>
                <span>$${rx.total_medicine_charge}</span>
              </div>
              <div style="margin-top:4px;">
                ${rx.medicines.map(m => `${m.medicine_name} (${m.dosage}, ${m.frequency})`).join("; ")}
              </div>
            </div>
          `).join("")}
        </div>
      `}

      <h4 style="font-size: 14px; font-weight: 700; margin-bottom: 8px;">Laboratory Diagnostic Reports (${history.lab_reports.length})</h4>
      ${history.lab_reports.length === 0 ? '<p class="text-muted" style="font-size:12px;">No lab reports found.</p>' : `
        <div style="display:flex; flex-direction:column; gap:8px;">
          ${history.lab_reports.map(rep => `
            <div style="border:1px solid var(--border-color); padding:10px; border-radius:var(--radius-sm); font-size:12.5px;">
              <div style="display:flex; justify-content:space-between; font-weight:600;">
                <span>${escapeHtml(rep.test_name)}</span>
                <span class="badge ${rep.status === 'Completed' ? 'badge-completed' : 'badge-pending'}">${rep.status}</span>
              </div>
              <div style="color:var(--text-muted); margin-top:4px;">Ordered: ${rep.ordered_date}</div>
            </div>
          `).join("")}
        </div>
      `}
    `;

    openModal("patientProfileModal");
  } catch (err) {
    console.error("Error viewing patient profile:", err);
    alert("Could not load patient profile.");
  }
}
