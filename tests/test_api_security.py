# ==========================================
# กลุ่มที่ 1: ลองของแบบมือเปล่า (ไม่มี Header Authorization) -> ต้องได้ 401
# ==========================================


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
