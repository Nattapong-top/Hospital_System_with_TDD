import uuid


import pytest
from api.main import app

# อ้างอิงตัวแปรยามที่ป๋าใช้ใน router (สมมติว่าประกาศไว้ที่ api.routers.examination)
from api.routers.examination import require_doctor


@pytest.fixture
def bypass_doctor_auth():
    """Fixture สำหรับสั่งพักงานยามชั่วคราว ดึงข้อมูลหมอจำลองให้เลย"""
    # 1. สั่งหลอก FastAPI ว่า ถ้าเจอ require_doctor ให้ข้ามไปเลย และคืนค่า dict นี้กลับไปแทน
    app.dependency_overrides[require_doctor] = lambda: {
        "role": "หมอ",
        "staff_id": uuid.uuid4(),
    }

    yield  # ปล่อยให้เทสต์ทำงานไป

    # 2. พอเทสต์ก้อนนี้ทำงานเสร็จปุ๊บ ล้างค่ายอมรับทั้งหมด เพื่อคืนค่ายามตัวจริงกลับมา
    app.dependency_overrides.clear()


def test_api_examination_should_start_consultation_and_update_state_in_progress(
    client, api_new_queues, api_staff_doctor, api_vitals
):
    staff_id = api_staff_doctor.json()["staff_id"]
    queue_data = api_new_queues.json()

    exam_payload = {
        "queue_id": queue_data["queue_id"],
        "staff_id": staff_id,
        # "patient_id": queue_data["patient_id"],
        # "vital_signs": api_vitals,
    }

    new_exam = client.post("/api/examination/start", json=exam_payload)
    assert new_exam.status_code == 200
    exam_data = new_exam.json()
    assert exam_data["queue_id"] == queue_data["queue_id"]
    assert exam_data["patient_id"] == queue_data["patient_id"]
    assert exam_data["doctor_id"] == staff_id
    assert exam_data["status"] == "กำลังพบหมอ"
    assert exam_data["consultation_id"] is not None


def test_api_examination_when_not_found_staff_id_should_raise_error(
    client, api_new_queues, api_vitals, bypass_doctor_auth
):

    staff_id = str(uuid.uuid4())
    queue_data = api_new_queues.json()

    not_found_staff_id = {
        "queue_id": queue_data["queue_id"],
        "staff_id": staff_id,
        # "patient_id": queue_data["patient_id"],
        # "vital_signs": api_vitals,
    }

    not_found = client.post("/api/examination/start", json=not_found_staff_id)

    assert not_found.status_code == 404
    assert "ไม่พบรหัสพนักงาน" == not_found.json()["detail"]


def test_api_exam_when_not_found_queue_id_should_raise_error(
    client, api_staff_doctor, api_vitals
):
    staff_id = api_staff_doctor.json()["staff_id"]
    queue_id = str(uuid.uuid4())
    queue_id_payload = {
        "queue_id": queue_id,
        "staff_id": staff_id,
        # "patient_id": queue_id,
        # "vital_signs": api_vitals,
    }
    not_found_queue_id = client.post("/api/examination/start", json=queue_id_payload)
    assert not_found_queue_id.status_code == 404
    assert "ไม่พบคิว" in not_found_queue_id.json()["detail"]


