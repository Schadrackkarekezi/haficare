from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from api.appointments.router import router as appointments_router
from api.auth.router import router as auth_router
from api.chat.router import router as chat_router
from api.clinics.router import router as clinics_router
from api.doctors.router import router as doctors_router

# No CORS configuration needed: the browser never calls this API directly.
# The Next.js frontend's Route Handlers (server-side, same-origin to the browser)
# proxy requests here with a Bearer token -- see frontend/ "BFF" pattern in the plan.
app = FastAPI(title="HafiCare API")

app.include_router(auth_router)
app.include_router(clinics_router)
app.include_router(doctors_router)
app.include_router(appointments_router)
app.include_router(chat_router)


@app.get("/health")
def health():
    return {"status": "ok"}
