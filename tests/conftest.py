import os
import uuid
from datetime import date, datetime

from fastapi.testclient import TestClient
from pytest import fixture

from api.main import app
from domain.consultation_entities import Consultation
from domain.domain_service.staff_service import StaffService
from domain.entities import Patient, Queue
from domain.hospital_registry import HospitalRegistry
from domain.staff_entities import Staff
from domain.value_object import (
    Address, Province, MedicineInfo, Diagnosis, Rights, PatientRights, \
    PhoneNumber, Name, DateOfBirth, NationalID, Temperature, Weight, Height,
    BloodPressure, VitalSigns, QueueStatus, \
    Number, Version, StaffRole)
from tests.fake_repository.fake_repository import FakeQueueRecord, InMemoryStaffRepository


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

# 🚩 2. ตัวเบิกอุปกรณ์: ไม่ต้องสร้างเอง ให้ไปเบิกจากผู้อำนวยการ (Registry)
@fixture
def registrar():
    return HospitalRegistry.patient_registrar()

@fixture
def queue_service():
    return HospitalRegistry.queue_service()


@fixture
def client():
    """🚩 กล่องเครื่องมือสำหรับยิง API (เหมือน Postman จำลอง)"""
    # ใช้งาน TestClient โดยส่งแอป FastAPI ของป๋าเข้าไป
    with TestClient(app) as c:
        yield c

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
def registered_address() -> Address:
    return Address(
        house_number='10',
        street='วิวิธสุรการ',
        sub_district='มุกดาหาร',
        district='เมือง',
        province=Province.MUKDAHAN,
        postal_code='49000'
    )


@fixture
def current_address() -> Address:
    return Address(  # ตั้งอยู่ที่ 173 ถนนดินสอ แขวงเสาชิงช้า เขตพระนคร กรุงเทพมหานคร 10200
        house_number='173',
        street='ดินสอ',
        sub_district='เสาชิงช้า',
        district='พระนคร',
        province=Province.BANGKOK,
        postal_code='10200'
    )


@fixture
def today_date() -> date:
    return date(2026, 3, 28)


@fixture
def now() -> datetime:
    return datetime(2026, 3, 28,
                    22, 43, 53, 302903)


@fixture
def vital_signs():
    return VitalSigns(
        blood_pressure=BloodPressure(systolic=120, diastolic=80),
        weight=Weight(value=80),
        height=Height(value=177),
        temperature=Temperature(value=39.0),
        symptom='น้ำหมูกไหล ปวดหัว ตัวร้อน หนาวสั่น'
    )


@fixture
def patient(current_address, registered_address):
    return Patient(
        id=uuid.uuid4(),
        national_id=NationalID(id='1234567890123'),
        first_name=Name(value='นนทพัฒน์'),
        last_name=Name(value='คนสุขภาพดี'),
        phone_number=PhoneNumber(value='0123456789'),
        date_of_birth=DateOfBirth(year=1990, month=12, day=31),
        registered_address=registered_address,
        current_address=current_address,
        rights=Rights(rights_type=PatientRights.SOCIAL_SECURITY),
        version=Version(number=1)
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
        version=Version(number=1)
    )


@fixture
def diagnosis(patient):
    return Diagnosis(
        disease='ไข้หวัดใหญ่',
        treatment='พักผ่อนน ดิ่มน้ำมากๆ',
        medicine_prescribed=[MedicineInfo(
            name='Paracetamol',
            strength='500mg',
            frequency='วันละ 3 ครั้ง หลักอาหาร'
        )]
    )

@fixture
def new_patient(registrar, vital_signs, registered_address, current_address):
    return registrar.register_new_patient(
        national_id=NationalID(id='1234567890123'),
        first_name=Name(value='นนทพัฒน์'),
        last_name=Name(value='คนสุขภาพดี'),
        phone_number=PhoneNumber(value='0123456789'),
        date_of_birth=DateOfBirth(year=1990, month=12, day=31),
        registered_address=registered_address,
        current_address=current_address,
        rights=Rights(rights_type=PatientRights.SOCIAL_SECURITY)
    )

