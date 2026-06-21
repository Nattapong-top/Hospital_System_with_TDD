# =====================================================================
# API Tests: Staff (ระบบจัดการพนักงาน)
# =====================================================================


def test_api_register_new_staff_should_success(client):
    """เทส API สมัครพนักงานใหม่ (พยาบาล/หมอ)"""

    # 1. ARRANGE: เตรียมแบบฟอร์ม JSON ที่หน้าเว็บ (หรือ Admin) จะกรอกส่งมาให้
    payload = {
        "username": "nurse_joy_api",
        "password": "secure-password123",
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


def test_api_staff_login_username_password_valid_should_success(
    client, api_staff_doctor
):

    staff = api_staff_doctor.json()

    assert staff is not None

    staff_login_payload = {"username": staff["username"], "password": "password123"}

    res_login = client.post("/api/staff/login", json=staff_login_payload)

    assert res_login.status_code == 200
    data = res_login.json()
    assert data["staff_id"] == staff["staff_id"]
    assert data["username"] == staff["username"]
    assert data["first_name"] == staff["first_name"]
    assert data["is_active"] is True


def test_api_staff_login_username_invalid_should_status_401(client, api_staff_doctor):

    staff = api_staff_doctor.json()

    assert staff is not None

    staff_login_payload = {"username": "invalid_username", "password": "password123"}

    res_login = client.post("/api/staff/login", json=staff_login_payload)

    assert res_login.status_code == 401
    assert res_login.json()["detail"] == "ชื่อผู้ใช้ หรือ รหัสผ่านไม่ถูกต้อง"


def test_api_staff_login_password_invalid_should_status_401(client, api_staff_doctor):

    staff = api_staff_doctor.json()

    assert staff is not None

    staff_login_payload = {
        "username": staff["username"],
        "password": "Invalid_password",
    }

    res_login = client.post("/api/staff/login", json=staff_login_payload)

    assert res_login.status_code == 401
    assert res_login.json()["detail"] == "ชื่อผู้ใช้ หรือ รหัสผ่านไม่ถูกต้อง"


def test_api_staff_login_user_pass_invalid_should_raise_error(client, api_staff_doctor):

    invalid_login_payload = {"username": "valid_username", "password": "valid_password"}

    invalid_login = client.post("/api/staff/login", json=invalid_login_payload)

    assert invalid_login.status_code == 401
    assert invalid_login.json()["detail"] == "ชื่อผู้ใช้ หรือ รหัสผ่านไม่ถูกต้อง"


def test_api_staff_access_protected_route_with_valid_token_should_success(
    client, api_staff_doctor
):
    staff = api_staff_doctor.json()

    login_payload = {"username": staff["username"], "password": "password123"}

    valid_token = client.post("/api/staff/login", json=login_payload)
    assert valid_token.status_code == 200
    token_str = valid_token.json()["access_token"]

    response = client.get(
        "/api/queues/today",
        headers={"Authorization": f"Bearer {token_str}"},
    )

    assert response.status_code == 200


def test_api_staff_access_protected_route_with_invalid_token_should_401(
    client, api_staff_doctor
):

    import uuid

    token_str = uuid.uuid4().hex

    response = client.get(
        "/api/queues/today", headers={"Authorization": f"Bearer {token_str}"}
    )

    assert response.status_code == 401
    data = response.json()
    assert "Token ไม่ถูกต้องหรือหมดอายุแล้ว" in data["detail"]


def test_api_staff_refresh_token_with_valid_token_should_success(
    client, api_staff_doctor
):
    staff = api_staff_doctor.json()
    login_payload = {"username": staff["username"], "password": "password123"}
    login_response = client.post("/api/staff/login", json=login_payload)
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "refresh_token" in tokens

    refresh_token_str = tokens["refresh_token"]

    refresh_payload = {"refresh_token": refresh_token_str}
    refresh_response = client.post("/api/staff/refresh", json=refresh_payload)

    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
    assert new_tokens["token_type"] == "bearer"


def test_api_staff_refresh_token_with_invalid_token_should_401(client):
    refresh_payload = {"refresh_token": "invalid_token"}
    response = client.post("/api/staff/refresh", json=refresh_payload)

    assert response.status_code == 401
    assert "Token ไม่ถูกต้องหรือหมดอายุแล้ว" in response.json()["detail"]
