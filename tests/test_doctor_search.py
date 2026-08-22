from features.doctor_search import vector_search_doctors, vector_search_doctors_for_clinic


def test_vector_search_doctors(monkeypatch, fake_neo4j_driver_factory):
    rows = [
        {"name": "Dr. Uwimana", "specialty": "Cardiology", "hospital": "King Faisal Hospital", "score": 0.87},
    ]
    fake_driver = fake_neo4j_driver_factory(rows)
    monkeypatch.setattr("features.doctor_search.get_neo4j_driver", lambda: fake_driver)
    monkeypatch.setattr("features.doctor_search.generate_embedding", lambda text: [0.1] * 1536)

    results = vector_search_doctors("chest pain", top_r=2)

    assert results == [
        {"name": "Dr. Uwimana", "specialty": "Cardiology", "hospital": "King Faisal Hospital", "score": 0.87}
    ]
    assert fake_driver.closed is True


def test_vector_search_doctors_no_match(monkeypatch, fake_neo4j_driver_factory):
    fake_driver = fake_neo4j_driver_factory([])
    monkeypatch.setattr("features.doctor_search.get_neo4j_driver", lambda: fake_driver)
    monkeypatch.setattr("features.doctor_search.generate_embedding", lambda text: [0.1] * 1536)

    results = vector_search_doctors("nonexistent condition")

    assert results == []


def test_vector_search_doctors_for_clinic_scopes_and_ranks(monkeypatch, fake_neo4j_driver_factory):
    query_vec = [1.0, 0.0]
    rows = [
        {"doctor_id": 1, "name": "Dr. Far Match", "specialty": "Radiology", "embedding": [0.0, 1.0]},
        {"doctor_id": 2, "name": "Dr. Close Match", "specialty": "Cardiology", "embedding": [1.0, 0.0]},
    ]
    fake_driver = fake_neo4j_driver_factory(rows)
    monkeypatch.setattr("features.doctor_search.get_neo4j_driver", lambda: fake_driver)
    monkeypatch.setattr("features.doctor_search.generate_embedding", lambda text: query_vec)

    results = vector_search_doctors_for_clinic("chest pain", clinic_id=42, top_r=2)

    assert [r["doctor_id"] for r in results] == [2, 1]  # closer cosine match ranked first
    assert results[0]["score"] > results[1]["score"]
    assert fake_driver.closed is True


def test_vector_search_doctors_for_clinic_no_doctors(monkeypatch, fake_neo4j_driver_factory):
    fake_driver = fake_neo4j_driver_factory([])
    monkeypatch.setattr("features.doctor_search.get_neo4j_driver", lambda: fake_driver)
    monkeypatch.setattr("features.doctor_search.generate_embedding", lambda text: [0.1, 0.2])

    results = vector_search_doctors_for_clinic("chest pain", clinic_id=42)

    assert results == []
