from uuid import uuid4, UUID

from pydantic import Field

from domain.custom_error import DoNotChangeIDError
from domain.entities import DomainEntity
from domain.value_object import Name, PhoneNumber, DateOfBirth, Version, NationalID, StaffRole, \
    Username, HashedPassword


class Staff(DomainEntity):
    staff_id: UUID = Field(default_factory=uuid4)
    username: Username
    hashed_password: HashedPassword
    national_id: NationalID
    first_name: Name
    last_name: Name
    date_of_birth: DateOfBirth
    phone_number: PhoneNumber
    role: StaffRole
    version: Version = Field(default=Version(number=1))
    is_active: bool = Field(default=True)

    def __setattr__(self, name: str, value) -> None:
        # ป้องกันการเปลี่ยนค่า field ที่ห้ามแก้ไข
        # รันทุกครั้งที่มีการ set ค่า field ใดๆ ใน object นี้
        # hasattr เช็คว่า field นั้นมีค่าอยู่แล้วหรือยัง
        # (ถ้ายังไม่มี = กำลังสร้างครั้งแรก → ให้ผ่าน)
        if name in ('staff_id', 'national_id') and hasattr(self, name):
            raise DoNotChangeIDError(f'ห้ามเปลี่ยน {name} ครับ')

        # ถ้าไม่ใช่ field ต้องห้าม → ให้ Pydantic จัดการต่อตามปกติ
        super().__setattr__(name, value)

    @classmethod
    def register(
        cls,
        username_str: str,
        password_str: str,
        national_id_str: str,
        first_name_str: str,
        last_name_str: str,
        dob_year: int, dob_month: int, dob_day: int,
        phone_number_str: str,
        role: StaffRole,
    ) -> 'Staff':
        '''
        การลงทะเบียนเจ้าหน้าที่ใหม่ ทำหน้าที่แปลง 'ข้อมูลดิบ' ให้เป็น 'Domain Object' ที่ถูกต้อง
        '''
        return cls(
                username=Username(id=username_str),
                hashed_password=HashedPassword.create(password_str),
                national_id=NationalID(id=national_id_str),
                first_name=Name(value=first_name_str),
                last_name=Name(value=last_name_str),
                date_of_birth=DateOfBirth(year=dob_year, month=dob_month, day=dob_day),
                phone_number=PhoneNumber(value=phone_number_str),
                role=role,
            )