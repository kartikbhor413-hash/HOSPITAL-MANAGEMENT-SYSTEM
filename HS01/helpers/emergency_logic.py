"""
helpers/emergency_logic.py
Smart Rule-Based Emergency Priority Engine & Triage Classification.
Evaluates vitals and symptoms to assign triage priorities (CRITICAL, HIGH, MEDIUM, LOW)
and monitors emergency/ICU bed availability for urgent alerts.
"""
from helpers.json_db import read_data
def evaluate_emergency_priority(patient_data: dict) -> dict:
    """
    Evaluates emergency patient symptoms and vitals based on college project clinical rules.

    Rules:
    - CRITICAL:
        SpO2 < 85% OR
        Systolic BP > 180 OR Systolic BP < 80 OR
        Severe Trauma OR
        Consciousness == 'Unconscious' / 'Comatose' OR
        Heart Rate > 140 OR Heart Rate < 40
    - HIGH:
        SpO2 85% - 92% OR
        Severe Abdominal Pain OR
        High Fever (> 103°F / 39.4°C) OR
        Deep Lacerations / Uncontrolled Bleeding OR
        Systolic BP 160-180
    - MEDIUM:
        SpO2 93% - 95% OR
        Moderate Fractures OR
        Persistent Vomiting / Dehydration OR
        Fever 101°F - 103°F
    - LOW:
        Stable Vitals (SpO2 >= 96%, Normal BP) OR
        Minor Injuries / Mild Aches / Mild Fever
    """
    reasons = []
    triage_score = 0  # 0 to 10 scale (10 is most critical)

    # Extract & sanitize vitals
    try:
        spo2 = float(patient_data.get("spo2", 98))
    except (ValueError, TypeError):
        spo2 = 98.0

    try:
        systolic_bp = float(patient_data.get("systolic_bp", 120))
    except (ValueError, TypeError):
        systolic_bp = 120.0

    try:
        heart_rate = float(patient_data.get("heart_rate", 75))
    except (ValueError, TypeError):
        heart_rate = 75.0

    try:
        temp_f = float(patient_data.get("temperature", 98.6))
    except (ValueError, TypeError):
        temp_f = 98.6

    consciousness = str(patient_data.get("consciousness", "Alert")).strip().lower()
    trauma_level = str(patient_data.get("trauma_level", "None")).strip().lower()
    symptoms = str(patient_data.get("symptoms", "")).lower()

    # Rule checks - CRITICAL evaluation
    is_critical = False
    if spo2 < 85:
        is_critical = True
        reasons.append(f"Severe Hypoxemia (SpO2 {spo2}% < 85%)")
        triage_score += 4

    if systolic_bp > 180:
        is_critical = True
        reasons.append(f"Hypertensive Crisis (Systolic BP {systolic_bp} > 180 mmHg)")
        triage_score += 4
    elif systolic_bp < 80 and systolic_bp > 0:
        is_critical = True
        reasons.append(f"Severe Hypotension / Shock (Systolic BP {systolic_bp} < 80 mmHg)")
        triage_score += 4

    if consciousness in ["unconscious", "comatose", "unresponsive"]:
        is_critical = True
        reasons.append(f"Altered Consciousness: {consciousness.capitalize()}")
        triage_score += 5

    if trauma_level in ["severe", "catastrophic", "critical"]:
        is_critical = True
        reasons.append("Severe Polytrauma")
        triage_score += 4

    if heart_rate > 140 or (heart_rate < 40 and heart_rate > 0):
        is_critical = True
        reasons.append(f"Severe Arrhythmia / Extreme Pulse ({heart_rate} bpm)")
        triage_score += 3

    # Rule checks - HIGH evaluation
    is_high = False
    if not is_critical:
        if 85 <= spo2 <= 92:
            is_high = True
            reasons.append(f"Moderate Hypoxemia (SpO2 {spo2}%)")
            triage_score += 3

        if temp_f > 103.0:
            is_high = True
            reasons.append(f"Hyperpyrexia (Temperature {temp_f}°F > 103°F)")
            triage_score += 2

        if "severe abdominal pain" in symptoms or "acute abdomen" in symptoms:
            is_high = True
            reasons.append("Acute Severe Abdominal Pain")
            triage_score += 3

        if "deep laceration" in symptoms or "bleeding" in symptoms or trauma_level == "high":
            is_high = True
            reasons.append("Deep Lacerations / Significant Bleeding")
            triage_score += 3

        if 160 <= systolic_bp <= 180 or (80 <= systolic_bp <= 90):
            is_high = True
            reasons.append(f"Borderline Unstable BP ({systolic_bp} mmHg)")
            triage_score += 2

    # Rule checks - MEDIUM evaluation
    is_medium = False
    if not is_critical and not is_high:
        if 93 <= spo2 <= 95:
            is_medium = True
            reasons.append(f"Mild Oxygen Deprivation (SpO2 {spo2}%)")
            triage_score += 2

        if "vomiting" in symptoms or "dehydration" in symptoms:
            is_medium = True
            reasons.append("Persistent Vomiting / Dehydration")
            triage_score += 1

        if "fracture" in symptoms or trauma_level == "moderate":
            is_medium = True
            reasons.append("Suspected Moderate Fracture / Dislocation")
            triage_score += 2

        if 101.0 <= temp_f <= 103.0:
            is_medium = True
            reasons.append(f"Moderate Fever ({temp_f}°F)")
            triage_score += 1

    # Determine final priority
    if is_critical:
        priority = "CRITICAL"
        recommended_bed_type = "ICU"
        color_code = "#dc2626"  # Red
        triage_score = max(8, min(10, triage_score))
        est_wait_time = "Immediate (0 mins)"
    elif is_high:
        priority = "HIGH"
        recommended_bed_type = "Emergency"
        color_code = "#ea580c"  # Orange
        triage_score = max(5, min(7, triage_score))
        est_wait_time = "< 15 mins"
    elif is_medium:
        priority = "MEDIUM"
        recommended_bed_type = "Emergency"
        color_code = "#d97706"  # Amber
        triage_score = max(3, min(4, triage_score))
        est_wait_time = "< 45 mins"
    else:
        priority = "LOW"
        recommended_bed_type = "General Ward"
        color_code = "#16a34a"  # Green
        reasons.append("Stable vital signs and minor presenting complaints.")
        triage_score = max(1, min(2, triage_score))
        est_wait_time = "< 90 mins"

    # Bed availability check
    bed_audit = check_bed_availability(recommended_bed_type)
    alert = None

    if priority == "CRITICAL" and bed_audit["icu_available"] == 0 and bed_audit["emergency_available"] == 0:
        alert = "CRITICAL ALERT: No ICU or Emergency beds currently available! Immediate transfer or escalation required."
    elif priority == "HIGH" and bed_audit["emergency_available"] == 0:
        alert = "WARNING: No Emergency beds available. Route to High-Dependency Ward or overflow area."

    return {
        "priority": priority,
        "triage_score": triage_score,
        "reasons": reasons,
        "recommended_bed_type": recommended_bed_type,
        "color_code": color_code,
        "estimated_wait_time": est_wait_time,
        "alert": alert,
        "bed_audit": bed_audit
    }


def check_bed_availability(needed_type: str = None) -> dict:
    """
    Scans beds.json to calculate total, occupied, and available beds by ward type.
    """
    beds = read_data("beds")

    total_beds = len(beds)
    occupied_beds = 0
    available_beds = 0
    icu_available = 0
    emergency_available = 0
    general_available = 0

    for bed in beds:
        status = str(bed.get("status", "Available")).strip().lower()
        ward = str(bed.get("ward_type", "")).strip().lower()

        if status == "available":
            available_beds += 1
            if "icu" in ward:
                icu_available += 1
            elif "emergency" in ward:
                emergency_available += 1
            else:
                general_available += 1
        else:
            occupied_beds += 1

    return {
        "total_beds": total_beds,
        "occupied_beds": occupied_beds,
        "available_beds": available_beds,
        "occupancy_rate_pct": round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0,
        "icu_available": icu_available,
        "emergency_available": emergency_available,
        "general_available": general_available,
        "is_needed_type_available": (icu_available > 0 if needed_type == "ICU" else
                                     emergency_available > 0 if needed_type == "Emergency" else
                                     available_beds > 0)
    }
