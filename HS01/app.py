"""
app.py
Smart Hospital Management System (SHMS) - Core Flask Application & REST API
Academic Final Year College Project.

Features:
- Thread-safe JSON storage integration
- Role-Based Access Control (Admin, Doctor, Nurse, Receptionist, Laboratory, Pharmacy, Patient)
- Smart Emergency Priority Triage Engine
- Automated Hospital Billing Engine
- Dynamic Medicine Inventory & Expiry Watcher
- Comprehensive Activity Auditing
"""

import os
import secrets
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

from helpers.json_db import (
    read_data, write_data, insert_record, update_record,
    delete_record, find_by_id, filter_data, generate_next_id,
    log_activity
)
from helpers.auth import (
    authenticate_user, login_required, role_required,
    get_current_user, hash_password
)
from helpers.emergency_logic import evaluate_emergency_priority, check_bed_availability

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "shms-super-secret-key-college-final-year-2026")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ============================================================================
# TEMPLATE CONTEXT PROCESSOR & PAGE ROUTES
# ============================================================================

@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())


@app.route("/")
def index():
    """Public Hospital Homepage with services, doctor showcase, and quick links."""
    return render_template("index.html")


@app.route("/login")
def login_page():
    """Central Role-Based Login Portal."""
    user = get_current_user()
    if user:
        return redirect(url_for("role_dashboard"))
    return render_template("login.html")


@app.route("/unauthorized")
def unauthorized_page():
    """Displays 403 Forbidden page for restricted roles."""
    return render_template("login.html", error_message="Access Denied: You do not have permission to view that module.")


@app.route("/dashboard")
@login_required
def role_dashboard():
    """Routes user to their appropriate role-specific dashboard."""
    user = get_current_user()
    role = user.get("role", "").lower()

    role_redirects = {
        "admin": "admin_dashboard",
        "doctor": "doctor_dashboard",
        "nurse": "nurse_dashboard",
        "receptionist": "receptionist_dashboard",
        "laboratory": "laboratory_dashboard",
        "pharmacy": "pharmacy_dashboard",
        "patient": "patient_dashboard"
    }

    target_endpoint = role_redirects.get(role, "admin_dashboard")
    return redirect(url_for(target_endpoint))


@app.route("/dashboard/admin")
@login_required
@role_required(["Admin"])
def admin_dashboard():
    return render_template("admin_dashboard.html")


@app.route("/dashboard/doctor")
@login_required
@role_required(["Doctor", "Admin"])
def doctor_dashboard():
    return render_template("doctor_dashboard.html")


@app.route("/dashboard/nurse")
@login_required
@role_required(["Nurse", "Admin"])
def nurse_dashboard():
    return render_template("nurse_dashboard.html")


@app.route("/dashboard/receptionist")
@login_required
@role_required(["Receptionist", "Admin"])
def receptionist_dashboard():
    return render_template("receptionist_dashboard.html")


@app.route("/dashboard/laboratory")
@login_required
@role_required(["Laboratory", "Admin"])
def laboratory_dashboard():
    return render_template("laboratory_dashboard.html")


@app.route("/dashboard/pharmacy")
@login_required
@role_required(["Pharmacy", "Admin"])
def pharmacy_dashboard():
    return render_template("pharmacy_dashboard.html")


@app.route("/dashboard/patient")
@login_required
@role_required(["Patient", "Admin"])
def patient_dashboard():
    return render_template("patient_dashboard.html")


# ============================================================================
# AUTHENTICATION REST APIS
# ============================================================================

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    user, error = authenticate_user(username, password)
    if error:
        return jsonify({"success": False, "message": error}), 401

    session["user"] = user
    log_activity(user["user_id"], user["role"], f"User {user['username']} logged in", "Authentication")

    return jsonify({
        "success": True,
        "message": f"Welcome back, {user['name']}!",
        "user": user,
        "redirect_url": url_for(f"{user['role'].lower()}_dashboard")
    })


@app.route("/api/logout", methods=["POST", "GET"])
def api_logout():
    user = get_current_user()
    if user:
        log_activity(user["user_id"], user["role"], f"User {user['username']} logged out", "Authentication")
    session.clear()
    if request.is_json or request.path.startswith("/api/"):
        return jsonify({"success": True, "message": "Logged out successfully"})
    return redirect(url_for("login_page"))


@app.route("/api/current-user", methods=["GET"])
def api_current_user():
    user = get_current_user()
    return jsonify({"success": True, "user": user})


# ============================================================================
# PATIENTS REST APIS
# ============================================================================

@app.route("/api/patients", methods=["GET"])
@login_required
def api_get_patients():
    query = request.args.get("query", "").strip().lower()
    patients = read_data("patients")

    if query:
        patients = [
            p for p in patients
            if query in str(p.get("patient_id", "")).lower()
            or query in str(p.get("name", "")).lower()
            or query in str(p.get("phone", "")).lower()
            or query in str(p.get("email", "")).lower()
            or query in str(p.get("blood_group", "")).lower()
        ]

    return jsonify({"success": True, "count": len(patients), "data": patients})


@app.route("/api/patients", methods=["POST"])
@login_required
@role_required(["Admin", "Receptionist", "Nurse"])
def api_create_patient():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()

    if not name or not phone:
        return jsonify({"success": False, "message": "Patient Name and Phone Number are required."}), 400

    new_patient = {
        "patient_id": generate_next_id("patients", "PAT", "patient_id", digits=3),
        "name": name,
        "age": int(data.get("age", 0)) if data.get("age") else None,
        "gender": data.get("gender", "Other"),
        "blood_group": data.get("blood_group", "Unknown"),
        "phone": phone,
        "email": data.get("email", "").strip(),
        "address": data.get("address", "").strip(),
        "emergency_contact": data.get("emergency_contact", "").strip(),
        "registration_date": datetime.now().strftime("%Y-%m-%d"),
        "status": data.get("status", "Outpatient"),
        "allergies": [a.strip() for a in data.get("allergies", "").split(",") if a.strip()] if isinstance(data.get("allergies"), str) else data.get("allergies", []),
        "chronic_conditions": [c.strip() for c in data.get("chronic_conditions", "").split(",") if c.strip()] if isinstance(data.get("chronic_conditions"), str) else data.get("chronic_conditions", [])
    }

    inserted = insert_record("patients", new_patient, id_field="patient_id")
    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Registered new patient {new_patient['name']} ({new_patient['patient_id']})", "Patient Management")

    return jsonify({"success": True, "message": "Patient registered successfully", "data": inserted}), 201


