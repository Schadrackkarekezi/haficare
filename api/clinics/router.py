from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.deps import get_db
from db.postgres_models import Clinic

router = APIRouter(prefix="/clinics", tags=["clinics"])


class ClinicSummary(BaseModel):
    slug: str
    name: str
    city: str | None


@router.get("", response_model=list[ClinicSummary])
def list_clinics(db: Session = Depends(get_db)):
    """Public list used by the patient signup picker -- no auth required."""
    clinics = db.scalars(select(Clinic).order_by(Clinic.name)).all()
    return [ClinicSummary(slug=c.slug, name=c.name, city=c.city) for c in clinics]
