"""One-off script to seed a demo clinic for manual/local testing.

Usage: python -m data.seed_demo_clinic
Requires DATABASE_URL, NEO4J_*, and OPENAI_API_KEY_2 to be set (.env).
"""

from api.auth.security import hash_password
from data.load_data import load_doctor_data
from db.neo4j_interface import upsert_clinic_doctor
from db.postgres_models import Clinic, Doctor, DoctorWeeklyHours, User, get_engine, get_session

DEMO_CLINIC_SLUG = "demo-clinic"
WEEKDAYS_MON_FRI = range(5)  # 0=Monday .. 4=Friday


def seed() -> None:
    engine = get_engine()
    session = get_session(engine)

    clinic = Clinic(name="HafiCare Demo Clinic", slug=DEMO_CLINIC_SLUG, city="Kigali")
    session.add(clinic)
    session.flush()

    staff = User(
        clinic_id=clinic.id,
        email="staff@demo-clinic.test",
        hashed_password=hash_password("demo-password"),
        role="staff",
        full_name="Demo Staff",
    )
    patient = User(
        clinic_id=clinic.id,
        email="patient@demo-clinic.test",
        hashed_password=hash_password("demo-password"),
        role="patient",
        full_name="Demo Patient",
    )
    session.add_all([staff, patient])
    session.flush()

    doctors_df = load_doctor_data().head(10)  # Kigali doctors -- a manageable demo roster
    for _, row in doctors_df.iterrows():
        doctor = Doctor(clinic_id=clinic.id, name=row["name"], specialty=row["specialty"], bio=row["description"])
        session.add(doctor)
        session.flush()

        for day in WEEKDAYS_MON_FRI:
            session.add(
                DoctorWeeklyHours(doctor_id=doctor.id, day_of_week=day, start_time="09:00", end_time="17:00")
            )

        print(f"Pushing {doctor.name} into Neo4j...")
        upsert_clinic_doctor(doctor.id, clinic.id, doctor.name, doctor.specialty, doctor.bio)

    clinic_name, clinic_slug = clinic.name, clinic.slug  # read before commit/close detaches the instance
    session.commit()
    session.close()

    print()
    print(f"Seeded clinic '{clinic_name}' (slug: {clinic_slug}) with {len(doctors_df)} doctors.")
    print("Demo staff login: staff@demo-clinic.test / demo-password")
    print("Demo patient login: patient@demo-clinic.test / demo-password")


if __name__ == "__main__":
    seed()
