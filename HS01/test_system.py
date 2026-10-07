"""
test_system.py
Automated end-to-end integration and algorithmic verification suite for
Smart Hospital Management System (SHMS).
"""

import json
from datetime import datetime
from app import app
from helpers.json_db import read_data, find_by_id
from helpers.emergency_logic import evaluate_emergency_priority

def run_tests():
    print("=" * 70)
    print("  RUNNING SHMS AUTOMATED TEST & ALGORITHM VERIFICATION SUITE")
    print("=" * 70)

    client = app.test_client()

    # -------------------------------------------------------------
    # 1. AUTHENTICATION & RBAC
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Authentication for 7 RBAC Roles...")
    roles_test = [
        ("admin", "admin123", "Admin"),
        ("doctor_smith", "doc123", "Doctor"),
        ("nurse_sarah", "nurse123", "Nurse"),
        ("reception_jane", "rec123", "Receptionist"),
        ("lab_tech", "lab123", "Laboratory"),
        ("pharma_john", "pharma123", "Pharmacy"),
        ("patient_alice", "pat123", "Patient")
    ]

    for uname, pwd, expected_role in roles_test:
        res = client.post("/api/login", json={"username": uname, "password": pwd})
        assert res.status_code == 200, f"Login failed for {uname}"
        data = res.get_json()
        assert data["success"] is True
        assert data["user"]["role"] == expected_role
        print(f"  [OK] Authenticated {uname} successfully as role: {expected_role}")

    # Test bad password
    bad_res = client.post("/api/login", json={"username": "admin", "password": "wrongpassword"})
    assert bad_res.status_code == 401
    print("  [OK] Invalid password rejected with 401.")

    # -------------------------------------------------------------
    # 2. EMERGENCY PRIORITY ENGINE (Rule-Based Classifier)
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Smart Emergency Priority Engine Rules...")

    # Case A: SpO2 < 85% -> CRITICAL
    crit_eval = evaluate_emergency_priority({
        "spo2": 81,
        "systolic_bp": 190,
        "consciousness": "Alert",
        "trauma_level": "None"
    })
    assert crit_eval["priority"] == "CRITICAL", f"Expected CRITICAL, got {crit_eval['priority']}"
    assert crit_eval["triage_score"] >= 8
    print(f"  [OK] SpO2 81% + BP 190 classified as CRITICAL (Triage Score: {crit_eval['triage_score']}/10)")

    # Case B: High Fever > 103°F -> HIGH
    high_eval = evaluate_emergency_priority({
        "spo2": 96,
        "systolic_bp": 120,
        "temperature": 104.2,
        "symptoms": "Severe abdominal pain",
        "consciousness": "Alert"
    })
    assert high_eval["priority"] == "HIGH", f"Expected HIGH, got {high_eval['priority']}"
    print(f"  [OK] High Fever 104.2°F + Abdominal Pain classified as HIGH (Score: {high_eval['triage_score']}/10)")

    # Case C: Moderate Fracture -> MEDIUM
    med_eval = evaluate_emergency_priority({
        "spo2": 98,
        "systolic_bp": 122,
        "temperature": 98.6,
        "symptoms": "Fracture wrist from bicycle fall",
        "trauma_level": "Moderate"
    })
    assert med_eval["priority"] == "MEDIUM", f"Expected MEDIUM, got {med_eval['priority']}"
    print(f"  [OK] Moderate Fracture classified as MEDIUM (Score: {med_eval['triage_score']}/10)")

    # Case D: Stable Vitals -> LOW
    low_eval = evaluate_emergency_priority({
        "spo2": 99,
        "systolic_bp": 118,
        "temperature": 98.4,
        "symptoms": "Mild headache since morning",
        "consciousness": "Alert"
    })
    assert low_eval["priority"] == "LOW", f"Expected LOW, got {low_eval['priority']}"
    print(f"  [OK] Stable Vitals classified as LOW (Score: {low_eval['triage_score']}/10)")

    # Test via API endpoint
    client.post("/api/login", json={"username": "doctor_smith", "password": "doc123"})
    emg_api = client.post("/api/emergency", json={
        "patient_name": "Test Emergency Patient",
        "spo2": 80,
        "systolic_bp": 195,
        "symptoms": "Cardiac arrest symptoms",
        "consciousness": "Unconscious"
    })
    assert emg_api.status_code == 201
    assert emg_api.get_json()["data"]["priority"] == "CRITICAL"
    print("  [OK] API /api/emergency created and triaged patient record successfully.")

    # -------------------------------------------------------------
    # 3. PATIENT REGISTRATION & SEARCH
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Patient Management...")
    client.post("/api/login", json={"username": "admin", "password": "admin123"})
    new_pat_res = client.post("/api/patients", json={
        "name": "Integration Test Patient",
        "phone": "+1 555-9988",
        "age": 29,
        "gender": "Female",
        "blood_group": "B+",
        "email": "test.patient@example.com"
    })
    assert new_pat_res.status_code == 201
    pat_data = new_pat_res.get_json()["data"]
    new_pat_id = pat_data["patient_id"]
    assert new_pat_id.startswith("PAT")
    print(f"  [OK] Patient registered with auto-formatted ID: {new_pat_id}")

    # Search for patient
    search_res = client.get("/api/patients?query=Integration")
    assert search_res.status_code == 200
    search_json = search_res.get_json()
    assert search_json["count"] >= 1
    print(f"  [OK] Patient search returned {search_json['count']} matching result(s).")

    # -------------------------------------------------------------
    # 4. DOCTOR AVAILABILITY & APPOINTMENT SCHEDULING
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Doctor Availability & Appointments...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    avail_res = client.get(f"/api/doctors/DOC001/availability?date={today_str}")
    assert avail_res.status_code == 200
    avail_json = avail_res.get_json()
    print(f"  [OK] Doctor DOC001 has {len(avail_json['available_slots'])} open slots for {today_str}.")

    # Book appointment
    chosen_slot = avail_json["available_slots"][0] if avail_json["available_slots"] else "03:30 PM"
    book_res = client.post("/api/appointments", json={
        "patient_id": new_pat_id,
        "doctor_id": "DOC001",
        "appointment_date": today_str,
        "time_slot": chosen_slot,
        "purpose": "Routine cardiac checkup"
    })
    assert book_res.status_code == 201
    apt_data = book_res.get_json()["data"]
    print(f"  [OK] Booked appointment {apt_data['appointment_id']} with Token #{apt_data['token_number']}")

    # -------------------------------------------------------------
    # 5. CLINICAL CONSULTATION & PRESCRIPTION
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Clinical Consultation & E-Prescribing...")
    rx_res = client.post("/api/prescriptions", json={
        "patient_id": new_pat_id,
        "doctor_id": "DOC001",
        "medicines": [
            {
                "medicine_id": "MED001",
                "medicine_name": "Amoxicillin 500mg",
                "dosage": "1 cap",
                "frequency": "3 times daily",
                "quantity": 15,
                "unit_price": 12.50
            }
        ]
    })
    assert rx_res.status_code == 201
    rx_data = rx_res.get_json()["data"]
    assert rx_data["total_medicine_charge"] == 187.50
    print(f"  [OK] Issued Prescription {rx_data['prescription_id']} (Total: ${rx_data['total_medicine_charge']})")

    # -------------------------------------------------------------
    # 6. BED ALLOCATION & DISCHARGE
    # -------------------------------------------------------------
    print("\n[TEST 6] Testing Bed Allocation & Discharge...")
    alloc_res = client.post("/api/beds/BED003/allocate", json={"patient_id": new_pat_id})
    assert alloc_res.status_code == 200
    print("  [OK] Allocated ICU Bed BED003 to patient.")

    beds_res = client.get("/api/beds")
    assert beds_res.status_code == 200
    bed_audit = beds_res.get_json()["summary"]
    print(f"  [OK] Bed Census: Occupied: {bed_audit['occupied_beds']}, Available: {bed_audit['available_beds']}, Occupancy Rate: {bed_audit['occupancy_rate_pct']}%")

    # Discharge bed
    dc_res = client.post("/api/beds/BED003/discharge")
    assert dc_res.status_code == 200
    print("  [OK] Bed BED003 released and returned to Available.")

    # -------------------------------------------------------------
    # 7. AUTOMATED MULTI-FACTOR BILLING ENGINE
    # -------------------------------------------------------------
    print("\n[TEST 7] Testing Automated Billing Calculation Engine...")
    calc_res = client.get(f"/api/billing/calculate/{new_pat_id}")
    assert calc_res.status_code == 200
    bill_calc = calc_res.get_json()["breakdown"]

    print("  [OK] Calculation Formula Components:")
    print(f"    - Consultation Fee:      ${bill_calc['consultation_fee']:.2f}")
    print(f"    - Bed Charges:           ${bill_calc['bed_info']['bed_charge_total']:.2f}")
    print(f"    - Lab Charges:           ${bill_calc['lab_charges_total']:.2f}")
    print(f"    - Medicine Charges:      ${bill_calc['medicine_charges_total']:.2f}")
    print(f"    - Calculated Grand Total: ${bill_calc['total_amount']:.2f}")

    # Generate Official Invoice
    gen_bill_res = client.post("/api/billing", json={
        "patient_id": new_pat_id,
        "consultation_fee": bill_calc["consultation_fee"],
        "bed_charge": bill_calc["bed_info"]["bed_charge_total"],
        "days_occupied": bill_calc["bed_info"]["days_occupied"],
        "lab_charges": bill_calc["lab_charges_total"],
        "medicine_charges": bill_calc["medicine_charges_total"],
        "discount": 10.0,
        "paid_amount": bill_calc["total_amount"] - 10.0,
        "payment_method": "Cash"
    })
    assert gen_bill_res.status_code == 201
    final_bill = gen_bill_res.get_json()["data"]
    print(f"  [OK] Official Bill {final_bill['bill_id']} recorded with status: {final_bill['status']}")

    # -------------------------------------------------------------
    # 8. PHARMACY INVENTORY & DYNAMIC EXPIRY WATCHER
    # -------------------------------------------------------------
    print("\n[TEST 8] Testing Pharmacy Inventory & Expiry Watcher...")
    meds_res = client.get("/api/medicines")
    assert meds_res.status_code == 200
    med_summary = meds_res.get_json()["summary"]
    print(f"  [OK] Evaluated {med_summary['total_medicines']} inventory items.")
    print(f"    - Low Stock Count:    {med_summary['low_stock_count']}")
    print(f"    - Expiring Soon (<30d): {med_summary['expiring_soon_count']}")
    print(f"    - Expired Count:      {med_summary['expired_count']}")

    # -------------------------------------------------------------
    # 9. DASHBOARD STATS AGGREGATION & AUDIT LOGS
    # -------------------------------------------------------------
    print("\n[TEST 9] Testing Dashboard Aggregated KPIs & Audit Logging...")
    stats_res = client.get("/api/dashboard/stats")
    assert stats_res.status_code == 200
    kpis = stats_res.get_json()["stats"]
    print(f"  [OK] Dashboard KPIs:")
    print(f"    - Total Patients: {kpis['total_patients']}")
    print(f"    - Total Doctors:  {kpis['total_doctors']}")
    print(f"    - Total Revenue:  ${kpis['total_revenue']:.2f}")

    logs_res = client.get("/api/activity-logs?limit=5")
    assert logs_res.status_code == 200
    logs = logs_res.get_json()["data"]
    assert len(logs) > 0
    print(f"  [OK] Activity Logs retrieved ({len(logs)} recent actions logged in activity_logs.json).")

    print("\n" + "=" * 70)
    print("  ALL TESTS PASSED SUCCESSFULLY! SYSTEM IS 100% OPERATIONAL.")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
