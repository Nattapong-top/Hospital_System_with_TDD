from pydantic import BaseModel, Field


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
