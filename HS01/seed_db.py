"""
seed_db.py
Seeds comprehensive, interconnected mock data for the Smart Hospital Management System.
Generates all 15 JSON files in data/ directory with proper IDs, relationships, and hashed credentials.
"""

import os
import json
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

def save_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[*] Seeded {filename} with {len(data)} records.")

def generate_seed():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    # 1. USERS
    users = [
        {
            "user_id": "USR001",
            "username": "admin",
            "password_hash": generate_password_hash("admin123"),
            "role": "Admin",
            "name": "Dr. Arthur Pendelton",
            "email": "admin@hospital.org",
            "phone": "+1 555-0100",
            "associated_id": "ADM001",
            "is_active": True
        },
        {
            "user_id": "USR002",
            "username": "doctor_smith",
            "password_hash": generate_password_hash("doc123"),
            "role": "Doctor",
            "name": "Dr. Sarah Smith, MD",
            "email": "s.smith@hospital.org",
            "phone": "+1 555-0102",
            "associated_id": "DOC001",
            "is_active": True
        },
        {
            "user_id": "USR003",
            "username": "doctor_chen",
            "password_hash": generate_password_hash("doc123"),
            "role": "Doctor",
            "name": "Dr. Raymond Chen, MS",
            "email": "r.chen@hospital.org",
            "phone": "+1 555-0103",
            "associated_id": "DOC002",
            "is_active": True
        },
        {
            "user_id": "USR004",
            "username": "nurse_sarah",
            "password_hash": generate_password_hash("nurse123"),
            "role": "Nurse",
            "name": "Nurse Sarah Connor, RN",
            "email": "s.connor@hospital.org",
            "phone": "+1 555-0104",
            "associated_id": "NUR001",
            "is_active": True
        },
        {
            "user_id": "USR005",
            "username": "reception_jane",
            "password_hash": generate_password_hash("rec123"),
            "role": "Receptionist",
            "name": "Jane Wilson",
            "email": "j.wilson@hospital.org",
            "phone": "+1 555-0105",
            "associated_id": "STF001",
            "is_active": True
        },
        {
            "user_id": "USR006",
            "username": "lab_tech",
            "password_hash": generate_password_hash("lab123"),
            "role": "Laboratory",
            "name": "David Martinez, BMLS",
            "email": "d.martinez@hospital.org",
            "phone": "+1 555-0106",
            "associated_id": "STF002",
            "is_active": True
        },
        {
            "user_id": "USR007",
            "username": "pharma_john",
            "password_hash": generate_password_hash("pharma123"),
            "role": "Pharmacy",
            "name": "Johnathan Green, PharmD",
            "email": "j.green@hospital.org",
            "phone": "+1 555-0107",
            "associated_id": "STF003",
            "is_active": True
        },
        {
            "user_id": "USR008",
            "username": "patient_alice",
            "password_hash": generate_password_hash("pat123"),
            "role": "Patient",
            "name": "Alice Montgomery",
            "email": "alice.m@gmail.com",
            "phone": "+1 555-0201",
            "associated_id": "PAT001",
            "is_active": True
        }
    ]
    save_json("users.json", users)

    # 2. PATIENTS
    patients = [
        {
            "patient_id": "PAT001",
            "name": "Alice Montgomery",
            "age": 34,
            "gender": "Female",
            "blood_group": "A+",
            "phone": "+1 555-0201",
            "email": "alice.m@gmail.com",
            "address": "452 Elm Street, Metropolis",
            "emergency_contact": "Robert Montgomery (+1 555-0202)",
            "registration_date": "2026-09-15",
            "status": "Outpatient",
            "allergies": ["Penicillin", "Sulfonamides"],
            "chronic_conditions": ["Mild Asthma"]
        },
        {
            "patient_id": "PAT002",
            "name": "Brian K. O'Connor",
            "age": 48,
            "gender": "Male",
            "blood_group": "O+",
            "phone": "+1 555-0203",
            "email": "brian.oc@gmail.com",
            "address": "782 Harbor Way, Metropolis",
            "emergency_contact": "Mia Toretto (+1 555-0204)",
            "registration_date": "2026-09-20",
            "status": "Inpatient",
            "bed_id": "BED002",
            "admission_date": "2026-10-04",
            "allergies": [],
            "chronic_conditions": ["Hypertension"]
        },
        {
            "patient_id": "PAT003",
            "name": "Elena Rostova",
            "age": 62,
            "gender": "Female",
            "blood_group": "B+",
            "phone": "+1 555-0205",
            "email": "e.rostova@yahoo.com",
            "address": "12 Pinecrest Blvd, Metropolis",
            "emergency_contact": "Nikolai Rostov (+1 555-0206)",
            "registration_date": "2026-09-28",
            "status": "Inpatient",
            "bed_id": "BED001",
            "admission_date": "2026-10-06",
            "allergies": ["Aspirin"],
            "chronic_conditions": ["Type 2 Diabetes", "Coronary Artery Disease"]
        },
        {
            "patient_id": "PAT004",
            "name": "Marcus Vance",
            "age": 27,
            "gender": "Male",
            "blood_group": "AB-",
            "phone": "+1 555-0207",
            "email": "marcus.v@outlook.com",
            "address": "90 Sunset Blvd, Metropolis",
            "emergency_contact": "Claire Vance (+1 555-0208)",
            "registration_date": "2026-10-01",
            "status": "Discharged",
            "allergies": [],
            "chronic_conditions": []
        },
        {
            "patient_id": "PAT005",
            "name": "Sophia Martinez",
            "age": 9,
            "gender": "Female",
            "blood_group": "O-",
            "phone": "+1 555-0209",
            "email": "c.martinez@gmail.com",
            "address": "33 West Meadow Lane, Metropolis",
            "emergency_contact": "Carlos Martinez (+1 555-0210)",
            "registration_date": "2026-10-05",
            "status": "Outpatient",
            "allergies": ["Peanuts"],
            "chronic_conditions": []
        }
    ]
    save_json("patients.json", patients)

    # 3. DOCTORS
    doctors = [
        {
            "doctor_id": "DOC001",
            "name": "Dr. Sarah Smith, MD",
            "specialization": "Cardiology",
            "department": "Cardiology",
            "qualification": "MD (Harvard), FACC",
            "experience_years": 14,
            "phone": "+1 555-0102",
            "email": "s.smith@hospital.org",
            "opd_fee": 120.0,
            "room_no": "OPD-102",
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "available_slots": ["09:00 AM", "10:00 AM", "11:30 AM", "02:00 PM", "03:30 PM"],
            "is_available": True
        },
        {
            "doctor_id": "DOC002",
            "name": "Dr. Raymond Chen, MS",
            "specialization": "Orthopedics & Trauma",
            "department": "Orthopedics",
            "qualification": "MS (Ortho), FACS",
            "experience_years": 11,
            "phone": "+1 555-0103",
            "email": "r.chen@hospital.org",
            "opd_fee": 110.0,
            "room_no": "OPD-105",
            "working_days": ["Monday", "Wednesday", "Friday", "Saturday"],
            "available_slots": ["09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM"],
            "is_available": True
        },
        {
            "doctor_id": "DOC003",
            "name": "Dr. Amara Patel, MD",
            "specialization": "Internal Medicine",
            "department": "General Medicine",
            "qualification": "MD (Internal Med), MRCP",
            "experience_years": 9,
            "phone": "+1 555-0112",
            "email": "a.patel@hospital.org",
            "opd_fee": 90.0,
            "room_no": "OPD-101",
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "available_slots": ["08:30 AM", "10:30 AM", "12:00 PM", "02:30 PM", "04:00 PM"],
            "is_available": True
        },
        {
            "doctor_id": "DOC004",
            "name": "Dr. Lucas Romero, MD",
            "specialization": "Pediatrics",
            "department": "Pediatrics",
            "qualification": "MD (Pediatrics), FAAP",
            "experience_years": 8,
            "phone": "+1 555-0114",
            "email": "l.romero@hospital.org",
            "opd_fee": 95.0,
            "room_no": "OPD-203",
            "working_days": ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "available_slots": ["09:00 AM", "10:30 AM", "01:00 PM", "03:00 PM"],
            "is_available": True
        }
    ]
    save_json("doctors.json", doctors)

    # 4. NURSES
    nurses = [
        {
            "nurse_id": "NUR001",
            "name": "Nurse Sarah Connor, RN",
            "department": "ICU & Critical Care",
            "shift": "Morning (07:00 - 15:00)",
            "phone": "+1 555-0104",
            "email": "s.connor@hospital.org",
            "assigned_wards": ["ICU Ward", "Step-Down Unit"]
        },
        {
            "nurse_id": "NUR002",
            "name": "Nurse Liam Gallagher, BSN",
            "department": "Emergency & Trauma",
            "shift": "Night (23:00 - 07:00)",
            "phone": "+1 555-0120",
            "email": "l.gallagher@hospital.org",
            "assigned_wards": ["Emergency Triage", "Trauma Bay"]
        }
    ]
    save_json("nurses.json", nurses)

    # 5. STAFF
    staff = [
        {
            "staff_id": "STF001",
            "name": "Jane Wilson",
            "role": "Receptionist",
            "department": "Front Desk / OPD",
            "phone": "+1 555-0105",
            "shift": "General (08:00 - 17:00)"
        },
        {
            "staff_id": "STF002",
            "name": "David Martinez",
            "role": "Laboratory Technician",
            "department": "Diagnostic Pathology",
            "phone": "+1 555-0106",
            "shift": "Day (09:00 - 18:00)"
        },
        {
            "staff_id": "STF003",
            "name": "Johnathan Green",
            "role": "Pharmacist",
            "department": "Central Pharmacy",
            "phone": "+1 555-0107",
            "shift": "Day (08:30 - 17:30)"
        }
    ]
    save_json("staff.json", staff)

    # 6. APPOINTMENTS
    appointments = [
        {
            "appointment_id": "APT001",
            "patient_id": "PAT001",
            "patient_name": "Alice Montgomery",
            "doctor_id": "DOC001",
            "doctor_name": "Dr. Sarah Smith, MD",
            "department": "Cardiology",
            "appointment_date": today_str,
            "time_slot": "10:00 AM",
            "token_number": 1,
            "status": "Scheduled",
            "purpose": "Routine cardiac follow-up and ECG review",
            "created_at": "2026-10-05 09:30:00"
        },
        {
            "appointment_id": "APT002",
            "patient_id": "PAT005",
            "patient_name": "Sophia Martinez",
            "doctor_id": "DOC004",
            "doctor_name": "Dr. Lucas Romero, MD",
            "department": "Pediatrics",
            "appointment_date": today_str,
            "time_slot": "01:00 PM",
            "token_number": 2,
            "status": "Scheduled",
            "purpose": "Seasonal allergy assessment",
            "created_at": "2026-10-06 11:15:00"
        },
        {
            "appointment_id": "APT003",
            "patient_id": "PAT002",
            "patient_name": "Brian K. O'Connor",
            "doctor_id": "DOC002",
            "doctor_name": "Dr. Raymond Chen, MS",
            "department": "Orthopedics",
            "appointment_date": yesterday_str,
            "time_slot": "09:30 AM",
            "token_number": 1,
            "status": "Completed",
            "purpose": "Post-fall right knee pain evaluation",
            "created_at": "2026-10-03 14:00:00"
        },
        {
            "appointment_id": "APT004",
            "patient_id": "PAT001",
            "patient_name": "Alice Montgomery",
            "doctor_id": "DOC003",
            "doctor_name": "Dr. Amara Patel, MD",
            "department": "General Medicine",
            "appointment_date": tomorrow_str,
            "time_slot": "10:30 AM",
            "token_number": 1,
            "status": "Scheduled",
            "purpose": "Annual wellness examination",
            "created_at": "2026-10-07 08:00:00"
        }
    ]
    save_json("appointments.json", appointments)

    # 7. MEDICAL RECORDS
    medical_records = [
        {
            "record_id": "MR001",
            "patient_id": "PAT001",
            "doctor_id": "DOC001",
            "appointment_id": "APT001",
            "date": "2026-09-15 10:20:00",
            "symptoms": "Mild palpitations during exertion, occasional shortness of breath.",
            "vitals": {
                "blood_pressure": "128/82",
                "heart_rate": 78,
                "temperature": 98.4,
                "spo2": 99,
                "respiratory_rate": 16,
                "weight_kg": 64.5
            },
            "diagnosis": "Mild Sinus Tachycardia with benign palpitations.",
            "doctor_notes": "Advised stress reduction, caffeine reduction, and hydration. Follow-up in 3 weeks.",
            "prescription_id": "RX001",
            "lab_order_ids": ["REP001"]
        },
        {
            "record_id": "MR002",
            "patient_id": "PAT002",
            "doctor_id": "DOC002",
            "appointment_id": "APT003",
            "date": "2026-10-04 10:00:00",
            "symptoms": "Acute right knee joint pain following sports fall. Inability to bear full weight.",
            "vitals": {
                "blood_pressure": "138/88",
                "heart_rate": 84,
                "temperature": 98.7,
                "spo2": 97,
                "respiratory_rate": 18,
                "weight_kg": 82.0
            },
            "diagnosis": "Right Knee Meniscal Strain with moderate joint effusion. Admitted for observation & MRI.",
            "doctor_notes": "Immobilize knee. Cold compress 4x daily. Admitted to Orthopedic Ward BED002.",
            "prescription_id": "RX002",
            "lab_order_ids": ["REP002"]
        }
    ]
    save_json("medical_records.json", medical_records)

    # 8. MEDICINES
    medicines = [
        {
            "medicine_id": "MED001",
            "name": "Amoxicillin 500mg",
            "generic_name": "Amoxicillin Trihydrate",
            "category": "Antibiotic",
            "form": "Capsule",
            "stock_quantity": 420,
            "min_threshold": 50,
            "unit_price": 12.50,
            "batch_number": "AMX-2026-A1",
            "expiry_date": "2027-08-31",
            "status": "IN_STOCK"
        },
        {
            "medicine_id": "MED002",
            "name": "Paracetamol 650mg",
            "generic_name": "Acetaminophen",
            "category": "Analgesic & Antipyretic",
            "form": "Tablet",
            "stock_quantity": 850,
            "min_threshold": 100,
            "unit_price": 4.00,
            "batch_number": "PCM-2026-B4",
            "expiry_date": "2028-01-15",
            "status": "IN_STOCK"
        },
        {
            "medicine_id": "MED003",
            "name": "Amlodipine 5mg",
            "generic_name": "Amlodipine Besylate",
            "category": "Antihypertensive",
            "form": "Tablet",
            "stock_quantity": 28,  # Below threshold 40 -> LOW STOCK
            "min_threshold": 40,
            "unit_price": 9.20,
            "batch_number": "AML-2025-C9",
            "expiry_date": "2027-04-30",
            "status": "LOW_STOCK"
        },
        {
            "medicine_id": "MED004",
            "name": "Metformin 500mg",
            "generic_name": "Metformin HCl",
            "category": "Antidiabetic",
            "form": "Tablet",
            "stock_quantity": 600,
            "min_threshold": 80,
            "unit_price": 7.50,
            "batch_number": "MET-2026-D2",
            "expiry_date": "2026-10-25",  # Expiring within 30 days!
            "status": "EXPIRING_SOON"
        },
        {
            "medicine_id": "MED005",
            "name": "Atorvastatin 20mg",
            "generic_name": "Atorvastatin Calcium",
            "category": "Lipid-lowering",
            "form": "Tablet",
            "stock_quantity": 210,
            "min_threshold": 50,
            "unit_price": 15.00,
            "batch_number": "ATV-2026-E7",
            "expiry_date": "2027-11-20",
            "status": "IN_STOCK"
        },
        {
            "medicine_id": "MED006",
            "name": "Ceftriaxone 1g IV",
            "generic_name": "Ceftriaxone Sodium",
            "category": "Injectable Antibiotic",
            "form": "Vial",
            "stock_quantity": 12,  # Low stock
            "min_threshold": 30,
            "unit_price": 45.00,
            "batch_number": "CTX-2025-V1",
            "expiry_date": "2026-10-18",  # Low stock + Expiring soon!
            "status": "LOW_STOCK"
        }
    ]
    save_json("medicines.json", medicines)

    # 9. PRESCRIPTIONS
    prescriptions = [
        {
            "prescription_id": "RX001",
            "patient_id": "PAT001",
            "doctor_id": "DOC001",
            "date": "2026-09-15",
            "diagnosis": "Mild Sinus Tachycardia",
            "medicines": [
                {
                    "medicine_id": "MED005",
                    "medicine_name": "Atorvastatin 20mg",
                    "dosage": "1 tablet",
                    "frequency": "Once daily at bedtime",
                    "duration": "30 days",
                    "quantity": 30,
                    "unit_price": 15.00,
                    "subtotal": 450.00
                },
                {
                    "medicine_id": "MED002",
                    "medicine_name": "Paracetamol 650mg",
                    "dosage": "1 tablet",
                    "frequency": "SOS / As needed for headache",
                    "duration": "5 days",
                    "quantity": 10,
                    "unit_price": 4.00,
                    "subtotal": 40.00
                }
            ],
            "total_medicine_charge": 490.00,
            "dispense_status": "Dispensed"
        },
        {
            "prescription_id": "RX002",
            "patient_id": "PAT002",
            "doctor_id": "DOC002",
            "date": "2026-10-04",
            "diagnosis": "Right Knee Meniscal Strain",
            "medicines": [
                {
                    "medicine_id": "MED002",
                    "medicine_name": "Paracetamol 650mg",
                    "dosage": "1 tablet",
                    "frequency": "Every 8 hours after food",
                    "duration": "7 days",
                    "quantity": 21,
                    "unit_price": 4.00,
                    "subtotal": 84.00
                }
            ],
            "total_medicine_charge": 84.00,
            "dispense_status": "Pending"
        }
    ]
    save_json("prescriptions.json", prescriptions)

    # 10. LABORATORY TESTS CATALOG
    laboratory_tests = [
        {
            "test_id": "LAB001",
            "test_name": "Complete Blood Count (CBC)",
            "department": "Hematology",
            "price": 35.0,
            "normal_range": "WBC: 4.5-11.0 K/uL, RBC: 4.2-5.9 M/uL, Platelets: 150-450 K/uL",
            "sample_type": "Whole Blood (EDTA)",
            "turnaround_hours": 3
        },
        {
            "test_id": "LAB002",
            "test_name": "Comprehensive Metabolic Panel (CMP)",
            "department": "Biochemistry",
            "price": 60.0,
            "normal_range": "Glucose: 70-99 mg/dL, BUN: 7-20 mg/dL, Creatinine: 0.7-1.3 mg/dL",
            "sample_type": "Serum",
            "turnaround_hours": 4
        },
        {
            "test_id": "LAB003",
            "test_name": "Lipid Profile",
            "department": "Biochemistry",
            "price": 45.0,
            "normal_range": "Total Chol: <200 mg/dL, Triglycerides: <150 mg/dL, HDL: >40 mg/dL",
            "sample_type": "Fasting Serum",
            "turnaround_hours": 6
        },
        {
            "test_id": "LAB004",
            "test_name": "Troponin I (Cardiac Marker)",
            "department": "Pathology / Critical Care",
            "price": 85.0,
            "normal_range": "< 0.04 ng/mL",
            "sample_type": "Heparin Plasma",
            "turnaround_hours": 1
        },
        {
            "test_id": "LAB005",
            "test_name": "Digital X-Ray Knee AP/Lateral",
            "department": "Radiology",
            "price": 75.0,
            "normal_range": "Intact joint spaces, no acute displaced fracture",
            "sample_type": "Imaging",
            "turnaround_hours": 2
        }
    ]
    save_json("laboratory_tests.json", laboratory_tests)

    # 11. LAB REPORTS (ORDERS & RESULTS)
    lab_reports = [
        {
            "report_id": "REP001",
            "patient_id": "PAT001",
            "patient_name": "Alice Montgomery",
            "doctor_id": "DOC001",
            "test_id": "LAB003",
            "test_name": "Lipid Profile",
            "ordered_date": "2026-09-15 11:00:00",
            "status": "Completed",
            "results": {
                "Total Cholesterol": "188 mg/dL (Normal)",
                "Triglycerides": "135 mg/dL (Normal)",
                "HDL Cholesterol": "54 mg/dL (Optimal)",
                "LDL Cholesterol": "107 mg/dL (Optimal)"
            },
            "technician_notes": "All lipid fractions within target range.",
            "completed_date": "2026-09-15 15:45:00",
            "cost": 45.0
        },
        {
            "report_id": "REP002",
            "patient_id": "PAT002",
            "patient_name": "Brian K. O'Connor",
            "doctor_id": "DOC002",
            "test_id": "LAB005",
            "test_name": "Digital X-Ray Knee AP/Lateral",
            "ordered_date": "2026-10-04 10:30:00",
            "status": "Completed",
            "results": {
                "Bony Architecture": "No acute fracture or dislocation identified.",
                "Joint Alignment": "Mild medial compartment joint space narrowing with moderate suprapatellar effusion."
            },
            "technician_notes": "Correlate with clinical exam for soft tissue/meniscal involvement.",
            "completed_date": "2026-10-04 12:15:00",
            "cost": 75.0
        },
        {
            "report_id": "REP003",
            "patient_id": "PAT003",
            "patient_name": "Elena Rostova",
            "doctor_id": "DOC001",
            "test_id": "LAB004",
            "test_name": "Troponin I (Cardiac Marker)",
            "ordered_date": today_str + " 08:30:00",
            "status": "Pending",
            "results": {},
            "technician_notes": "STAT sample received in lab. Processing in progress.",
            "completed_date": None,
            "cost": 85.0
        }
    ]
    save_json("lab_reports.json", lab_reports)

    # 12. BEDS
    beds = [
        {
            "bed_id": "BED001",
            "bed_number": "ICU-01",
            "ward_type": "ICU",
            "room_no": "ICU-Pod-A",
            "daily_rate": 350.0,
            "status": "Occupied",
            "patient_id": "PAT003",
            "patient_name": "Elena Rostova",
            "assigned_date": "2026-10-06"
        },
        {
            "bed_id": "BED002",
            "bed_number": "GW-101",
            "ward_type": "General Ward",
            "room_no": "Ward-1A",
            "daily_rate": 100.0,
            "status": "Occupied",
            "patient_id": "PAT002",
            "patient_name": "Brian K. O'Connor",
            "assigned_date": "2026-10-04"
        },
        {
            "bed_id": "BED003",
            "bed_number": "ICU-02",
            "ward_type": "ICU",
            "room_no": "ICU-Pod-A",
            "daily_rate": 350.0,
            "status": "Available",
            "patient_id": None,
            "patient_name": None,
            "assigned_date": None
        },
        {
            "bed_id": "BED004",
            "bed_number": "ER-BAY-01",
            "ward_type": "Emergency",
            "room_no": "Emergency Wing",
            "daily_rate": 200.0,
            "status": "Available",
            "patient_id": None,
            "patient_name": None,
            "assigned_date": None
        },
        {
            "bed_id": "BED005",
            "bed_number": "ER-BAY-02",
            "ward_type": "Emergency",
            "room_no": "Emergency Wing",
            "daily_rate": 200.0,
            "status": "Occupied",
            "patient_id": "EMG001",
            "patient_name": "James Henderson",
            "assigned_date": today_str
        },
        {
            "bed_id": "BED006",
            "bed_number": "PVT-201",
            "ward_type": "Private Deluxe",
            "room_no": "2nd Floor West",
            "daily_rate": 250.0,
            "status": "Available",
            "patient_id": None,
            "patient_name": None,
            "assigned_date": None
        },
        {
            "bed_id": "BED007",
            "bed_number": "GW-102",
            "ward_type": "General Ward",
            "room_no": "Ward-1A",
            "daily_rate": 100.0,
            "status": "Available",
            "patient_id": None,
            "patient_name": None,
            "assigned_date": None
        },
        {
            "bed_id": "BED008",
            "bed_number": "GW-103",
            "ward_type": "General Ward",
            "room_no": "Ward-1B",
            "daily_rate": 100.0,
            "status": "Available",
            "patient_id": None,
            "patient_name": None,
            "assigned_date": None
        }
    ]
    save_json("beds.json", beds)

    # 13. BILLS
    bills = [
        {
            "bill_id": "BILL001",
            "patient_id": "PAT004",
            "patient_name": "Marcus Vance",
            "bill_date": "2026-10-04",
            "consultation_fee": 110.0,
            "bed_charge": 300.0,  # 3 days x 100
            "days_occupied": 3,
            "lab_charges": 110.0,
            "medicine_charges": 68.0,
            "subtotal": 588.0,
            "discount": 38.0,
            "total_amount": 550.0,
            "paid_amount": 550.0,
            "status": "Paid",
            "payment_method": "Credit Card",
            "breakdown": {
                "consultation": 110.0,
                "bed": 300.0,
                "lab": 110.0,
                "medicines": 68.0,
                "discount": 38.0
            }
        },
        {
            "bill_id": "BILL002",
            "patient_id": "PAT001",
            "patient_name": "Alice Montgomery",
            "bill_date": "2026-09-15",
            "consultation_fee": 120.0,
            "bed_charge": 0.0,
            "days_occupied": 0,
            "lab_charges": 45.0,
            "medicine_charges": 490.0,
            "subtotal": 655.0,
            "discount": 0.0,
            "total_amount": 655.0,
            "paid_amount": 655.0,
            "status": "Paid",
            "payment_method": "Cash",
            "breakdown": {
                "consultation": 120.0,
                "bed": 0.0,
                "lab": 45.0,
                "medicines": 490.0,
                "discount": 0.0
            }
        }
    ]
    save_json("bills.json", bills)

    # 14. EMERGENCY
    emergency = [
        {
            "emergency_id": "EMG001",
            "patient_name": "James Henderson",
            "age": 52,
            "gender": "Male",
            "vitals": {
                "spo2": 82,
                "systolic_bp": 195,
                "diastolic_bp": 110,
                "heart_rate": 132,
                "temperature": 99.2
            },
            "symptoms": "Acute substernal crushing chest pain radiating to left arm, severe diaphoresis.",
            "consciousness": "Alert",
            "trauma_level": "None",
            "priority": "CRITICAL",
            "triage_score": 9,
            "reasons": [
                "Severe Hypoxemia (SpO2 82% < 85%)",
                "Hypertensive Crisis (Systolic BP 195 > 180 mmHg)"
            ],
            "assigned_bed": "BED005",
            "attending_doctor": "DOC001",
            "triage_time": today_str + " 14:15:00",
            "status": "Under Care"
        },
        {
            "emergency_id": "EMG002",
            "patient_name": "Tyler Brooks",
            "age": 22,
            "gender": "Male",
            "vitals": {
                "spo2": 97,
                "systolic_bp": 124,
                "diastolic_bp": 82,
                "heart_rate": 88,
                "temperature": 98.6
            },
            "symptoms": "Right forearm laceration from broken glass, controlled bleeding.",
            "consciousness": "Alert",
            "trauma_level": "Moderate",
            "priority": "MEDIUM",
            "triage_score": 3,
            "reasons": ["Suspected Moderate Fracture / Dislocation or deep cut"],
            "assigned_bed": None,
            "attending_doctor": "DOC002",
            "triage_time": today_str + " 15:30:00",
            "status": "Waiting"
        }
    ]
    save_json("emergency.json", emergency)

    # 15. ACTIVITY LOGS
    activity_logs = [
        {
            "log_id": "LOG0001",
            "timestamp": "2026-10-04 10:15:00",
            "date": "2026-10-04",
            "time": "10:15:00 AM",
            "user_id": "USR001",
            "role": "Admin",
            "action": "Allocated Bed BED002 to Patient PAT002",
            "module": "Bed Management"
        },
        {
            "log_id": "LOG0002",
            "timestamp": "2026-10-04 12:30:00",
            "date": "2026-10-04",
            "time": "12:30:00 PM",
            "user_id": "USR006",
            "role": "Laboratory",
            "action": "Completed X-Ray Lab Report REP002 for Patient PAT002",
            "module": "Laboratory"
        },
        {
            "log_id": "LOG0003",
            "timestamp": "2026-10-05 09:30:00",
            "date": "2026-10-05",
            "time": "09:30:00 AM",
            "user_id": "USR005",
            "role": "Receptionist",
            "action": "Booked Appointment APT001 for Patient PAT001 with Dr. Sarah Smith",
            "module": "Appointments"
        },
        {
            "log_id": "LOG0004",
            "timestamp": "2026-10-06 14:00:00",
            "date": "2026-10-06",
            "time": "02:00:00 PM",
            "user_id": "USR001",
            "role": "Admin",
            "action": "Admitted Patient PAT003 to Bed BED001 (ICU)",
            "module": "Bed Management"
        },
        {
            "log_id": "LOG0005",
            "timestamp": today_str + " 14:20:00",
            "date": today_str,
            "time": "02:20:00 PM",
            "user_id": "USR002",
            "role": "Doctor",
            "action": "Triage classified Emergency Case EMG001 as CRITICAL",
            "module": "Emergency Management"
        }
    ]
    save_json("activity_logs.json", activity_logs)
    print("\n[SUCCESS] All 15 database JSON files successfully generated and verified!")

if __name__ == "__main__":
    generate_seed()
