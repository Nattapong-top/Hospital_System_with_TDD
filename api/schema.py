from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from domain.value_object import PatientRights, Province, QueueStatus

# ==========================================
# 1. BASE SCHEMAS (สำหรับใช้สืบทอดเพื่อลดโค้ดซ้ำตามหลัก DRY)
# ==========================================

class PersonalInfoBase(BaseModel):
    """ข้อมูลส่วนบุคคลพื้นฐาน ใช้ร่วมกันทั้งตอนสมัครพนักงานและลงทะเบียนคนไข้"""
    national_id: str = Field(..., min_length=13, max_length=13, description="เลขบัตรประชาชน 13 หลัก")
    first_name: str
    last_name: str
    phone_number: str
    dob_year: int
    dob_month: int
    dob_day: int

class StaffInfoBase(BaseModel):
    """ข้อมูลพื้นฐานของพนักงานในระบบ"""
    staff_id: UUID
    username: str
    first_name: str
    last_name: str
    phone_number: str
    role: str

class TokenBaseResponse(BaseModel):
    """โครงสร้างพื้นฐานของ JWT Token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class ConsultationBaseResponse(BaseModel):
    """โครงสร้างพื้นฐานขากลับของระบบคิวและการตรวจ"""
    consultation_id: UUID
    queue_id: UUID
    patient_id: UUID
    status: QueueStatus


# ==========================================
# 2. ADDRESS SCHEMAS
# ==========================================

class AddressSchema(BaseModel):
    house_number: str
    street: str
    sub_district: str
    district: str
    province: Province
    postal_code: str


# ==========================================
# 3. STAFF / AUTH SCHEMAS
# ==========================================

class RegisterStaffRequest(PersonalInfoBase):
    """รับข้อมูลเพื่อลงทะเบียนพนักงานใหม่"""
    username: str = Field(..., min_length=4, description="ชื่อผู้ใช้งาน")
    password: str = Field(..., min_length=6, description="รหัสผ่าน")
    role: str

class StaffRegisterResponse(StaffInfoBase):
    is_active: bool

class StaffLoginRequest(BaseModel):
    username: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class StaffLoginResponse(TokenBaseResponse, StaffInfoBase):
    """พ่นข้อมูลกลับหลังพนักงาน Login สำเร็จ (รวมทั้ง Token และข้อมูลส่วนตัว)"""
    is_active: bool

class TokenRefreshResponse(TokenBaseResponse):
    """ส่งกุญแจชุดใหม่กลับไปเมื่อมีการขอ Refresh Token"""
    pass

class StaffProfileResponse(StaffInfoBase):
    """ข้อมูลหน้าตาโปรไฟล์สำหรับ Endpoint /me"""
    message: str = "ดึงข้อมูลโปรไฟล์สำเร็จ!"


# ==========================================
# 4. PATIENT SCHEMAS
# ==========================================

class RegisterRequest(PersonalInfoBase):
    """รับข้อมูลลงทะเบียนคนไข้ใหม่"""
    registered_address: AddressSchema
    current_address: AddressSchema
    rights_type: PatientRights

class PatientRegisterResponse(PersonalInfoBase):
    id: UUID
    message: str = "ลงทะเบียนสำเร็จ!"



# ==========================================
# 5. VITAL SIGNS / TRIAGE SCHEMAS
# ==========================================

class VitalSignsSchema(BaseModel):
    systolic: int
    diastolic: int
    weight: float
    height: float
    temperature: float
    symptom: str

class TriageRequest(BaseModel):
    patient_id: UUID
    vitals: Optional[VitalSignsSchema] = None


# ==========================================
# 6. EXAMINATION / CONSULTATION SCHEMAS
# ==========================================

class ExamRequestSchema(BaseModel):
    queue_id: UUID
    staff_id: UUID

class ExamResponseSchema(ConsultationBaseResponse):
    doctor_id: UUID

class CancelRequestSchema(BaseModel):
    consultation_id: UUID
    staff_id: UUID

class CancelResponseSchema(ConsultationBaseResponse):
    staff_id: UUID

class MedicineInfoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    strength: str
    frequency: str

class DiagnosisSchema(BaseModel):
    disease: str
    treatment: str
    medicine_prescribed: list[MedicineInfoSchema]

class FinishRequestSchema(BaseModel):
    consultation_id: UUID
    doctor_id: UUID
    diagnosis: DiagnosisSchema

class ExamFinishResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    consultation_id: UUID
    queue_id: UUID
    patient_id: UUID
    doctor_id: UUID
    disease: str
    treatment: str
    medicines: list[MedicineInfoSchema]
    finished_at: datetime