@fixture
def new_staff_doctor():
    return Staff.register(
        username_str="nattapong-top",
        password_str="Paa-TopIT_12123", # ส่งรหัสสดเข้าไป
        national_id_str="1234567890123",
        first_name_str="ณัฐพงศ์",
        last_name_str="คนรักษาดี",
        dob_year=1990, dob_month=12, dob_day=31,
        phone_number_str="0999999999",
        role=StaffRole.DOCTOR
    )

@fixture
def new_staff_nurse():
    return Staff.register(
        username_str="nontanan-nan",
        password_str="nontanan_12123", # ส่งรหัสสดเข้าไป
        national_id_str="1234567890123",
        first_name_str="นนทนัน",
        last_name_str="พยาบาลดี",
        dob_year=1998, dob_month=1, dob_day=31,
        phone_number_str="0888888888",
        role=StaffRole.NURSE
    )

@fixture
def InMem_staff_repo():
    return InMemoryStaffRepository()

@fixture
def staff_service(InMem_staff_repo):
    return StaffService(InMem_staff_repo)

@fixture
def new_register_staff(staff_service):
    new_staff = staff_service.register_staff(
        username_str="nattapong-top",
        password_str="Paa-TopIT_12123",  # ส่งรหัสสดเข้าไป
        national_id_str="1234567890123",
        first_name_str="ณัฐพงศ์",
        last_name_str="คนรักษาดี",
        dob_year=1990, dob_month=12, dob_day=31,
        phone_number_str="0999999999",
        role=StaffRole.DOCTOR
    )
    return new_staff



@fixture
def new_consultation(new_queue, new_staff_doctor):
    return Consultation(
        queue_id=new_queue.id,
        doctor=new_staff_doctor,
        patient_id=new_queue.patient_id,
        vital_signs=new_queue.vital_signs,
    )


@fixture
def valid_patient_payload():
    return {
        "national_id": "1234567890123",
        "first_name": "นนทพัฒน์",
        "last_name": "ใจดี",
        "phone_number": "0812345678",
        "dob_year": 1990, "dob_month": 5, "dob_day": 20,
        "registered_address": {
            "house_number": "1/1", "street": "ราชดำเนิน",
            "sub_district": "บวรนิเวศ", "district": "พระนคร",
            "province": "กรุงเทพมหานคร", "postal_code": "10200"
        },
        "current_address": {
            "house_number": "99/9", "street": "สุขุมวิท",
            "sub_district": "คลองเตย", "district": "คลองเตย",
            "province": "กรุงเทพมหานคร", "postal_code": "10110"
        },
        "rights_type": "ประกันสังคม"
    }

@fixture
def api_new_queues(client, valid_patient_payload):
    reg_res = client.post('/api/patients/register', json=valid_patient_payload)
    new_patient_id = reg_res.json()['id']

    triage_payload = {
        "patient_id": new_patient_id,
        "vitals": {
            "systolic": 120, "diastolic": 80,
            "weight": 70.5, "height": 175.0,
            "temperature": 36.5,
            "symptom": "ปวดหัว ตัวร้อน"
        }
    }
    # ออกคิว ส่ง ข้อมูลสัญญาชีพและซักประวัติ
    new_queue = client.post('/api/triage', json=triage_payload)
    return new_queue

@fixture
def diagnosis_payload(diagnosis):
    diagnosis_payload = {
        "disease": "ไข้หวัดใหญ่ สายพันธุ์ A",
        "treatment": "พักผ่อนเยอะๆ และทานยาตามอาการ",
        "medicine_prescribed": [
            {
                "name": "Tamiflu",
                "strength": "75mg",
                "frequency": "เช้า-เย็น หลังอาหาร"
            }
        ]
    }
    return diagnosis_payload