from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.deps import AuthenticatedUser, get_current_user, get_db, require_role
from api.doctors.schemas import (
    AvailabilityResponse,
    DoctorCreateRequest,
    DoctorResponse,
    DoctorUpdateRequest,
    WeeklyHoursRequest,
)
from db.neo4j_interface import deactivate_clinic_doctor, upsert_clinic_doctor
from db.postgres_models import Doctor, DoctorWeeklyHours
from features.appointments import get_available_slots

router = APIRouter(prefix="/doctors", tags=["doctors"])


def _to_response(doctor: Doctor) -> DoctorResponse:
    return DoctorResponse(
        id=doctor.id, name=doctor.name, specialty=doctor.specialty, bio=doctor.bio, is_active=doctor.is_active
    )


def _get_clinic_doctor(db: Session, clinic_id: int, doctor_id: int) -> Doctor:
    doctor = db.get(Doctor, doctor_id)
    if doctor is None or doctor.clinic_id != clinic_id:
        raise HTTPException(status_code=404, detail="Doctor not found.")
    return doctor


@router.get("", response_model=list[DoctorResponse])
def list_doctors(
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doctors = db.scalars(
        select(Doctor).where(Doctor.clinic_id == user.clinic_id, Doctor.is_active.is_(True))
    ).all()
    return [_to_response(d) for d in doctors]


@router.post("", response_model=DoctorResponse)
def create_doctor(
    req: DoctorCreateRequest,
    user: AuthenticatedUser = Depends(require_role("staff")),
    db: Session = Depends(get_db),
):
    doctor = Doctor(clinic_id=user.clinic_id, name=req.name, specialty=req.specialty, bio=req.bio)
    db.add(doctor)
    db.commit()
    upsert_clinic_doctor(doctor.id, user.clinic_id, doctor.name, doctor.specialty, doctor.bio)
    return _to_response(doctor)


@router.patch("/{doctor_id}", response_model=DoctorResponse)
def update_doctor(
    doctor_id: int,
    req: DoctorUpdateRequest,
    user: AuthenticatedUser = Depends(require_role("staff")),
    db: Session = Depends(get_db),
):
    doctor = _get_clinic_doctor(db, user.clinic_id, doctor_id)
    if req.name is not None:
        doctor.name = req.name
    if req.specialty is not None:
        doctor.specialty = req.specialty
    if req.bio is not None:
        doctor.bio = req.bio
    if req.is_active is not None:
        doctor.is_active = req.is_active
    db.commit()

    if doctor.is_active:
        upsert_clinic_doctor(doctor.id, user.clinic_id, doctor.name, doctor.specialty, doctor.bio)
    else:
        deactivate_clinic_doctor(doctor.id)
    return _to_response(doctor)


@router.delete("/{doctor_id}")
def delete_doctor(
    doctor_id: int,
    user: AuthenticatedUser = Depends(require_role("staff")),
    db: Session = Depends(get_db),
):
    doctor = _get_clinic_doctor(db, user.clinic_id, doctor_id)
    doctor.is_active = False
    db.commit()
    deactivate_clinic_doctor(doctor.id)
    return {"ok": True}


@router.put("/{doctor_id}/weekly-hours")
def set_weekly_hours(
    doctor_id: int,
    req: WeeklyHoursRequest,
    user: AuthenticatedUser = Depends(require_role("staff")),
    db: Session = Depends(get_db),
):
    _get_clinic_doctor(db, user.clinic_id, doctor_id)
    db.query(DoctorWeeklyHours).filter(DoctorWeeklyHours.doctor_id == doctor_id).delete()
    for entry in req.hours:
        db.add(
            DoctorWeeklyHours(
                doctor_id=doctor_id,
                day_of_week=entry.day_of_week,
                start_time=entry.start_time,
                end_time=entry.end_time,
            )
        )
    db.commit()
    return {"ok": True}


@router.get("/{doctor_id}/availability", response_model=AvailabilityResponse)
def availability(
    doctor_id: int,
    date: str,
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_clinic_doctor(db, user.clinic_id, doctor_id)
    slots = get_available_slots(user.clinic_id, doctor_id, date, session=db)
    return AvailabilityResponse(date=date, slots=slots)
