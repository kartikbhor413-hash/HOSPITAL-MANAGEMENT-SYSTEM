/**
 * medical.js
 * Doctor consultation, electronic prescription composer, laboratory order & result handling, and pharmacy dispensing.
 */

let availableMedicinesCatalog = [];

document.addEventListener("DOMContentLoaded", () => {
  // Pre-load medicines catalog for prescription composer dropdowns
  loadMedicinesCatalog();

  const consultationForm = document.getElementById("consultationForm");
  if (consultationForm) {
    consultationForm.addEventListener("submit", handleSaveConsultation);
  }

  const addMedRowBtn = document.getElementById("addMedRowBtn");
  if (addMedRowBtn) {
    addMedRowBtn.addEventListener("click", addMedicineRow);
  }

  // Load Lab queue if on lab dashboard
  if (document.getElementById("labOrdersTableBody")) {
    loadLabOrders();
  }

  // Load Pharmacy inventory & pending RX if on pharmacy dashboard
  if (document.getElementById("pharmacyInventoryTableBody")) {
    loadPharmacyData();
  }
});

async function loadMedicinesCatalog() {
  try {
    const res = await fetch("/api/medicines");
    const json = await res.json();
    if (json.success && json.data) {
      availableMedicinesCatalog = json.data;
    }
  } catch (err) {
    console.error("Error loading medicines:", err);
  }
}

function openConsultationModal(aptId, patientId, patientName) {
  document.getElementById("c_apt_id").value = aptId || "";
  document.getElementById("c_patient_id").value = patientId || "";
  document.getElementById("c_patient_name").value = patientName || "";

  // Reset med rows
  const container = document.getElementById("prescribedMedsContainer");
  if (container) {
    container.innerHTML = "";
    addMedicineRow(); // Add initial blank row
  }

  openModal("consultationModal");
}

function addMedicineRow() {
  const container = document.getElementById("prescribedMedsContainer");
  if (!container) return;

  const rowId = `med_row_${Date.now()}`;
  const row = document.createElement("div");
  row.className = "form-row med-row";
  row.id = rowId;
  row.style.marginBottom = "10px";
  row.style.alignItems = "center";

  const options = availableMedicinesCatalog.map(m =>
    `<option value="${m.medicine_id}" data-price="${m.unit_price}">${escapeHtml(m.name)} ($${m.unit_price})</option>`
  ).join("");

  row.innerHTML = `
    <div style="flex:2;">
      <select class="form-control med-select" onchange="updateMedRowTotal('${rowId}')">
        <option value="">-- Choose Medicine --</option>
        ${options}
      </select>
    </div>
    <div style="flex:1.5;">
      <input type="text" class="form-control med-dosage" placeholder="e.g. 1 tablet" />
    </div>
    <div style="flex:1.5;">
      <input type="text" class="form-control med-freq" placeholder="e.g. Twice daily" />
    </div>
    <div style="flex:1;">
      <input type="number" class="form-control med-qty" value="10" min="1" onchange="updateMedRowTotal('${rowId}')" />
    </div>
    <div style="flex:1; text-align:right; font-weight:700;" class="med-row-price">$0.00</div>
    <div style="flex:0.5; text-align:center;">
      <button type="button" class="btn btn-sm btn-danger" onclick="document.getElementById('${rowId}').remove(); calculatePrescriptionGrandTotal();">✕</button>
    </div>
  `;

  container.appendChild(row);
}

function updateMedRowTotal(rowId) {
  const row = document.getElementById(rowId);
  if (!row) return;

  const select = row.querySelector(".med-select");
  const qtyInput = row.querySelector(".med-qty");
  const priceDisplay = row.querySelector(".med-row-price");

  const selectedOption = select.options[select.selectedIndex];
  const unitPrice = parseFloat(selectedOption.getAttribute("data-price") || 0);
  const qty = parseInt(qtyInput.value || 1);

  const total = unitPrice * qty;
  priceDisplay.textContent = `$${total.toFixed(2)}`;

  calculatePrescriptionGrandTotal();
}

function calculatePrescriptionGrandTotal() {
  const priceDisplays = document.querySelectorAll(".med-row-price");
  let grandTotal = 0;
  priceDisplays.forEach(el => {
    grandTotal += parseFloat(el.textContent.replace("$", "") || 0);
  });
  const grandEl = document.getElementById("prescriptionGrandTotal");
  if (grandEl) grandEl.textContent = `$${grandTotal.toFixed(2)}`;
}

