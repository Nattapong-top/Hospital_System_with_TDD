from uuid import UUID

from pytest import raises

from domain.custom_error import DuplicateUsernameError
from domain.domain_service.staff_service import StaffService
from domain.hospital_registry import HospitalRegistry
from domain.value_object import StaffRole, HashedPassword
from tests.conftest import new_register_staff, InMem_staff_repo


def test_staff_service_register_new_staff_should_succeed(InMem_staff_repo):
    new_staff = StaffService(InMem_staff_repo).register_staff(
        username_str="nattapong-top",
        password_str="Paa-TopIT_12123",  # ส่งรหัสสดเข้าไป
        national_id_str="1234567890123",
        first_name_str="ณัฐพงศ์",
        last_name_str="คนรักษาดี",
        dob_year=1990, dob_month=12, dob_day=31,
        phone_number_str="0999999999",
        role=StaffRole.DOCTOR
    )
    assert new_staff.username.id == "nattapong-top"
    assert new_staff.national_id.id == '1234567890123'
    assert isinstance(new_staff.hashed_password, HashedPassword)
    assert new_staff.hashed_password.value != "Paa-TopIT_12123"
    assert new_staff.role == StaffRole.DOCTOR


def test_staff_service_register_staff_with_staff_id_should_type_uuid_valid(new_register_staff,
                                                                           InMem_staff_repo):
    staff_1 = new_register_staff
    staff_2 = StaffService(InMem_staff_repo).register_staff(
        username_str="PaaTop-IT",
        password_str="Paa-TopIT_12123",  # ส่งรหัสสดเข้าไป
        national_id_str="1234567890123",
        first_name_str="ณัฐพงศ์",
        last_name_str="คนรักษาดี",
        dob_year=1990, dob_month=12, dob_day=31,
        phone_number_str="0999999999",
        role=StaffRole.DOCTOR
    )

    assert staff_1.staff_id is not None
    assert staff_2.staff_id is not None
    assert isinstance(staff_1.staff_id, UUID)
    assert staff_1.staff_id != staff_2.staff_id



def test_staff_service_register_staff_should_save_to_repo_success():
    service = HospitalRegistry.staff_service()
    new_staff = service.register_staff(
        username_str="nattapong-top",
        password_str="Paa-TopIT_12123",  # ส่งรหัสสดเข้าไป
        national_id_str="1234567890123",
        first_name_str="ณัฐพงศ์",
        last_name_str="คนรักษาดี",
        dob_year=1990, dob_month=12, dob_day=31,
        phone_number_str="0999999999",
        role=StaffRole.DOCTOR
    )
    db_staff = service.get_by_username(new_staff.username.id)
    assert db_staff is not None
    assert new_staff == db_staff


def test_staff_service_register_staff_with_duplicate_username_should_error(new_register_staff, staff_service,
                                                                           InMem_staff_repo):
    with raises(DuplicateUsernameError) as err:
        staff_service.register_staff(
            username_str="nattapong-top",
            password_str="Paa-TopIT_12123",  # ส่งรหัสสดเข้าไป
            national_id_str="1234567890123",
            first_name_str="ณัฐพงศ์",
            last_name_str="คนรักษาดี",
            dob_year=1990, dob_month=12, dob_day=31,
            phone_number_str="0999999999",
            role=StaffRole.DOCTOR
        )

    assert 'มีคนใช้แล้ว' in str(err.value)


def test_staff_service_with_authenticate_should_return_staff_when_credential_are_correct(new_register_staff,
                                                                                         staff_service):
    staff = new_register_staff
    auth_staff = staff_service.authenticate_staff(
        username_str='nattapong-top',
        plain_password="Paa-TopIT_12123")

    assert auth_staff is not None
    assert auth_staff.username.id == staff.username.id
    assert auth_staff.hashed_password.value != "Paa-TopIT_12123"
    assert isinstance(auth_staff.hashed_password, HashedPassword)


def test_staff_service_with_authenticate_should_return_none_when_are_password_incorrect(new_register_staff,
                                                                                        staff_service):
    auth_staff = staff_service.authenticate_staff(
        username_str='nattapong-top',
        plain_password="Paa-Top_No_IT_5555"
    )
    assert auth_staff is None


def test_staff_service_with_authenticate_should_return_none_when_are_username_incorrect(new_register_staff,
                                                                                        staff_service):
    auth_staff = staff_service.authenticate_staff(
        username_str='Top_No_IT',
        plain_password="Paa-TopIT_12123"
    )
    assert auth_staff is None


def test_staff_service_with_authenticate_should_return_none_when_is_active_false(staff_service):
    # 1. สมัครพนักงานใหม่เลย ใช้เลขบัตรและ Username ที่ "ไม่ซ้ำ" กับเทสข้ออื่น
    staff = staff_service.register_staff(
        username_str="banned_doctor_999",  # 🚩 เปลี่ยนชื่อไม่ให้ซ้ำ
        password_str="Paa-TopIT_12123",
        national_id_str="9999999978999",  # 🚩 เปลี่ยนเลขบัตรไม่ให้ซ้ำ
        first_name_str="หมอโดน",
        last_name_str="แบน",
        dob_year=1990, dob_month=12, dob_day=31,
        phone_number_str="0999999999",
        role=StaffRole.DOCTOR
    )

    # ตอนนี้มั่นใจได้ 100% ว่ามีหมอคนนี้อยู่ใน DB แน่นอนและเวอร์ชันเป็น 1
    assert staff.version.number == 1

    # 2. สั่งแบนใน Memory
    staff.is_active = False

    # 3. สั่ง Update ลงตู้เหล็ก
    staff_service.update(staff)

    # 4. ลองล็อกอินด้วยรหัสสด
    auth_staff = staff_service.authenticate_staff(
        username_str="banned_doctor_999",
        plain_password="Paa-TopIT_12123"
    )

    # 5. ต้องเข้าไม่ได้ (return None)
    assert auth_staff is None
