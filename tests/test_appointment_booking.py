from features.appointment_booking import book_appointment, cancel_appointment, list_appointments


def test_book_appointment_success(sqlite_session):
    result = book_appointment(
        doctor_name="Dr. Uwimana",
        patient_name="Jean",
        contact="jean@example.com",
        date="2026-09-01",
        time_slot="10:00",
        session=sqlite_session,
    )
    assert result["ok"] is True
    assert result["appointment_id"] is not None


def test_double_booking_rejected(sqlite_session):
    book_appointment("Dr. Uwimana", "Jean", "jean@example.com", "2026-09-01", "10:00", session=sqlite_session)
    result = book_appointment("Dr. Uwimana", "Alice", "alice@example.com", "2026-09-01", "10:00", session=sqlite_session)
    assert result["ok"] is False
    assert "already booked" in result["error"]


def test_same_doctor_different_slot_allowed(sqlite_session):
    first = book_appointment("Dr. Uwimana", "Jean", "jean@example.com", "2026-09-01", "10:00", session=sqlite_session)
    second = book_appointment("Dr. Uwimana", "Alice", "alice@example.com", "2026-09-01", "11:00", session=sqlite_session)
    assert first["ok"] is True
    assert second["ok"] is True


def test_list_appointments_filters(sqlite_session):
    book_appointment("Dr. Uwimana", "Jean", "jean@example.com", "2026-09-01", "10:00", session=sqlite_session)
    book_appointment("Dr. Mugisha", "Jean", "jean@example.com", "2026-09-02", "09:00", session=sqlite_session)
    book_appointment("Dr. Uwimana", "Alice", "alice@example.com", "2026-09-03", "09:00", session=sqlite_session)

    by_patient = list_appointments(patient_name="Jean", session=sqlite_session)
    assert len(by_patient) == 2

    by_doctor = list_appointments(doctor_name="Dr. Uwimana", session=sqlite_session)
    assert len(by_doctor) == 2

    by_both = list_appointments(patient_name="Jean", doctor_name="Dr. Uwimana", session=sqlite_session)
    assert len(by_both) == 1


def test_cancel_appointment(sqlite_session):
    booked = book_appointment("Dr. Uwimana", "Jean", "jean@example.com", "2026-09-01", "10:00", session=sqlite_session)
    result = cancel_appointment(booked["appointment_id"], session=sqlite_session)
    assert result["ok"] is True

    appointments = list_appointments(patient_name="Jean", session=sqlite_session)
    assert appointments[0]["status"] == "cancelled"


def test_cancel_unknown_appointment(sqlite_session):
    result = cancel_appointment(9999, session=sqlite_session)
    assert result["ok"] is False
