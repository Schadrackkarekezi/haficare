import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.auth.schemas import (
    ClinicSignupRequest,
    LoginRequest,
    MeResponse,
    PatientSignupRequest,
    TokenResponse,
)
from api.auth.security import create_access_token, hash_password, verify_password
from api.deps import AuthenticatedUser, get_current_user, get_db
from db.postgres_models import Clinic, User

router = APIRouter(prefix="/auth", tags=["auth"])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "clinic"


@router.post("/signup/clinic", response_model=TokenResponse)
def signup_clinic(req: ClinicSignupRequest, db: Session = Depends(get_db)):
    base_slug = _slugify(req.clinic_name)
    slug = base_slug
    suffix = 1
    while db.scalar(select(Clinic).where(Clinic.slug == slug)) is not None:
        suffix += 1
        slug = f"{base_slug}-{suffix}"

    clinic = Clinic(name=req.clinic_name, slug=slug, city=req.clinic_city)
    db.add(clinic)
    db.flush()

    user = User(
        clinic_id=clinic.id,
        email=req.email,
        hashed_password=hash_password(req.password),
        role="staff",
        full_name=req.full_name,
        phone=req.phone,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="That email is already registered.")

    token = create_access_token(user_id=user.id, clinic_id=clinic.id, role="staff")
    return TokenResponse(access_token=token, role="staff")


@router.post("/signup/patient", response_model=TokenResponse)
def signup_patient(req: PatientSignupRequest, db: Session = Depends(get_db)):
    clinic = db.scalar(select(Clinic).where(Clinic.slug == req.clinic_slug))
    if clinic is None:
        raise HTTPException(status_code=404, detail="No clinic found with that code.")

    user = User(
        clinic_id=clinic.id,
        email=req.email,
        hashed_password=hash_password(req.password),
        role="patient",
        full_name=req.full_name,
        phone=req.phone,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="That email is already registered.")

    token = create_access_token(user_id=user.id, clinic_id=clinic.id, role="patient")
    return TokenResponse(access_token=token, role="patient")


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == req.email))
    if user is None or not user.is_active or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token(user_id=user.id, clinic_id=user.clinic_id, role=user.role)
    return TokenResponse(access_token=token, role=user.role)


@router.get("/me", response_model=MeResponse)
def me(current: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.get(User, current.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return MeResponse(
        user_id=user.id,
        clinic_id=user.clinic_id,
        role=user.role,
        full_name=user.full_name,
        email=user.email,
    )
