import pandas as pd
import uuid
from datetime import datetime
import os

DATA_DIR = "data"
PATIENTS_FILE = os.path.join(DATA_DIR, "patients.csv")
SLOTS_FILE = os.path.join(DATA_DIR, "slots.csv")
APPOINTMENTS_FILE = os.path.join(DATA_DIR, "appointments.csv")

def _load_df(file_path):
    if not os.path.exists(file_path):
        return pd.DataFrame()
    return pd.read_csv(file_path)

def _save_df(df, file_path):
    df.to_csv(file_path, index=False)

def search_patient(name: str):
    """Search for a patient by name (partial match)."""
    df = _load_df(PATIENTS_FILE)
    if df.empty:
        return []
    
    results = df[df['name'].str.contains(name, case=False, na=False)]
    return results.to_dict(orient='records')

def get_patient_by_id(patient_id: str):
    """Get exact patient details by ID."""
    df = _load_df(PATIENTS_FILE)
    if df.empty:
        return None
    results = df[df['id'] == patient_id]
    if results.empty:
        return None
    return results.iloc[0].to_dict()

def check_insurance_eligibility(patient_id: str):
    """Check insurance status for a patient."""
    patient = get_patient_by_id(patient_id)
    if not patient:
        return {"error": "Patient not found"}
    
    return {
        "patient_id": patient_id,
        "insurance_id": patient['insurance_id'],
        "status": patient['insurance_status']
    }

def find_available_slots(department: str = None, date_str: str = None):
    """
    Find available slots.
    department: Filter by department (optional)
    date_str: Filter by date YYYY-MM-DD (optional)
    """
    df = _load_df(SLOTS_FILE)
    if df.empty:
        return []
    
    df['is_booked'] = df['is_booked'].astype(str).str.lower() == 'true'
    available = df[~df['is_booked']]
    
    if department:
        available = available[available['department'].str.contains(department, case=False, na=False)]
    
    if date_str:
        available = available[available['start_time'].str.startswith(date_str)]
        
    return available.to_dict(orient='records')

def book_appointment(patient_id: str, slot_id: str, notes: str = ""):
    """Book a specific slot for a patient."""
    if not get_patient_by_id(patient_id):
        return {"error": "Patient not found"}

    slots_df = _load_df(SLOTS_FILE)
    
    slot_idx = slots_df.index[slots_df['id'] == slot_id].tolist()
    if not slot_idx:
        return {"error": "Slot not found"}
    
    idx = slot_idx[0]
    is_booked = str(slots_df.at[idx, 'is_booked']).lower() == 'true'
    
    if is_booked:
        return {"error": "Slot already booked"}
    
    slots_df.at[idx, 'is_booked'] = True
    _save_df(slots_df, SLOTS_FILE)
    
    appt_df = _load_df(APPOINTMENTS_FILE)
    new_appt = {
        "id": f"A{uuid.uuid4().hex[:6].upper()}",
        "patient_id": patient_id,
        "slot_id": slot_id,
        "status": "Confirmed",
        "notes": notes
    }
    
    appt_df = pd.concat([appt_df, pd.DataFrame([new_appt])], ignore_index=True)
    _save_df(appt_df, APPOINTMENTS_FILE)
    
    return new_appt
