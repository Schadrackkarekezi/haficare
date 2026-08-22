from langchain_core.messages import HumanMessage

from graph.planner import PlannerOutput, planner_node, route_from_planner


class FakeStructuredLLM:
    def __init__(self, output: PlannerOutput):
        self.output = output

    def invoke(self, messages):
        return self.output


class FakeLLM:
    def __init__(self, output: PlannerOutput):
        self.output = output

    def with_structured_output(self, schema, **kwargs):
        return FakeStructuredLLM(self.output)


def _run_planner(monkeypatch, output: PlannerOutput) -> dict:
    monkeypatch.setattr("graph.planner.get_llm_model", lambda: FakeLLM(output))
    state = {"messages": [HumanMessage(content="hi")], "intent": "unknown", "query": "", "slots": {}, "needs_clarification": False, "result": ""}
    return planner_node(state)


def test_doctor_intent_routes_to_doctor_agent(monkeypatch):
    output = PlannerOutput(intent="doctor", query="chest pain specialist")
    update = _run_planner(monkeypatch, output)
    state = {**update, "intent": update["intent"], "needs_clarification": update["needs_clarification"]}
    assert route_from_planner(state) == "doctor"
    assert update["query"] == "chest pain specialist"


def test_pharmacy_missing_city_requires_clarification(monkeypatch):
    output = PlannerOutput(intent="pharmacy", slots={}, response="Which city are you in?")
    update = _run_planner(monkeypatch, output)
    assert update["needs_clarification"] is True
    assert route_from_planner(update) == "end"
    assert update["result"] == "Which city are you in?"


def test_pharmacy_with_city_routes_to_pharmacy_agent(monkeypatch):
    output = PlannerOutput(intent="pharmacy", slots={"city": "Kigali"})
    update = _run_planner(monkeypatch, output)
    assert update["needs_clarification"] is False
    assert route_from_planner(update) == "pharmacy"


def test_appointment_missing_doctor_name_requires_clarification(monkeypatch):
    # Only doctor_name gates routing now -- date/contact/time_slot are optional at this
    # stage, since appointment_agent shows a real availability picker once the doctor is known.
    output = PlannerOutput(
        intent="appointment",
        slots={},
        response="Which doctor would you like to see?",
    )
    update = _run_planner(monkeypatch, output)
    assert update["needs_clarification"] is True
    assert route_from_planner(update) == "end"


def test_appointment_doctor_name_only_routes_to_appointment_agent(monkeypatch):
    output = PlannerOutput(intent="appointment", slots={"doctor_name": "Dr. Uwimana"})
    update = _run_planner(monkeypatch, output)
    assert update["needs_clarification"] is False
    assert route_from_planner(update) == "appointment"


def test_appointment_all_slots_present_routes_to_appointment_agent(monkeypatch):
    output = PlannerOutput(
        intent="appointment",
        slots={
            "doctor_name": "Dr. Uwimana",
            "contact": "jean@example.com",
            "date": "2026-09-01",
            "time_slot": "10:00",
        },
    )
    update = _run_planner(monkeypatch, output)
    assert update["needs_clarification"] is False
    assert route_from_planner(update) == "appointment"


def test_unknown_intent_gets_a_direct_reply(monkeypatch):
    output = PlannerOutput(intent="unknown", response="Hi! I can help you find a doctor or pharmacy.")
    update = _run_planner(monkeypatch, output)
    assert route_from_planner(update) == "end"
    assert update["result"] == "Hi! I can help you find a doctor or pharmacy."
