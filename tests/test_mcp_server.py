import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from sqlalchemy import create_engine

from db.postgres_models import Clinic, Doctor, User, get_session, init_db

REPO_ROOT = Path(__file__).resolve().parent.parent


def _server_params(database_url: str) -> StdioServerParameters:
    env = {**os.environ, "DATABASE_URL": database_url}
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_server.server"],
        cwd=str(REPO_ROOT),
        env=env,
    )


def _seed_clinic_doctor_patient(database_url: str) -> tuple[int, int, int]:
    engine = create_engine(database_url)
    init_db(engine)
    session = get_session(engine)
    clinic = Clinic(name="Demo Clinic", slug="demo-clinic")
    session.add(clinic)
    session.flush()
    doctor = Doctor(clinic_id=clinic.id, name="Dr. Uwimana", specialty="Cardiology", bio="Heart stuff.")
    patient = User(clinic_id=clinic.id, email="jean@example.com", hashed_password="x", role="patient", full_name="Jean")
    session.add_all([doctor, patient])
    session.commit()
    ids = (clinic.id, doctor.id, patient.id)
    session.close()
    return ids


@pytest.mark.asyncio
async def test_list_tools_registers_all_six(tmp_path):
    params = _server_params(f"sqlite:///{tmp_path / 'test.db'}")
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            assert names == {
                "find_doctors",
                "find_pharmacies",
                "get_diagnosis",
                "book_appointment",
                "list_appointments",
                "cancel_appointment",
            }


@pytest.mark.asyncio
async def test_appointment_tools_end_to_end(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    clinic_id, doctor_id, patient_id = _seed_clinic_doctor_patient(database_url)
    params = _server_params(database_url)

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            book_result = await session.call_tool(
                "book_appointment",
                {
                    "clinic_id": clinic_id,
                    "doctor_id": doctor_id,
                    "patient_user_id": patient_id,
                    "date": "2026-09-01",
                    "time_slot": "10:00",
                    "contact": "jean@example.com",
                },
            )
            assert book_result.isError is False
            assert '"ok": true' in book_result.content[0].text.lower()

            duplicate_result = await session.call_tool(
                "book_appointment",
                {
                    "clinic_id": clinic_id,
                    "doctor_id": doctor_id,
                    "patient_user_id": patient_id,
                    "date": "2026-09-01",
                    "time_slot": "10:00",
                    "contact": "jean@example.com",
                },
            )
            assert duplicate_result.isError is False
            assert "already booked" in duplicate_result.content[0].text

            list_result = await session.call_tool(
                "list_appointments", {"clinic_id": clinic_id, "patient_user_id": patient_id}
            )
            assert list_result.isError is False
            assert "jean@example.com" in list_result.content[0].text

            cancel_result = await session.call_tool(
                "cancel_appointment", {"clinic_id": clinic_id, "appointment_id": 1}
            )
            assert cancel_result.isError is False
            assert "cancelled" in cancel_result.content[0].text