@app.route("/api/patients/<id>", methods=["GET"])
@login_required
def api_get_patient_by_id(id):
    patient = find_by_id("patients", id, "patient_id")
    if not patient:
        return jsonify({"success": False, "message": "Patient not found."}), 404

    # Attach related records for comprehensive profile lookup
    appointments = filter_data("appointments", lambda a: a.get("patient_id") == id)
    medical_records = filter_data("medical_records", lambda m: m.get("patient_id") == id)
    prescriptions = filter_data("prescriptions", lambda p: p.get("patient_id") == id)
    lab_reports = filter_data("lab_reports", lambda r: r.get("patient_id") == id)
    bills = filter_data("bills", lambda b: b.get("patient_id") == id)

    return jsonify({
        "success": True,
        "patient": patient,
        "history": {
            "appointments": appointments,
            "medical_records": medical_records,
            "prescriptions": prescriptions,
            "lab_reports": lab_reports,
            "bills": bills
        }
    })


@app.route("/api/patients/<id>", methods=["PUT"])
@login_required
@role_required(["Admin", "Receptionist", "Doctor", "Nurse"])
def api_update_patient(id):
    data = request.get_json() or {}
    updated = update_record("patients", id, data, "patient_id")
    if not updated:
        return jsonify({"success": False, "message": "Patient not found."}), 404

    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Updated record for patient {id}", "Patient Management")
    return jsonify({"success": True, "message": "Patient details updated", "data": updated})


@app.route("/api/patients/<id>", methods=["DELETE"])
@login_required
@role_required(["Admin"])
def api_delete_patient(id):
    deleted = delete_record("patients", id, "patient_id")
    if not deleted:
        return jsonify({"success": False, "message": "Patient not found."}), 404

    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Deleted patient record {id}", "Patient Management")
    return jsonify({"success": True, "message": f"Patient {id} removed."})


# ============================================================================
# DOCTORS REST APIS
# ============================================================================

@app.route("/api/doctors", methods=["GET"])
@login_required
def api_get_doctors():
    department = request.args.get("department")
    doctors = read_data("doctors")
    if department:
        doctors = [d for d in doctors if d.get("department", "").lower() == department.lower()]
    return jsonify({"success": True, "count": len(doctors), "data": doctors})


