from db.postgres_models import Clinic, Doctor, DoctorWeeklyHours, User
from features.appointments import (
    book_appointment,
    cancel_appointment,
    find_doctor_id_by_name,
    get_available_slots,
    get_doctor,
    list_appointments,
)


def _seed_clinic_with_doctor(session, clinic_name="Clinic A", doctor_name="Dr. Uwimana"):
    clinic = Clinic(name=clinic_name, slug=clinic_name.lower().replace(" ", "-"))
    session.add(clinic)
    session.flush()

    patient = User(
        clinic_id=clinic.id,
        email=f"{doctor_name.lower().replace(' ', '')}-{clinic_name.lower()}@example.com",
        hashed_password="x",
        role="patient",
        full_name="Jean Patient",
    )
    doctor = Doctor(clinic_id=clinic.id, name=doctor_name, specialty="Cardiology", bio="Heart stuff.")
    session.add_all([patient, doctor])
    session.flush()
    return clinic, doctor, patient


def test_book_appointment_success(pg_session):
    clinic, doctor, patient = _seed_clinic_with_doctor(pg_session)

    result = book_appointment(
        clinic_id=clinic.id,
        doctor_id=doctor.id,
        patient_user_id=patient.id,
        date="2026-09-01",
        time_slot="10:00",
        contact="jean@example.com",
        session=pg_session,
    )

    assert result["ok"] is True
    assert result["doctor_name"] == "Dr. Uwimana"


def test_double_booking_rejected(pg_session):
    clinic, doctor, patient = _seed_clinic_with_doctor(pg_session)
    book_appointment(clinic.id, doctor.id, patient.id, "2026-09-01", "10:00", "jean@example.com", session=pg_session)

    result = book_appointment(clinic.id, doctor.id, patient.id, "2026-09-01", "10:00", "jean@example.com", session=pg_session)

    assert result["ok"] is False
    assert "already booked" in result["error"]


def test_book_appointment_rejects_doctor_from_other_clinic(pg_session):
    clinic_a, doctor_a, patient_a = _seed_clinic_with_doctor(pg_session, "Clinic A", "Dr. Uwimana")
    clinic_b, doctor_b, patient_b = _seed_clinic_with_doctor(pg_session, "Clinic B", "Dr. Mugisha")

    # patient_a (clinic A) tries to book doctor_b, who belongs to clinic B
    result = book_appointment(
        clinic_id=clinic_a.id,
        doctor_id=doctor_b.id,
        patient_user_id=patient_a.id,
        date="2026-09-01",
        time_slot="10:00",
        contact="jean@example.com",
        session=pg_session,
    )

    assert result["ok"] is False
    assert "isn't part of this clinic" in result["error"]


def test_book_appointment_rejects_patient_from_other_clinic(pg_session):
    clinic_a, doctor_a, patient_a = _seed_clinic_with_doctor(pg_session, "Clinic A", "Dr. Uwimana")
    clinic_b, doctor_b, patient_b = _seed_clinic_with_doctor(pg_session, "Clinic B", "Dr. Mugisha")

    # staff at clinic A tries to book their own doctor for a clinic B patient
    result = book_appointment(
        clinic_id=clinic_a.id,
        doctor_id=doctor_a.id,
        patient_user_id=patient_b.id,
        date="2026-09-01",
        time_slot="10:00",
        contact="jean@example.com",
        session=pg_session,
    )

    assert result["ok"] is False
    assert "isn't part of this clinic" in result["error"]


def test_list_appointments_excludes_other_clinics(pg_session):
    clinic_a, doctor_a, patient_a = _seed_clinic_with_doctor(pg_session, "Clinic A", "Dr. Uwimana")
    clinic_b, doctor_b, patient_b = _seed_clinic_with_doctor(pg_session, "Clinic B", "Dr. Mugisha")
    book_appointment(clinic_a.id, doctor_a.id, patient_a.id, "2026-09-01", "10:00", "a@example.com", session=pg_session)
    book_appointment(clinic_b.id, doctor_b.id, patient_b.id, "2026-09-01", "10:00", "b@example.com", session=pg_session)

    results = list_appointments(clinic_id=clinic_a.id, session=pg_session)

    assert len(results) == 1
    assert results[0]["doctor_id"] == doctor_a.id


