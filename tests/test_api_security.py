# ==========================================
# กลุ่มที่ 1: ลองของแบบมือเปล่า (ไม่มี Header Authorization) -> ต้องได้ 401
# ==========================================
import uuid


def test_security_patient_register_without_token_should_return_401(client):
    response = client.post("/api/patients/register", json={})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


# ==========================================
# กลุ่มที่ 2: ลองของด้วยบัตรปลอม (Token มั่ว) -> ต้องได้ 401
# ==========================================


def test_security_patient_register_with_invalid_token_should_return_401(client):
    headers = {"Authorization": "Bearer fake_token_string"}
    response = client.post("/api/patients/register", headers=headers, json={})
    assert response.status_code == 401


# ==========================================
# ด่านที่ 2: ตึก Queues (ระบบจัดการคิว)
# ==========================================


def test_security_queues_issue_without_token_should_return_401(client):
    """เทสต์ยิง API ออกคิว มือเปล่า ต้องโดนเตะ 401"""
    response = client.post(
        "/api/queues/triage", json={}
    )  # อย่าลืมเช็ค prefix /api ของป๋าด้วยนะครับ
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_security_queues_issue_with_invalid_token_should_return_401(client):
    """เทสต์ยิง API ออกคิว ด้วยบัตรปลอม ต้องโดนเตะ 401"""
    headers = {"Authorization": "Bearer fake_token_queues_123"}
    response = client.post("/api/queues/triage", headers=headers, json={})
    assert response.status_code == 401


# ==========================================
# ด่านที่ 3: ตึก Staff (ระบบพนักงาน)
# ==========================================


def test_security_staff_me_without_token_should_return_401(client):
    """เทสต์ขอดูโปรไฟล์ตัวเอง มือเปล่า ต้องโดนเตะ 401"""
    response = client.get("/api/staff/me")  # สังเกตว่าเป็น .get() นะครับ
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_security_staff_me_with_invalid_token_should_return_401(client):
    """เทสต์ขอดูโปรไฟล์ตัวเอง บัตรปลอม ต้องโดนเตะ 401"""
    headers = {"Authorization": "Bearer fake_token_staff_123"}
    response = client.get("/api/staff/me", headers=headers)
    assert response.status_code == 401


def test_security_consultation_without_token_should_return_401(client):
    response = client.post(f"/api/consultations/{uuid.uuid4()}/start", json={})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_security_consultation_invalid_token_should_return_401(client):
    headers = {"Authorization": "Bearer fake_token_staff_123"}
    response = client.post(f"/api/consultations/{uuid.uuid4()}/start", headers=headers)
    assert response.status_code == 401
