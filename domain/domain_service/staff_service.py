from domain.interfaces import StaffRepository
from domain.staff_entities import Staff
from domain.value_object import Username, HashedPassword
from domain.custom_error import DuplicateUsernameError


class StaffService:
    def __init__(self, staff_repo: StaffRepository) -> None:
        self.staff_repo = staff_repo

    def register_staff(self,
                       username_str, password_str, national_id_str,
                       first_name_str, last_name_str, dob_year,
                       dob_month, dob_day, phone_number_str, role) -> Staff:

        self._chack_duplicate_username(username_str)

        new_staff = Staff.register(
            username_str=username_str,
            password_str=password_str,  # ส่งรหัสสดเข้าไป
            national_id_str=national_id_str,
            first_name_str=first_name_str,
            last_name_str=last_name_str,
            dob_year=dob_year, dob_month=dob_month, dob_day=dob_day,
            phone_number_str=phone_number_str,
            role=role
        )

        self.staff_repo.save(new_staff)
        return new_staff

    def _chack_duplicate_username(self, username_str) -> None:
        if self.staff_repo and self.staff_repo.get_by_username(Username(id=username_str)):
            raise DuplicateUsernameError(f'ชื่อ {username_str} มีคนใช้แล้ว')

    def authenticate_staff(self, username_str: str, plain_password: str) -> Optional[Staff]:
        """
        กระบวนการยืนยันตัวตนพนักงาน
        """
        # 1. ค้นหาพนักงานจาก Username
        staff = self.staff_repo.get_by_username(Username(id=username_str))

        # 2. ถ้าไม่พบพนักงาน หรือ พนักงานถูกระงับการใช้งาน (is_active = False)
        if not staff or not staff.is_active:
            return None  # หรือป๋าจะ raise Error ก็ได้ แต่ส่ง None จะปลอดภัยกว่าในแง่ข้อมูล

        # 3. ใช้ "กุญแจ" (plain_password) ไข "ตู้เซฟ" (hashed_password) นี่คือที่ที่เราเรียกใช้ .verify()
        # ที่เราเขียนไว้ใน VO ครับป๋า!
        if not staff.hashed_password.verify(plain_password):
            return None

        # 4. ถ้าทุกอย่างถูกต้อง ส่งตัวพนักงานกลับไปให้ระบบอื่นใช้งานต่อ (เช่น ไปออก Token)
        return staff
