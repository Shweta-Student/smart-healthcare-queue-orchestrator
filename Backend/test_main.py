from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_patients():
    response = client.get("/patients")
    assert response.status_code == 200


def test_get_appointments():
    response = client.get("/appointments")
    assert response.status_code == 200


def test_get_queue():
    response = client.get("/queue")
    assert response.status_code == 200


def test_get_referrals():
    response = client.get("/referrals")
    assert response.status_code == 200


def test_get_notifications():
    response = client.get("/notifications")
    assert response.status_code == 200


def test_referral_priority():
    response = client.post(
        "/referral-priority",
        json={
            "patient_name": "Test Patient",
            "reason": "Urgent cardiac consultation required"
        }
    )

    assert response.status_code == 200
    assert response.json()["priority"] == "Urgent"