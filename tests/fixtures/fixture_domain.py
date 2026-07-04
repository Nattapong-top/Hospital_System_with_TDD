import uuid
from datetime import datetime, date

from pytest import fixture

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
        version=Version.initial(),
    )


@fixture
def dummy_patient() -> Patient:
    """สร้าง Mock Data ของ Patient สำหรับใช้ใน Test"""
    return Patient(
        id=uuid.uuid4(),
        national_id=NationalID(id="1234567890123"),
        first_name=Name(value="สมชาย"),
        last_name=Name(value="ใจดี"),
        phone_number=PhoneNumber(value="0812345678"),
        date_of_birth=DateOfBirth(day=1, month=1, year=1990),
        registered_address=Address(
            house_number="123",
            sub_district="บางกะปิ",
            district="บางกะปิ",
            province=Province.BANGKOK,
            postal_code="10240",
        ),
        current_address=Address(
            house_number="123",
            sub_district="บางกะปิ",
            district="บางกะปิ",
            province=Province.BANGKOK,
            postal_code="10240",
        ),
        rights=Rights(rights_type=PatientRights.GOLD_CARD),
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
        version=Version.initial(),
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
