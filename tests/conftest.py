import os
import uuid
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from pytest import fixture

from api.main import app
from domain.consultation_entities import Consultation
from domain.domain_service.examination_service import ExaminationService
from domain.entities import Patient, Queue
from domain.hospital_registry import HospitalRegistry
from domain.staff_entities import Staff
from domain.value_object import (
    Address,
    Province,
    MedicineInfo,
    Diagnosis,
    Rights,
    PatientRights,
    PhoneNumber,
    Name,
    DateOfBirth,
    NationalID,
    Temperature,
    Weight,
    Height,
    BloodPressure,
    VitalSigns,
    QueueStatus,
    Number,
    Version,
    StaffRole,
)


from infrastructure.sqlite_consultation_repository import SqlConsultationRepository
from tests.fake_repository.fake_repository import (
    FakeQueueRecord,
    InMemoryStaffRepository,
    InMemConsulRepo,
)


# =====================================================================
# 1. SYSTEM & DATABASE SETUP (ตัวคุมระบบและฐานข้อมูล)
# =====================================================================
# 🚩 1. ตัวคุมระบบ: เคลียร์ทุกอย่างก่อนเริ่มเทสแต่ละครั้ง
@fixture(autouse=True)
def setup_database():
    # 1. ตั้งค่าให้ใช้ DB สำหรับเทส
    HospitalRegistry.set_test_db()
    HospitalRegistry.init_database()

    yield  # รันเทสตรงนี้...

    # 2. หลังเทสจบ ปิดการเชื่อมต่อ และลบไฟล์ทิ้ง (ถ้ามี)
    HospitalRegistry.reset()
    db_path = HospitalRegistry.get_db_path()

    # ถ้าไม่ใช่ของจริง และไฟล์มีอยู่จริง ให้ลบทิ้ง
    if "test_database.db" in db_path and os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            # ถ้า Windows ล็อกไฟล์ไว้ ไม่ต้องตกใจครับ ปล่อยผ่านไปก่อน
            pass


@pytest.fixture
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
# 3. REPOSITORIES (ตู้เหล็กเก็บข้อมูล)
# =====================================================================
@fixture
def fake_repo():
    return FakeQueueRecord()


@fixture
def queue_sql():
    return HospitalRegistry.queue_service().queue_repo


# 🚩 1. เพิ่ม Fixture สำหรับตู้เหล็กคิว (ที่เทสเก่าถามหา)
@fixture
def queue_repo():
    """เบิกตู้เหล็กเก็บคิวจากผู้อำนวยการ"""
    # ดึงมาจาก Service ที่ Registry เตรียมไว้ให้แล้ว
    return HospitalRegistry.queue_service().queue_repo


# 🚩 2. (แถม) เผื่อเทสไหนถามหาตู้เหล็กคนไข้
@fixture
def patient_repo():
    """เบิกตู้เหล็กเก็บคนไข้จากผู้อำนวยการ"""
    return HospitalRegistry.patient_repo()


@fixture
def InMem_staff_repo():
    return InMemoryStaffRepository()


@fixture
def InMem_consul_repo():
    return InMemConsulRepo()


@fixture
def consul_repo():
    return SqlConsultationRepository(HospitalRegistry.set_test_db())


# =====================================================================
# 4. SERVICES (ผู้จัดการแผนกต่างๆ)
# =====================================================================
# 🚩 2. ตัวเบิกอุปกรณ์: ไม่ต้องสร้างเอง ให้ไปเบิกจากผู้อำนวยการ (Registry)
@fixture
def registrar():
    return HospitalRegistry.patient_registrar()


@fixture
def queue_service():
    return HospitalRegistry.queue_service()


@fixture
def exam_service() -> ExaminationService:
    exam_service = HospitalRegistry.consultation_service()
    return exam_service


@fixture
def staff_service():
    return HospitalRegistry.staff_service()


# =====================================================================
# 5. VALUE OBJECTS & MOCK DATA (ข้อมูลพื้นฐานจำลอง)
# =====================================================================
@fixture
def registered_address() -> Address:
    return Address(
        house_number="10",
        street="วิวิธสุรการ",
        sub_district="มุกดาหาร",
        district="เมือง",
        province=Province.MUKDAHAN,
        postal_code="49000",
    )


@fixture
def current_address() -> Address:
    return (
        Address(  # ตั้งอยู่ที่ 173 ถนนดินสอ แขวงเสาชิงช้า เขตพระนคร กรุงเทพมหานคร 10200
            house_number="173",
            street="ดินสอ",
            sub_district="เสาชิงช้า",
            district="พระนคร",
            province=Province.BANGKOK,
            postal_code="10200",
        )
    )


@fixture
def today_date() -> date:
    return date(2026, 3, 28)


@fixture
def now() -> datetime:
    return datetime(2026, 3, 28, 22, 43, 53, 302903)


