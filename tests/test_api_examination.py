import uuid

import pytest

from core.config import settings
from domain.hospital_registry import HospitalRegistry


@pytest.fixture(autouse=True)
def force_enable_new_examination_flow(monkeypatch):
    """ฟิกเจอร์บังคับเปิดสวิตช์ตัวใหม่ และล้างตู้แช่ขยะ เพื่อไม่ให้ระบบเก่ามาปนครับป๋า"""
    # 1. บังคับสับรางให้เป็น True เสมอเฉพาะในไฟล์เทสนี้
    monkeypatch.setattr(settings, "ENABLE_NEW_EXAMINATION_FLOW", True)

    # 2. สั่งล้างตู้จำลอง (Cache) ของเก่าทิ้งไปซะ ไม่งั้นมันจะจำเอา QueueService ของเทสข้อก่อนหน้ามาใช้
    HospitalRegistry.reset()
    HospitalRegistry.init_database()

    yield

    # 3. พอเทสไฟล์นี้เสร็จ สั่งล้างไพ่เคลียร์ทางให้เทสข้อถัดไปรันต่อได้สบายใจ
    HospitalRegistry.reset()


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
    print(exam_data)
    assert exam_data["queue_id"] == queue_data["queue_id"]
    assert exam_data["patient_id"] == queue_data["patient_id"]
    assert exam_data["doctor_id"] == staff_id
    assert exam_data["status"] == "กำลังพบหมอ"
    assert exam_data["consultation_id"] is not None


def test_api_examination_when_not_found_staff_id_should_raise_error(
    client, api_new_queues, api_vitals
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

    print("\n[Exception Handler Response]:", not_found.json())

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
    print("\n[Exception Handler Response]:", not_found_queue_id.json())
    assert not_found_queue_id.status_code == 404
    assert "ไม่พบคิว" in not_found_queue_id.json()["detail"]


def test_api_exam_should_finish_consul_and_update_state_complete_successfully(
    client, api_staff_doctor, api_new_queues, diagnosis_payload
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

    # 🟢 1. ตรวจสอบ ID หลักๆ (ที่ป๋าเขียนไว้ ดีอยู่แล้วครับ)
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