def test_api_exam_should_finish_consul_and_update_state_complete_successfully(
    client, api_staff_doctor, api_new_queues, diagnosis_payload, bypass_doctor_auth
):
    staff_id = api_staff_doctor.json()["staff_id"]
    queue_data = api_new_queues.json()

    exam_payload = {
        "queue_id": queue_data["queue_id"],
        "staff_id": staff_id,
    }

    new_exam = client.post("/api/examination/start", json=exam_payload)
    assert new_exam.status_code == 200

    exam_data = new_exam.json()

    finished_payload = {
        "consultation_id": exam_data["consultation_id"],
        "doctor_id": api_staff_doctor.json()["staff_id"],
        "diagnosis": diagnosis_payload,
    }

    finished_exam = client.post("/api/examination/finish", json=finished_payload)

    assert finished_exam.status_code == 200
    finished_data = finished_exam.json()

    # 🟢 1. ตรวจสอบ ID หลักๆ
    assert finished_data["consultation_id"] == exam_data["consultation_id"]
    assert finished_data["queue_id"] == exam_data["queue_id"]
    assert finished_data["patient_id"] == exam_data["patient_id"]
    assert (
        finished_data["doctor_id"] == staff_id
    )  # (💡 แนะนำแก้เป็น staff_id หรือ exam_data["doctor_id"] ตามตัวแปรที่เก็บนะครับป๋า)

    # 🟢 2. ตรวจสอบ "โรค" และ "วิธีรักษา" ว่าตรงกับที่เราส่งไปไหม
    assert finished_data["disease"] == diagnosis_payload["disease"]
    assert finished_data["treatment"] == diagnosis_payload["treatment"]

    # 🟢 3. ตรวจสอบ "รายการยา" (เพราะยามาเป็น List/Array)
    # เช็คจำนวนยารวมก่อนว่าได้ครบเท่าที่สั่งไหม
    assert len(finished_data["medicines"]) == len(
        diagnosis_payload["medicine_prescribed"]
    )

    # วนลูปแกะเช็คไส้ในของยาตัวแรก (อินเด็กซ์ 0) เพื่อความชัวร์ว่าข้อมูลไม่สลับกัน
    actual_medicine = finished_data["medicines"][0]
    expected_medicine = diagnosis_payload["medicine_prescribed"][0]

    assert actual_medicine["name"] == expected_medicine["name"]
    assert actual_medicine["strength"] == expected_medicine["strength"]
    assert actual_medicine["frequency"] == expected_medicine["frequency"]

    # 🟢 4. ตรวจสอบ "เวลาที่ตรวจเสร็จ"
    assert finished_data["finished_at"] is not None


def test_api_examination_should_cancel_consultation_successfully(
    client, api_new_queues, api_staff_doctor
):
    staff_id = api_staff_doctor.json()["staff_id"]
    queue_data = api_new_queues.json()

    exam_payload = {
        "queue_id": queue_data["queue_id"],
        "staff_id": staff_id,
    }

    new_exam = client.post("/api/examination/start", json=exam_payload)
    assert new_exam.status_code == 200

    exam_data = new_exam.json()
    staff_id = exam_data["doctor_id"]

    canceled_payload = {
        "consultation_id": exam_data["consultation_id"],
        "staff_id": staff_id,
    }
    cancel_exam = client.post("/api/examination/cancel", json=canceled_payload)
    assert cancel_exam.status_code == 200
    canceled_data = cancel_exam.json()
    assert canceled_data["status"] == "ยกเลิกการตรวจ"
    assert canceled_data["consultation_id"] == exam_data["consultation_id"]
    assert canceled_data["staff_id"] == staff_id


def test_api_exam_when_finish_with_not_found_consultation_id_should_raise_404(
    client, api_staff_doctor, diagnosis_payload, bypass_doctor_auth
):
    # 1. Arrange: เสก ID มั่วๆ ขึ้นมา
    fake_consultation_id = str(uuid.uuid4())
    staff_id = api_staff_doctor.json()["staff_id"]

    finished_payload = {
        "consultation_id": fake_consultation_id,
        "doctor_id": staff_id,
        "diagnosis": diagnosis_payload,
    }

    # 2. Act: ลองสั่งจบการตรวจ
    res = client.post("/api/examination/finish", json=finished_payload)

    # 3. Assert: ต้องด่ากลับว่าไม่พบใบตรวจ
    assert res.status_code == 404
    assert "ไม่พบ" in res.json()["detail"]


def test_api_exam_when_cancel_with_not_found_consultation_id_should_raise_404(
    client, api_staff_doctor
):
    fake_consultation_id = str(uuid.uuid4())
    staff_id = api_staff_doctor.json()["staff_id"]

    canceled_payload = {
        "consultation_id": fake_consultation_id,
        "staff_id": staff_id,
    }

    res = client.post("/api/examination/cancel", json=canceled_payload)

    assert res.status_code == 404
    assert "ไม่พบ" in res.json()["detail"]


