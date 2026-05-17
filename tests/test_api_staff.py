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


def test_api_register_staff_duplicate_username_should_return_400(client):
    """เทส Unhappy Path: สมัครพนักงานด้วย Username ที่มีคนใช้ไปแล้ว ระบบต้องด่ากลับมา"""

    # 1. ARRANGE: เตรียมข้อมูลพนักงานคนแรก
    payload_1 = {
        "username": "doctor_strange",  # 🚩 เล็งชื่อนี้ไว้
        "password": "password123",
        "national_id": "9998887776665",
        "first_name": "สตีเฟน",
        "last_name": "สเตรนจ์",
        "dob_year": 1980,
        "dob_month": 1,
        "dob_day": 1,
        "phone_number": "0800000000",
        "role": "DOCTOR",
    }

    # สมัครคนแรกเข้าทำงาน (ผ่านฉลุย)
    client.post("/api/staff/register", json=payload_1)

    # 2. ACT: มีพนักงานคนที่ 2 พยายามสมัคร แต่ดันใช้ Username เดิม!
    # (เปลี่ยนบัตร ปชช. กับชื่อ เพื่อให้รู้ว่าคนละคนกันจริงๆ แต่แอบเนียนใช้ชื่อล็อกอินซ้ำ)
    payload_2 = payload_1.copy()
    payload_2["national_id"] = "1112223334445"
    payload_2["first_name"] = "หมอปลอม"

    # ยิงคนที่ 2 เข้าไป
    response = client.post("/api/staff/register", json=payload_2)

    # 3. ASSERT: ต้องโดนเตะก้านคอกลับมา!
    assert response.status_code == 400  # ต้องเป็น 400 Bad Request (หรือ 409 Conflict)
    assert "มีคนใช้แล้ว" in response.json()["detail"]
