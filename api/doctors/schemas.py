from pydantic import BaseModel


class DoctorCreateRequest(BaseModel):
    name: str
    specialty: str
    bio: str


class DoctorUpdateRequest(BaseModel):
    name: str | None = None
    specialty: str | None = None
    bio: str | None = None
    is_active: bool | None = None


class DoctorResponse(BaseModel):
    id: int
    name: str
    specialty: str
    bio: str
    is_active: bool


class WeeklyHoursEntry(BaseModel):
    day_of_week: int  # 0=Monday .. 6=Sunday
    start_time: str  # "HH:MM"
    end_time: str  # "HH:MM"


class WeeklyHoursRequest(BaseModel):
    hours: list[WeeklyHoursEntry]


class AvailabilityResponse(BaseModel):
    date: str
    slots: list[str]