def test_api_exam_should_not_allow_cancel_if_already_finished(
    client, api_staff_doctor, api_new_queues, diagnosis_payload, bypass_doctor_auth
):
    # 1. Arrange: ทำการ Start และ Finish ให้เสร็จสมบูรณ์ก่อน
    staff_id = api_staff_doctor.json()["staff_id"]
    queue_data = api_new_queues.json()

    # Start
    start_res = client.post(
        "/api/examination/start",
        json={"queue_id": queue_data["queue_id"], "staff_id": staff_id},
    )
    exam_data = start_res.json()

    # Finish
    finish_res = client.post(
        "/api/examination/finish",
        json={
            "consultation_id": exam_data["consultation_id"],
            "doctor_id": staff_id,
            "diagnosis": diagnosis_payload,
        },
    )
    assert finish_res.status_code == 200

    # 2. Act: หน้าด้านกดยกเลิกคิวที่เพิ่งตรวจเสร็จไปเมื่อกี้!
    canceled_payload = {
        "consultation_id": exam_data["consultation_id"],
        "staff_id": staff_id,
    }
    cancel_res = client.post("/api/examination/cancel", json=canceled_payload)

    # 3. Assert: ระบบต้องด่าว่าทำไม่ได้ (ขึ้นอยู่กับว่าป๋าพ่น Exception 400 หรือ 422 ไว้ครับ)
    assert cancel_res.status_code == 400
    # assert "ไม่สามารถยกเลิกได้" in cancel_res.json()["detail"]


def test_api_examination_finish_by_nurse_should_be_forbidden(
    client, api_staff_nurse, diagnosis_payload, api_new_queues
):
    # 1. ให้ "พยาบาล" (NURSE) ล็อกอินเพื่อเอา Token
    nurse = api_staff_nurse.json()
    login_response = client.post(
        "/api/staff/login",
        json={"username": nurse["username"], "password": "secure-password123"},
    )
    token_str = login_response.json()["access_token"]
    queue_data = api_new_queues.json()

    exam_payload = {
        "queue_id": queue_data["queue_id"],
        "staff_id": nurse["staff_id"],
    }

    new_exam = client.post("/api/examination/start", json=exam_payload)
    assert new_exam.status_code == 200

    exam_data = new_exam.json()

    finished_payload = {
        "consultation_id": exam_data["consultation_id"],
        "doctor_id": api_staff_nurse.json()["staff_id"],
        "diagnosis": diagnosis_payload,
    }

    # 2. พยาบาลพยายามแอบยิง API จบการตรวจ (ซึ่งปกติหมอควรทำ)
    response = client.post(
        "/api/examination/finish",  # สมมติว่าเป็นเส้นนี้
        json=finished_payload,  # ใส่ payload ที่จำเป็น
        headers={"Authorization": f"Bearer {token_str}"},
    )

    # 3. คาดหวังว่าระบบจะเตะกระเด็น! (403 Forbidden)
    assert response.status_code == 403
    assert "ไม่มีสิทธิ์เข้าถึง (Requires หมอ role)" in response.json()["detail"]


def test_api_examination_finish_by_doctor_with_auth_should_success(
    client, api_staff_doctor, diagnosis_payload, api_new_queues
):
    doctor = api_staff_doctor.json()
    login_response = client.post(
        "/api/staff/login",
        json={"username": doctor["username"], "password": "password123"},
    )
    token_str = login_response.json()["access_token"]
    queue_data = api_new_queues.json()

    exam_payload = {
        "queue_id": queue_data["queue_id"],
        "staff_id": doctor["staff_id"],
    }

    new_exam = client.post("/api/examination/start", json=exam_payload)
    assert new_exam.status_code == 200

    exam_data = new_exam.json()

    finished_payload = {
        "consultation_id": exam_data["consultation_id"],
        "doctor_id": api_staff_doctor.json()["staff_id"],
        "diagnosis": diagnosis_payload,
    }

    response = client.post(
        "/api/examination/finish",  # สมมติว่าเป็นเส้นนี้
        json=finished_payload,  # ใส่ payload ที่จำเป็น
        headers={"Authorization": f"Bearer {token_str}"},
    )

    # 3. คาดหวังว่าระบบจะได้ 200 != 403 Forbidden
    assert response.status_code == 200
