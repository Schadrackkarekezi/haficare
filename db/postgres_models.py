import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

load_dotenv()


class Base(DeclarativeBase):
    pass


class Clinic(Base):
    __tablename__ = "clinics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    city: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"), nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)  # "staff" | "patient"
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    specialty: Mapped[str] = mapped_column(String, nullable=False)
    bio: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    neo4j_synced_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Appointment(Base):
    __tablename__ = "clinic_appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    patient_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    contact: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    time_slot: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="booked")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("doctor_id", "date", "time_slot", name="uq_clinic_doctor_slot"),
    )


class DoctorWeeklyHours(Base):
    __tablename__ = "doctor_weekly_hours"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(nullable=False)  # 0=Monday .. 6=Sunday
    start_time: Mapped[str] = mapped_column(String, nullable=False)  # "HH:MM"
    end_time: Mapped[str] = mapped_column(String, nullable=False)  # "HH:MM"


def get_engine(database_url: str | None = None) -> Engine:
    database_url = database_url or os.environ["DATABASE_URL"]
    engine = create_engine(database_url)
    init_db(engine)
    return engine


def get_session(engine: Engine) -> Session:
    return Session(engine)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)