@fixture
def vital_signs():
    return VitalSigns(
        blood_pressure=BloodPressure(systolic=120, diastolic=80),
        weight=Weight(value=80),
        height=Height(value=177),
        temperature=Temperature(value=39.0),
        symptom="น้ำหมูกไหล ปวดหัว ตัวร้อน หนาวสั่น",
    )


@fixture
def diagnosis(patient):
    return Diagnosis(
        disease="ไข้หวัดใหญ่",
        treatment="พักผ่อนน ดิ่มน้ำมากๆ",
        medicine_prescribed=[
            MedicineInfo(
                name="Paracetamol",
                strength="500mg",
                frequency="วันละ 3 ครั้ง หลักอาหาร",
            )
        ],
    )


# =====================================================================
# 6. MOCK ENTITIES (จำลอง Entity ต่างๆ เช่น คนไข้, หมอ, ใบตรวจ)
# =====================================================================
@fixture
def patient(current_address, registered_address):
    return Patient(
        id=uuid.uuid4(),
        national_id=NationalID(id="1234567890123"),
        first_name=Name(value="นนทพัฒน์"),
        last_name=Name(value="คนสุขภาพดี"),
        phone_number=PhoneNumber(value="0123456789"),
        date_of_birth=DateOfBirth(year=1990, month=12, day=31),
        registered_address=registered_address,
        current_address=current_address,
        rights=Rights(rights_type=PatientRights.SOCIAL_SECURITY),
        version=Version(number=1),
    )


@fixture
def new_queue(queue_service, patient, vital_signs, today_date):
    return queue_service.issue_new_queue(
        patient_id=patient.id,
        today=today_date,
        vital_signs=vital_signs,
    )


@fixture
def queue(patient, today_date, vital_signs):
    return Queue(
        patient_id=patient.id,
        queue_number=Number(id=1),
        queue_date=today_date,
        vital_signs=vital_signs,
        status=QueueStatus.WAITING,
        version=Version(number=1),
    )


@fixture
def new_patient(registrar, vital_signs, registered_address, current_address):
    return registrar.register_new_patient(
        national_id=NationalID(id="1234567890123"),
        first_name=Name(value="นนทพัฒน์"),
        last_name=Name(value="คนสุขภาพดี"),
        phone_number=PhoneNumber(value="0123456789"),
        date_of_birth=DateOfBirth(year=1990, month=12, day=31),
        registered_address=registered_address,
        current_address=current_address,
        rights=Rights(rights_type=PatientRights.SOCIAL_SECURITY),
    )


@fixture
def new_staff_doctor():
    return Staff.register(
        username_str="nattapong-top",
        password_str="Paa-TopIT_12123",  # ส่งรหัสสดเข้าไป
        national_id_str="1234567890123",
        first_name_str="ณัฐพงศ์",
        last_name_str="คนรักษาดี",
        dob_year=1990,
        dob_month=12,
        dob_day=31,
        phone_number_str="0999999999",
        role=StaffRole.DOCTOR,
    )


@fixture
def new_staff_nurse():
    return Staff.register(
        username_str="nontanan-nan",
        password_str="nontanan_12123",  # ส่งรหัสสดเข้าไป
        national_id_str="1234567890123",
        first_name_str="นนทนัน",
        last_name_str="พยาบาลดี",
        dob_year=1998,
        dob_month=1,
        dob_day=31,
        phone_number_str="0888888888",
        role=StaffRole.NURSE,
    )


@fixture
def new_staff_admin():
    return Staff.register(
        username_str="admin",
        password_str="can't_start",  # ส่งรหัสสดเข้าไป
        national_id_str="1234567894444",
        first_name_str="admin",
        last_name_str="can't start",
        dob_year=1998,
        dob_month=1,
        dob_day=31,
        phone_number_str="0999888888",
        role=StaffRole.ADMIN,
    )


@fixture
def new_examination(new_queue, new_staff_doctor, exam_service):
    return exam_service.start_consultation(
        queue_id=new_queue.id, staff=new_staff_doctor
    )


@fixture
def new_register_staff(staff_service):
    new_staff = staff_service.register_staff(
        username_str="nattapong-top",
        password_str="Paa-TopIT_12123",  # ส่งรหัสสดเข้าไป
        national_id_str="1234567890123",
        first_name_str="ณัฐพงศ์",
        last_name_str="คนรักษาดี",
        dob_year=1990,
        dob_month=12,
        dob_day=31,
        phone_number_str="0999999999",
        role=StaffRole.DOCTOR,
    )
    return new_staff


@fixture
def new_consultation(new_queue, new_staff_doctor):
    return Consultation(
        queue_id=new_queue.id,
        doctor_id=new_staff_doctor.staff_id,
        patient_id=new_queue.patient_id,
        vital_signs=new_queue.vital_signs,
    )


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
def diagnosis_payload(diagnosis):
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
