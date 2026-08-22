from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.appointments.schemas import AppointmentBookRequest, AppointmentResponse
from api.deps import AuthenticatedUser, get_current_user, get_db
from db.postgres_models import Doctor, User
from features.appointments import book_appointment, cancel_appointment, list_appointments

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _with_names(db: Session, rows: list[dict]) -> list[AppointmentResponse]:
    doctor_ids = {r["doctor_id"] for r in rows}
    patient_ids = {r["patient_user_id"] for r in rows}
    doctor_names = {
        d.id: d.name for d in db.scalars(select(Doctor).where(Doctor.id.in_(doctor_ids))).all()
    } if doctor_ids else {}
    patient_names = {
        u.id: u.full_name for u in db.scalars(select(User).where(User.id.in_(patient_ids))).all()
    } if patient_ids else {}

    return [
        AppointmentResponse(
            **r,
            doctor_name=doctor_names.get(r["doctor_id"], "Unknown doctor"),
            patient_name=patient_names.get(r["patient_user_id"], "Unknown patient"),
        )
        for r in rows
    ]


@router.get("", response_model=list[AppointmentResponse])
def get_appointments(
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Patients only ever see their own bookings; staff see everyone's in their clinic.
    patient_filter = user.user_id if user.role == "patient" else None
    results = list_appointments(clinic_id=user.clinic_id, patient_user_id=patient_filter, session=db)
    return _with_names(db, results)


@router.post("", response_model=AppointmentResponse)
def create_appointment(
    req: AppointmentBookRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role == "patient":
        patient_user_id = user.user_id  # never trust the body for a patient caller
    else:
        if req.patient_user_id is None:
            raise HTTPException(status_code=400, detail="patient_user_id is required when staff book on a patient's behalf.")
        patient_user_id = req.patient_user_id

    result = book_appointment(
        clinic_id=user.clinic_id,
        doctor_id=req.doctor_id,
        patient_user_id=patient_user_id,
        date=req.date,
        time_slot=req.time_slot,
        contact=req.contact,
        session=db,
    )
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])

    patient = db.get(User, patient_user_id)
    return AppointmentResponse(
        appointment_id=result["appointment_id"],
        doctor_id=result["doctor_id"],
        doctor_name=result["doctor_name"],
        patient_user_id=patient_user_id,
        patient_name=patient.full_name if patient else "Unknown patient",
        contact=req.contact,
        date=result["date"],
        time_slot=result["time_slot"],
        status="booked",
    )


@router.post("/{appointment_id}/cancel")
def cancel(
    appointment_id: int,
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role == "patient":
        owned = list_appointments(clinic_id=user.clinic_id, patient_user_id=user.user_id, session=db)
        if not any(a["appointment_id"] == appointment_id for a in owned):
            raise HTTPException(status_code=404, detail="Appointment not found.")

    result = cancel_appointment(clinic_id=user.clinic_id, appointment_id=appointment_id, session=db)
    if not result["ok"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
