import json

from features.appointments import find_doctor_id_by_name, get_doctor
from graph.mcp_client import get_mcp_tools
from graph.state import ChatState


async def _call_tool(name: str, args: dict):
    tools = await get_mcp_tools()
    tool = tools[name]
    raw = await tool.ainvoke(args)
    # FastMCP encodes a list-returning tool as one JSON text block per item,
    # and a dict-returning tool as a single JSON text block.
    if isinstance(raw, list):
        return [json.loads(item) for item in raw]
    return json.loads(raw)


def _respond(text: str, **extra) -> dict:
    return {"result": text, "messages": [{"role": "assistant", "content": text}], **extra}


async def doctor_agent(state: ChatState) -> dict:
    clinic_id = state.get("clinic_id")
    args = {"query": state["query"]}
    if clinic_id is not None:
        args["clinic_id"] = clinic_id
    doctors = await _call_tool("find_doctors", args)

    if not doctors:
        return _respond("Sorry, I couldn't find any doctors matching your question.")

    lines = [
        f"{i}. **{d['name']}** — *{d['specialty']}*" + (f", {d['hospital']}" if d.get("hospital") else "")
        for i, d in enumerate(doctors, 1)
    ]
    text = "**Here are some doctors I found:**\n" + "\n".join(lines)
    return _respond(text, doctor_recommendations=doctors)


async def pharmacy_agent(state: ChatState) -> dict:
    city = state["slots"].get("city", "")
    pharmacies = await _call_tool("find_pharmacies", {"city": city})
    if not pharmacies:
        return _respond(f"Sorry, I couldn't find any pharmacies in {city}.")
    lines = [f"- **{p['name']}** — {p['address']} ({p['phone']})" for p in pharmacies]
    return _respond(f"**Pharmacies in {city}:**\n" + "\n".join(lines))


async def diagnosis_agent(state: ChatState) -> dict:
    diagnosis = await _call_tool("get_diagnosis", {"symptoms": state["query"]})
    text = f"{diagnosis['summary']}\n\n_{diagnosis['disclaimer']}_"
    return _respond(text)


async def appointment_agent(state: ChatState) -> dict:
    clinic_id = state.get("clinic_id")
    patient_user_id = state.get("patient_user_id")
    slots = state["slots"]

    if clinic_id is None or patient_user_id is None:
        return _respond(
            "Appointment booking through chat needs you to be signed in to a clinic. "
            "Please log in and try again."
        )

    doctor_id = find_doctor_id_by_name(clinic_id, slots["doctor_name"])
    if doctor_id is None:
        return _respond(
            f"I couldn't find a doctor named \"{slots['doctor_name']}\" at your clinic — could you check the name?"
        )

    # Only attempt a direct booking if the user already volunteered date/time/contact in
    # the conversation. Otherwise we don't know their real availability -- hand off to the
    # same recommendation-card + slot-picker UI the doctor-search flow uses, rather than
    # having the LLM guess at open times via text.
    if slots.get("date") and slots.get("time_slot") and slots.get("contact"):
        booking = await _call_tool(
            "book_appointment",
            {
                "clinic_id": clinic_id,
                "doctor_id": doctor_id,
                "patient_user_id": patient_user_id,
                "date": slots["date"],
                "time_slot": slots["time_slot"],
                "contact": slots["contact"],
            },
        )
        if booking.get("ok"):
            text = (
                f"Booked! Appointment #{booking['appointment_id']} with {booking['doctor_name']} "
                f"on {booking['date']} at {booking['time_slot']}."
            )
        else:
            text = f"Couldn't book that appointment: {booking.get('error')}"
        return _respond(text)

    doctor = get_doctor(clinic_id, doctor_id)
    text = f"Here's {doctor['name']} — pick a time that works for you:"
    return _respond(text, doctor_recommendations=[doctor])
