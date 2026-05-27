from fastapi import APIRouter, HTTPException

from api.schema import RegisterStaffRequest, StaffLoginRequest, StaffLoginResponse
from domain.hospital_registry import HospitalRegistry
from domain.value_object import StaffRole

# สร้าง Router ประจำแผนก (prefix จะไปแปะหน้า URL ทุกตัวในไฟล์นี้)
router = APIRouter(prefix="/api/staff", tags=["Staff"])


# 🚩 สังเกตตรงนี้! เปลี่ยนจาก @app.post เป็น @router.post
# และตัดคำว่า /api/staff ออก (เพราะมันมีใน prefix แล้ว)
@router.post("/register")
def api_register_new_staff(request: RegisterStaffRequest):
    staff_service = HospitalRegistry.staff_service()
    try:
        staff_role = StaffRole[request.role.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400, detail="Ro   le ต้องเป็น DOCTOR หรือ NURSE"
        )

    new_staff = staff_service.register_staff(
        username_str=request.username,
        password_str=request.password,
        national_id_str=request.national_id,
        first_name_str=request.first_name,
        last_name_str=request.last_name,
        dob_year=request.dob_year,
        dob_month=request.dob_month,
        dob_day=request.dob_day,
        phone_number_str=request.phone_number,
        role=staff_role,
    )

    return {
        "staff_id": new_staff.staff_id,
        "username": new_staff.username.id,
        "first_name": new_staff.first_name.value,
        "role": new_staff.role.value,
        "is_active": new_staff.is_active,
    }


@router.post("/login")
def api_staff_login(login_request: StaffLoginRequest) -> StaffLoginResponse:

    staff_service = HospitalRegistry.staff_service()

    valid_login = staff_service.authenticate_staff(
        username_str=login_request.username,
        plain_password=login_request.password,
    )

    return StaffLoginResponse(
        staff_id=valid_login.staff_id,
        username=valid_login.username.id,
        first_name=valid_login.first_name.value,
        role=valid_login.role.value,
        is_active=valid_login.is_active,
    )
