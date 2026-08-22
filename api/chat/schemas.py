from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    thread_id: str


class ChatResponse(BaseModel):
    reply: str
    intent: str
    doctor_recommendations: list[dict] | None = None
