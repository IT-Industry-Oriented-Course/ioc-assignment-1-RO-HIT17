from langchain_core.tools import tool
import core.mock_db as mock_db
import core.audit as audit
import core.config as config
from pydantic import BaseModel, Field
from typing import Optional, List

class SearchPatientInput(BaseModel):
    name: str = Field(description="Name of the patient to search for (partial match allowed).")

@tool("search_patient", args_schema=SearchPatientInput)
def search_patient(name: str):
    """
    Search for a patient by name. 
    Returns list of matching patients with their IDs and DOBs.
    Always use this to find the patient_id before other actions.
    """
    result = mock_db.search_patient(name)
    audit.log_action("search_patient", {"name": name}, result)
    return result

class CheckInsuranceInput(BaseModel):
    patient_id: str = Field(description="The unique ID of the patient.")

@tool("check_insurance_eligibility", args_schema=CheckInsuranceInput)
def check_insurance_eligibility(patient_id: str):
    """
    Check the insurance eligibility status of a patient.
    Returns insurance ID and status (Active/Inactive).
    """
    result = mock_db.check_insurance_eligibility(patient_id)
    audit.log_action("check_insurance_eligibility", {"patient_id": patient_id}, result)
    return result

class FindSlotsInput(BaseModel):
    department: Optional[str] = Field(default=None, description="Medical department (e.g., Cardiology, General Medicine).")
    date: Optional[str] = Field(default=None, description="Date in YYYY-MM-DD format.")

@tool("find_available_slots", args_schema=FindSlotsInput)
def find_available_slots(department: str = None, date: str = None):
    """
    Find available appointment slots. Can filter by department and date.
    Returns a list of available slots with slot_id, doctor, and time.
    If the user's date request is vague (e.g., "next week"), call this WITHOUT a date to get all upcoming slots.
    """
    result = mock_db.find_available_slots(department, date)
    audit.log_action("find_available_slots", {"department": department, "date": date}, result)
    return result

class BookAppointmentInput(BaseModel):
    patient_id: str = Field(description="The unique ID of the patient.")
    slot_id: str = Field(description="The unique ID of the appointment slot.")
    notes: Optional[str] = Field(default="", description="Reason for visit or other notes.")

@tool("book_appointment", args_schema=BookAppointmentInput)
def book_appointment(patient_id: str, slot_id: str, notes: str = ""):
    """
    Book an appointment for a patient.
    Requires patient_id and slot_id from previous searches.
    """
    inputs = {"patient_id": patient_id, "slot_id": slot_id, "notes": notes}
    
    if config.DRY_RUN:
        result = {
            "status": "DRY_RUN_SUCCESS",
            "message": "Appointment would be booked in production.",
            "data": inputs
        }
    else:
        result = mock_db.book_appointment(patient_id, slot_id, notes)
        
    audit.log_action("book_appointment", inputs, result)
    return result
