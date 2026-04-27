import uuid

from pytest import raises

from domain.custom_error import DuplicateNationalIDError
from domain.value_object import (
    NationalID, Name, PhoneNumber)


# --- Test Cases: ไล่บี้ตั้งแต่ปกติจนถึงเคสแปลกๆ ---
def test_sql_patient_repository_should_save_retrieve_patient_when_info_valid(patient_repo, patient):
    """CASE 1: เซฟได้-ดึงได้ (Happy Path)"""
    patient_repo.save(patient=patient)
    assert patient_repo is not None

    retrieved = patient_repo.get_by_national_id(national_id=patient.national_id)
    assert retrieved is not None
    assert retrieved.national_id == patient.national_id
    assert retrieved == patient # Entity ต้องหน้าตาเหมือนเดิมเป๊ะ


def test_sql_patient_repository_should_raise_error_when_duplicate_national_id(patient_repo, patient):
    """CASE 2: ป้องกันเลขบัตรซ้ำ (Integrity Check)"""
    patient_repo.save(patient=patient)

    # สร้างคนใหม่ (ID ใหม่) แต่ใช้เลขบัตรเดิม
    duplicate_patient = patient.model_copy(update={'id': uuid.uuid4()})

    with raises(DuplicateNationalIDError) as error:
        patient_repo.save(patient=duplicate_patient)
    assert 'เลขบัตรประชาชนนี้มีในระบบแล้ว' in str(error.value)


def test_sql_patient_repository_should_return_none_when_patient_not_found(patient_repo, patient):
    """CASE 3: คืนค่า None เมื่อหาคนไข้ไม่เจอ (Sad Path)"""
    not_found = patient_repo.get_by_national_id(NationalID(id='0000000000000'))
    assert not_found is None


def test_sql_patient_repository_handle_special_characters_and_long_strings(patient_repo, patient):
    """CASE 4: รองรับชื่อยาวและอักขระพิเศษ (Edge Case)"""
    complex_name = Name(value="สมชาย 'สายฟ้า' มหานคร-อัครสถาน & *")
    patient.first_name = complex_name

    # อัปเดตที่อยู่ผ่าน model_copy เพราะเป็น Frozen Instance
    new_address = patient.registered_address.model_copy(
        update= {'street': "ถนน ๑๒๓/๔๕๖ (พิเศษ) & * ^ % $ # @"}
    )
    patient.registered_address = new_address

    patient_repo.save(patient=patient)
    assert patient_repo is not None

    retrieved = patient_repo.get_by_national_id(national_id=patient.national_id)
    assert retrieved.registered_address.street == new_address.street
    assert retrieved.first_name.value == complex_name.value

def test_sql_patient_repository_should_save_retrieve_patient_with_version(patient_repo, patient):
    patient_repo.save(patient=patient)
    retrieved = patient_repo.get_by_national_id(patient.national_id)

    assert retrieved is not None
    assert retrieved == patient
    assert retrieved.version.number == 1

def test_sql_patient_repository_should_update_phone_number_and_increment_version(patient_repo, patient):
    patient_repo.save(patient=patient)
    new_phone = PhoneNumber(value='0999999999')

    patient.update_phone_number(new_phone)
    patient_repo.update(patient=patient)

    updated = patient_repo.get_by_national_id(national_id=patient.national_id)
    assert updated.phone_number.value == '0999999999'
    assert updated.version.number == 2

def test_sql_patient_repository_should_raise_error_when_concurrency_conflict(patient_repo, patient):
    patient_repo.save(patient=patient)

    nurse_a_view = patient_repo.get_by_national_id(national_id=patient.national_id)
    nurse_b_view = patient_repo.get_by_national_id(national_id=patient.national_id)

    nurse_a_view.update_first_name(Name(value="สมชาย 'สายฟ้า' มหานคร-อัครสถาน & *"))
    patient_repo.update(nurse_a_view)

    nurse_b_view.update_first_name(Name(value="มหานครอัครสถาน"))

    with raises(RuntimeError) as error:
        patient_repo.update(nurse_b_view)

    assert 'update' in str(error.value)