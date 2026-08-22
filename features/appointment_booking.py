from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.sqlite_models import Appointment, get_engine, get_session

_DEFAULT_ENGINE = None


def _default_session() -> Session:
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = get_engine()
    return get_session(_DEFAULT_ENGINE)


def book_appointment(
    doctor_name: str,
    patient_name: str,
    contact: str,
    date: str,
    time_slot: str,
    session: Session | None = None,
) -> dict:
    owns_session = session is None
    session = session or _default_session()
    try:
        appointment = Appointment(
            doctor_name=doctor_name,
            patient_name=patient_name,
            contact=contact,
            date=date,
            time_slot=time_slot,
        )
        session.add(appointment)
        session.commit()
        return {
            "ok": True,
            "appointment_id": appointment.id,
            "doctor_name": doctor_name,
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
    patient_name: str | None = None,
    doctor_name: str | None = None,
    session: Session | None = None,
) -> list[dict]:
    owns_session = session is None
    session = session or _default_session()
    try:
        query = select(Appointment)
        if patient_name:
            query = query.where(Appointment.patient_name == patient_name)
        if doctor_name:
            query = query.where(Appointment.doctor_name == doctor_name)
        appointments = session.scalars(query).all()
        return [
            {
                "appointment_id": a.id,
                "doctor_name": a.doctor_name,
                "patient_name": a.patient_name,
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


def cancel_appointment(appointment_id: int, session: Session | None = None) -> dict:
    owns_session = session is None
    session = session or _default_session()
    try:
        appointment = session.get(Appointment, appointment_id)
        if appointment is None:
            return {"ok": False, "error": f"No appointment with id {appointment_id}."}
        appointment.status = "cancelled"
        session.commit()
        return {"ok": True, "appointment_id": appointment_id, "status": "cancelled"}
    finally:
        if owns_session:
            session.close()
