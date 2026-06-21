# "tests.fixtures.fixture_api",
import uuid

from pytest import fixture
from starlette.testclient import TestClient

from api.main import app


@fixture
def bypass_general_auth():
    """บัตรผ่าน VIP: พักงานยามหน้าตึก (ตึกคนไข้, ตึกคิว) สำหรับเทสต์เก่า"""

    # 1. หลอกส่งข้อมูลพนักงานจำลองกลับไปให้เลย โดยไม่ต้องสนใจ Token
    from api.main import app
    from infrastructure.auth.jwt_service import get_current_staff

    app.dependency_overrides[get_current_staff] = lambda: {
        "staff_id": str(uuid.uuid4()),
        "role": "STAFF",
        "username": "test_staff",
    }

    yield  # ปล่อยให้เทสต์ทำงานไป

    # 2. ทำงานเสร็จ คืนค่ายามตัวจริงกลับมาให้ระบบ
    app.dependency_overrides.pop(get_current_staff, None)


# =====================================================================
# 2. API TEST CLIENT (กล่องเครื่องมือยิง API)
# =====================================================================
@fixture
def client():
    """🚩 กล่องเครื่องมือสำหรับยิง API (เหมือน Postman จำลอง)"""
    # ใช้งาน TestClient โดยส่งแอป FastAPI ของป๋าเข้าไป
    with TestClient(app) as c:
        yield c


# =====================================================================
# 7. API PAYLOADS (ข้อมูล JSON สำหรับยิงเข้า API)
# =====================================================================
@fixture
def valid_patient_payload():
    return {
        "national_id": "1234567890123",
        "first_name": "นนทพัฒน์",
        "last_name": "ใจดี",
        "phone_number": "0812345678",
        "dob_year": 1990,
        "dob_month": 5,
        "dob_day": 20,
        "registered_address": {
            "house_number": "1/1",
            "street": "ราชดำเนิน",
            "sub_district": "บวรนิเวศ",
            "district": "พระนคร",
            "province": "กรุงเทพมหานคร",
            "postal_code": "10200",
        },
        "current_address": {
            "house_number": "99/9",
            "street": "สุขุมวิท",
            "sub_district": "คลองเตย",
            "district": "คลองเตย",
            "province": "กรุงเทพมหานคร",
            "postal_code": "10110",
        },
        "rights_type": "ประกันสังคม",
    }


@fixture
def payload_staff_doctor():
    payload_staff_doctor = {
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
    return payload_staff_doctor


@fixture
def payload_staff_nurse():
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
    return payload


@fixture
def payload_staff_admin():
    payload = {
        "username": "admin_jone",
        "password": "very_secure",
        "national_id": "5552223334445",
        "first_name": "จอน",
        "last_name": "จัด",
        "dob_year": 1995,
        "dob_month": 10,
        "dob_day": 15,
        "phone_number": "0855555555",
        "role": "admin",
    }
    return payload


@fixture
def diagnosis_payload():
    diagnosis_payload = {
        "disease": "ไข้หวัดใหญ่ สายพันธุ์ A",
        "treatment": "พักผ่อนเยอะๆ และทานยาตามอาการ",
        "medicine_prescribed": [
            {"name": "Tamiflu", "strength": "75mg", "frequency": "เช้า-เย็น หลังอาหาร"}
        ],
    }
    return diagnosis_payload


@fixture
def triage_payload(api_patient_id):
    triage_payload = {
        "patient_id": api_patient_id,
        "vitals": {
            "systolic": 120,
            "diastolic": 80,
            "weight": 70.5,
            "height": 175.0,
            "temperature": 36.5,
            "symptom": "ปวดหัว ตัวร้อน",
        },
    }
    return triage_payload


@fixture
def api_vitals():
    return {
        "systolic": 120,
        "diastolic": 80,
        "weight": 70.5,
        "height": 175.0,
        "temperature": 36.5,
        "symptom": "ปวดหัว ตัวร้อน",
    }


@fixture
def api_new_queues(client, api_patient_id, triage_payload):
    # ออกคิว ส่ง ข้อมูลสัญญาชีพและซักประวัติ
    new_queue = client.post("/api/queues/triage", json=triage_payload)
    return new_queue


@fixture
def api_patient_id(client, valid_patient_payload):
    reg_res = client.post("/api/patients/register", json=valid_patient_payload)
    new_patient_id = reg_res.json()["id"]
    return new_patient_id


@fixture
def api_staff_doctor(client, payload_staff_doctor):
    # สมัครคนแรกเข้าทำงาน (ผ่านฉลุย)
    staff_doctor = client.post("/api/staff/register", json=payload_staff_doctor)
    return staff_doctor


@fixture
def api_staff_nurse(client, payload_staff_nurse):
    staff_nurse = client.post("/api/staff/register", json=payload_staff_nurse)
    return staff_nurse


@fixture
def api_staff_admin(client, payload_staff_admin):
    staff_admin = client.post("/api/staff/register", json=payload_staff_admin)
    return staff_admin


@fixture
def token_doctor(client, api_staff_doctor):
    staff = api_staff_doctor.json()
    login_payload = {"username": staff["username"], "password": "password123"}
    response = client.post("/api/staff/login", json=login_payload)
    return response


@fixture
def token_nurse(client, api_staff_nurse):
    login_payload = {
        "username": api_staff_nurse.json()["username"],
        "password": "secure-password123",
    }
    response = client.post("/api/staff/login", json=login_payload)
    return response


@fixture
def token_admin(client, api_staff_admin):
    login_payload = {
        "username": api_staff_admin.json()["username"],
        "password": "very_secure",
    }
    response = client.post("/api/staff/login", json=login_payload)
    return response