async function handleSaveConsultation(e) {
  e.preventDefault();
  const btn = e.target.querySelector("button[type='submit']");
  btn.disabled = true;

  const patientId = document.getElementById("c_patient_id").value;
  const aptId = document.getElementById("c_apt_id").value;
  const diagnosis = document.getElementById("c_diagnosis").value.trim();
  const symptoms = document.getElementById("c_symptoms").value.trim();
  const notes = document.getElementById("c_notes").value.trim();

  const vitals = {
    blood_pressure: document.getElementById("c_bp").value.trim(),
    heart_rate: document.getElementById("c_hr").value.trim(),
    temperature: document.getElementById("c_temp").value.trim(),
    spo2: document.getElementById("c_spo2").value.trim()
  };

  // Collect Prescribed Medicines
  const medRows = document.querySelectorAll(".med-row");
  const medicines = [];
  medRows.forEach(row => {
    const select = row.querySelector(".med-select");
    const dosage = row.querySelector(".med-dosage").value.trim();
    const frequency = row.querySelector(".med-freq").value.trim();
    const qty = parseInt(row.querySelector(".med-qty").value || 1);
    if (select.value) {
      const selectedOption = select.options[select.selectedIndex];
      const unitPrice = parseFloat(selectedOption.getAttribute("data-price") || 0);
      medicines.push({
        medicine_id: select.value,
        medicine_name: selectedOption.textContent.split(" ($")[0],
        dosage: dosage || "As directed",
        frequency: frequency || "Once daily",
        duration: "7 days",
        quantity: qty,
        unit_price: unitPrice
      });
    }
  });

  try {
    let prescriptionId = null;

    // 1. If medicines were added, create prescription first
    if (medicines.length > 0) {
      const rxRes = await fetch("/api/prescriptions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_id: patientId,
          doctor_id: "DOC001",
          diagnosis: diagnosis,
          medicines: medicines
        })
      });
      const rxJson = await rxRes.json();
      if (rxJson.success) {
        prescriptionId = rxJson.data.prescription_id;
      }
    }

    // 2. Save Medical Record
    const mrRes = await fetch("/api/medical-records", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        patient_id: patientId,
        doctor_id: "DOC001",
        appointment_id: aptId || null,
        symptoms: symptoms,
        vitals: vitals,
        diagnosis: diagnosis,
        doctor_notes: notes,
        prescription_id: prescriptionId
      })
    });
    const mrJson = await mrRes.json();

    if (mrJson.success) {
      alert("✓ Patient consultation, clinical record, and prescription saved successfully!");
      closeModal("consultationModal");
      e.target.reset();
      if (typeof loadAppointments === "function") {
        loadAppointments();
      } else {
        location.reload();
      }
    } else {
      alert(`⚠️ ${mrJson.message || "Failed to save consultation."}`);
    }
  } catch (err) {
    console.error("Consultation save error:", err);
    alert("⚠️ Network error while saving medical record.");
  } finally {
    btn.disabled = false;
  }
}

/* ==========================================================================
   LABORATORY WORKFLOW
   ========================================================================== */