def test_cancel_appointment_cross_tenant_returns_not_found(pg_session):
    clinic_a, doctor_a, patient_a = _seed_clinic_with_doctor(pg_session, "Clinic A", "Dr. Uwimana")
    clinic_b, _, _ = _seed_clinic_with_doctor(pg_session, "Clinic B", "Dr. Mugisha")
    booked = book_appointment(clinic_a.id, doctor_a.id, patient_a.id, "2026-09-01", "10:00", "a@example.com", session=pg_session)

    # clinic B guesses clinic A's appointment id
    result = cancel_appointment(clinic_id=clinic_b.id, appointment_id=booked["appointment_id"], session=pg_session)

    assert result["ok"] is False
    still_there = list_appointments(clinic_id=clinic_a.id, session=pg_session)
    assert still_there[0]["status"] == "booked"


def test_cancel_appointment_success(pg_session):
    clinic, doctor, patient = _seed_clinic_with_doctor(pg_session)
    booked = book_appointment(clinic.id, doctor.id, patient.id, "2026-09-01", "10:00", "a@example.com", session=pg_session)

    result = cancel_appointment(clinic_id=clinic.id, appointment_id=booked["appointment_id"], session=pg_session)

    assert result["ok"] is True
    assert list_appointments(clinic_id=clinic.id, session=pg_session)[0]["status"] == "cancelled"


def test_find_doctor_id_by_name_case_insensitive_and_scoped(pg_session):
    clinic_a, doctor_a, _ = _seed_clinic_with_doctor(pg_session, "Clinic A", "Dr. Uwimana")
    clinic_b, doctor_b, _ = _seed_clinic_with_doctor(pg_session, "Clinic B", "Dr. Uwimana")

    found = find_doctor_id_by_name(clinic_a.id, "dr. uwimana", session=pg_session)

    assert found == doctor_a.id
    assert found != doctor_b.id


def test_find_doctor_id_by_name_not_found(pg_session):
    clinic, _, _ = _seed_clinic_with_doctor(pg_session)

    assert find_doctor_id_by_name(clinic.id, "Dr. Nobody", session=pg_session) is None


def test_get_available_slots_excludes_booked_and_respects_hours(pg_session):
    clinic, doctor, patient = _seed_clinic_with_doctor(pg_session)
    # 2026-09-01 is a Tuesday -> weekday() == 1
    pg_session.add(DoctorWeeklyHours(doctor_id=doctor.id, day_of_week=1, start_time="09:00", end_time="10:00"))
    pg_session.flush()
    book_appointment(clinic.id, doctor.id, patient.id, "2026-09-01", "09:00", "a@example.com", session=pg_session)

    slots = get_available_slots(clinic.id, doctor.id, "2026-09-01", session=pg_session)

    assert slots == ["09:30"]  # 09:00 booked, 30-min increments up to (not including) 10:00


def test_get_available_slots_no_hours_configured_returns_empty(pg_session):
    clinic, doctor, _ = _seed_clinic_with_doctor(pg_session)

    slots = get_available_slots(clinic.id, doctor.id, "2026-09-01", session=pg_session)

    assert slots == []


def test_get_available_slots_wrong_weekday_returns_empty(pg_session):
    clinic, doctor, _ = _seed_clinic_with_doctor(pg_session)
    # Configure Monday (0) hours, but query a Tuesday (2026-09-01, weekday() == 1)
    pg_session.add(DoctorWeeklyHours(doctor_id=doctor.id, day_of_week=0, start_time="09:00", end_time="10:00"))
    pg_session.flush()

    slots = get_available_slots(clinic.id, doctor.id, "2026-09-01", session=pg_session)

    assert slots == []


def test_get_doctor_returns_summary(pg_session):
    clinic, doctor, _ = _seed_clinic_with_doctor(pg_session)

    result = get_doctor(clinic.id, doctor.id, session=pg_session)

    assert result == {"doctor_id": doctor.id, "name": "Dr. Uwimana", "specialty": "Cardiology"}


def test_get_doctor_cross_tenant_returns_none(pg_session):
    clinic_a, doctor_a, _ = _seed_clinic_with_doctor(pg_session, "Clinic A", "Dr. Uwimana")
    clinic_b, _, _ = _seed_clinic_with_doctor(pg_session, "Clinic B", "Dr. Mugisha")

    assert get_doctor(clinic_b.id, doctor_a.id, session=pg_session) is None
