import os
from datetime import datetime

from sqlalchemy import String, UniqueConstraint, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

DEFAULT_DB_PATH = os.getenv("HAFICARE_DB_PATH", "sqlite:///data/haficare.db")


class Base(DeclarativeBase):
    pass


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_name: Mapped[str] = mapped_column(String, nullable=False)
    patient_name: Mapped[str] = mapped_column(String, nullable=False)
    contact: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    time_slot: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="booked")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("doctor_name", "date", "time_slot", name="uq_doctor_slot"),
    )


def get_engine(db_path: str = DEFAULT_DB_PATH) -> Engine:
    engine = create_engine(db_path)
    init_db(engine)
    return engine


def get_session(engine: Engine) -> Session:
    return Session(engine)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)
