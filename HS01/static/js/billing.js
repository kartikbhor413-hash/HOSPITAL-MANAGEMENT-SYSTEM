/**
 * billing.js
 * Automated Billing Calculation Engine, Invoice Generator, and Payment Processor.
 * Total Bill = Consultation + (Bed Daily Rate * Days Occupied) + Sum(Lab Tests) + Sum(Medicine Prices)
 */

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("billsTableBody")) {
    loadBills();
  }

  const calcBtn = document.getElementById("calculateBillBtn");
  if (calcBtn) {
    calcBtn.addEventListener("click", handleCalculateBill);
  }

  const generateBillBtn = document.getElementById("confirmGenerateBillBtn");
  if (generateBillBtn) {
    generateBillBtn.addEventListener("click", handleGenerateOfficialBill);
  }

  const discountInput = document.getElementById("bill_discount_input");
  if (discountInput) {
    discountInput.addEventListener("input", recomputeBillGrandTotal);
  }
});

let currentCalculatedBill = null;

async function loadBills() {
  const tbody = document.getElementById("billsTableBody");
  if (!tbody) return;

  try {
    const res = await fetch("/api/bills");
    const json = await res.json();
    if (!json.success || !json.data) return;

    if (json.data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding:24px;">No bills recorded.</td></tr>`;
      return;
    }

    tbody.innerHTML = json.data.map(b => `
      <tr>
        <td><strong>${escapeHtml(b.bill_id)}</strong></td>
        <td>
          <div style="font-weight: 600;">${escapeHtml(b.patient_name)}</div>
          <div style="font-size: 11px; color: var(--text-muted);">ID: ${b.patient_id}</div>
        </td>
        <td>${b.bill_date}</td>
        <td><strong>$${b.total_amount.toFixed(2)}</strong></td>
        <td>$${b.paid_amount.toFixed(2)} (${escapeHtml(b.payment_method)})</td>
        <td>
          <span class="badge ${b.status === 'Paid' ? 'badge-paid' : 'badge-pending'}">${b.status}</span>
        </td>
        <td>
          <button class="btn btn-sm btn-secondary" onclick="viewPrintableInvoice('${b.bill_id}')">View Invoice</button>
          ${b.status !== 'Paid' ? `
            <button class="btn btn-sm btn-success" onclick="payBill('${b.bill_id}')">Pay Now</button>
          ` : ''}
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading bills:", err);
  }
}

async function handleCalculateBill() {
  const patientId = document.getElementById("calc_patient_id").value.trim();
  if (!patientId) {
    alert("Please enter a valid Patient ID (e.g. PAT001, PAT002).");
    return;
  }

  const container = document.getElementById("billingBreakdownContainer");
  if (container) {
    container.innerHTML = "<p class='text-muted'>Calculating itemized hospital charges...</p>";
    container.style.display = "block";
  }

  try {
    const res = await fetch(`/api/billing/calculate/${patientId}`);
    const json = await res.json();

    if (!json.success) {
      alert(`⚠️ ${json.message || "Failed to calculate bill."}`);
      if (container) container.style.display = "none";
      return;
    }

    const b = json.breakdown;
    currentCalculatedBill = b;

    document.getElementById("calc_consultation").textContent = `$${b.consultation_fee.toFixed(2)}`;
    document.getElementById("calc_bed").textContent = `$${b.bed_info.bed_charge_total.toFixed(2)} (${b.bed_info.days_occupied} days @ $${b.bed_info.daily_rate}/day)`;
    document.getElementById("calc_lab").textContent = `$${b.lab_charges_total.toFixed(2)} (${b.lab_reports_count} diagnostic test orders)`;
    document.getElementById("calc_pharmacy").textContent = `$${b.medicine_charges_total.toFixed(2)} (${b.prescriptions_count} prescription orders)`;
    document.getElementById("calc_subtotal").textContent = `$${b.subtotal.toFixed(2)}`;

    const discountInput = document.getElementById("bill_discount_input");
    if (discountInput) discountInput.value = "0.00";

    document.getElementById("calc_grand_total").textContent = `$${b.total_amount.toFixed(2)}`;
    document.getElementById("confirmGenerateBillBtn").disabled = false;

  } catch (err) {
    console.error("Calculation error:", err);
    alert("Network error connecting to billing engine.");
  }
}

function recomputeBillGrandTotal() {
  if (!currentCalculatedBill) return;
  const discount = parseFloat(document.getElementById("bill_discount_input")?.value || 0);
  const subtotal = currentCalculatedBill.subtotal;
  const grandTotal = Math.max(0, subtotal - discount);
  document.getElementById("calc_grand_total").textContent = `$${grandTotal.toFixed(2)}`;
}

async function handleGenerateOfficialBill() {
  if (!currentCalculatedBill) return;
  const discount = parseFloat(document.getElementById("bill_discount_input")?.value || 0);
  const paymentMethod = document.getElementById("bill_payment_method")?.value || "Cash";
  const markAsPaid = document.getElementById("bill_mark_paid")?.checked;

  const subtotal = currentCalculatedBill.subtotal;
  const totalAmount = Math.max(0, subtotal - discount);
  const paidAmount = markAsPaid ? totalAmount : 0;

  const payload = {
    patient_id: currentCalculatedBill.patient_id,
    consultation_fee: currentCalculatedBill.consultation_fee,
    bed_charge: currentCalculatedBill.bed_info.bed_charge_total,
    days_occupied: currentCalculatedBill.bed_info.days_occupied,
    lab_charges: currentCalculatedBill.lab_charges_total,
    medicine_charges: currentCalculatedBill.medicine_charges_total,
    discount: discount,
    paid_amount: paidAmount,
    payment_method: paymentMethod
  };

  try {
    const res = await fetch("/api/billing", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const json = await res.json();

    if (json.success) {
      alert(`✓ Invoice ${json.data.bill_id} generated successfully!`);
      closeModal("generateBillModal");
      loadBills();
      viewPrintableInvoice(json.data.bill_id);
    } else {
      alert(`⚠️ ${json.message}`);
    }
  } catch (err) {
    console.error("Generate bill error:", err);
    alert("Network error generating bill.");
  }
}

async function payBill(billId) {
  if (!confirm(`Mark Invoice ${billId} as PAID?`)) return;

  try {
    const res = await fetch(`/api/bills/${billId}/pay`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ payment_method: "Credit Card / Cash" })
    });
    const json = await res.json();
    if (json.success) {
      alert("✓ Payment recorded successfully.");
      loadBills();
    }
  } catch (err) {
    console.error("Payment error:", err);
  }
}

async function viewPrintableInvoice(billId) {
  try {
    const res = await fetch("/api/bills");
    const json = await res.json();
    const bill = json.data.find(b => b.bill_id === billId);
    if (!bill) return;

    const invoiceContainer = document.getElementById("printableInvoiceContent");
    if (!invoiceContainer) return;

    invoiceContainer.innerHTML = `
      <div style="border: 2px solid var(--border-color); padding: 30px; border-radius: var(--radius-md); background: white;">
        <div style="display: flex; justify-content: space-between; border-bottom: 2px solid var(--primary); padding-bottom: 20px; margin-bottom: 20px;">
          <div>
            <h2 style="color: var(--primary); font-size: 24px; font-weight: 800;">METROPOLIS GENERAL HOSPITAL</h2>
            <p style="font-size: 12px; color: var(--text-muted);">Smart Hospital Management System (SHMS)</p>
            <p style="font-size: 12px; color: var(--text-muted);">100 Healthcare Blvd, Metro City • (555) 0100</p>
          </div>
          <div style="text-align: right;">
            <h3 style="font-size: 20px; color: var(--text-main);">OFFICIAL INVOICE</h3>
            <p style="font-size: 13px; font-weight: 700;">#${bill.bill_id}</p>
            <p style="font-size: 12px; color: var(--text-muted);">Date: ${bill.bill_date}</p>
            <span class="badge ${bill.status === 'Paid' ? 'badge-paid' : 'badge-pending'}" style="margin-top: 6px;">${bill.status}</span>
          </div>
        </div>

        <div style="margin-bottom: 24px; font-size: 13px;">
          <strong>Billed To:</strong><br>
          <span style="font-size: 15px; font-weight: 600;">${escapeHtml(bill.patient_name)}</span><br>
          Patient ID: ${bill.patient_id}
        </div>

        <table class="data-table" style="margin-bottom: 24px;">
          <thead>
            <tr>
              <th>Description</th>
              <th style="text-align: right;">Subtotal</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Physician Consultation Fee (OPD/Emergency)</td>
              <td style="text-align: right;">$${bill.consultation_fee.toFixed(2)}</td>
            </tr>
            <tr>
              <td>Inpatient Bed Accommodation (${bill.days_occupied || 0} days)</td>
              <td style="text-align: right;">$${bill.bed_charge.toFixed(2)}</td>
            </tr>
            <tr>
              <td>Diagnostic Laboratory & Radiology Procedures</td>
              <td style="text-align: right;">$${bill.lab_charges.toFixed(2)}</td>
            </tr>
            <tr>
              <td>Pharmacy Medications & Dispensed Prescriptions</td>
              <td style="text-align: right;">$${bill.medicine_charges.toFixed(2)}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <th style="font-weight: 600;">Subtotal:</th>
              <th style="text-align: right;">$${bill.subtotal.toFixed(2)}</th>
            </tr>
            ${bill.discount > 0 ? `
              <tr>
                <th style="color: var(--accent);">Institutional Discount:</th>
                <th style="text-align: right; color: var(--accent);">-$${bill.discount.toFixed(2)}</th>
              </tr>
            ` : ''}
            <tr style="font-size: 16px; border-top: 2px solid var(--text-main);">
              <th>Grand Total Due:</th>
              <th style="text-align: right; color: var(--primary);">$${bill.total_amount.toFixed(2)}</th>
            </tr>
            <tr>
              <th>Amount Paid (${escapeHtml(bill.payment_method)}):</th>
              <th style="text-align: right; color: var(--success);">$${bill.paid_amount.toFixed(2)}</th>
            </tr>
          </tfoot>
        </table>

        <div style="font-size: 11px; color: var(--text-muted); text-align: center; border-top: 1px dashed var(--border-color); padding-top: 12px;">
          Thank you for trusting Metropolis General Hospital. System-generated electronic document.
        </div>
      </div>
    `;

    openModal("printableInvoiceModal");
  } catch (err) {
    console.error("View invoice error:", err);
  }
}