async function loadLabOrders() {
  const tbody = document.getElementById("labOrdersTableBody");
  if (!tbody) return;

  try {
    const res = await fetch("/api/laboratory/reports");
    const json = await res.json();
    if (!json.success || !json.data) return;

    if (json.data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding:24px;">No diagnostic requests pending.</td></tr>`;
      return;
    }

    tbody.innerHTML = json.data.map(r => `
      <tr>
        <td><strong>${escapeHtml(r.report_id)}</strong></td>
        <td>
          <div style="font-weight: 600;">${escapeHtml(r.patient_name)}</div>
          <div style="font-size: 11px; color: var(--text-muted);">ID: ${r.patient_id}</div>
        </td>
        <td><strong>${escapeHtml(r.test_name)}</strong></td>
        <td>${r.ordered_date}</td>
        <td>$${r.cost}</td>
        <td>
          <span class="badge ${r.status === 'Completed' ? 'badge-completed' : 'badge-pending'}">${r.status}</span>
        </td>
        <td>
          ${r.status === 'Pending' ? `
            <button class="btn btn-sm btn-primary" onclick="openLabResultModal('${r.report_id}', '${escapeHtml(r.test_name)}', '${escapeHtml(r.patient_name)}')">Enter Results</button>
          ` : `
            <button class="btn btn-sm btn-secondary" onclick="viewLabResults('${r.report_id}')">View Report</button>
          `}
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading lab orders:", err);
  }
}

function openLabResultModal(reportId, testName, patientName) {
  document.getElementById("lab_report_id").value = reportId;
  document.getElementById("lab_test_title").textContent = `${testName} - ${patientName}`;
  openModal("enterLabResultModal");
}

async function submitLabResult() {
  const reportId = document.getElementById("lab_report_id").value;
  const findings = document.getElementById("lab_findings").value.trim();
  const notes = document.getElementById("lab_notes").value.trim();

  if (!findings) {
    alert("Please provide the diagnostic test findings.");
    return;
  }

  try {
    const res = await fetch(`/api/laboratory/reports/${reportId}/result`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        results: { "Clinical Findings": findings },
        technician_notes: notes || "Verified by Pathology Technician"
      })
    });
    const json = await res.json();
    if (json.success) {
      alert("✓ Lab Report finalized and saved.");
      closeModal("enterLabResultModal");
      loadLabOrders();
    } else {
      alert(`⚠️ ${json.message}`);
    }
  } catch (err) {
    console.error("Submit lab result error:", err);
  }
}

async function viewLabResults(reportId) {
  try {
    const res = await fetch("/api/laboratory/reports");
    const json = await res.json();
    const report = json.data.find(r => r.report_id === reportId);
    if (!report) return;

    let resultsHtml = "";
    if (typeof report.results === "object") {
      resultsHtml = Object.entries(report.results).map(([k, v]) => `<div><strong>${escapeHtml(k)}:</strong> ${escapeHtml(v)}</div>`).join("");
    }

    alert(`DIAGNOSTIC REPORT: ${report.test_name}\nPatient: ${report.patient_name}\nStatus: ${report.status}\nCompleted: ${report.completed_date}\n\nFindings:\n${resultsHtml.replace(/<[^>]+>/g, '')}\n\nNotes: ${report.technician_notes}`);
  } catch (err) {
    console.error("View lab result error:", err);
  }
}

/* ==========================================================================
   PHARMACY WORKFLOW
   ========================================================================== */

async function loadPharmacyData() {
  const invTbody = document.getElementById("pharmacyInventoryTableBody");
  const rxTbody = document.getElementById("pendingRxTableBody");

  // 1. Load Inventory & Alerts
  try {
    const res = await fetch("/api/medicines");
    const json = await res.json();
    if (json.success && json.data && invTbody) {
      invTbody.innerHTML = json.data.map(m => `
        <tr>
          <td><strong>${escapeHtml(m.medicine_id)}</strong></td>
          <td>
            <div style="font-weight: 600;">${escapeHtml(m.name)}</div>
            <div style="font-size: 11px; color: var(--text-muted);">${escapeHtml(m.generic_name)}</div>
          </td>
          <td>${escapeHtml(m.category)}</td>
          <td><strong>${m.stock_quantity}</strong> (Min: ${m.min_threshold})</td>
          <td>$${m.unit_price.toFixed(2)}</td>
          <td>${m.expiry_date}</td>
          <td>
            <span class="badge ${m.status === 'LOW_STOCK' ? 'badge-lowstock' : m.status === 'EXPIRING_SOON' ? 'badge-expiring' : m.status === 'EXPIRED' ? 'badge-expired' : 'badge-instock'}">
              ${m.status}
            </span>
          </td>
        </tr>
      `).join("");
    }
  } catch (err) {
    console.error("Error loading pharmacy inventory:", err);
  }

  // 2. Load Prescriptions
  try {
    const res = await fetch("/api/prescriptions");
    const json = await res.json();
    if (json.success && json.data && rxTbody) {
      rxTbody.innerHTML = json.data.map(rx => `
        <tr>
          <td><strong>${escapeHtml(rx.prescription_id)}</strong></td>
          <td><strong>${escapeHtml(rx.patient_id)}</strong></td>
          <td>${rx.date}</td>
          <td>
            <div style="font-size: 12px;">
              ${rx.medicines.map(m => `${m.medicine_name} (x${m.quantity})`).join(", ")}
            </div>
          </td>
          <td><strong>$${rx.total_medicine_charge}</strong></td>
          <td>
            <span class="badge ${rx.dispense_status === 'Dispensed' ? 'badge-completed' : 'badge-pending'}">${rx.dispense_status}</span>
          </td>
          <td>
            ${rx.dispense_status === 'Pending' ? `
              <button class="btn btn-sm btn-primary" onclick="dispensePrescription('${rx.prescription_id}')">Dispense & Deduct</button>
            ` : `<span class="text-muted" style="font-size:12px;">Dispensed</span>`}
          </td>
        </tr>
      `).join("");
    }
  } catch (err) {
    console.error("Error loading prescriptions for pharmacy:", err);
  }
}

async function dispensePrescription(rxId) {
  if (!confirm(`Dispense medicines for Prescription ${rxId} and deduct stock from inventory?`)) return;

  try {
    const res = await fetch(`/api/prescriptions/${rxId}/dispense`, { method: "POST" });
    const json = await res.json();
    if (json.success) {
      alert(`✓ ${json.message}`);
      loadPharmacyData();
    } else {
      alert(`⚠️ ${json.message}`);
    }
  } catch (err) {
    console.error("Dispense error:", err);
  }
}
