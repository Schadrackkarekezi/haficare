from features.pharmacy_search import find_pharmacies_by_city


def test_find_pharmacies_by_city(monkeypatch, fake_neo4j_driver_factory):
    rows = [
        {"name": "City Pharmacy", "address": "KN 4 Ave", "phone": "+250...", "services": "prescription;otc"},
    ]
    fake_driver = fake_neo4j_driver_factory(rows)
    monkeypatch.setattr("features.pharmacy_search.get_neo4j_driver", lambda: fake_driver)

    results = find_pharmacies_by_city("Kigali")

    assert results == [
        {"name": "City Pharmacy", "address": "KN 4 Ave", "phone": "+250...", "services": "prescription;otc"}
    ]
    assert fake_driver.closed is True


def test_find_pharmacies_by_city_no_match(monkeypatch, fake_neo4j_driver_factory):
    fake_driver = fake_neo4j_driver_factory([])
    monkeypatch.setattr("features.pharmacy_search.get_neo4j_driver", lambda: fake_driver)

    results = find_pharmacies_by_city("Nowhere")

    assert results == []
