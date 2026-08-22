from features.diagnosis import DISCLAIMER_TEXT, get_diagnosis_from_symptoms


class FakeLLMResponse:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    def __init__(self, content="You may have a mild viral infection; rest and monitor your symptoms."):
        self.content = content
        self.last_prompt = None

    def invoke(self, prompt):
        self.last_prompt = prompt
        return FakeLLMResponse(self.content)


def test_diagnosis_always_includes_disclaimer(monkeypatch, fake_neo4j_driver_factory):
    rows = [
        {
            "symptom_summary": "fever, cough, fatigue, body aches",
            "possible_condition": "Common cold or flu",
            "advice": "Rest, fluids, and OTC fever reducers.",
            "urgency": "low",
            "score": 0.91,
        }
    ]
    fake_driver = fake_neo4j_driver_factory(rows)
    monkeypatch.setattr("features.diagnosis.get_neo4j_driver", lambda: fake_driver)
    monkeypatch.setattr("features.diagnosis.generate_embedding", lambda text: [0.1] * 1536)
    monkeypatch.setattr("features.diagnosis.get_llm_model", lambda: FakeLLM())

    result = get_diagnosis_from_symptoms("fever and cough")

    assert result["disclaimer"] == DISCLAIMER_TEXT
    assert len(result["possible_conditions"]) == 1
    assert result["possible_conditions"][0]["possible_condition"] == "Common cold or flu"
    assert "viral infection" in result["summary"]


def test_diagnosis_no_matches_still_has_disclaimer(monkeypatch, fake_neo4j_driver_factory):
    fake_driver = fake_neo4j_driver_factory([])
    monkeypatch.setattr("features.diagnosis.get_neo4j_driver", lambda: fake_driver)
    monkeypatch.setattr("features.diagnosis.generate_embedding", lambda text: [0.1] * 1536)

    result = get_diagnosis_from_symptoms("something very unusual")

    assert result["disclaimer"] == DISCLAIMER_TEXT
    assert result["possible_conditions"] == []


def test_diagnosis_handles_lookup_failure(monkeypatch):
    def boom():
        raise RuntimeError("neo4j down")

    monkeypatch.setattr("features.diagnosis.get_neo4j_driver", boom)

    result = get_diagnosis_from_symptoms("fever")

    assert result["disclaimer"] == DISCLAIMER_TEXT
    assert result["possible_conditions"] == []
    assert "couldn't look up" in result["summary"]
