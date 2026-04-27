from uuid import uuid4, UUID

from pytest import raises

from domain.custom_error import DoNotChangeIDError
from domain.value_object import StaffRole, HashedPassword


def test_staff_create_valid_should_success(new_staff_doctor):
    staff = new_staff_doctor
    assert isinstance(staff.staff_id, UUID)
    assert staff.username.id == 'nattapong-top'
    assert staff.national_id.id == '1234567890123'
    assert staff.first_name.value == 'ณัฐพงศ์'
    assert staff.role == StaffRole.DOCTOR

def test_staff_whit_update_staff_id_should_raise_error_not_change(new_staff_doctor):
    change_id = uuid4()
    staff =  new_staff_doctor
    with raises(DoNotChangeIDError):
        staff.staff_id = change_id

def test_staff_whit_password_should_hashed_password_and_verify_valid(new_staff_doctor):
    staff = new_staff_doctor
    assert staff.username.id == 'nattapong-top'
    # 1. เช็คว่าเป็น Object ประเภท HashedPassword จริงไหม
    assert isinstance(staff.hashed_password, HashedPassword)
    # 2. เช็คว่ามัน "ไม่ใช่" รหัสผ่านตัวจริง (ต้องปั่นแล้ว)
    assert staff.hashed_password.value != "Paa-TopIT_12123"
    # 3. ไฮไลท์: ใช้เมธอด .verify() เช็คว่ารหัสจริง "ไข" รหัสในเครื่องได้ไหม (สมมติว่าใน fixture ป๋าตั้งรหัสไว้ว่า
    # Paa-TopIT_12123)
    assert staff.hashed_password.verify("Paa-TopIT_12123") is True
    # 4. ลองส่งรหัสผิดเข้าไป ต้องคืนค่า False
    assert staff.hashed_password.verify("wrong_password") is False