@app.route("/api/doctors", methods=["POST"])
@login_required
@role_required(["Admin"])
def api_create_doctor():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    specialization = data.get("specialization", "").strip()

    if not name or not specialization:
        return jsonify({"success": False, "message": "Name and Specialization are required."}), 400

    new_doc = {
        "doctor_id": generate_next_id("doctors", "DOC", "doctor_id", digits=3),
        "name": name,
        "specialization": specialization,
        "department": data.get("department", specialization),
        "qualification": data.get("qualification", "MBBS, MD"),
        "experience_years": int(data.get("experience_years", 5)),
        "phone": data.get("phone", ""),
        "email": data.get("email", ""),
        "opd_fee": float(data.get("opd_fee", 100.0)),
        "room_no": data.get("room_no", "OPD-101"),
        "working_days": data.get("working_days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
        "available_slots": data.get("available_slots", ["09:00 AM", "10:00 AM", "11:30 AM", "02:00 PM", "03:30 PM"]),
        "is_available": True
    }

    inserted = insert_record("doctors", new_doc, id_field="doctor_id")
    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Created doctor profile for {new_doc['name']} ({new_doc['doctor_id']})", "Doctor Management")

    return jsonify({"success": True, "message": "Doctor profile created successfully", "data": inserted}), 201


@app.route("/api/doctors/<id>/availability", methods=["GET"])
@login_required
def api_doctor_availability(id):
    """
    Checks doctor's working schedule and booked slots for a given date.
    Returns list of remaining open slots.
    """
    req_date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    doc = find_by_id("doctors", id, "doctor_id")
    if not doc:
        return jsonify({"success": False, "message": "Doctor not found."}), 404

    all_slots = doc.get("available_slots", ["09:00 AM", "10:00 AM", "11:30 AM", "02:00 PM", "03:30 PM"])
    appointments = filter_data("appointments", lambda a: a.get("doctor_id") == id and a.get("appointment_date") == req_date and a.get("status") != "Cancelled")
    booked_slots = [a.get("time_slot") for a in appointments]

    available_slots = [slot for slot in all_slots if slot not in booked_slots]

    return jsonify({
        "success": True,
        "doctor": doc,
        "date": req_date,
        "all_slots": all_slots,
        "booked_slots": booked_slots,
        "available_slots": available_slots,
        "has_open_slots": len(available_slots) > 0
    })


# ============================================================================
# APPOINTMENTS REST APIS
# ============================================================================

@app.route("/api/appointments", methods=["GET"])
@login_required
def api_get_appointments():
    date_filter = request.args.get("date")
    doc_filter = request.args.get("doctor_id")
    pat_filter = request.args.get("patient_id")
    status_filter = request.args.get("status")

    user = get_current_user()
    appointments = read_data("appointments")

    # If patient is viewing, automatically scope to their patient record
    if user.get("role") == "Patient" and user.get("associated_id"):
        appointments = [a for a in appointments if a.get("patient_id") == user["associated_id"]]
    elif user.get("role") == "Doctor" and user.get("associated_id") and not doc_filter:
        appointments = [a for a in appointments if a.get("doctor_id") == user["associated_id"]]

    if date_filter:
        appointments = [a for a in appointments if a.get("appointment_date") == date_filter]
    if doc_filter:
        appointments = [a for a in appointments if a.get("doctor_id") == doc_filter]
    if pat_filter:
        appointments = [a for a in appointments if a.get("patient_id") == pat_filter]
    if status_filter:
        appointments = [a for a in appointments if a.get("status", "").lower() == status_filter.lower()]

    return jsonify({"success": True, "count": len(appointments), "data": appointments})


@app.route("/api/appointments", methods=["POST"])
@login_required
def api_create_appointment():
    data = request.get_json() or {}
    patient_id = data.get("patient_id", "").strip()
    doctor_id = data.get("doctor_id", "").strip()
    apt_date = data.get("appointment_date", datetime.now().strftime("%Y-%m-%d"))
    time_slot = data.get("time_slot", "").strip()

    if not patient_id or not doctor_id or not time_slot:
        return jsonify({"success": False, "message": "Patient ID, Doctor ID, and Time Slot are required."}), 400

    patient = find_by_id("patients", patient_id, "patient_id")
    doctor = find_by_id("doctors", doctor_id, "doctor_id")

    if not patient:
        return jsonify({"success": False, "message": f"Patient with ID {patient_id} does not exist."}), 404
    if not doctor:
        return jsonify({"success": False, "message": f"Doctor with ID {doctor_id} does not exist."}), 404

    # Check slot conflict
    existing = filter_data("appointments", lambda a: a.get("doctor_id") == doctor_id and a.get("appointment_date") == apt_date and a.get("time_slot") == time_slot and a.get("status") != "Cancelled")
    if existing:
        return jsonify({"success": False, "message": f"Time slot {time_slot} is already booked for Dr. {doctor['name']} on {apt_date}."}), 409

    # Calculate token number for doctor on that date
    same_day_apts = filter_data("appointments", lambda a: a.get("doctor_id") == doctor_id and a.get("appointment_date") == apt_date)
    token_num = len(same_day_apts) + 1

    new_apt = {
        "appointment_id": generate_next_id("appointments", "APT", "appointment_id", digits=3),
        "patient_id": patient_id,
        "patient_name": patient.get("name"),
        "doctor_id": doctor_id,
        "doctor_name": doctor.get("name"),
        "department": doctor.get("department"),
        "appointment_date": apt_date,
        "time_slot": time_slot,
        "token_number": token_num,
        "status": "Scheduled",
        "purpose": data.get("purpose", "General OPD consultation"),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    inserted = insert_record("appointments", new_apt, id_field="appointment_id")
    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Booked appointment {new_apt['appointment_id']} (Token #{token_num}) for {patient.get('name')} with {doctor.get('name')}", "Appointments")

    return jsonify({"success": True, "message": f"Appointment booked successfully! Token #{token_num}", "data": inserted}), 201


@app.route("/api/appointments/<id>/status", methods=["PUT"])
@login_required
@role_required(["Admin", "Doctor", "Receptionist", "Nurse"])
def api_update_appointment_status(id):
    data = request.get_json() or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"success": False, "message": "Status is required."}), 400

    updated = update_record("appointments", id, {"status": new_status}, "appointment_id")
    if not updated:
        return jsonify({"success": False, "message": "Appointment not found."}), 404

    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Updated status of appointment {id} to '{new_status}'", "Appointments")
    return jsonify({"success": True, "message": "Appointment status updated", "data": updated})


# ============================================================================
# EMERGENCY & TRIAGE PRIORITY REST APIS
# ============================================================================

@app.route("/api/emergency", methods=["GET"])
@login_required
def api_get_emergencies():
    emergencies = read_data("emergency")
    # Sort with CRITICAL first, then HIGH, MEDIUM, LOW
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    emergencies.sort(key=lambda x: priority_order.get(x.get("priority", "LOW"), 4))
    return jsonify({"success": True, "count": len(emergencies), "data": emergencies})


@app.route("/api/emergency", methods=["POST"])
@login_required
@role_required(["Admin", "Doctor", "Nurse", "Receptionist"])
def api_create_emergency():
    """
    Evaluates patient vital signs and symptoms using the Smart Emergency Priority Engine,
    assigns triage level (CRITICAL, HIGH, MEDIUM, LOW), logs to emergency.json,
    and returns immediate alerts if ICU/Emergency bed shortage is detected.
    """
    data = request.get_json() or {}
    patient_name = data.get("patient_name", "").strip()
    if not patient_name:
        return jsonify({"success": False, "message": "Patient Name is required for Emergency registration."}), 400

    # Execute Rule-Based Emergency Priority Classifier
    triage_evaluation = evaluate_emergency_priority(data)

    new_emg = {
        "emergency_id": generate_next_id("emergency", "EMG", "emergency_id", digits=3),
        "patient_name": patient_name,
        "age": int(data.get("age", 0)) if data.get("age") else None,
        "gender": data.get("gender", "Unknown"),
        "vitals": {
            "spo2": float(data.get("spo2", 98)),
            "systolic_bp": float(data.get("systolic_bp", 120)),
            "diastolic_bp": float(data.get("diastolic_bp", 80)),
            "heart_rate": float(data.get("heart_rate", 75)),
            "temperature": float(data.get("temperature", 98.6))
        },
        "symptoms": data.get("symptoms", "Acute Distress"),
        "consciousness": data.get("consciousness", "Alert"),
        "trauma_level": data.get("trauma_level", "None"),
        "priority": triage_evaluation["priority"],
        "triage_score": triage_evaluation["triage_score"],
        "reasons": triage_evaluation["reasons"],
        "recommended_bed_type": triage_evaluation["recommended_bed_type"],
        "assigned_bed": data.get("assigned_bed", None),
        "attending_doctor": data.get("attending_doctor", "On-Duty ER Physician"),
        "triage_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Under Care"
    }

    inserted = insert_record("emergency", new_emg, id_field="emergency_id")
    user = get_current_user()
    log_activity(
        user["user_id"],
        user["role"],
        f"Emergency triage: {new_emg['patient_name']} classified as {triage_evaluation['priority']} (Score: {triage_evaluation['triage_score']}/10)",
        "Emergency Management"
    )

    return jsonify({
        "success": True,
        "message": f"Emergency admission classified as {triage_evaluation['priority']}",
        "data": inserted,
        "triage_evaluation": triage_evaluation
    }), 201


@app.route("/api/emergency/<id>/status", methods=["PUT"])
@login_required
@role_required(["Admin", "Doctor", "Nurse"])
def api_update_emergency_status(id):
    data = request.get_json() or {}
    updated = update_record("emergency", id, data, "emergency_id")
    if not updated:
        return jsonify({"success": False, "message": "Emergency case not found."}), 404

    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Updated emergency case {id} status to '{data.get('status', 'Updated')}'", "Emergency Management")
    return jsonify({"success": True, "message": "Emergency status updated", "data": updated})


# ============================================================================
# BED & WARD MANAGEMENT REST APIS
# ============================================================================

@app.route("/api/beds", methods=["GET"])
@login_required
def api_get_beds():
    beds = read_data("beds")
    audit = check_bed_availability()
    return jsonify({
        "success": True,
        "summary": audit,
        "beds": beds
    })


@app.route("/api/beds", methods=["POST"])
@login_required
@role_required(["Admin"])
def api_create_bed():
    data = request.get_json() or {}
    bed_number = data.get("bed_number", "").strip()
    ward_type = data.get("ward_type", "General Ward").strip()

    if not bed_number:
        return jsonify({"success": False, "message": "Bed number is required."}), 400

    new_bed = {
        "bed_id": generate_next_id("beds", "BED", "bed_id", digits=3),
        "bed_number": bed_number,
        "ward_type": ward_type,
        "room_no": data.get("room_no", "Ward-A"),
        "daily_rate": float(data.get("daily_rate", 100.0)),
        "status": "Available",
        "patient_id": None,
        "patient_name": None,
        "assigned_date": None
    }

    inserted = insert_record("beds", new_bed, id_field="bed_id")
    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Created new bed {new_bed['bed_number']} ({new_bed['ward_type']})", "Bed Management")

    return jsonify({"success": True, "message": "Bed registered successfully", "data": inserted}), 201


@app.route("/api/beds/<id>/allocate", methods=["POST"])
@login_required
@role_required(["Admin", "Doctor", "Nurse", "Receptionist"])
def api_allocate_bed(id):
    """
    Allocates a bed to a patient, updates bed status to 'Occupied',
    and updates patient status to 'Inpatient' with admission date.
    """
    data = request.get_json() or {}
    patient_id = data.get("patient_id", "").strip()
    if not patient_id:
        return jsonify({"success": False, "message": "Patient ID is required."}), 400

    bed = find_by_id("beds", id, "bed_id")
    if not bed:
        return jsonify({"success": False, "message": "Bed not found."}), 404

    if bed.get("status") == "Occupied":
        return jsonify({"success": False, "message": f"Bed {bed.get('bed_number')} is already occupied."}), 409

    patient = find_by_id("patients", patient_id, "patient_id")
    if not patient:
        return jsonify({"success": False, "message": f"Patient {patient_id} not found."}), 404

    now_date = datetime.now().strftime("%Y-%m-%d")

    # Update bed
    updated_bed = update_record("beds", id, {
        "status": "Occupied",
        "patient_id": patient_id,
        "patient_name": patient.get("name"),
        "assigned_date": now_date
    }, "bed_id")

    # Update patient
    update_record("patients", patient_id, {
        "status": "Inpatient",
        "bed_id": id,
        "admission_date": now_date
    }, "patient_id")

    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Allocated bed {bed.get('bed_number')} to patient {patient.get('name')} ({patient_id})", "Bed Management")

    return jsonify({"success": True, "message": f"Bed {bed.get('bed_number')} successfully allocated.", "bed": updated_bed})


@app.route("/api/beds/<id>/discharge", methods=["POST"])
@login_required
@role_required(["Admin", "Doctor", "Nurse", "Receptionist"])
def api_discharge_bed(id):
    """
    Releases bed back to 'Available' status and marks patient as 'Discharged'.
    """
    bed = find_by_id("beds", id, "bed_id")
    if not bed:
        return jsonify({"success": False, "message": "Bed not found."}), 404

    patient_id = bed.get("patient_id")
    patient_name = bed.get("patient_name")

    # Update bed
    updated_bed = update_record("beds", id, {
        "status": "Available",
        "patient_id": None,
        "patient_name": None,
        "assigned_date": None
    }, "bed_id")

    # Update patient if attached
    if patient_id:
        update_record("patients", patient_id, {
            "status": "Discharged",
            "bed_id": None
        }, "patient_id")

    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Discharged bed {bed.get('bed_number')} (Previously: {patient_name})", "Bed Management")

    return jsonify({"success": True, "message": f"Bed {bed.get('bed_number')} released and marked Available.", "bed": updated_bed})


# ============================================================================
# MEDICAL RECORDS & CONSULTATION REST APIS
# ============================================================================

@app.route("/api/medical-records", methods=["GET"])
@login_required
def api_get_medical_records():
    pat_filter = request.args.get("patient_id")
    doc_filter = request.args.get("doctor_id")
    records = read_data("medical_records")

    if pat_filter:
        records = [r for r in records if r.get("patient_id") == pat_filter]
    if doc_filter:
        records = [r for r in records if r.get("doctor_id") == doc_filter]

    return jsonify({"success": True, "count": len(records), "data": records})


@app.route("/api/medical-records", methods=["POST"])
@login_required
@role_required(["Doctor", "Admin"])
def api_create_medical_record():
    data = request.get_json() or {}
    patient_id = data.get("patient_id", "").strip()
    doctor_id = data.get("doctor_id", "").strip()
    diagnosis = data.get("diagnosis", "").strip()

    if not patient_id or not diagnosis:
        return jsonify({"success": False, "message": "Patient ID and Clinical Diagnosis are required."}), 400

    new_record = {
        "record_id": generate_next_id("medical_records", "MR", "record_id", digits=3),
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "appointment_id": data.get("appointment_id"),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symptoms": data.get("symptoms", ""),
        "vitals": data.get("vitals", {}),
        "diagnosis": diagnosis,
        "doctor_notes": data.get("doctor_notes", ""),
        "prescription_id": data.get("prescription_id"),
        "lab_order_ids": data.get("lab_order_ids", [])
    }

    inserted = insert_record("medical_records", new_record, id_field="record_id")

    # If appointment was attached, mark it completed
    if data.get("appointment_id"):
        update_record("appointments", data.get("appointment_id"), {"status": "Completed"}, "appointment_id")

    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Added clinical consultation record {new_record['record_id']} for Patient {patient_id}", "Medical Records")

    return jsonify({"success": True, "message": "Medical record saved successfully", "data": inserted}), 201


@app.route("/api/medical-records/patient/<id>", methods=["GET"])
@login_required
def api_patient_medical_records(id):
    records = filter_data("medical_records", lambda r: r.get("patient_id") == id)
    return jsonify({"success": True, "patient_id": id, "records": records})


# ============================================================================
# PRESCRIPTIONS REST APIS
# ============================================================================

@app.route("/api/prescriptions", methods=["GET"])
@login_required
def api_get_prescriptions():
    pat_filter = request.args.get("patient_id")
    user = get_current_user()
    prescriptions = read_data("prescriptions")

    if user.get("role") == "Patient" and user.get("associated_id"):
        prescriptions = [p for p in prescriptions if p.get("patient_id") == user["associated_id"]]
    elif pat_filter:
        prescriptions = [p for p in prescriptions if p.get("patient_id") == pat_filter]

    return jsonify({"success": True, "count": len(prescriptions), "data": prescriptions})


@app.route("/api/prescriptions", methods=["POST"])
@login_required
@role_required(["Doctor", "Admin"])
def api_create_prescription():
    data = request.get_json() or {}
    patient_id = data.get("patient_id", "").strip()
    doctor_id = data.get("doctor_id", "").strip()
    medicines_list = data.get("medicines", [])

    if not patient_id or not medicines_list:
        return jsonify({"success": False, "message": "Patient ID and at least one medicine are required."}), 400

    # Calculate itemized subtotals and prescription total
    total_med_cost = 0.0
    for med in medicines_list:
        unit_price = float(med.get("unit_price", 0.0))
        qty = int(med.get("quantity", 1))
        subtotal = round(unit_price * qty, 2)
        med["subtotal"] = subtotal
        total_med_cost += subtotal

    new_rx = {
        "prescription_id": generate_next_id("prescriptions", "RX", "prescription_id", digits=3),
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "diagnosis": data.get("diagnosis", ""),
        "medicines": medicines_list,
        "total_medicine_charge": round(total_med_cost, 2),
        "dispense_status": "Pending"
    }

    inserted = insert_record("prescriptions", new_rx, id_field="prescription_id")
    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Issued prescription {new_rx['prescription_id']} for Patient {patient_id} (${total_med_cost})", "Prescriptions")

    return jsonify({"success": True, "message": "Prescription generated successfully", "data": inserted}), 201


@app.route("/api/prescriptions/<id>/dispense", methods=["POST"])
@login_required
@role_required(["Pharmacy", "Admin"])
def api_dispense_prescription(id):
    """
    Pharmacy marks prescription as Dispensed and decrements medicine inventory stock.
    """
    rx = find_by_id("prescriptions", id, "prescription_id")
    if not rx:
        return jsonify({"success": False, "message": "Prescription not found."}), 404

    if rx.get("dispense_status") == "Dispensed":
        return jsonify({"success": False, "message": "Prescription has already been dispensed."}), 400

    # Deduct stock for each prescribed item
    medicines = read_data("medicines")
    for prescribed in rx.get("medicines", []):
        med_id = prescribed.get("medicine_id")
        qty = int(prescribed.get("quantity", 1))

        for m in medicines:
            if m.get("medicine_id") == med_id:
                m["stock_quantity"] = max(0, m.get("stock_quantity", 0) - qty)
                # Update status if low
                if m["stock_quantity"] <= m.get("min_threshold", 20):
                    m["status"] = "LOW_STOCK"
                break

    write_data("medicines", medicines)

    # Mark RX as Dispensed
    updated_rx = update_record("prescriptions", id, {"dispense_status": "Dispensed"}, "prescription_id")
    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Dispensed prescription {id} and updated medicine stocks", "Pharmacy")

    return jsonify({"success": True, "message": f"Prescription {id} dispensed successfully", "data": updated_rx})


# ============================================================================
# LABORATORY REST APIS
# ============================================================================

@app.route("/api/laboratory/tests", methods=["GET"])
@login_required
def api_get_lab_tests():
    tests = read_data("laboratory_tests")
    return jsonify({"success": True, "count": len(tests), "data": tests})


@app.route("/api/laboratory/tests", methods=["POST"])
@login_required
@role_required(["Admin", "Laboratory"])
def api_create_lab_test():
    data = request.get_json() or {}
    test_name = data.get("test_name", "").strip()
    if not test_name:
        return jsonify({"success": False, "message": "Test name is required."}), 400

    new_test = {
        "test_id": generate_next_id("laboratory_tests", "LAB", "test_id", digits=3),
        "test_name": test_name,
        "department": data.get("department", "Diagnostic Pathology"),
        "price": float(data.get("price", 50.0)),
        "normal_range": data.get("normal_range", "N/A"),
        "sample_type": data.get("sample_type", "Blood"),
        "turnaround_hours": int(data.get("turnaround_hours", 4))
    }

    inserted = insert_record("laboratory_tests", new_test, id_field="test_id")
    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Added diagnostic test '{new_test['test_name']}' to catalog", "Laboratory")

    return jsonify({"success": True, "message": "Laboratory test added", "data": inserted}), 201


@app.route("/api/laboratory/reports", methods=["GET"])
@login_required
def api_get_lab_reports():
    pat_filter = request.args.get("patient_id")
    status_filter = request.args.get("status")
    user = get_current_user()
    reports = read_data("lab_reports")

    if user.get("role") == "Patient" and user.get("associated_id"):
        reports = [r for r in reports if r.get("patient_id") == user["associated_id"]]
    elif pat_filter:
        reports = [r for r in reports if r.get("patient_id") == pat_filter]

    if status_filter:
        reports = [r for r in reports if r.get("status", "").lower() == status_filter.lower()]

    return jsonify({"success": True, "count": len(reports), "data": reports})


@app.route("/api/laboratory/reports", methods=["POST"])
@login_required
@role_required(["Doctor", "Admin", "Laboratory"])
def api_order_lab_test():
    data = request.get_json() or {}
    patient_id = data.get("patient_id", "").strip()
    test_id = data.get("test_id", "").strip()

    if not patient_id or not test_id:
        return jsonify({"success": False, "message": "Patient ID and Test ID are required."}), 400

    patient = find_by_id("patients", patient_id, "patient_id")
    test = find_by_id("laboratory_tests", test_id, "test_id")

    if not patient:
        return jsonify({"success": False, "message": "Patient not found."}), 404
    if not test:
        return jsonify({"success": False, "message": "Diagnostic test not found."}), 404

    new_report = {
        "report_id": generate_next_id("lab_reports", "REP", "report_id", digits=3),
        "patient_id": patient_id,
        "patient_name": patient.get("name"),
        "doctor_id": data.get("doctor_id", "DOC001"),
        "test_id": test_id,
        "test_name": test.get("test_name"),
        "ordered_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Pending",
        "results": {},
        "technician_notes": data.get("notes", "Specimen collected and pending analysis."),
        "completed_date": None,
        "cost": float(test.get("price", 50.0))
    }

    inserted = insert_record("lab_reports", new_report, id_field="report_id")
    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Requested Lab Order {new_report['report_id']} ({test.get('test_name')}) for {patient.get('name')}", "Laboratory")

    return jsonify({"success": True, "message": "Lab test order placed successfully", "data": inserted}), 201


@app.route("/api/laboratory/reports/<id>/result", methods=["PUT"])
@login_required
@role_required(["Laboratory", "Admin"])
def api_submit_lab_result(id):
    data = request.get_json() or {}
    results = data.get("results", {})
    notes = data.get("technician_notes", "Analysis verified by laboratory.")

    report = find_by_id("lab_reports", id, "report_id")
    if not report:
        return jsonify({"success": False, "message": "Report order not found."}), 404

    updated = update_record("lab_reports", id, {
        "results": results,
        "technician_notes": notes,
        "status": "Completed",
        "completed_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }, "report_id")

    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Published lab results for Report {id} ({report.get('test_name')})", "Laboratory")

    return jsonify({"success": True, "message": "Test report finalized and signed off.", "data": updated})


# ============================================================================
# MEDICINE INVENTORY & PHARMACY REST APIS
# ============================================================================

@app.route("/api/medicines", methods=["GET"])
@login_required
def api_get_medicines():
    """
    Evaluates inventory dynamic conditions:
    - stock_quantity <= min_threshold -> 'LOW_STOCK'
    - expiry_date - today <= 30 days -> 'EXPIRING_SOON'
    - expiry_date < today -> 'EXPIRED'
    """
    medicines = read_data("medicines")
    today = date.today()

    low_stock_count = 0
    expiring_soon_count = 0
    expired_count = 0

    for med in medicines:
        stock = int(med.get("stock_quantity", 0))
        threshold = int(med.get("min_threshold", 20))
        exp_str = med.get("expiry_date", "")

        is_expired = False
        is_expiring = False

        if exp_str:
            try:
                exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
                days_left = (exp_date - today).days
                if days_left < 0:
                    is_expired = True
                    med["status"] = "EXPIRED"
                    expired_count += 1
                elif days_left <= 30:
                    is_expiring = True
                    med["status"] = "EXPIRING_SOON"
                    expiring_soon_count += 1
            except ValueError:
                pass

        if not is_expired and not is_expiring:
            if stock <= threshold:
                med["status"] = "LOW_STOCK"
                low_stock_count += 1
            else:
                med["status"] = "IN_STOCK"

    # Save any computed statuses back for consistency
    write_data("medicines", medicines)

    return jsonify({
        "success": True,
        "summary": {
            "total_medicines": len(medicines),
            "low_stock_count": low_stock_count,
            "expiring_soon_count": expiring_soon_count,
            "expired_count": expired_count
        },
        "data": medicines
    })


@app.route("/api/medicines", methods=["POST"])
@login_required
@role_required(["Pharmacy", "Admin"])
def api_create_medicine():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"success": False, "message": "Medicine name is required."}), 400

    new_med = {
        "medicine_id": generate_next_id("medicines", "MED", "medicine_id", digits=3),
        "name": name,
        "generic_name": data.get("generic_name", name),
        "category": data.get("category", "General"),
        "form": data.get("form", "Tablet"),
        "stock_quantity": int(data.get("stock_quantity", 100)),
        "min_threshold": int(data.get("min_threshold", 30)),
        "unit_price": float(data.get("unit_price", 10.0)),
        "batch_number": data.get("batch_number", f"BAT-{secrets.token_hex(3).upper()}"),
        "expiry_date": data.get("expiry_date", (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")),
        "status": "IN_STOCK"
    }

    inserted = insert_record("medicines", new_med, id_field="medicine_id")
    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Added medicine '{new_med['name']}' to pharmacy stock", "Pharmacy")

    return jsonify({"success": True, "message": "Medicine added to inventory", "data": inserted}), 201


@app.route("/api/medicines/<id>", methods=["PUT"])
@login_required
@role_required(["Pharmacy", "Admin"])
def api_update_medicine(id):
    data = request.get_json() or {}
    updated = update_record("medicines", id, data, "medicine_id")
    if not updated:
        return jsonify({"success": False, "message": "Medicine not found."}), 404

    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Updated inventory record for medicine {id}", "Pharmacy")
    return jsonify({"success": True, "message": "Medicine inventory updated", "data": updated})


# ============================================================================
# AUTOMATED BILLING CALCULATION ENGINE REST APIS
# ============================================================================

@app.route("/api/billing/calculate/<patient_id>", methods=["GET"])
@login_required
def api_calculate_patient_bill(patient_id):
    """
    Automated Billing Engine:
    Total = Consultation Fee + (Bed Rate * Days Occupied) + Sum(Lab Tests) + Sum(Prescribed Medicines)
    """
    patient = find_by_id("patients", patient_id, "patient_id")
    if not patient:
        return jsonify({"success": False, "message": "Patient not found."}), 404

    today = date.today()

    # 1. Consultation Fee (find latest doctor consultation)
    consultation_fee = 100.0  # Default standard OPD
    appointments = filter_data("appointments", lambda a: a.get("patient_id") == patient_id and a.get("status") == "Completed")
    if appointments:
        latest_apt = appointments[-1]
        doc = find_by_id("doctors", latest_apt.get("doctor_id"), "doctor_id")
        if doc:
            consultation_fee = float(doc.get("opd_fee", 100.0))

    # 2. Bed Charges & Days Occupied
    bed_charges = 0.0
    days_occupied = 0
    bed_daily_rate = 0.0
    bed_number = None

    if patient.get("bed_id"):
        bed = find_by_id("beds", patient.get("bed_id"), "bed_id")
        if bed:
            bed_number = bed.get("bed_number")
            bed_daily_rate = float(bed.get("daily_rate", 100.0))
            admission_str = patient.get("admission_date", str(today))
            try:
                admission_date = datetime.strptime(admission_str, "%Y-%m-%d").date()
                days_occupied = max(1, (today - admission_date).days)
            except ValueError:
                days_occupied = 1
            bed_charges = round(bed_daily_rate * days_occupied, 2)

    # 3. Lab Test Charges
    lab_reports = filter_data("lab_reports", lambda r: r.get("patient_id") == patient_id)
    lab_charges = sum(float(r.get("cost", 0.0)) for r in lab_reports)

    # 4. Medicine Charges from Prescriptions
    prescriptions = filter_data("prescriptions", lambda p: p.get("patient_id") == patient_id)
    medicine_charges = sum(float(p.get("total_medicine_charge", 0.0)) for p in prescriptions)

    subtotal = consultation_fee + bed_charges + lab_charges + medicine_charges
    suggested_discount = 0.0
    total_amount = round(subtotal - suggested_discount, 2)

    breakdown = {
        "patient_id": patient_id,
        "patient_name": patient.get("name"),
        "consultation_fee": consultation_fee,
        "bed_info": {
            "bed_number": bed_number,
            "daily_rate": bed_daily_rate,
            "days_occupied": days_occupied,
            "bed_charge_total": bed_charges
        },
        "lab_reports_count": len(lab_reports),
        "lab_charges_total": round(lab_charges, 2),
        "prescriptions_count": len(prescriptions),
        "medicine_charges_total": round(medicine_charges, 2),
        "subtotal": round(subtotal, 2),
        "suggested_discount": suggested_discount,
        "total_amount": total_amount
    }

    return jsonify({"success": True, "breakdown": breakdown})


@app.route("/api/bills", methods=["GET"])
@app.route("/api/billing", methods=["GET"])
@login_required
def api_get_bills():
    pat_filter = request.args.get("patient_id")
    user = get_current_user()
    bills = read_data("bills")

    if user.get("role") == "Patient" and user.get("associated_id"):
        bills = [b for b in bills if b.get("patient_id") == user["associated_id"]]
    elif pat_filter:
        bills = [b for b in bills if b.get("patient_id") == pat_filter]

    return jsonify({"success": True, "count": len(bills), "data": bills})


@app.route("/api/bills", methods=["POST"])
@app.route("/api/billing", methods=["POST"])
@login_required
@role_required(["Admin", "Receptionist"])
def api_create_bill():
    data = request.get_json() or {}
    patient_id = data.get("patient_id", "").strip()

    if not patient_id:
        return jsonify({"success": False, "message": "Patient ID is required."}), 400

    patient = find_by_id("patients", patient_id, "patient_id")
    if not patient:
        return jsonify({"success": False, "message": "Patient not found."}), 404

    consultation_fee = float(data.get("consultation_fee", 0.0))
    bed_charge = float(data.get("bed_charge", 0.0))
    days_occupied = int(data.get("days_occupied", 0))
    lab_charges = float(data.get("lab_charges", 0.0))
    medicine_charges = float(data.get("medicine_charges", 0.0))
    discount = float(data.get("discount", 0.0))

    subtotal = consultation_fee + bed_charge + lab_charges + medicine_charges
    total_amount = max(0.0, round(subtotal - discount, 2))
    paid_amount = float(data.get("paid_amount", total_amount))
    status = "Paid" if paid_amount >= total_amount else "Pending"

    new_bill = {
        "bill_id": generate_next_id("bills", "BILL", "bill_id", digits=3),
        "patient_id": patient_id,
        "patient_name": patient.get("name"),
        "bill_date": datetime.now().strftime("%Y-%m-%d"),
        "consultation_fee": consultation_fee,
        "bed_charge": bed_charge,
        "days_occupied": days_occupied,
        "lab_charges": lab_charges,
        "medicine_charges": medicine_charges,
        "subtotal": round(subtotal, 2),
        "discount": discount,
        "total_amount": total_amount,
        "paid_amount": paid_amount,
        "status": status,
        "payment_method": data.get("payment_method", "Cash"),
        "breakdown": {
            "consultation": consultation_fee,
            "bed": bed_charge,
            "lab": lab_charges,
            "medicines": medicine_charges,
            "discount": discount
        }
    }

    inserted = insert_record("bills", new_bill, id_field="bill_id")
    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Generated Invoice {new_bill['bill_id']} for Patient {patient.get('name')} (${total_amount})", "Billing")

    return jsonify({"success": True, "message": "Invoice generated successfully", "data": inserted}), 201


@app.route("/api/bills/<id>/pay", methods=["POST"])
@login_required
@role_required(["Admin", "Receptionist", "Patient"])
def api_pay_bill(id):
    data = request.get_json() or {}
    bill = find_by_id("bills", id, "bill_id")
    if not bill:
        return jsonify({"success": False, "message": "Bill not found."}), 404

    updated = update_record("bills", id, {
        "status": "Paid",
        "paid_amount": bill.get("total_amount", 0.0),
        "payment_method": data.get("payment_method", "Online Payment")
    }, "bill_id")

    user = get_current_user()
    log_activity(user["user_id"], user["role"], f"Processed payment for Invoice {id} (${bill.get('total_amount')})", "Billing")

    return jsonify({"success": True, "message": "Payment recorded successfully", "data": updated})


# ============================================================================
# DASHBOARD AGGREGATED STATS & ANALYTICS REST API
# ============================================================================

@app.route("/api/dashboard/stats", methods=["GET"])
@login_required
def api_dashboard_stats():
    """
    Computes real-time KPI metrics and aggregated analytics across all hospital modules.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")

    patients = read_data("patients")
    doctors = read_data("doctors")
    appointments = read_data("appointments")
    beds = read_data("beds")
    emergency = read_data("emergency")
    lab_reports = read_data("lab_reports")
    medicines = read_data("medicines")
    bills = read_data("bills")
    activity_logs = read_data("activity_logs")

    # Metrics
    total_patients = len(patients)
    total_doctors = len(doctors)
    today_appointments = len([a for a in appointments if a.get("appointment_date") == today_str])
    pending_appointments = len([a for a in appointments if a.get("status") == "Scheduled"])

    total_beds = len(beds)
    occupied_beds = len([b for b in beds if str(b.get("status", "")).lower() == "occupied"])
    available_beds = total_beds - occupied_beds
    bed_occupancy_rate = round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0

    emergency_patients = len([e for e in emergency if e.get("status") != "Discharged"])
    critical_emergency = len([e for e in emergency if e.get("priority") == "CRITICAL" and e.get("status") != "Discharged"])

    pending_lab_tests = len([r for r in lab_reports if r.get("status") == "Pending"])
    low_stock_medicines = len([m for m in medicines if m.get("status") in ["LOW_STOCK", "EXPIRING_SOON", "EXPIRED"]])

    total_revenue = sum(float(b.get("paid_amount", 0.0)) for b in bills)
    today_revenue = sum(float(b.get("paid_amount", 0.0)) for b in bills if b.get("bill_date") == today_str)

    # Department breakdown
    dept_counts = {}
    for d in doctors:
        dept = d.get("department", "General")
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    # Emergency bed safety alert
    icu_available = len([b for b in beds if "icu" in str(b.get("ward_type", "")).lower() and str(b.get("status", "")).lower() == "available"])
    emergency_bed_available = len([b for b in beds if "emergency" in str(b.get("ward_type", "")).lower() and str(b.get("status", "")).lower() == "available"])

    emergency_alert = None
    if critical_emergency > 0 and icu_available == 0 and emergency_bed_available == 0:
        emergency_alert = "CRITICAL CODE RED: Critical emergency patients active with ZERO available ICU/Emergency beds!"
    elif critical_emergency > 0:
        emergency_alert = f"ACTIVE TRIAGE: {critical_emergency} CRITICAL emergency patient(s) under observation."

    # Top recent 10 activity logs
    recent_logs = sorted(activity_logs, key=lambda l: l.get("timestamp", ""), reverse=True)[:10]

    return jsonify({
        "success": True,
        "stats": {
            "total_patients": total_patients,
            "total_doctors": total_doctors,
            "today_appointments": today_appointments,
            "pending_appointments": pending_appointments,
            "total_beds": total_beds,
            "occupied_beds": occupied_beds,
            "available_beds": available_beds,
            "bed_occupancy_rate": bed_occupancy_rate,
            "emergency_patients": emergency_patients,
            "critical_emergency": critical_emergency,
            "pending_lab_tests": pending_lab_tests,
            "low_stock_medicines": low_stock_medicines,
            "total_revenue": round(total_revenue, 2),
            "today_revenue": round(today_revenue, 2),
            "icu_available": icu_available,
            "emergency_bed_available": emergency_bed_available
        },
        "emergency_alert": emergency_alert,
        "department_distribution": dept_counts,
        "recent_activity": recent_logs
    })


# ============================================================================
# AUDIT LOGS REST API
# ============================================================================

@app.route("/api/activity-logs", methods=["GET"])
@login_required
def api_get_activity_logs():
    limit = int(request.args.get("limit", 25))
    logs = read_data("activity_logs")
    sorted_logs = sorted(logs, key=lambda l: l.get("timestamp", ""), reverse=True)[:limit]
    return jsonify({"success": True, "count": len(sorted_logs), "data": sorted_logs})


# ============================================================================
# APP STARTUP
# ============================================================================

if __name__ == "__main__":
    print("=" * 65)
    print(" Smart Hospital Management System (SHMS) - Starting Server")
    print(" Access Web Application at: http://127.0.0.1:5000")
    print(" Default Login Accounts:")
    print("   Admin:         admin / admin123")
    print("   Doctor:        doctor_smith / doc123")
    print("   Nurse:         nurse_sarah / nurse123")
    print("   Receptionist:  reception_jane / rec123")
    print("   Laboratory:    lab_tech / lab123")
    print("   Pharmacy:      pharma_john / pharma123")
    print("   Patient:       patient_alice / pat123")
    print("=" * 65)
    app.run(host="0.0.0.0", port=5000, debug=True)
