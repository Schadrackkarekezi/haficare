import json

import pytest
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from graph.build import build_graph
from graph.planner import PlannerOutput


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


def _fake_tools(name_to_result: dict):
    tools = {}
    for name, result in name_to_result.items():

        def make(result=result):
            @tool
            async def _t(**kwargs) -> str:
                """Fake MCP tool for testing."""
                return json.dumps(result)

            return _t

        tools[name] = make()
    return tools


@pytest.mark.asyncio
async def test_doctor_intent_end_to_end(monkeypatch):
    monkeypatch.setattr("graph.planner.get_llm_model", lambda: FakeLLM(PlannerOutput(intent="doctor", query="chest pain")))

    async def fake_get_tools():
        return _fake_tools({"find_doctors": [{"name": "Dr. Uwimana", "specialty": "Cardiology", "score": 0.9}]})

    monkeypatch.setattr("graph.nodes.get_mcp_tools", fake_get_tools)

    graph = build_graph()
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="who can see me for chest pain?")]},
        config={"configurable": {"thread_id": "t1"}},
    )
    assert "Dr. Uwimana" in result["result"]


@pytest.mark.asyncio
async def test_pharmacy_intent_end_to_end(monkeypatch):
    monkeypatch.setattr(
        "graph.planner.get_llm_model",
        lambda: FakeLLM(PlannerOutput(intent="pharmacy", slots={"city": "Kigali"})),
    )

    async def fake_get_tools():
        return _fake_tools({"find_pharmacies": [{"name": "City Pharmacy", "address": "KN 4 Ave", "phone": "+250"}]})

    monkeypatch.setattr("graph.nodes.get_mcp_tools", fake_get_tools)

    graph = build_graph()
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="pharmacy in kigali")]},
        config={"configurable": {"thread_id": "t2"}},
    )
    assert "City Pharmacy" in result["result"]


@pytest.mark.asyncio
async def test_diagnosis_intent_end_to_end(monkeypatch):
    monkeypatch.setattr(
        "graph.planner.get_llm_model",
        lambda: FakeLLM(PlannerOutput(intent="diagnosis", query="fever and cough")),
    )

    async def fake_get_tools():
        return _fake_tools(
            {"get_diagnosis": {"summary": "Sounds like a mild cold.", "disclaimer": "Not medical advice."}}
        )

    monkeypatch.setattr("graph.nodes.get_mcp_tools", fake_get_tools)

    graph = build_graph()
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="I have a fever and cough")]},
        config={"configurable": {"thread_id": "t3"}},
    )
    assert "mild cold" in result["result"]
    assert "Not medical advice" in result["result"]


@pytest.mark.asyncio
async def test_appointment_intent_end_to_end(monkeypatch):
    monkeypatch.setattr(
        "graph.planner.get_llm_model",
        lambda: FakeLLM(
            PlannerOutput(
                intent="appointment",
                slots={
                    "doctor_name": "Dr. Uwimana",
                    "contact": "jean@example.com",
                    "date": "2026-09-01",
                    "time_slot": "10:00",
                },
            )
        ),
    )
    monkeypatch.setattr("graph.nodes.find_doctor_id_by_name", lambda clinic_id, name: 12)

    async def fake_get_tools():
        return _fake_tools(
            {
                "book_appointment": {
                    "ok": True,
                    "appointment_id": 1,
                    "doctor_id": 12,
                    "doctor_name": "Dr. Uwimana",
                    "date": "2026-09-01",
                    "time_slot": "10:00",
                }
            }
        )

    monkeypatch.setattr("graph.nodes.get_mcp_tools", fake_get_tools)

    graph = build_graph()
    result = await graph.ainvoke(
        {
            "messages": [HumanMessage(content="book me with Dr. Uwimana")],
            "clinic_id": 7,
            "patient_user_id": 42,
        },
        config={"configurable": {"thread_id": "t4"}},
    )
    assert "Booked!" in result["result"]
    assert "Dr. Uwimana" in result["result"]


@pytest.mark.asyncio
async def test_appointment_intent_without_clinic_session_declines(monkeypatch):
    monkeypatch.setattr(
        "graph.planner.get_llm_model",
        lambda: FakeLLM(
            PlannerOutput(
                intent="appointment",
                slots={
                    "doctor_name": "Dr. Uwimana",
                    "patient_name": "Jean",
                    "contact": "jean@example.com",
                    "date": "2026-09-01",
                    "time_slot": "10:00",
                },
            )
        ),
    )

    graph = build_graph()
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="book me with Dr. Uwimana")]},  # no clinic_id/patient_user_id
        config={"configurable": {"thread_id": "t4b"}},
    )
    assert "signed in" in result["result"]


@pytest.mark.asyncio
async def test_appointment_unknown_doctor_name_asks_to_check(monkeypatch):
    monkeypatch.setattr(
        "graph.planner.get_llm_model",
        lambda: FakeLLM(
            PlannerOutput(
                intent="appointment",
                slots={"doctor_name": "Dr. Nobody", "contact": "jean@example.com", "date": "2026-09-01", "time_slot": "10:00"},
            )
        ),
    )
    monkeypatch.setattr("graph.nodes.find_doctor_id_by_name", lambda clinic_id, name: None)

    graph = build_graph()
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="book me with Dr. Nobody")], "clinic_id": 7, "patient_user_id": 42},
        config={"configurable": {"thread_id": "t4c"}},
    )
    assert "couldn't find a doctor" in result["result"]


@pytest.mark.asyncio
async def test_appointment_doctor_known_but_no_time_hands_off_to_picker(monkeypatch):
    # doctor_name resolved but no date/time/contact yet -- should NOT ask a blind text
    # question; should surface the doctor as a recommendation card for the frontend's
    # real availability picker instead.
    monkeypatch.setattr(
        "graph.planner.get_llm_model",
        lambda: FakeLLM(PlannerOutput(intent="appointment", slots={"doctor_name": "Dr. Uwimana"})),
    )
    monkeypatch.setattr("graph.nodes.find_doctor_id_by_name", lambda clinic_id, name: 12)
    monkeypatch.setattr(
        "graph.nodes.get_doctor",
        lambda clinic_id, doctor_id: {"doctor_id": 12, "name": "Dr. Uwimana", "specialty": "Cardiology"},
    )

    graph = build_graph()
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="book me with Dr. Uwimana")], "clinic_id": 7, "patient_user_id": 42},
        config={"configurable": {"thread_id": "t4d"}},
    )
    assert "Dr. Uwimana" in result["result"]
    assert result["doctor_recommendations"] == [{"doctor_id": 12, "name": "Dr. Uwimana", "specialty": "Cardiology"}]


@pytest.mark.asyncio
async def test_missing_doctor_name_asks_for_clarification(monkeypatch):
    # No doctor_name at all -- the only thing that still gates routing -- so the planner
    # asks a follow-up instead of ever reaching appointment_agent.
    monkeypatch.setattr(
        "graph.planner.get_llm_model",
        lambda: FakeLLM(
            PlannerOutput(
                intent="appointment",
                slots={},
                response="Which doctor would you like to see?",
            )
        ),
    )

    graph = build_graph()
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="I want to book an appointment")]},
        config={"configurable": {"thread_id": "t5"}},
    )
    assert "Which doctor" in result["result"]
