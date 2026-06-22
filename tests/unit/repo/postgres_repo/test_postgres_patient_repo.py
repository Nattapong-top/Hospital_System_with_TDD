import pytest
from uuid import uuid4

from domain.custom_error import ConcurrentUpdateError, DuplicateNationalIDError
from domain.value_object import (
    NationalID,
    Name,
)
from infrastructure.postgres_patient_repository import PostgresPatientRepository

# ---------------------------------------------------------
# 2. TEST CASES (เริ่มทดสอบ)
# ---------------------------------------------------------


def test_save_new_patient_successfully(pg_patient_table, dummy_patient):
    # Arrange: เตรียม Repository (ตรงนี้แหละที่จะ Error เพราะเรายังไม่ได้สร้างคลาส)
    repo = PostgresPatientRepository(pg_patient_table)

    # Act: สั่งบันทึกข้อมูล
    repo.save(dummy_patient)

    # Assert: ดึงข้อมูลจากฐานข้อมูลตรงๆ มาเช็คว่าบันทึกลงไปจริงไหม
    with pg_patient_table.cursor() as cur:
        cur.execute(
            "SELECT id, national_id, first_name FROM patient WHERE id = %s;",
            (str(dummy_patient.id),),
        )
        result = cur.fetchone()

    assert result is not None, "ต้องเจอข้อมูลใน Database"
    assert result[1] == "1234567890123"
    assert result[2] == "สมชาย"


def test_get_patient_national_id_successfully(pg_patient_table, dummy_patient):
    repo = PostgresPatientRepository(pg_patient_table)
    repo.save(dummy_patient)

    target_national_id = NationalID(id="1234567890123")
    retrieved_patient = repo.get_by_national_id(target_national_id)

    assert retrieved_patient is not None
    assert retrieved_patient.id == dummy_patient.id
    assert retrieved_patient.national_id.id == "1234567890123"
    assert retrieved_patient.first_name.value == "สมชาย"


def test_update_patient_first_name_successfully(pg_patient_table, dummy_patient):
    repo = PostgresPatientRepository(pg_patient_table)
    repo.save(dummy_patient)

    dummy_patient.update_first_name(Name(value="สมปอง"))

    repo.update(dummy_patient)
    updated_patient = repo.get_by_national_id(dummy_patient.national_id)

    assert updated_patient is not None
    assert updated_patient.national_id == dummy_patient.national_id
    assert updated_patient.first_name.value == "สมปอง"
    assert updated_patient.version.number == 2


def test_update_patient_raise_concurrent_update_error_when_old_version(
    pg_patient_table, dummy_patient
):
    repo = PostgresPatientRepository(pg_patient_table)
    repo.save(dummy_patient)

    nurse_a = repo.get_by_national_id(dummy_patient.national_id)
    if nurse_a:
        nurse_a.update_first_name(Name(value="พยาบาลเอ"))
        repo.update(nurse_a)

    dummy_patient.update_first_name(Name(value="พยาบาลบี"))

    with pytest.raises(ConcurrentUpdateError) as exc_info:
        repo.update(dummy_patient)

    assert "อัปเดตข้อมูลไป" in str(exc_info.value)


def test_get_by_national_id_not_found_should_return_none(pg_patient_table):
    repo = PostgresPatientRepository(pg_patient_table)
    result = repo.get_by_national_id(NationalID(id="1111111111111"))
    assert result is None


def test_save_duplicate_national_id_should_raise_error(pg_patient_table, dummy_patient):
    repo = PostgresPatientRepository(pg_patient_table)
    repo.save(dummy_patient)

    patient_with_same_nid = dummy_patient.model_copy(update={"id": uuid4()})

    with pytest.raises(DuplicateNationalIDError) as e:
        repo.save(patient_with_same_nid)

    assert "เลขบัตรประชาชนนี้มีในระบบแล้ว" in str(e.value)
