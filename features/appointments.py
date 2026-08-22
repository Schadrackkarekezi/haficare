from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.postgres_models import Appointment, Doctor, DoctorWeeklyHours, User, get_engine, get_session

_DEFAULT_ENGINE = None

SLOT_MINUTES = 30


def _default_session() -> Session:
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = get_engine()
    return get_session(_DEFAULT_ENGINE)


def book_appointment(
    clinic_id: int,
    doctor_id: int,
    patient_user_id: int,
    date: str,
    time_slot: str,
    contact: str,
    session: Session | None = None,
) -> dict:
    owns_session = session is None
    session = session or _default_session()
    try:
        doctor = session.get(Doctor, doctor_id)
        if doctor is None or doctor.clinic_id != clinic_id:
            return {"ok": False, "error": "That doctor isn't part of this clinic."}

        patient = session.get(User, patient_user_id)
        if patient is None or patient.clinic_id != clinic_id or patient.role != "patient":
            return {"ok": False, "error": "That patient isn't part of this clinic."}

        appointment = Appointment(
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            patient_user_id=patient_user_id,
            contact=contact,
            date=date,
            time_slot=time_slot,
        )
        session.add(appointment)
        session.commit()
        return {
            "ok": True,
            "appointment_id": appointment.id,
            "doctor_id": doctor_id,
            "doctor_name": doctor.name,
            "date": date,
            "time_slot": time_slot,
        }
    except IntegrityError:
        session.rollback()
        return {"ok": False, "error": "That doctor is already booked for this date and time slot."}
    finally:
        if owns_session:
            session.close()


def list_appointments(
    clinic_id: int,
    patient_user_id: int | None = None,
    doctor_id: int | None = None,
    session: Session | None = None,
) -> list[dict]:
    owns_session = session is None
    session = session or _default_session()
    try:
        query = select(Appointment).where(Appointment.clinic_id == clinic_id)
        if patient_user_id is not None:
            query = query.where(Appointment.patient_user_id == patient_user_id)
        if doctor_id is not None:
            query = query.where(Appointment.doctor_id == doctor_id)
        appointments = session.scalars(query).all()
        return [
            {
                "appointment_id": a.id,
                "doctor_id": a.doctor_id,
                "patient_user_id": a.patient_user_id,
                "contact": a.contact,
                "date": a.date,
                "time_slot": a.time_slot,
                "status": a.status,
            }
            for a in appointments
        ]
    finally:
        if owns_session:
            session.close()


def cancel_appointment(clinic_id: int, appointment_id: int, session: Session | None = None) -> dict:
    owns_session = session is None
    session = session or _default_session()
    try:
        appointment = session.scalar(
            select(Appointment).where(Appointment.id == appointment_id, Appointment.clinic_id == clinic_id)
        )
        if appointment is None:
            return {"ok": False, "error": f"No appointment with id {appointment_id}."}
        appointment.status = "cancelled"
        session.commit()
        return {"ok": True, "appointment_id": appointment_id, "status": "cancelled"}
    finally:
        if owns_session:
            session.close()


def find_doctor_id_by_name(clinic_id: int, name: str, session: Session | None = None) -> int | None:
    owns_session = session is None
    session = session or _default_session()
    try:
        doctor = session.scalar(
            select(Doctor).where(
                Doctor.clinic_id == clinic_id,
                Doctor.is_active.is_(True),
                func.lower(Doctor.name) == name.strip().lower(),
            )
        )
        return doctor.id if doctor else None
    finally:
        if owns_session:
            session.close()


def get_doctor(clinic_id: int, doctor_id: int, session: Session | None = None) -> dict | None:
    owns_session = session is None
    session = session or _default_session()
    try:
        doctor = session.get(Doctor, doctor_id)
        if doctor is None or doctor.clinic_id != clinic_id:
            return None
        return {"doctor_id": doctor.id, "name": doctor.name, "specialty": doctor.specialty}
    finally:
        if owns_session:
            session.close()


def get_available_slots(clinic_id: int, doctor_id: int, date: str, session: Session | None = None) -> list[str]:
    owns_session = session is None
    session = session or _default_session()
    try:
        doctor = session.get(Doctor, doctor_id)
        if doctor is None or doctor.clinic_id != clinic_id:
            return []

        weekday = datetime.strptime(date, "%Y-%m-%d").weekday()
        hours = session.scalar(
            select(DoctorWeeklyHours).where(
                DoctorWeeklyHours.doctor_id == doctor_id,
                DoctorWeeklyHours.day_of_week == weekday,
            )
        )
        if hours is None:
            return []

        booked = set(
            session.scalars(
                select(Appointment.time_slot).where(
                    Appointment.doctor_id == doctor_id,
                    Appointment.date == date,
                    Appointment.status == "booked",
                )
            ).all()
        )

        start = datetime.strptime(hours.start_time, "%H:%M")
        end = datetime.strptime(hours.end_time, "%H:%M")
        slots = []
        current = start
        while current + timedelta(minutes=SLOT_MINUTES) <= end:
            slot = current.strftime("%H:%M")
            if slot not in booked:
                slots.append(slot)
            current += timedelta(minutes=SLOT_MINUTES)
        return slots
    finally:
        if owns_session:
            session.close()
