from api.auth.router import _slugify


def test_clinic_signup_then_me(client):
    resp = client.post(
        "/auth/signup/clinic",
        json={
            "clinic_name": "Kigali Wellness Clinic",
            "clinic_city": "Kigali",
            "full_name": "Alice Staff",
            "email": "alice@clinic.test",
            "password": "hunter2",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "staff"
    assert "hunter2" not in resp.text

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    me_body = me.json()
    assert me_body["role"] == "staff"
    assert me_body["email"] == "alice@clinic.test"
    assert "hashed_password" not in me.text


def test_patient_signup_joins_existing_clinic(client):
    client.post(
        "/auth/signup/clinic",
        json={"clinic_name": "Kigali Wellness Clinic", "full_name": "Alice", "email": "alice@clinic.test", "password": "x"},
    )
    slug = _slugify("Kigali Wellness Clinic")

    resp = client.post(
        "/auth/signup/patient",
        json={"clinic_slug": slug, "full_name": "Jean Patient", "email": "jean@patient.test", "password": "y"},
    )

    assert resp.status_code == 200
    assert resp.json()["role"] == "patient"


def test_patient_signup_unknown_clinic_rejected(client):
    resp = client.post(
        "/auth/signup/patient",
        json={"clinic_slug": "does-not-exist", "full_name": "Jean", "email": "jean@patient.test", "password": "y"},
    )

    assert resp.status_code == 404


def test_duplicate_email_signup_rejected(client):
    payload = {"clinic_name": "Clinic A", "full_name": "Alice", "email": "dupe@clinic.test", "password": "x"}
    client.post("/auth/signup/clinic", json=payload)

    resp = client.post("/auth/signup/clinic", json={**payload, "clinic_name": "Clinic B"})

    assert resp.status_code == 400


def test_login_success_and_wrong_password(client):
    client.post(
        "/auth/signup/clinic",
        json={"clinic_name": "Clinic A", "full_name": "Alice", "email": "alice@clinic.test", "password": "correct-pw"},
    )

    good = client.post("/auth/login", json={"email": "alice@clinic.test", "password": "correct-pw"})
    assert good.status_code == 200

    bad = client.post("/auth/login", json={"email": "alice@clinic.test", "password": "wrong-pw"})
    assert bad.status_code == 401


def test_me_requires_authorization_header(client):
    resp = client.get("/auth/me")

    assert resp.status_code in (401, 422)  # missing required header


def test_me_rejects_garbage_token(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert resp.status_code == 401
