from pydantic import BaseModel, Field

from graph.state import ChatState, Intent
from llm.openai_model import get_llm_model

# Only doctor_name gates routing for "appointment" -- once we know who, appointment_agent
# hands off to a real availability picker instead of the LLM guessing at open time slots via
# text. contact/date/time_slot are still extracted opportunistically (see slots) so a user who
# volunteers everything in one message ("book me with Dr. X at 2pm Tuesday, contact ...") still
# gets booked directly without ever seeing the picker.
REQUIRED_SLOTS: dict[str, list[str]] = {
    "appointment": ["doctor_name"],
    "pharmacy": ["city"],
}


def _system_prompt(patient_identity_known: bool) -> str:
    identity_note = (
        " The patient's own identity is already known from their logged-in account -- never ask for "
        "their name, and never list it as missing."
        if patient_identity_known
        else ""
    )
    return (
        "You are the planning module for HafiCare, a health assistant for patients in Rwanda. "
        "Classify the user's intent from the conversation as one of: doctor, pharmacy, diagnosis, appointment, unknown.\n"
        "- doctor: user wants to find a doctor or ask a health question that should be matched to a doctor. "
        "Put their question in `query`.\n"
        "- pharmacy: user wants to find a pharmacy. Extract `city` into `slots`.\n"
        "- diagnosis: user is describing symptoms and wants informational possibilities. "
        "Put their symptom description in `query`.\n"
        "- appointment: user wants to book an appointment. Extract doctor_name into `slots` -- this is the "
        "only thing you need to ask for. If the user already volunteered contact/date/time_slot in the same "
        "message, extract those into `slots` too, but never ask for them proactively: once the doctor is known, "
        "the app shows real available times for the user to pick from, so don't guess or request a date/time "
        f"yourself unless the user already gave one.{identity_note}\n"
        "- unknown: greeting, small talk, or anything that doesn't fit the above.\n"
        "If required information for the current intent is still missing, set needs_clarification=true and put "
        "a short, specific follow-up question in `response` asking only for what's missing. "
        "Otherwise leave `response` empty."
    )


class PlannerOutput(BaseModel):
    response: str = Field(default="", description="Follow-up question if clarification is needed, else empty.")
    intent: Intent = "unknown"
    query: str = Field(default="", description="Free-text query for the doctor or diagnosis sub-agent.")
    slots: dict[str, str] = Field(default_factory=dict, description="Extracted slot values.")
    needs_clarification: bool = Field(default=False)


def planner_node(state: ChatState) -> dict:
    patient_identity_known = state.get("patient_user_id") is not None
    llm = get_llm_model().with_structured_output(PlannerOutput, method="function_calling")
    messages = [{"role": "system", "content": _system_prompt(patient_identity_known)}, *state["messages"]]
    output: PlannerOutput = llm.invoke(messages)

    required = REQUIRED_SLOTS.get(output.intent, [])
    missing = [s for s in required if not output.slots.get(s)]
    needs_clarification = output.needs_clarification or bool(missing)

    update: dict = {
        "intent": output.intent,
        "query": output.query,
        "slots": output.slots,
        "needs_clarification": needs_clarification,
    }
    if needs_clarification or output.intent == "unknown":
        text = output.response or "Could you share a bit more detail so I can help?"
        update["result"] = text
        update["messages"] = [{"role": "assistant", "content": text}]
    return update


def route_from_planner(state: ChatState) -> str:
    if state["needs_clarification"] or state["intent"] == "unknown":
        return "end"
    return state["intent"]
