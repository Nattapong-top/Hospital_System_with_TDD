from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError

from domain.custom_error import MissingDiagnosisError
from domain.domain_service.patient_registrar import PatientRegistrar
from domain.entities import Patient
from domain.value_object import (
    PatientRights,
    Province,
    Address,
    NationalID,
    Name,
    PhoneNumber,
    DateOfBirth,
    Rights,
    VitalSigns,
    BloodPressure,
    Weight,
    Height,
    Temperature,
    Diagnosis,
    MedicineInfo,
)


# --- จุดบริการ (Endpoints) ---
class AddressSchema(BaseModel):
    house_number: str
    street: str
    sub_district: str
    district: str
    province: Province
    postal_code: str


# --- Pydantic Schemas สำหรับระบบพนักงาน ---
class RegisterStaffRequest(BaseModel):
    username: str = Field(..., min_length=4, description="ชื่อผู้ใช้งาน")
    password: str = Field(..., min_length=6, description="รหัสผ่าน")
    national_id: str = Field(..., min_length=13, max_length=13)  # บังคับ 13 หลัก
    first_name: str
    last_name: str
    dob_year: int
    dob_month: int
    dob_day: int
    phone_number: str
    role: str


# --- ข้อมูลรับเข้า (Request Schema) ---
class RegisterRequest(BaseModel):
    national_id: str
    first_name: str
    last_name: str
    phone_number: str
    dob_year: int
    dob_month: int
    dob_day: int
    registered_address: AddressSchema
    current_address: AddressSchema
    rights_type: PatientRights


# --- ข้อมูลสัญญาณชีพ (Schema) ---
class VitalSignsSchema(BaseModel):
    systolic: int
    diastolic: int
    weight: float
    height: float
    temperature: float
    symptom: str


# --- ข้อมูลรับเข้าสำหรับการออกคิว ---
class TriageRequest(BaseModel):
    patient_id: UUID  # ต้องส่ง ID ของคนไข้ที่ได้จากตอนลงทะเบียนมาด้วย
    vitals: Optional[VitalSignsSchema] = None


# 1. สร้างฟังก์ชันแปลงโฉม (Mapper)
# ให้มันรับ AddressSchema (ก้อนเล็ก) แล้วคืนค่าเป็น Address VO
def to_address_vo(addr_schema: AddressSchema) -> Address:
    return Address(
        house_number=addr_schema.house_number,
        street=addr_schema.street,
        sub_district=addr_schema.sub_district,
        district=addr_schema.district,
        province=addr_schema.province,
        postal_code=addr_schema.postal_code,
    )


def registrar_patient_detail(
    current_addr: Address,
    registered_addr: Address,
    registrar: PatientRegistrar,
    request: RegisterRequest,
) -> Patient:
    registered_patient = registrar.register_new_patient(
        national_id=NationalID(id=request.national_id),
        first_name=Name(value=request.first_name),
        last_name=Name(value=request.last_name),
        phone_number=PhoneNumber(value=request.phone_number),
        date_of_birth=DateOfBirth(
            year=request.dob_year, month=request.dob_month, day=request.dob_day
        ),
        registered_address=registered_addr,
        current_address=current_addr,
        rights=Rights(rights_type=request.rights_type),
    )
    return registered_patient


def _to_vital_signs_vo(request: TriageRequest) -> VitalSigns:
    vitals = VitalSigns(
        blood_pressure=BloodPressure(
            systolic=request.vitals.systolic, diastolic=request.vitals.diastolic
        ),
        weight=Weight(value=request.vitals.weight),
        height=Height(value=request.vitals.height),
        temperature=Temperature(value=request.vitals.temperature),
        symptom=request.vitals.symptom,
    )
    return vitals


def _prepare_diagnostic_vo(diagnosis_payload: dict) -> Diagnosis:
    # 🚩 เช็คเบื้องต้นก่อนส่งให้ Pydantic
    if not diagnosis_payload or not diagnosis_payload.get("disease"):
        raise MissingDiagnosisError()

    try:
        meds_data = diagnosis_payload.get("medicine_prescribed", [])
        meds = [MedicineInfo(**m) for m in meds_data]

        return Diagnosis(
            disease=diagnosis_payload.get("disease"),
            treatment=diagnosis_payload.get("treatment"),
            medicine_prescribed=meds,
        )
    except (ValidationError, TypeError, ValueError) as e:
        # พ่นเป็น Domain Error ออกไปแทน
        raise MissingDiagnosisError(f"ข้อมูลวินิจฉัยไม่ถูกต้อง: {str(e)}")
