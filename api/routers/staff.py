from fastapi import APIRouter, HTTPException

from api.schema import (
    RegisterStaffRequest,
    StaffLoginRequest,
    StaffLoginResponse,
    RefreshTokenRequest,
    TokenRefreshResponse,
)
from domain.hospital_registry import HospitalRegistry
from domain.value_object import StaffRole
from infrastructure.auth.jwt_service import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
)

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
        raise HTTPException(status_code=400, detail="Role ต้องเป็น DOCTOR หรือ NURSE")

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


@router.post("/login", response_model=StaffLoginResponse)
def api_staff_login(login_request: StaffLoginRequest) -> StaffLoginResponse:

    staff_service = HospitalRegistry.staff_service()

    valid_login = staff_service.authenticate_staff(
        username_str=login_request.username,
        plain_password=login_request.password,
    )

    token_data = {"sub": str(valid_login.staff_id), "role": valid_login.role.value}

    return StaffLoginResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        staff_id=valid_login.staff_id,
        username=valid_login.username.id,
        first_name=valid_login.first_name.value,
        role=valid_login.role.value,
        is_active=valid_login.is_active,
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh_access_token(request: RefreshTokenRequest) -> TokenRefreshResponse:
    payload = decode_access_token(request.refresh_token)

    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Token ไม่ถูกต้องหรือหมดอายุแล้ว")

    token_data = {"sub": payload["sub"], "role": payload.get("role")}

    return TokenRefreshResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )
