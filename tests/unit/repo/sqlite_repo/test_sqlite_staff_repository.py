from domain.hospital_registry import HospitalRegistry
from domain.domain_service.staff_service import StaffService
from domain.staff_entities import Staff
from domain.value_object import StaffRole


def test_staff_repo_should_save_and_get_staff_success(new_staff_doctor):
    staff_service = HospitalRegistry.staff_service()
    staff_service.staff_repo.save(new_staff_doctor)
    staff_db = staff_service.staff_repo.get_by_staff_id(new_staff_doctor.staff_id)

    assert isinstance(staff_service, StaffService)
    assert isinstance(staff_db, Staff)
    assert staff_db is not None
    assert staff_db.staff_id == new_staff_doctor.staff_id
    # 🚩 เพิ่มการตรวจฟิลด์อื่นๆ เพื่อการันตีว่า Mapper เราทำงานเป๊ะ!
    assert staff_db.username.id == new_staff_doctor.username.id
    assert staff_db.national_id.id == new_staff_doctor.national_id.id
    assert staff_db.first_name.value == new_staff_doctor.first_name.value
    assert staff_db.role.value == new_staff_doctor.role.value


def test_staff_service_register_staff_should_return_staff():
    staff_service = HospitalRegistry.staff_service()
    new_staff = staff_service.register_staff(
        username_str="nattapong-top",
        password_str="Paa-TopIT_12123",  # ส่งรหัสสดเข้าไป
        national_id_str="1234567890123",
        first_name_str="ณัฐพงศ์",
        last_name_str="คนรักษาดี",
        dob_year=1990,
        dob_month=12,
        dob_day=31,
        phone_number_str="0999999999",
        role=StaffRole.DOCTOR,
    )
    assert new_staff.username.id == "nattapong-top"
    assert new_staff.first_name.value == "ณัฐพงศ์"

    db_staff = staff_service.get_by_username(username_str="nattapong-top")
    assert isinstance(db_staff, Staff)
    assert db_staff.staff_id == new_staff.staff_id
    assert db_staff.username.id == new_staff.username.id
