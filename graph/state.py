from typing import Annotated, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import NotRequired, TypedDict

Intent = Literal["doctor", "pharmacy", "diagnosis", "appointment", "unknown"]


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    intent: Intent
    query: str
    slots: dict[str, str]
    needs_clarification: bool
    result: str
    # Set server-side from the authenticated JWT before the graph ever runs -- never
    # derived from message text. Absent (legacy app.py / existing tests) means the
    # unscoped, global-directory behavior is used everywhere it matters.
    clinic_id: NotRequired[int]
    patient_user_id: NotRequired[int | None]
    # Structured doctor matches for the frontend to render as cards, alongside `result`'s text.
    doctor_recommendations: NotRequired[list[dict]]
