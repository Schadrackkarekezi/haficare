from pydantic import BaseModel


class ClinicSignupRequest(BaseModel):
    clinic_name: str
    clinic_city: str | None = None
    full_name: str
    email: str
    password: str
    phone: str | None = None


class PatientSignupRequest(BaseModel):
    clinic_slug: str
    full_name: str
    email: str
    password: str
    phone: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    role: str


class MeResponse(BaseModel):
    user_id: int
    clinic_id: int
    role: str
    full_name: str
    email: str
