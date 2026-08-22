from pydantic import BaseModel


class AppointmentBookRequest(BaseModel):
    doctor_id: int
    date: str
    time_slot: str
    contact: str
    patient_user_id: int | None = None  # staff-only: book on behalf of a patient; ignored for patient callers


class AppointmentResponse(BaseModel):
    appointment_id: int
    doctor_id: int
    doctor_name: str
    patient_user_id: int
    patient_name: str
    contact: str
    date: str
    time_slot: str
    status: str
