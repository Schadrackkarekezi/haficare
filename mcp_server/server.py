from mcp.server.fastmcp import FastMCP

from features.appointments import book_appointment as _book_appointment
from features.appointments import cancel_appointment as _cancel_appointment
from features.appointments import list_appointments as _list_appointments
from features.diagnosis import get_diagnosis_from_symptoms as _get_diagnosis_from_symptoms
from features.doctor_search import vector_search_doctors as _vector_search_doctors
from features.doctor_search import vector_search_doctors_for_clinic as _vector_search_doctors_for_clinic
from features.pharmacy_search import find_pharmacies_by_city as _find_pharmacies_by_city

mcp = FastMCP("haficare")


@mcp.tool()
def find_doctors(query: str, top_k: int = 3, clinic_id: int | None = None) -> list[dict]:
    """Find doctors relevant to a health question or specialty, ranked by relevance.
    If clinic_id is given, search is scoped to that clinic's own doctor roster;
    otherwise falls back to the legacy, unscoped Rwanda-wide directory."""
    if clinic_id is not None:
        return _vector_search_doctors_for_clinic(query, clinic_id=clinic_id, top_r=top_k)
    return _vector_search_doctors(query, top_r=top_k)


@mcp.tool()
def find_pharmacies(city: str) -> list[dict]:
    """Find pharmacies located in the given city."""
    return _find_pharmacies_by_city(city)


@mcp.tool()
def get_diagnosis(symptoms: str) -> dict:
    """Given a free-text description of symptoms, return possible conditions, a plain-language
    summary, and a medical disclaimer. This is informational only, not a real diagnosis."""
    return _get_diagnosis_from_symptoms(symptoms)


@mcp.tool()
def book_appointment(clinic_id: int, doctor_id: int, patient_user_id: int, date: str, time_slot: str, contact: str) -> dict:
    """Book an appointment with a clinic's doctor for a given date (YYYY-MM-DD) and time slot (HH:MM)."""
    return _book_appointment(clinic_id, doctor_id, patient_user_id, date, time_slot, contact)


@mcp.tool()
def list_appointments(clinic_id: int, patient_user_id: int | None = None, doctor_id: int | None = None) -> list[dict]:
    """List a clinic's booked appointments, optionally filtered by patient or doctor."""
    return _list_appointments(clinic_id, patient_user_id, doctor_id)


@mcp.tool()
def cancel_appointment(clinic_id: int, appointment_id: int) -> dict:
    """Cancel a previously booked appointment by its id, scoped to the clinic."""
    return _cancel_appointment(clinic_id, appointment_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
