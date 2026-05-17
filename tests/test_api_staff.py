# =====================================================================
# API Tests: Staff (ระบบจัดการพนักงาน)
# =====================================================================


def test_api_register_new_staff_should_success(client):
    """เทส API สมัครพนักงานใหม่ (พยาบาล/หมอ)"""

    # 1. ARRANGE: เตรียมแบบฟอร์ม JSON ที่หน้าเว็บ (หรือ Admin) จะกรอกส่งมาให้
    payload = {
        "username": "nurse_joy_api",
        "password": "securepassword123",
        "national_id": "1112223334445",
        "first_name": "จอย",
        "last_name": "ใจดี",
        "dob_year": 1995,
        "dob_month": 10,
        "dob_day": 15,
        "phone_number": "0899999999",
        "role": "nurse",
    }

    # 2. ACT: ยิง POST ไปที่ประตูรับสมัครพนักงาน
    response = client.post("/api/staff/register", json=payload)

    # 3. ASSERT: ตรวจสอบผลลัพธ์
    # - ต้องตอบกลับมาว่า 200 OK
    assert response.status_code == 200

    # - ข้อมูลที่ตอบกลับมาต้องถูกต้อง
    data = response.json()
    assert "staff_id" in data  # ต้องมี ID พนักงานเด้งกลับมาให้
    assert data["username"] == payload["username"]
    assert data["role"] == "พยาบาล"
    assert data["first_name"] == payload["first_name"]
    assert data["is_active"] is True  # พนักงานใหม่ต้องพร้อมทำงานทันที
