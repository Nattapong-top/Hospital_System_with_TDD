from uuid import UUID
from domain.custom_error import (
    DuplicateUsernameError,
    InvalidCredentialsError,
    AccountSuspendedError,
)
from domain.staff_entities import Staff
from domain.value_object import Username
from infrastructure.sqllite_staff_repository import SqlStaffRepository


class StaffService:
    def __init__(self, staff_repo: SqlStaffRepository) -> None:
        self.staff_repo = staff_repo

    def register_staff(
        self,
        username_str: str,
        password_str: str,
        national_id_str: str,
        first_name_str: str,
        last_name_str: str,
        dob_year: int,
        dob_month: int,
        dob_day: int,
        phone_number_str: str,
        role,
    ) -> Staff:
        """ลงทะเบียนพนักงานใหม่"""
        # 1. ตรวจสอบว่าชื่อผู้ใช้ซ้ำไหม
        self._check_duplicate_username(username_str)

        # 2. ให้ Entity จัดการแปลงข้อมูลดิบเป็น Domain Object
        new_staff = Staff.register(
            username_str=username_str,
            password_str=password_str,
            national_id_str=national_id_str,
            first_name_str=first_name_str,
            last_name_str=last_name_str,
            dob_year=dob_year,
            dob_month=dob_month,
            dob_day=dob_day,
            phone_number_str=phone_number_str,
            role=role,
        )

        # 3. บันทึกลงตู้เหล็ก
        self.staff_repo.save(new_staff)
        return new_staff

    def authenticate_staff(self, username_str: str, plain_password: str) -> Staff:
        """ยืนยันตัวตนพนักงาน (Login)"""
        staff = self.get_by_username(username_str)

        if not staff or not staff.hashed_password.verify(plain_password):
            raise InvalidCredentialsError()

        if not staff.is_active:
            raise AccountSuspendedError()

        return staff

    def suspend_staff(self, staff_id: UUID) -> None:
        """ระงับสิทธิ์การใช้งานพนักงาน (สั่งแบน)"""
        staff = self._get_staff_or_raise(staff_id)

        # 🚩 สั่งให้พนักงานจัดการตัวเอง (Entity จะเปลี่ยน is_active และบวก Version เอง)
        staff.suspend()

        # บันทึกการเปลี่ยนแปลง
        self.staff_repo.update(staff)

    def reactivate_staff(self, staff_id: UUID) -> None:
        """คืนสิทธิ์การใช้งานพนักงาน (ปลดแบน)"""
        staff = self._get_staff_or_raise(staff_id)

        # 🚩 สั่งให้พนักงานจัดการตัวเอง
        staff.reactivate()

        self.staff_repo.update(staff)

    def get_by_username(self, username_str: str) -> Staff | None:
        """ค้นหาพนักงานด้วยชื่อผู้ใช้"""
        valid_username = Username(id=username_str)
        return self.staff_repo.get_by_username(valid_username.id)

    def get_by_staff_id(self, staff_id: UUID) -> Staff | None:
        return self.staff_repo.get_by_staff_id(staff_id)

    def update(self, staff: Staff) -> None:
        """อัปเดตข้อมูลพนักงาน (ใช้กรณีทั่วไป)"""
        self.staff_repo.update(staff)

    # --- Private Helpers ---

    def _check_duplicate_username(self, username_str: str) -> None:
        if self.get_by_username(username_str):
            raise DuplicateUsernameError(f"ชื่อ {username_str} มีคนใช้แล้ว")

    def _get_staff_or_raise(self, staff_id: UUID) -> Staff:
        staff = self.staff_repo.get_by_staff_id(staff_id)
        if not staff:
            raise ValueError(f"ไม่พบพนักงานรหัส {staff_id} ในระบบ")
        return staff
