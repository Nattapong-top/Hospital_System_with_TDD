import pytest
import psycopg
from uuid import uuid4
from testcontainers.postgres import PostgresContainer

from domain.entities import Patient
from domain.value_object import (
    NationalID,
    Name,
    PhoneNumber,
    DateOfBirth,
    Address,
    Rights,
    PatientRights,
    Province,
)
from infrastructure.postgres_patient_repository import PostgresPatientRepository

# ---------------------------------------------------------
# 1. SETUP FIXTURES (เตรียมสภาพแวดล้อม)
# ---------------------------------------------------------


@pytest.fixture(scope="module")
def postgres_container():
    """สร้าง PostgreSQL Container 1 ครั้ง ใช้ร่วมกันทั้งไฟล์เพื่อความรวดเร็ว"""
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres


@pytest.fixture
def db_connection(postgres_container):
    """จัดการ Connection และสร้าง Schema ก่อนรันแต่ละ Test"""
    raw_url = postgres_container.get_connection_url()
    db_url = raw_url.replace("+psycopg2", "")

    with psycopg.connect(db_url) as conn:
        # เรียกใช้ create_schema ผ่านตัว Repository ได้เลย
        repo = PostgresPatientRepository(conn)
        repo.create_schema()

        with conn.cursor() as cur:
            # ล้างข้อมูลก่อนรันเทสต์ทุกครั้ง
            cur.execute("TRUNCATE TABLE patient;")
        conn.commit()

        yield conn


@pytest.fixture
def dummy_patient() -> Patient:
    """สร้าง Mock Data ของ Patient สำหรับใช้ใน Test"""
    return Patient(
        id=uuid4(),
        national_id=NationalID(id="1234567890123"),
        first_name=Name(value="สมชาย"),
        last_name=Name(value="ใจดี"),
        phone_number=PhoneNumber(value="0812345678"),
        date_of_birth=DateOfBirth(day=1, month=1, year=1990),
        registered_address=Address(
            house_number="123",
            sub_district="บางกะปิ",
            district="บางกะปิ",
            province=Province.BANGKOK,
            postal_code="10240",
        ),
        current_address=Address(
            house_number="123",
            sub_district="บางกะปิ",
            district="บางกะปิ",
            province=Province.BANGKOK,
            postal_code="10240",
        ),
        rights=Rights(rights_type=PatientRights.GOLD_CARD),
    )


# ---------------------------------------------------------
# 2. TEST CASES (เริ่มทดสอบ)
# ---------------------------------------------------------


def test_save_new_patient_successfully(db_connection, dummy_patient):
    # Arrange: เตรียม Repository (ตรงนี้แหละที่จะ Error เพราะเรายังไม่ได้สร้างคลาส)
    repo = PostgresPatientRepository(db_connection)

    # Act: สั่งบันทึกข้อมูล
    repo.save(dummy_patient)

    # Assert: ดึงข้อมูลจากฐานข้อมูลตรงๆ มาเช็คว่าบันทึกลงไปจริงไหม
    with db_connection.cursor() as cur:
        cur.execute(
            "SELECT id, national_id, first_name FROM patient WHERE id = %s;",
            (str(dummy_patient.id),),
        )
        result = cur.fetchone()

    assert result is not None, "ต้องเจอข้อมูลใน Database"
    assert result[1] == "1234567890123"
    assert result[2] == "สมชาย"


def test_get_patient_national_id_successfully(db_connection, dummy_patient):
    repo = PostgresPatientRepository(db_connection)
    repo.save(dummy_patient)

    target_national_id = NationalID(id="1234567890123")
    retrieved_patient = repo.get_by_national_id(target_national_id)

    assert retrieved_patient is not None
    assert retrieved_patient.id == dummy_patient.id
    assert retrieved_patient.national_id.id == "1234567890123"
    assert retrieved_patient.first_name.value == "สมชาย"
